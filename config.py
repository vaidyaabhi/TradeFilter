import os
from dotenv import load_dotenv, set_key, find_dotenv

# Load .env once
ENV_PATH = find_dotenv()
load_dotenv(ENV_PATH, override=True)

# Expose config constants
DB_PATH = os.getenv("DB_PATH", "trading.db")
INITIAL_PAPER_BALANCE = float(os.getenv("INITIAL_PAPER_BALANCE", "500000.0"))
CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "http://127.0.0.1:5000/login")
# Optional placeholders / defaults for ported ProSimulator behavior
BUFFER_PERCENT = float(os.getenv("BUFFER_PERCENT", "0.5"))          # percent buffer when trailing to candle low
REFRESH_RATE = int(os.getenv("REFRESH_RATE", "60"))                # polling frequency (seconds) for background workers
SQUARE_OFF_TIME = os.getenv("SQUARE_OFF_TIME", "15:15")            # market square-off time

# Telegram placeholders (optional)
TELE_TOKEN = os.getenv("TELE_TOKEN", "")
TELE_CHAT_ID = os.getenv("TELE_CHAT_ID", "")

# Environment token name used by the app
FYERS_ACCESS_ENV = os.getenv("FYERS_ACCESS_ENV", "FYERS_ACCESS_TOKEN")

# Helper to write back to .env
def set_env_key(key: str, value: str):
    # wrapper around dotenv.set_key for callers
    return set_key(ENV_PATH, key, value)
