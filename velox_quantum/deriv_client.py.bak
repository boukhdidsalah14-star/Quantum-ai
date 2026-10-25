import asyncio
import itertools
import json
import logging
from typing import Any

import aiohttp
import websockets

log = logging.getLogger(__name__)
PUBLIC_WS = "wss://api.derivws.com/trading/v1/options/ws/public"
REST_BASE = "https://api.derivws.com"

class DerivError(RuntimeError):
    pass

class DerivClient:
    """One async WebSocket reader with request correlation and event queues."""
    def __init__(self, app_id: str, pat: str = "", account_id: str = ""):
        self.app_id, self.pat, self.account_id = app_id, pat, account_id
        self.ws = None
        self.reader_task = None
        self._counter = itertools.count(1)
        self._pending: dict[int, asyncio.Future] = {}
        self.tick_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=500)
        self.contract_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self.balance: dict[str, Any] | None = None
        self.authorized = False
        self.account_mode = "UNKNOWN"
        self.loginid = account_id
        self.currency = ""

    async def connect_public(self):
        self.ws = await websockets.connect(PUBLIC_WS, open_timeout=20, ping_interval=20, ping_timeout=20)
        self.reader_task = asyncio.create_task(self._reader(), name="deriv-public-reader")
        await self.request({"ping": 1}, timeout=10)

    async def connect_authenticated(self):
        if not (self.pat and self.account_id and self.app_id):
            raise DerivError("DERIV_PAT, DERIV_ACCOUNT_ID and DERIV_APP_ID are required for authenticated trading.")
        headers = {
            "Authorization": f"Bearer {self.pat}",
            "Deriv-App-ID": self.app_id,
            "Content-Type": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{REST_BASE}/trading/v1/options/accounts/{self.account_id}/otp",
                headers=headers,
            ) as response:
                body = await response.text()
                if response.status < 200 or response.status >= 300:
                    raise DerivError(f"Deriv OTP request failed (HTTP {response.status}): {body[:300]}")
                try:
                    data = json.loads(body)
                    ws_url = data["data"]["url"]
                except (ValueError, KeyError, TypeError) as exc:
                    raise DerivError("Deriv OTP response did not contain data.url.") from exc
        self.ws = await websockets.connect(ws_url, open_timeout=20, ping_interval=20, ping_timeout=20)
        self.reader_task = asyncio.create_task(self._reader(), name="deriv-auth-reader")
        # OTP URL authenticates the WebSocket session; do not send PAT to old authorize endpoint.
        balance_msg = await self.request({"balance": 1}, timeout=15)
        b = balance_msg.get("balance", {})
        self.balance = b
        self.currency = str(b.get("currency", ""))
        self.loginid = str(b.get("loginid", self.account_id))
        self.account_mode = "DEMO" if self.loginid.upper().startswith(("VRTC", "VR")) else "REAL"
        self.authorized = True
        return {
            "loginid": self.loginid,
            "balance": b.get("balance"),
            "currency": self.currency,
            "mode": self.account_mode,
        }

    async def _reader(self):
        try:
            async for raw in self.ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                req_id = msg.get("req_id")
                if req_id is not None and req_id in self._pending:
                    future = self._pending.pop(req_id)
                    if not future.done():
                        if "error" in msg:
                            future.set_exception(DerivError(msg["error"].get("message", "Deriv API error")))
                        else:
                            future.set_result(msg)
                kind = msg.get("msg_type")
                if kind == "tick":
                    self._put_latest(self.tick_queue, msg)
                elif kind == "proposal_open_contract":
                    self._put_latest(self.contract_queue, msg)
                elif kind == "balance":
                    self.balance = msg.get("balance", self.balance)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("Deriv WebSocket reader stopped: %s", exc)
        finally:
            for fut in list(self._pending.values()):
                if not fut.done():
                    fut.set_exception(DerivError("Deriv WebSocket closed"))
            self._pending.clear()

    @staticmethod
    def _put_latest(queue: asyncio.Queue, item: dict):
        try:
            queue.put_nowait(item)
        except asyncio.QueueFull:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(item)
            except asyncio.QueueFull:
                pass

    async def request(self, payload: dict, timeout: float = 15) -> dict:
        if self.ws is None:
            raise DerivError("WebSocket is not connected.")
        req_id = next(self._counter)
        message = dict(payload)
        message["req_id"] = req_id
        future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = future
        try:
            await self.ws.send(json.dumps(message))
            return await asyncio.wait_for(future, timeout=timeout)
        except Exception:
            self._pending.pop(req_id, None)
            raise

    async def subscribe_ticks(self, symbol: str):
        return await self.request({"ticks": symbol, "subscribe": 1}, timeout=15)

    async def buy_call_put(self, symbol: str, direction: str, stake: float, duration_minutes: int):
        if not self.authorized:
            raise DerivError("Authenticated trading session required.")
        contract_type = {"CALL": "CALL", "PUT": "PUT"}.get(direction.upper())
        if not contract_type:
            raise DerivError("Direction must be CALL or PUT.")
        proposal = await self.request({
            "proposal": 1,
            "amount": round(stake, 2),
            "basis": "stake",
            "contract_type": contract_type,
            "currency": self.currency,
            "duration": int(duration_minutes),
            "duration_unit": "m",
            "symbol": symbol,
        })
        proposal_id = proposal.get("proposal", {}).get("id")
        ask_price = proposal.get("proposal", {}).get("ask_price")
        if not proposal_id or ask_price is None:
            raise DerivError("Proposal response missing proposal ID or ask price.")
        bought = await self.request({"buy": proposal_id, "price": float(ask_price)}, timeout=20)
        contract = bought.get("buy", {})
        contract_id = contract.get("contract_id")
        if not contract_id:
            raise DerivError("Buy response did not include a contract ID.")
        # Subscribe to settlement updates. The first response is correlated by req_id.
        await self.request({
            "proposal_open_contract": 1,
            "contract_id": int(contract_id),
            "subscribe": 1,
        }, timeout=15)
        return {
            "contract_id": contract_id,
            "buy_price": contract.get("buy_price", ask_price),
            "transaction_id": contract.get("transaction_id"),
        }

    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
            try:
                await self.reader_task
            except (asyncio.CancelledError, Exception):
                pass
            self.reader_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
