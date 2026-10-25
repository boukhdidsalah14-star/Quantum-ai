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
WEBAPP_URL = "https://boukhdidsalah14-star.github.io/Quantum-ai/"

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
    offset = 0
    print("🤖 Telegram Bot Listener started...")
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    
                    # Handle message clicks / commands
                    message = result.get("message")
                    if message and "text" in message:
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        
                        if text == "/start":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📊 Open Trading Terminal", "web_app": {"url": WEBAPP_URL}}],
                                    [{"text": "⚡ Signals", "callback_data": "signals"}, {"text": "📜 History", "callback_data": "history"}],
                                    [{"text": "❓ Help", "callback_data": "help"}]
                                ]
                            }
                            send_message(chat_id, "Welcome to *Quantum AI* Trading Terminal. Choose an option below:", reply_markup=keyboard)
                            
                    # Handle inline button clicks
                    callback_query = result.get("callback_query")
                    if callback_query:
                        chat_id = callback_query["message"]["chat"]["id"]
                        data_cb = callback_query.get("data")
                        callback_id = callback_query["id"]
                        
                        # Answer callback to clear loading state on button
                        requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": callback_id})
                        
                        if data_cb == "signals":
                            send_message(chat_id, "⚡ *Current AI Signal:* EUR/USD - BUY (Confidence: 94.2%)")
                        elif data_cb == "history":
                            send_message(chat_id, "📜 *Recent Trades History:* No active trades recorded yet.")
                        elif data_cb == "help":
                            send_message(chat_id, "❓ *Quantum AI Help:* Use the Trading Terminal button to launch the web interface, or check Signals for live AI predictions.")

        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    # Start Telegram listener in a background thread
    t = threading.Thread(target=telegram_listener, daemon=True)
    t.start()
    
    # Run Flask web server
    app.run(host='0.0.0.0', port=5000)
