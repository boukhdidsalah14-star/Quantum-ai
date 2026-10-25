#!/usr/bin/env python3
"""
QuantPulse AI — Telegram bot MVP.
Honest statistical analysis, not a guaranteed betting system.

Required environment variable:
  TELEGRAM_BOT_TOKEN

Optional:
  POLL_SECONDS=30
  DB_PATH=velox_bet_analyzer.sqlite3
  TZ=UTC

This bot uses Telegram long polling and a public ESPN scoreboard endpoint for
football fixtures. Public endpoints can change or rate-limit; failures are
reported instead of fabricating results.
"""
import os
import re
import json
import math
import time
import logging
import sqlite3
import asyncio
from datetime import datetime, timezone
from typing import Optional

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", "velox_bet_analyzer.sqlite3")
POLL_SECONDS = max(15, int(os.getenv("POLL_SECONDS", "30")))
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?limit=50"
USER_AGENT = "VeloxBetAnalyzer/1.0 (Telegram bot; public scoreboard data)"
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("velox-bet-analyzer")


def db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS crash_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            multiplier REAL NOT NULL CHECK(multiplier > 0),
            created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL,
            created_at TEXT NOT NULL,
            outcome TEXT DEFAULT 'pending'
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(source, event_id)
        )""")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def remember_user(update: Update):
    user = update.effective_user
    if not user:
        return
    with db() as con:
        con.execute(
            "INSERT INTO users(user_id, username, first_seen) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
            (user.id, user.username or "", now_iso()),
        )


def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚽ Sports fixtures", callback_data="sports"),
         InlineKeyboardButton("📊 My statistics", callback_data="stats")],
        [InlineKeyboardButton("✈️ Crash analysis", callback_data="crash_help"),
         InlineKeyboardButton("💎 Mines odds", callback_data="mines_help")],
        [InlineKeyboardButton("🎯 Plinko odds", callback_data="plinko_help"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ])


async def safe_send(update: Update, text: str, **kwargs):
    if update.callback_query:
        await update.callback_query.message.reply_text(text, **kwargs)
    elif update.effective_message:
        await update.effective_message.reply_text(text, **kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    msg = (
        "🟢 <b>QUANTPULSE AI</b>\n"
        "<i>Statistical tools • Transparent probabilities • Result tracking</i>\n\n"
        "Explore sports fixtures, analyze recorded crash multipliers, and calculate "
        "casino-game odds. This bot does not know hidden outcomes and never guarantees wins.\n\n"
        "Choose a tool below or type /help."
    )
    await safe_send(update, msg, parse_mode=ParseMode.HTML, reply_markup=home_keyboard())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    msg = (
        "🧭 <b>COMMANDS</b>\n\n"
        "/start — main menu\n"
        "/sports — upcoming English football fixtures from a public ESPN endpoint\n"
        "/crash 1.2 2.4 1.1 5.0 — record and analyze multipliers you provide\n"
        "/crashstats — summary of your recorded multipliers\n"
        "/mines 25 3 4 — chance of surviving 4 picks on a 25-cell board with 3 mines\n"
        "/plinko — explanation of probability/expected value\n"
        "/stats — your usage and tracked records\n"
        "/health — bot/data-source status\n\n"
        "⚠️ Historical sequences do not reveal the next independent crash, Mines, or Plinko result. "
        "Sports data here is a fixture feed, not a verified betting edge. Never stake money you cannot afford to lose."
    )
    await safe_send(update, msg, parse_mode=ParseMode.HTML, reply_markup=home_keyboard())


async def fetch_fixtures():
    timeout = aiohttp.ClientTimeout(total=12)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(ESPN_URL) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Fixture provider returned HTTP {resp.status}")
            payload = await resp.json(content_type=None)
    events = payload.get("events", [])
    out = []
    for event in events:
        comp = (event.get("competitions") or [{}])[0]
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        status = (event.get("status") or {}).get("type") or {}
        out.append({
            "id": str(event.get("id", "")),
            "name": event.get("name") or f"{away.get('team', {}).get('displayName','Away')} at {home.get('team', {}).get('displayName','Home')}",
            "home": (home.get("team") or {}).get("displayName", "Home"),
            "away": (away.get("team") or {}).get("displayName", "Away"),
            "date": event.get("date", ""),
            "state": status.get("description", status.get("name", "Scheduled")),
            "completed": bool(status.get("completed", False)),
            "home_score": home.get("score"),
            "away_score": away.get("score"),
        })
    return out


async def sports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    await safe_send(update, "🔎 Checking the public football fixture feed…")
    try:
        events = await fetch_fixtures()
    except Exception as exc:
        log.warning("Fixture fetch failed: %s", exc)
        await safe_send(
            update,
            "⚠️ I couldn't retrieve fixtures right now. The public provider may be unavailable or rate-limiting requests. "
            "No predictions were fabricated. Try /sports again later."
        )
        return
    upcoming = [e for e in events if not e["completed"]][:10]
    if not upcoming:
        await safe_send(update, "No upcoming fixtures were returned by the provider right now. Try again later.")
        return
    lines = ["⚽ <b>FOOTBALL FIXTURE SCANNER</b>", "<i>Competition feed: English football • Public ESPN data</i>", ""]
    for e in upcoming:
        try:
            dt = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
            date_label = dt.strftime("%d %b, %H:%M UTC")
        except Exception:
            date_label = "Time unavailable"
        lines.append(f"• <b>{e['away']} vs {e['home']}</b>\n  🕒 {date_label} · {e['state']}")
    lines += ["", "ℹ️ This feed lists fixtures only. It does not provide enough verified form/odds data to claim a reliable match prediction."]
    await safe_send(update, "\n".join(lines), parse_mode=ParseMode.HTML)


def parse_numbers(args):
    nums = []
    for item in args:
        item = item.replace("x", "").replace("X", "")
        try:
            n = float(item)
        except ValueError:
            continue
        if math.isfinite(n) and n > 0:
            nums.append(n)
    return nums[:500]


async def crash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    nums = parse_numbers(context.args or [])
    if not nums:
        await safe_send(
            update,
            "✈️ <b>CRASH HISTORY ANALYZER</b>\n\n"
            "Send recorded multipliers after the command, for example:\n"
            "<code>/crash 1.2 2.4 1.1 5.0 1.8</code>\n\n"
            "I'll save these values and summarize the sample. I cannot predict the next multiplier.",
            parse_mode=ParseMode.HTML
        )
        return
    with db() as con:
        con.executemany(
            "INSERT INTO crash_rounds(user_id, multiplier, created_at) VALUES(?,?,?)",
            [(update.effective_user.id, n, now_iso()) for n in nums]
        )
    await safe_send(update, format_crash_stats(nums, len(nums)))


def format_crash_stats(nums, added=0):
    n = len(nums)
    under2 = sum(x < 2 for x in nums) / n * 100
    under15 = sum(x < 1.5 for x in nums) / n * 100
    avg = sum(nums) / n
    sorted_nums = sorted(nums)
    med = sorted_nums[n // 2] if n % 2 else (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    return (
        "✈️ <b>CRASH SAMPLE SUMMARY</b>\n\n"
        f"Rounds in sample: <b>{n}</b>\n"
        f"Average multiplier: <b>{avg:.2f}x</b>\n"
        f"Median multiplier: <b>{med:.2f}x</b>\n"
        f"Below 1.50x: <b>{under15:.1f}%</b>\n"
        f"Below 2.00x: <b>{under2:.1f}%</b>\n\n"
        "⚠️ These are descriptive statistics for the sample, not a forecast. Past multipliers do not reveal the next independent outcome."
    )


async def crashstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    with db() as con:
        rows = con.execute(
            "SELECT multiplier FROM crash_rounds WHERE user_id=? ORDER BY id DESC LIMIT 200",
            (update.effective_user.id,)
        ).fetchall()
    nums = [float(r["multiplier"]) for r in rows]
    if not nums:
        await safe_send(update, "No multipliers saved yet. Use /crash 1.2 2.4 1.1 5.0")
        return
    await safe_send(update, format_crash_stats(nums), parse_mode=ParseMode.HTML)


async def mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    args = context.args or []
    try:
        cells = int(args[0]) if len(args) > 0 else 25
        mine_count = int(args[1]) if len(args) > 1 else 3
        picks = int(args[2]) if len(args) > 2 else 1
        if not (2 <= cells <= 100 and 1 <= mine_count < cells and 1 <= picks <= cells - mine_count):
            raise ValueError
    except (ValueError, IndexError):
        await safe_send(update, "Usage: <code>/mines CELLS MINES PICKS</code>\nExample: <code>/mines 25 3 4</code>", parse_mode=ParseMode.HTML)
        return
    # Sequentially pick without replacement. Probability all picks are safe.
    safe_prob = 1.0
    for i in range(picks):
        safe_prob *= (cells - mine_count - i) / (cells - i)
    bust_prob = 1 - safe_prob
    fair_multiplier = 1 / safe_prob if safe_prob > 0 else float("inf")
    await safe_send(
        update,
        "💎 <b>MINES PROBABILITY CALCULATOR</b>\n\n"
        f"Board: <b>{cells}</b> cells · Mines: <b>{mine_count}</b> · Picks: <b>{picks}</b>\n"
        f"Chance all picks are safe: <b>{safe_prob*100:.4f}%</b>\n"
        f"Chance of hitting a mine: <b>{bust_prob*100:.4f}%</b>\n"
        f"Fair break-even multiplier (before house edge): <b>{fair_multiplier:.4f}x</b>\n\n"
        "This assumes uniformly random mine placement and no extra game rules. It calculates odds; it does not identify safe cells.",
        parse_mode=ParseMode.HTML
    )


async def plinko(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    await safe_send(
        update,
        "🎯 <b>PLINKO ANALYSIS</b>\n\n"
        "To calculate exact probabilities or expected value, we need the specific game's row count, risk setting, payout table, and stake rules.\n\n"
        "Expected value = sum(probability of each outcome × net payout for that outcome) − stake, "
        "or equivalently use net returns consistently.\n\n"
        "A payout table alone is not enough if the landing probabilities are unknown. Past balls do not determine the next drop.",
        parse_mode=ParseMode.HTML
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    uid = update.effective_user.id
    with db() as con:
        user_count = con.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        rounds = con.execute("SELECT COUNT(*) n FROM crash_rounds WHERE user_id=?", (uid,)).fetchone()["n"]
        preds = con.execute("SELECT COUNT(*) n FROM predictions WHERE user_id=?", (uid,)).fetchone()["n"]
    await safe_send(
        update,
        "📊 <b>YOUR ANALYTICS</b>\n\n"
        f"Users who have opened the bot: <b>{user_count}</b>\n"
        f"Crash multipliers you recorded: <b>{rounds}</b>\n"
        f"Predictions logged: <b>{preds}</b>\n\n"
        "This first version does not claim prediction accuracy until predictions and verified outcomes are actually recorded.",
        parse_mode=ParseMode.HTML
    )


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    try:
        events = await fetch_fixtures()
        source_status = f"reachable ({len(events)} events returned)"
    except Exception as exc:
        source_status = f"unavailable ({type(exc).__name__})"
    with db() as con:
        con.execute("SELECT 1")
    await safe_send(
        update,
        "🩺 <b>BOT HEALTH</b>\n\n"
        "Telegram process: <b>running</b>\n"
        "Local database: <b>reachable</b>\n"
        f"Public football feed: <b>{source_status}</b>\n"
        f"Polling interval: <b>{POLL_SECONDS}s</b>\n\n"
        "This checks the bot process while it is running; it cannot guarantee the hosting service will stay awake 24/7.",
        parse_mode=ParseMode.HTML
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data
    if key == "sports":
        await sports(update, context)
    elif key == "stats":
        await stats(update, context)
    elif key == "crash_help":
        await query.message.reply_text(
            "✈️ Record multipliers with /crash 1.2 2.4 1.1 5.0, then inspect them with /crashstats.\n"
            "The bot analyzes the sample; it cannot forecast the next hidden result."
        )
    elif key == "mines_help":
        await query.message.reply_text("💎 Example: /mines 25 3 4 — 25 cells, 3 mines, 4 picks.")
    elif key == "plinko_help":
        await plinko(update, context)
    elif key == "help":
        await help_cmd(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled exception", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN. Set it as an environment variable; never hard-code or share your token."
        )
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("sports", sports))
    app.add_handler(CommandHandler("crash", crash))
    app.add_handler(CommandHandler("crashstats", crashstats))
    app.add_handler(CommandHandler("mines", mines))
    app.add_handler(CommandHandler("plinko", plinko))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    log.info("Starting QuantPulse AI polling bot")
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
