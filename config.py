import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# 🔑 FYERS CREDENTIALS (Loaded from .env)
CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "9RX3UXDLG9-100")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
REDIRECT_URI = "http://127.0.0.1:5000/login"

# 📱 TELEGRAM CREDENTIALS
TELE_TOKEN = os.getenv("TELE_TOKEN")
TELE_CHAT_ID = os.getenv("TELE_CHAT_ID")

# ⚙️ TRADING SETTINGS
BUFFER_PERCENT = 0.05
RISK_PER_TRADE = 1000
REFRESH_RATE = 2 
NGROK_URL = os.getenv("NGROK_URL", "https://hwa-peerless-confinedly.ngrok-free.dev")

# --- SCANNER & RANKING SETTINGS ---
MIN_DAY_CHANGE = 0.75  
TIMEFRAME = "5" 
MAX_WORKERS = 10

# --- DATABASE CONFIG ---
DB_URL = "sqlite:///trading.db"
