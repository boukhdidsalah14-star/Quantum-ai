import os
import threading
import time
import requests
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

@app.route('/')
def index():
    return render_template('index.html')

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def telegram_listener():
    if not TOKEN:
        return
    offset = 0
    while True:
        try:
            res = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30})
            if res.status_code == 200:
                for r in res.json().get("result", []):
                    offset = r["update_id"] + 1
                    msg = r.get("message")
                    if msg:
                        chat_id = msg["chat"]["id"]
                        txt = msg.get("text", "")
                        if txt.startswith("/start"):
                            kb = {
                                "inline_keyboard": [[
                                    {
                                        "text": "🚀 Open Quantum AI Terminal",
                                        "web_app": {"url": "https://core.telegram.org/bots/samples/selectablebounty"}
                                    }
                                ]]
                            }
                            send_message(chat_id, "Welcome to *Quantum AI Trading*!\n\nClick below to open your terminal:", reply_markup=kb)
                        elif txt.startswith("/signal"):
                            send_message(chat_id, "📊 *Quantum AI Signal*\nPair: `EURUSD`\nAction: `CALL (HIGHER)`")
        except:
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=telegram_listener, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
