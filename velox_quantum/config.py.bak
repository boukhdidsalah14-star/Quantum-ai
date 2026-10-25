import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _csv_ints(value: str) -> set[int]:
    out = set()
    for part in value.split(","):
        part = part.strip()
        if part:
            try:
                out.add(int(part))
            except ValueError:
                pass
    return out

def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    telegram_token: str
    allowed_user_ids: set[int]
    deriv_pat: str
    deriv_account_id: str
    deriv_app_id: str
    default_symbol: str
    default_stake: float
    max_stake: float
    default_duration_minutes: int
    max_daily_loss: float
    max_consecutive_losses: int
    allow_real_trading: bool

def load_settings() -> Settings:
    return Settings(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        allowed_user_ids=_csv_ints(os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")),
        deriv_pat=os.getenv("DERIV_PAT", "").strip(),
        deriv_account_id=os.getenv("DERIV_ACCOUNT_ID", "").strip(),
        deriv_app_id=os.getenv("DERIV_APP_ID", "1089").strip(),
        default_symbol=os.getenv("DEFAULT_SYMBOL", "R_100").strip(),
        default_stake=float(os.getenv("DEFAULT_STAKE", "1.00")),
        max_stake=float(os.getenv("MAX_STAKE", "2.00")),
        default_duration_minutes=int(os.getenv("DEFAULT_DURATION_MINUTES", "1")),
        max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "10.00")),
        max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3")),
        allow_real_trading=_bool(os.getenv("ALLOW_REAL_TRADING", "false")),
    )
