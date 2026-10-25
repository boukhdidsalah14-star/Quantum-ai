import asyncio
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from deriv_client import DerivClient, DerivError
from strategy import MomentumStrategy

log = logging.getLogger(__name__)

class VeloxTelegram:
    def __init__(self, settings):
        self.s = settings
        self.client = None
        self.running = False
        self.monitor_task = None
        self.symbol_value = settings.default_symbol
        self.stake_value = settings.default_stake
        self.duration_value = settings.default_duration_minutes
        self.trading_mode = "OFF"  # OFF, DEMO, REAL
        self.last_tick = None
        self.last_signal = "No signal yet"
        self.daily_loss = 0.0
        self.consecutive_losses = 0
        self.day_key = time.strftime("%Y-%m-%d")

    def _roll_daily_counters(self):
        current_day = time.strftime("%Y-%m-%d")
        if current_day != self.day_key:
            self.day_key = current_day
            self.daily_loss = 0.0
            self.consecutive_losses = 0

    def allowed(self, update: Update) -> bool:
        user = update.effective_user
        return bool(user and user.id in self.s.allowed_user_ids)

    async def reply(self, update, text, **kwargs):
        if not self.allowed(update):
            if update.effective_message:
                await update.effective_message.reply_text("⛔ Unauthorized user.")
            return
        if update.effective_message:
            await update.effective_message.reply_text(text, **kwargs)

    async def initialize(self):
        # Public connection is optional; actual connection is created by /monitor.
        log.info("Velox Quantum initialized; trading is DISARMED.")

    async def shutdown(self):
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except (asyncio.CancelledError, Exception):
                pass
        if self.client:
            await self.client.close()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        keyboard = [[InlineKeyboardButton("📊 Status", callback_data="status")]]
        await self.reply(update,
            "⚛️ *VELOX QUANTUM*\n\n"
            "🟡 Engine: stopped\n🔒 Trading: DISARMED\n"
            "Use /monitor for live ticks and signals. No trades occur until explicitly armed.\n\n"
            "Commands: /status /balance /monitor /stop /stake 1 /duration 1 /symbol R_100 /arm_demo /disarm",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reply(update,
            "⚛️ *Velox Quantum commands*\n"
            "/status — engine state\n/balance — account balance\n"
            "/monitor — start live ticks and example signals\n/stop — stop engine\n"
            "/stake 1 — set stake (bounded by MAX_STAKE)\n"
            "/duration 1 — contract duration in minutes\n/symbol R_100 — market symbol\n"
            "/arm_demo — allow demo trades\n/arm_real — allow real trades only if enabled in .env\n"
            "/disarm — block new trades\n\n"
            "Binary options are high risk. The sample momentum rule is not a proven strategy.",
            parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        connected = bool(self.client and self.client.ws)
        mode = self.client.account_mode if self.client else "NOT CONNECTED"
        text = (
            "⚛️ *VELOX QUANTUM STATUS*\n\n"
            f"Connection: {'🟢 connected' if connected else '🔴 disconnected'}\n"
            f"Account mode: `{mode}`\n"
            f"Engine: {'🟢 running' if self.running else '⚪ stopped'}\n"
            f"Trading: `{self.trading_mode}`\n"
            f"Symbol: `{self.symbol_value}`\nStake: `{self.stake_value:.2f}`\n"
            f"Duration: `{self.duration_value} min`\n"
            f"Last tick: `{self.last_tick if self.last_tick is not None else '—'}`\n"
            f"Signal: {self.last_signal}\n"
            f"Daily loss tracked: `{self.daily_loss:.2f}`"
        )
        await self.reply(update, text, parse_mode="Markdown")

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        if not self.s.deriv_pat or not self.s.deriv_account_id:
            return await self.reply(update, "⚠️ Set DERIV_PAT and DERIV_ACCOUNT_ID in .env first.")
        try:
            client = await self._ensure_authenticated()
            b = client.balance or {}
            await self.reply(update, f"💰 *Balance*\nAccount: `{client.loginid}`\nMode: `{client.account_mode}`\nBalance: `{b.get('balance', 'unknown')} {b.get('currency', '')}`", parse_mode="Markdown")
        except Exception as exc:
            await self.reply(update, f"❌ Account connection failed: {str(exc)[:300]}")

    async def monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        if self.running:
            return await self.reply(update, "📊 Monitoring is already running.")
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(context.application, update.effective_chat.id))
        await self.reply(update, "🔄 Connecting to Deriv public market feed…\nTrading remains disarmed unless you explicitly arm it.")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        self.running = False
        self.trading_mode = "OFF"
        await self.reply(update, "🛑 Engine stopped. New trades disarmed.")
        # monitor loop exits on its next iteration; don't cancel handler task from itself.

    async def stake(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        try:
            value = float(context.args[0])
            if value <= 0 or value > self.s.max_stake:
                raise ValueError
            self.stake_value = value
            await self.reply(update, f"✅ Stake set to {value:.2f}. Maximum configured stake: {self.s.max_stake:.2f}.")
        except (IndexError, ValueError):
            await self.reply(update, f"Usage: /stake 1 — value must be greater than 0 and no more than {self.s.max_stake:.2f}.")

    async def duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")

        allowed_durations = (1, 5, 10, 15, 30, 60)

        try:
            value = int(context.args[0])
            if value not in allowed_durations:
                raise ValueError
            self.duration_value = value
            label = "1 hour" if value == 60 else f"{value} minute(s)"
            await self.reply(
                update,
                f"✅ Trade duration set to {label}.\n"
                f"Available: {', '.join(map(str, allowed_durations))} minutes."
            )
        except (IndexError, ValueError):
            await self.reply(
                update,
                "Usage: /duration 1, 5, 10, 15, 30, or 60"
            )

    async def symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        if not context.args:
            return await self.reply(update, "Usage: /symbol R_100")
        value = context.args[0].strip().upper()
        if not value.replace("_", "").isalnum() or len(value) > 20:
            return await self.reply(update, "Invalid symbol format.")
        self.symbol_value = value
        await self.reply(update, f"✅ Symbol set to `{value}`. Confirm availability in Deriv before trading.", parse_mode="Markdown")

    async def arm_demo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        try:
            client = await self._ensure_authenticated()
            if client.account_mode != "DEMO":
                return await self.reply(update, "⛔ This token/account is not identified as DEMO. No trades armed.")
            self.trading_mode = "DEMO"
            await self.reply(update, "🟢 Demo trading armed. Example strategy only; losses are possible. Use /disarm to stop new entries.")
        except Exception as exc:
            await self.reply(update, f"❌ Could not arm demo: {str(exc)[:250]}")

    async def arm_real(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        if not self.s.allow_real_trading:
            return await self.reply(update, "🔒 Real trading is disabled. Set ALLOW_REAL_TRADING=true in .env only after testing on demo.")
        await self.reply(update,
            "⚠️ REAL ACCOUNT CONFIRMATION REQUIRED.\n"
            "This starter is not audited, and its sample strategy is not validated. To prevent accidental real-money trades, real trading is not armed by this command. Change the code only after independent review and demo testing.")
        # Deliberately do not arm real trading in this starter.

    async def disarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.allowed(update):
            return await self.reply(update, "⛔ Unauthorized user.")
        self.trading_mode = "OFF"
        await self.reply(update, "🔒 Trading disarmed. Monitoring can continue.")

    async def _ensure_authenticated(self):
        if self.client and self.client.ws and self.client.authorized:
            return self.client
        client = DerivClient(self.s.deriv_app_id, self.s.deriv_pat, self.s.deriv_account_id)
        info = await client.connect_authenticated()
        self.client = client
        log.info("Deriv authenticated: account=%s mode=%s currency=%s", info["loginid"], info["mode"], info["currency"])
        return client

    async def _monitor_loop(self, application, chat_id: int):
        strategy = MomentumStrategy()
        client = DerivClient(self.s.deriv_app_id)
        self.client = client
        try:
            await client.connect_public()
            await client.subscribe_ticks(self.symbol_value)
            await application.bot.send_message(chat_id, f"🟢 *Market feed connected*\nSymbol: `{self.symbol_value}`\nMode: `PUBLIC MONITORING`\nTrading: `DISARMED`", parse_mode="Markdown")
            while self.running:
                try:
                    message = await asyncio.wait_for(client.tick_queue.get(), timeout=30)
                except asyncio.TimeoutError:
                    await application.bot.send_message(chat_id, "⏳ Waiting for the next market tick…")
                    continue
                tick = message.get("tick", {})
                price = tick.get("quote")
                if price is None:
                    continue
                self.last_tick = price
                signal = strategy.update(float(price))
                if signal:
                    self.last_signal = f"{signal.direction} — {signal.reason}"
                    await application.bot.send_message(
                        chat_id,
                        f"📊 *Signal update*\nSymbol: `{self.symbol_value}`\nDirection: *{signal.direction}*\nPrice: `{price}`\nRule: {signal.reason}\n⚠️ Example signal only; not a guarantee.",
                        parse_mode="Markdown",
                    )
                    # Live order execution is permitted ONLY in explicitly armed DEMO mode.
                    # Real-money execution is intentionally not implemented in this starter.
                    self._roll_daily_counters()
                    if self.trading_mode == "DEMO":
                        if self.daily_loss >= self.s.max_daily_loss:
                            self.trading_mode = "OFF"
                            await application.bot.send_message(
                                chat_id,
                                f"🛑 Daily loss limit reached ({self.daily_loss:.2f}). Trading disarmed."
                            )
                            continue
                        if self.consecutive_losses >= self.s.max_consecutive_losses:
                            self.trading_mode = "OFF"
                            await application.bot.send_message(
                                chat_id,
                                f"🛑 Consecutive-loss limit reached ({self.consecutive_losses}). Trading disarmed."
                            )
                            continue
                        try:
                            auth_client = await self._ensure_authenticated()
                            if auth_client.account_mode != "DEMO":
                                self.trading_mode = "OFF"
                                await application.bot.send_message(chat_id, "⛔ Account is not DEMO. Trading disarmed.")
                                continue
                            order = await auth_client.buy_call_put(
                                self.symbol_value, signal.direction,
                                self.stake_value, self.duration_value
                            )
                            cid = str(order["contract_id"])
                            await application.bot.send_message(
                                chat_id,
                                f"🟢 *DEMO CONTRACT OPENED*\n"
                                f"ID: `{cid}`\nSymbol: `{self.symbol_value}`\n"
                                f"Direction: *{signal.direction}*\nStake: `{order['buy_price']}`\n"
                                f"Duration: `{self.duration_value} min`",
                                parse_mode="Markdown"
                            )
                            # Wait for the matching contract settlement before another entry.
                            deadline = asyncio.get_running_loop().time() + max(180, self.duration_value * 60 + 60)
                            settled = None
                            while self.running and asyncio.get_running_loop().time() < deadline:
                                try:
                                    update_msg = await asyncio.wait_for(auth_client.contract_queue.get(), timeout=10)
                                except asyncio.TimeoutError:
                                    continue
                                contract = update_msg.get("proposal_open_contract", {})
                                if str(contract.get("contract_id")) == cid and contract.get("is_sold"):
                                    settled = contract
                                    break
                            self._roll_daily_counters()
                            if settled:
                                profit = float(settled.get("profit", 0) or 0)
                                if profit < 0:
                                    self.daily_loss += abs(profit)
                                if profit < 0:
                                    self.consecutive_losses += 1
                                else:
                                    self.consecutive_losses = 0
                                await application.bot.send_message(
                                    chat_id,
                                    f"{'🏆' if profit > 0 else '🔴' if profit < 0 else '⚪'} *DEMO SETTLEMENT*\n"
                                    f"Contract: `{cid}`\nP/L: `{profit:.2f} {auth_client.currency}`\n"
                                    f"Balance: `{(auth_client.balance or {}).get('balance', 'check /balance')}`\n"
                                    f"Consecutive losses: `{self.consecutive_losses}`",
                                    parse_mode="Markdown"
                                )
                            else:
                                self.trading_mode = "OFF"
                                await application.bot.send_message(chat_id, f"⚠️ Could not confirm settlement for `{cid}`. Trading disarmed for safety.", parse_mode="Markdown")
                        except Exception as trade_exc:
                            self.trading_mode = "OFF"
                            log.exception("Demo trade failed")
                            await application.bot.send_message(chat_id, f"❌ Demo order failed; trading disarmed: {str(trade_exc)[:250]}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.exception("Monitor loop failed")
            await application.bot.send_message(chat_id, f"❌ Market feed error: {str(exc)[:250]}")
        finally:
            self.running = False
            await client.close()
            if self.client is client:
                self.client = None
            log.info("Market monitoring stopped")
