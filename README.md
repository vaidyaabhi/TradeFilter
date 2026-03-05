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

## Refactor: 3-tier architecture

The project has been refactored into a simple 3-tier layout to separate concerns and make the codebase easier to maintain.

- `dashboard_ui.py` — UI layer (Streamlit). Contains layout, styling, and user interactions only.
- `engine.py` — Engine layer. Contains Supertrend math, FYERS market-data fetching, API health check, and the defense monitor thread.
- `database.py` — Data layer. All SQLite schema and helper functions (init, trades, wallet, logs, inserts/updates).
- `config.py` — Configuration loader for `.env` values (client id, secret, redirect URI, DB path, initial balance) and helper to write tokens back to `.env`.

How to run

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Ensure `.env` has required keys (see `.env.example` if present). At minimum set `FYERS_CLIENT_ID` and `FYERS_SECRET_KEY`.

3. Start the app:

```bash
streamlit run dashboard_ui.py
```

Notes

- The app writes `FYERS_ACCESS_TOKEN` to your `.env` after successful login using `config.set_env_key()`.
- Keep `.env` out of version control; ensure `.gitignore` contains it.
