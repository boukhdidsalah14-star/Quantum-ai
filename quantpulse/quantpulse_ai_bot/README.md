# QuantPulse AI — Telegram bot MVP

## Included
- Telegram commands and inline menu
- SQLite storage for users and recorded crash multipliers
- `/sports` fixture list using a public ESPN English-football scoreboard endpoint
- `/mines` probability calculator
- `/crash` and `/crashstats` descriptive analysis of user-supplied multipliers
- `/plinko`, `/stats`, `/health`, `/help`

## Important limitations
This is an initial working foundation, not a universal 1xBet predictor. It does not log in to 1xBet, scrape private pages, place bets, or know hidden casino outcomes. The sports command currently lists fixtures; it does not yet provide validated match predictions. A proper sports model requires reliable historical results, team ratings, and careful out-of-sample testing. Public data endpoints may change or rate-limit requests.

## 1. Create the Telegram bot
1. Open https://t.me/BotFather in Telegram.
2. Send `/newbot` and follow its prompts.
3. Copy the token privately. Never share it or commit it to GitHub.

## 2. Run on Android using Termux
Install Termux from a trusted source. Then run:

```bash
pkg update -y
pkg install python -y
mkdir -p ~/quantpulse-ai
cd ~/quantpulse-ai
```

Copy `bot.py` and `requirements.txt` into this folder, then:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN='PASTE_YOUR_TOKEN_HERE'
python bot.py
```

Keep the Termux session open for the bot to keep running. Android battery optimization or a closed session may stop it. This is not reliable 24/7 hosting.

## 3. Commands
- `/start`
- `/help`
- `/sports`
- `/crash 1.2 2.4 1.1 5.0`
- `/crashstats`
- `/mines 25 3 4`
- `/plinko`
- `/stats`
- `/health`

## 4. Keep secrets safe
- Do not upload your bot token to GitHub.
- If the token leaks, revoke it through BotFather and create a new one.
- The SQLite database is local to the machine; on ephemeral hosts it may be lost after a restart/redeploy unless persistent storage is configured.

## 5. Free 24/7 hosting reality
Free hosting policies change. Some free web services sleep and are not designed for persistent Telegram long polling. Test locally first; then choose a host whose current free plan explicitly supports a continuously running worker and persistent storage. Do not assume 24/7 uptime until it is verified.
