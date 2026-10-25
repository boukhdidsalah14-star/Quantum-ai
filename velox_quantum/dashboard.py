import asyncio
import hashlib
import hmac
import json
import os
import threading
import time
from pathlib import Path
from urllib.parse import parse_qsl

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
_controller = None
_settings = None


def verify_telegram_init_data(raw):
    if not raw or not _settings or not _settings.telegram_token:
        return None

    try:
        values = dict(parse_qsl(raw, keep_blank_values=True))
        received_hash = values.pop("hash", "")
        if not received_hash:
            return None

        auth_date = int(values.get("auth_date", "0"))
        now = int(time.time())
        if auth_date <= 0 or auth_date > now + 60 or now - auth_date > 86400:
            return None

        check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(values.items())
        )
        secret = hmac.new(
            b"WebAppData",
            _settings.telegram_token.encode(),
            hashlib.sha256,
        ).digest()
        calculated = hmac.new(
            secret, check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated, received_hash):
            return None

        user = json.loads(values.get("user", "{}"))
        user_id = int(user.get("id", 0))
        if user_id not in _settings.allowed_user_ids:
            return None

        return user_id
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


@app.get("/")
def dashboard_home():
    return send_file(BASE_DIR / "webapp" / "index.html")


@app.get("/api/state")
def dashboard_state():
    user_id = verify_telegram_init_data(
        request.headers.get("X-Telegram-Init-Data", "")
    )
    if user_id is None:
        return jsonify({"ok": False, "error": "Telegram authentication required"}), 401

    c = _controller
    if c is None:
        return jsonify({"ok": False, "error": "Bot controller unavailable"}), 503

    return jsonify({
        "ok": True,
        "telegram_verified": True,
        "running": bool(c.running),
        "trading_mode": str(c.trading_mode),
        "symbol": str(c.symbol_value),
        "stake": float(c.stake_value),
        "duration": int(c.duration_value),
        "last_tick": c.last_tick,
        "last_signal": str(c.last_signal),
    })




async def _dashboard_arm_demo(c):
    client = await c._ensure_authenticated()
    if str(getattr(client, "account_mode", "")).upper() != "DEMO":
        raise RuntimeError("Deriv account is not verified as DEMO. No trades armed.")
    c.trading_mode = "DEMO"
    return "Demo trading armed. Verify account, stake and risk limits."


async def _dashboard_disarm(c):
    c.trading_mode = "OFF"
    return "Trading disarmed. Monitoring may continue."


@app.post("/api/demo")
def dashboard_arm_demo():
    user_id = verify_telegram_init_data(
        request.headers.get("X-Telegram-Init-Data", "")
    )
    if user_id is None:
        return jsonify({"ok": False, "error": "Telegram authentication required"}), 401
    if _controller is None or _loop is None:
        return jsonify({"ok": False, "error": "Bot controller or event loop unavailable"}), 503
    try:
        result = asyncio.run_coroutine_threadsafe(
            _dashboard_arm_demo(_controller), _loop
        ).result(timeout=20)
        return jsonify({"ok": True, "message": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)[:200]}), 400


@app.post("/api/disarm")
def dashboard_disarm():
    user_id = verify_telegram_init_data(
        request.headers.get("X-Telegram-Init-Data", "")
    )
    if user_id is None:
        return jsonify({"ok": False, "error": "Telegram authentication required"}), 401
    if _controller is None or _loop is None:
        return jsonify({"ok": False, "error": "Bot controller or event loop unavailable"}), 503
    try:
        result = asyncio.run_coroutine_threadsafe(
            _dashboard_disarm(_controller), _loop
        ).result(timeout=5)
        return jsonify({"ok": True, "message": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)[:200]}), 400


def start_dashboard(controller, settings, loop=None):
    global _controller, _settings, _loop
    _controller = controller
    _settings = settings
    _loop = loop

    port = int(os.environ.get("PORT", "8080"))
    thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
        ),
        daemon=True,
        name="velox-dashboard",
    )
    thread.start()
    return thread
