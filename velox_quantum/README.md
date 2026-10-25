# Velox Quantum

A Termux-friendly Telegram control panel and Deriv WebSocket client. This is a software starter package, not a guarantee of profitability or a fully audited financial product.

## Safety defaults
- Monitoring can run without placing trades.
- Trading is disabled until explicitly armed in Telegram.
- Real-account trading is blocked unless `ALLOW_REAL_TRADING=true` is set and the operator explicitly arms it.
- Start with a Deriv demo account. Binary options can lose the full stake.
- No HTTP workaround is used to bypass Cloudflare or other access controls.

## Requirements
- Python 3.11+ recommended (Termux's current Python may be newer).
- A Telegram bot token from BotFather.
- A Deriv Personal Access Token (PAT) with the required read/trade scopes, and the Deriv account ID that belongs to it.
- A Deriv App ID registered for your application. `1089` is retained as a default for compatibility/testing; use your own registered App ID for a product you distribute.

## Install in Termux
```bash
pkg update
pkg install python
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

Set `TELEGRAM_BOT_TOKEN`, `DERIV_PAT`, `DERIV_ACCOUNT_ID`, `DERIV_APP_ID`, and your Telegram numeric user ID in `.env`. Never put credentials in public GitHub repositories or share screenshots containing them.

## Telegram commands
- `/start` — menu and safety status
- `/status` — connection and run state
- `/balance` — query account balance (when authenticated)
- `/monitor` — start live tick monitoring and demo signal generation; does not trade
- `/stop` — stop monitoring/trading loop
- `/stake 1` — set stake (bounded by `MAX_STAKE`)
- `/duration 1` — contract duration in minutes (supported values depend on market/contract)
- `/symbol R_100` — choose a symbol
- `/arm_demo` — explicitly enable demo trades
- `/arm_real` — real trading only if `ALLOW_REAL_TRADING=true`; use extreme caution
- `/disarm` — disable new trades
- `/help` — command guide

Only `ALLOWED_TELEGRAM_USER_IDS` can operate the bot. Keep the Telegram bot private.

## Authentication notes
The current Deriv workflow for authenticated trading uses a REST request to obtain a short-lived authenticated WebSocket URL:
`POST https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp`
with `Authorization: Bearer <PAT>` and `Deriv-App-ID: <APP_ID>`. The returned URL is then used for WebSocket trading. This is different from sending a PAT as an `authorize` payload to an older WebSocket endpoint.

Public market ticks use the public endpoint. If Deriv returns HTTP 520, do not attempt to spoof TLS or bypass Cloudflare. Retry with backoff, check Deriv status/network, and use the documented endpoints.

## Strategy and limits
The included strategy is deliberately simple: a short rolling-momentum rule on incoming ticks. It is an example signal generator, not a validated edge. It can generate losses and should be backtested independently before use. Monitoring mode is the default. Do not sell this as profitable or guaranteed.

The app is a starting codebase. Before commercial distribution, add formal testing, monitoring, secure secret management, platform terms review, and an independent audit of trading and risk logic.
