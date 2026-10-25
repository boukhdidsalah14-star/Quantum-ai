for line in Path(".env").read_text().splitlines():
    if line.startswith(("DERIV_PAT=", "DERIV_ACCOUNT_ID=")):
        key, value = line.split("=", 1)
        value = value.strip()
        if key == "DERIV_PAT":
            print(key, "SET" if value.startswith("pat_") else "EMPTY/FORMAT CHECK")
        else:
            print(key, "EMPTY" if not value else
                  "LIKELY TOKEN IN WRONG FIELD" if value.startswith("pat_")
                  else "SET — FORMAT NEEDS VERIFICATION")
PY

cd ~/velox_quantum
nano .env
python app.py
cd ~/velox_quantum && nano .env
cd ~/velox_quantum
python app.py
ls
cd ~/velox_quantum
cat README.md
cd ~/velox_quantum
sed -n '1,220p' main.py
cd ~/velox_quantum
python -c "from config import load_settings; s=load_settings(); print('Telegram token:', 'SET' if s.telegram_token else 'MISSING'); print('Allowed user IDs:', 'SET' if s.allowed_user_ids else 'MISSING'); print('Deriv PAT:', 'SET' if s.deriv_pat else 'MISSING'); print('Deriv account ID:', 'SET' if s.deriv_account_id else 'MISSING'); print('App ID:', 'SET' if s.deriv_app_id else 'MISSING'); print('Default stake:', s.default_stake); print('Maximum stake:', s.max_stake); print('Real trading allowed:', s.allow_real_trading)"
cd ~/velox_quantum
grep -n '^ALLOW_REAL_TRADING=' .env
grep -n -E 'arm_real|arm_demo|ALLOW_REAL_TRADING|account_id|is_demo|disarm' telegram_app.py deriv_client.py config.py
cd ~/velox_quantum
grep -n -E 'async def |def |proposal|buy|contract|sell|settle|balance|authorize|otp|WebSocket|websocket' deriv_client.py telegram_app.py strategy.py main.py
cd ~/velox_quantum && tar -czf ~/velox_quantum_review.tar.gz README.md main.py config.py deriv_client.py strategy.py telegram_app.py requirements.txt
termux-setup-storage
cp ~/velox_quantum_review.tar.gz ~/storage/shared/Download/
cd ~/velox_quantum && cat README.md
cd ~/velox_quantum
ls -la
cd ~/velox_quantum
python -c "from pathlib import Path; p=Path('.env'); d={}; exec('for line in p.read_text().splitlines():\n line=line.strip()\n if line and not line.startswith(\"#\") and \"=\" in line:\n  k,v=line.split(\"=\",1); d[k.strip()]=v.strip()'); keys=['TELEGRAM_BOT_TOKEN','ALLOWED_TELEGRAM_USER_IDS','DERIV_PAT','DERIV_ACCOUNT_ID','DERIV_APP_ID','ALLOW_REAL_TRADING']; [print(f'{k}: {\"SET\" if d.get(k) else \"MISSING\"}') for k in keys]"
cd ~/velox_quantum
python -m py_compile main.py config.py deriv_client.py strategy.py telegram_app.py
cd ~/velox_quantum
python main.py
cd ~/velox_quantum
find . -maxdepth 2 -type f ! -name '.env' ! -name '*.bak' ! -path './__pycache__/*' | sort
cat requirements.txt
sed -n '1,240p' main.py
sed -n '1,260p' telegram_app.py
cd ~/velox_quantum && find . -maxdepth 2 -type f ! -name '.env' ! -name '*.bak' ! -path './__pycache__/*' | sort
cd ~/velox_quantum
cat requirements.txt
sed -n '1,180p' main.py
cd ~/velox_quantum
cat requirements.txt
python -c "import importlib.util; print('Flask:', bool(importlib.util.find_spec('flask'))); print('FastAPI:', bool(importlib.util.find_spec('fastapi')))"
cd ~/velox_quantum
sed -n '1,220p' config.py
grep -nE 'class VeloxTelegram|def __init__|async def (start|status|balance|monitor|stop|stake|duration|symbol|arm_demo|arm_real|disarm)|trading_mode|last_tick|last_signal|self\.running' telegram_app.py
grep -nE '_monitor_loop|create_task|cancel\(|post_init|post_shutdown|run_polling' main.py telegram_app.py
cd ~/velox_quantum
sed -n '1,220p' config.py
grep -nE 'class VeloxTelegram|def __init__|async def (start|status|balance|monitor|stop|stake|duration|symbol|arm_demo|arm_real|disarm)|trading_mode|last_tick|last_signal|self\.running' telegram_app.py
cd ~/velox_quantum
sed -n '1,130p' telegram_app.py
sed -n '1,100p' main.py
cd ~/velox_quantum
mkdir -p webapp
cat > webapp/index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="theme-color" content="#050907">
<title>VELOX QUANTUM</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:dark;--bg:#050907;--panel:#0b1410;--line:#183426;--green:#00ff78;--muted:#8ca99a;--red:#ff6377}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 50% -20%,#123b27 0,transparent 55%),var(--bg);color:#e8fff0;font-family:Inter,system-ui,sans-serif;min-height:100vh}
body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.14;background-image:linear-gradient(#00ff7810 1px,transparent 1px),linear-gradient(90deg,#00ff7810 1px,transparent 1px);background-size:28px 28px}
main{position:relative;max-width:720px;margin:auto;padding:22px 16px 40px}
header{display:flex;align-items:center;gap:12px;margin-bottom:24px}
.logo{width:48px;height:48px;border:1px solid var(--green);border-radius:14px;display:grid;place-items:center;color:var(--green);font-size:24px;box-shadow:0 0 24px #00ff7822}
h1{font-size:19px;letter-spacing:2px;margin:0;color:var(--green)}
.sub{font-size:10px;color:var(--muted);letter-spacing:2px;margin-top:5px}
.status{margin-left:auto;color:var(--green);font-size:11px;border:1px solid #185c36;padding:7px 9px;border-radius:20px}
h2{font-size:12px;letter-spacing:1.5px;color:var(--muted);font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.panel{background:linear-gradient(145deg,#0d1912,#08100c);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:12px;min-width:0}
.metric{font-size:22px;font-weight:700;overflow-wrap:anywhere;margin-top:10px}
.small{font-size:11px;color:var(--muted);margin-top:6px}
.green{color:var(--green)}.red{color:var(--red)}
.chart{height:180px;width:100%;display:block}
.signal{display:flex;align-items:center;justify-content:space-between;gap:12px}
.direction{font-size:28px;font-weight:800;color:var(--green)}
button{font:inherit;cursor:pointer;border:1px solid #23633e;border-radius:12px;background:#0d2518;color:var(--green);padding:14px 10px;font-size:12px;font-weight:700;letter-spacing:.5px}
button:active{transform:scale(.98)}
.buttons{display:grid;grid-template-columns:1fr 1fr;gap:10px}
button.secondary{background:#111b15;border-color:#283a30;color:#e8fff0}
button.danger{background:#281116;border-color:#65232e;color:#ff8290}
button:disabled{opacity:.45;cursor:default}
.notice{font-size:11px;line-height:1.6;color:var(--muted)}
#feed{display:flex;flex-direction:column;gap:10px}
.event{display:flex;justify-content:space-between;gap:12px;font-size:12px;padding-bottom:10px;border-bottom:1px solid #14261c}
footer{text-align:center;color:#607e6d;font-size:10px;letter-spacing:1px;padding-top:14px}
@media(min-width:560px){main{padding-top:32px}.metric{font-size:28px}}
</style>
</head>
<body>
<main>
<header>
<div class="logo">ϟ</div>
<div><h1>VELOX QUANTUM</h1><div class="sub">QUANTITATIVE TERMINAL</div></div>
<div class="status" id="connection">CONNECTING</div>
</header>

<div class="grid">
<section class="panel"><h2>ENGINE</h2><div class="metric green" id="engine">CHECKING</div><div class="small">Market monitoring</div></section>
<section class="panel"><h2>TRADING MODE</h2><div class="metric" id="mode">OFF</div><div class="small">Execution status</div></section>
</div>

<section class="panel">
<div class="signal"><div><h2>MARKET</h2><div class="metric" id="symbol">R_100</div><div class="small">Latest received quote</div></div><div style="text-align:right"><h2>LAST PRICE</h2><div class="metric green" id="price">—</div><div class="small" id="updated">Awaiting data</div></div></div>
<canvas id="chart" class="chart"></canvas>
</section>

<section class="panel">
<h2>LATEST SIGNAL</h2>
<div class="signal"><div class="direction" id="direction">—</div><div class="small" id="reason" style="text-align:right">No signal received</div></div>
</section>

<section class="panel">
<h2>CONTROL CENTER</h2>
<div class="buttons">
<button id="openBot">OPEN BOT</button>
<button class="secondary" id="refresh">REFRESH STATUS</button>
<button class="secondary" id="demo">ARM DEMO</button>
<button class="danger" id="disarm">DISARM</button>
</div>
<p class="notice">Demo control will work only after a secure backend endpoint is connected. Real-money trading is not enabled by this interface.</p>
</section>

<section class="panel"><h2>MARKET ACTIVITY</h2><div id="feed"><div class="event"><span>Dashboard initialized</span><span class="green">READY</span></div></div></section>
<footer>VELOX QUANTUM · RISK FIRST · NO PROFIT GUARANTEE</footer>
</main>
<script>
const tg=window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
const $=id=>document.getElementById(id);
let prices=[];
function draw(){
 const c=$("chart"),ctx=c.getContext("2d"),w=c.clientWidth,h=c.clientHeight,dpr=window.devicePixelRatio||1;
 c.width=w*dpr;c.height=h*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);
 ctx.strokeStyle="#153423";ctx.lineWidth=1;
 for(let y=20;y<h;y+=35){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}
 if(prices.length<2)return;
 let lo=Math.min(...prices),hi=Math.max(...prices),range=hi-lo||1;
 ctx.beginPath();prices.forEach((p,i)=>{let x=i*w/(Math.max(prices.length-1,1)),y=h-12-(p-lo)/range*(h-24);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});
 ctx.strokeStyle="#00ff78";ctx.lineWidth=2;ctx.shadowColor="#00ff78";ctx.shadowBlur=10;ctx.stroke();ctx.shadowBlur=0;
}
function event(label,value){
 const row=document.createElement("div");row.className="event";
 const a=document.createElement("span"),b=document.createElement("span");
 a.textContent=label;b.textContent=value;b.className="green";row.append(a,b);
 $("feed").prepend(row);while($("feed").children.length>8)$("feed").lastChild.remove();
}
function update(data){
 if(!data||typeof data!=="object")return;
 if(data.running!==undefined)$("engine").textContent=data.running?"RUNNING":"STOPPED";
 if(data.trading_mode)$("mode").textContent=data.trading_mode;
 if(data.symbol)$("symbol").textContent=data.symbol;
 if(data.last_tick!==undefined&&data.last_tick!==null){
  const p=Number(data.last_tick);if(Number.isFinite(p)){ $("price").textContent=p.toFixed(2);prices.push(p);prices=prices.slice(-60);draw();$("updated").textContent="Price received";}
 }
 if(data.last_signal){$("reason").textContent=data.last_signal;$("direction").textContent=data.last_signal.toUpperCase().includes("PUT")?"PUT":data.last_signal.toUpperCase().includes("CALL")?"CALL":"SIGNAL";}
 if(data.authenticated!==undefined)$("connection").textContent=data.authenticated?"ACCOUNT LINKED":"MONITORING";
}
async function refresh(){
 // No endpoint is assumed: wait for the secure backend to be implemented.
 $("connection").textContent="UI PREVIEW";
}
$("refresh").addEventListener("click",refresh);
$("openBot").addEventListener("click",()=>tg?.close());
$("demo").addEventListener("click",()=>event("Demo control","Backend not connected"));
$("disarm").addEventListener("click",()=>event("Disarm control","Backend not connected"));
window.addEventListener("resize",draw);
refresh();
</script>
</body>
</html>
EOF

wc -l webapp/index.html
ls -lh webapp/index.html
cd ~/velox_quantum
python -c "from pathlib import Path; p=Path('webapp/index.html'); s=p.read_text(); print('File size:',len(s),'characters'); print('HTML start:',s[:100]); print('HTML end:',s[-300:]); print('Has closing HTML:', '</html>' in s.lower()); print('Has chart:', 'canvas' in s.lower()); print('Has broken paste marker:', 'EOF' in s)"
cd ~/velox_quantum
grep -nE 'canvas|function refresh|function draw|telegram-web-app.js|backgEOFtml|</script>' webapp/index.html
cd ~/velox_quantum
sed -n '100,124p' webapp/index.html
cd ~/velox_quantum
sed -n '1,125p' telegram_app.py
sed -n '125,255p' telegram_app.py
cd ~/velox_quantum
sed -n '1,125p' telegram_app.py
sed -n '125,255p' telegram_app.py
cd ~/velox_quantum
sed -n '1,125p' telegram_app.py
cd ~/velox_quantum
sed -n '1,100p' telegram_app.py
cd ~/velox_quantum
sed -n '1,55p' telegram_app.py
cd ~/velox_quantum
cp main.py main.py.before_dashboard
cp telegram_app.py telegram_app.py.before_dashboard
cp webapp/index.html webapp/index.html.before_dashboard
ls -lh main.py.before_dashboard telegram_app.py.before_dashboard webapp/index.html.before_dashboard
cd ~/velox_quantum
cat > dashboard.py <<'PY'
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


def start_dashboard(controller, settings):
    global _controller, _settings
    _controller = controller
    _settings = settings

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
PY

grep -q '^Flask' requirements.txt || echo 'Flask>=3.0,<4' >> requirements.txt
python -m py_compile dashboard.py
cd ~/velox_quantum
python -c "from pathlib import Path; p=Path('dashboard.py'); s=p.read_text(); print('Size:',len(s)); print('Lines:',len(s.splitlines())); print('Starts correctly:',s.startswith('import hashlib')); print('Has verification:', 'def verify_telegram_init_data' in s); print('Has API endpoint:', \"@app.get('/api/state')\" in s or '@app.get(\"/api/state\")' in s); print('Has startup function:', 'def start_dashboard' in s); print('Last 250 chars:',repr(s[-250:]))"
cd ~/velox_quantum
python - <<'PY'
from pathlib import Path

p = Path("main.py")
s = p.read_text()

if "from dashboard import start_dashboard" not in s:
    s = s.replace(
        "from telegram_app import VeloxTelegram",
        "from telegram_app import VeloxTelegram\nfrom dashboard import start_dashboard"
    )

old = '''async def post_init(application: Application):
    app = application.bot_data["velox"]
    await app.initialize()'''

new = '''async def post_init(application: Application):
    controller = application.bot_data["velox"]
    await controller.initialize()
    start_dashboard(controller, controller.s)'''

if new not in s:
    if old not in s:
        print("STOP: Could not find the expected post_init function.")
        print("main.py was not changed.")
        raise SystemExit(1)
    s = s.replace(old, new, 1)

p.write_text(s)
print("Dashboard startup connected to main.py.")
PY

python -m py_compile main.py dashboard.py telegram_app.py
cd ~/velox_quantum
python - <<'PY'
from pathlib import Path

p = Path("webapp/index.html")
s = p.read_text()

old = '''async function refresh(){
 // No endpoint is assumed: wait for the secure backend to be implemented.
 $("connection").textContent="UI PREVIEW";
}'''

new = '''async function refresh(){
 if(!tg || !tg.initData){
   $("connection").textContent="OPEN INSIDE TELEGRAM";
   return;
 }
 $("connection").textContent="CONNECTING...";
 try {
   const response = await fetch("/api/state", {
     method: "GET",
     headers: {"X-Telegram-Init-Data": tg.initData},
     cache: "no-store"
   });
   if(!response.ok) {
     $("connection").textContent =
       response.status === 401 ? "AUTHENTICATION FAILED" : "API UNAVAILABLE";
     return;
   }
   const data = await response.json();
   if(!data.ok) {
     $("connection").textContent="API ERROR";
     return;
   }
   $("connection").textContent="LIVE DATA";
   if(data.running !== undefined)
     $("engine").textContent=data.running ? "RUNNING" : "STOPPED";
   if(data.trading_mode)
     $("mode").textContent=data.trading_mode;
   if(data.symbol)
     $("symbol").textContent=data.symbol;
   if(data.last_tick !== undefined && data.last_tick !== null) {
     const p=Number(data.last_tick);
     if(Number.isFinite(p)) {
       $("price").textContent=p.toFixed(2);
       if(!prices.length || prices[prices.length-1] !== p) {
         prices.push(p);
         prices=prices.slice(-60);
         draw();
       }
       $("updated").textContent="Live tick received";
     }
   }
   if(data.last_signal) {
     $("reason").textContent=data.last_signal;
     $("direction").textContent=
       data.last_signal.toUpperCase().includes("PUT") ? "PUT" :
       data.last_signal.toUpperCase().includes("CALL") ? "CALL" : "SIGNAL";
   }
 } catch(e) {
   $("connection").textContent="CONNECTION ERROR";
 }
}'''

if old not in s:
    print("STOP: Exact preview function not found.")
    print("HTML unchanged; send me the output of: grep -n -A5 'async function refresh' webapp/index.html")
    raise SystemExit(1)

p.write_text(s.replace(old, new, 1))
print("Dashboard refresh now requests authenticated API data.")
PY

grep -n -A8 'async function refresh' webapp/index.html
cd ~/velox_quantum
sed -n '108,175p' webapp/index.html
grep -n -E 'dashboard|post_init|start_dashboard' main.py
node --version
cd ~/velox_quantum
python - <<'PY'
from pathlib import Path
import re

p = Path("webapp/index.html")
s = p.read_text()
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script\s*>", s, re.S)

print("HTML file:", "FOUND" if p.exists() else "MISSING")
print("Script blocks:", len(scripts))
print("Dashboard refresh:", "FOUND" if "async function refresh()" in s else "MISSING")
print("API endpoint:", "FOUND" if "/api/state" in s else "MISSING")
print("HTML closing tag:", "FOUND" if "</html>" in s.lower() else "MISSING")
print("JavaScript syntax: not yet checked by a JavaScript parser")
PY

python -m py_compile main.py dashboard.py telegram_app.py config.py deriv_client.py strategy.py
cd ~/velox_quantum
python -c "import dashboard; print('Dashboard import OK'); print('API routes:', sorted(str(r) for r in dashboard.app.url_map.iter_rules()))"
sed -n '1,65p' main.py
cd ~/velox_quantum
python -c "import dashboard; print('Dashboard import OK'); print('Routes:', sorted(str(r) for r in dashboard.app.url_map.iter_rules()))"
python - <<'PY'
import dashboard

client = dashboard.app.test_client()

home = client.get("/")
api = client.get("/api/state")

print("Dashboard page HTTP:", home.status_code)
print("Unauthenticated API HTTP:", api.status_code)

if home.status_code == 200 and api.status_code == 401:
    print("PASS: page loads and API rejects unauthenticated requests")
else:
    print("CHECK REQUIRED: unexpected response")
PY

cd ~/velox_quantum
python - <<'PY'
from config import load_settings

s = load_settings()
print("Telegram token:", "SET" if s.telegram_token else "MISSING")
print("Allowed Telegram user IDs:", "SET" if s.allowed_user_ids else "MISSING")
print("Default symbol:", s.default_symbol)
print("Default stake:", s.default_stake)
print("Dashboard module: READY")
PY

python main.py
cd ~/velox_quantum
git remote -v
git status --short
