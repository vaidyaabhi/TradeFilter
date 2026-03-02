# 🛡️ TradeFilter Terminal v9

Professional intraday filtering and execution terminal with a side-by-side Bullish/Bearish view and a 2-trade discipline limit.

## 🚀 Quick Start for Ganesh
1. **Sync**: `git pull origin main`
2. **Install**: `pip install python-dotenv streamlit-autorefresh flask fyers-apiv3`
3. **Setup**: Create a `.env` file with your Fyers and Telegram credentials.
4. **Initialize**: `python db_setup.py`

## 🚦 Daily Morning Routine
1. **Login**: `python login_manager.py`
2. **Listen**: `python backend_listener.py`
3. **Launch**: `streamlit run dashboard_ui.py`
