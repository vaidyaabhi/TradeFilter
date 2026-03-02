import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

# Always load the fresh token from .env
load_dotenv(override=True)

class ProSimulator:
    def __init__(self, limit=2):
        self.limit = limit
        self.client_id = os.getenv("FYERS_CLIENT_ID")
        self.access_token = os.getenv("FYERS_ACCESS_TOKEN")
        
        # Initialize Fyers Model
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id, 
            token=self.access_token, 
            is_async=False, 
            log_path=""
        )

    def get_fyers_balance(self):
        """Fetches live Available Balance from Fyers"""
        try:
            funds = self.fyers.funds()
            if funds.get('s') == 'ok':
                # Extract 'Total Balance' from the fund_limit list
                for item in funds.get('fund_limit', []):
                    if item.get('title') == 'Total Balance':
                        return float(item.get('value', 0.0))
        except Exception:
            return 0.0
        return 0.0

    def get_session_stats(self):
        """Calculates trade count and active positions from DB"""
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        # Count trades taken today
        cursor.execute("SELECT COUNT(*) FROM trades WHERE date(timestamp) = date('now')")
        count = cursor.fetchone()[0]
        
        # Get active trades for the table
        cursor.execute("SELECT symbol, side, entry_price, status, timestamp FROM trades ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        active_trades = []
        for r in rows:
            active_trades.append({
                "Symbol": r[0], "Side": r[1], 
                "Entry": r[2], "Status": r[3], "Time": r[4]
            })
            
        conn.close()
        return {
            "pnl": 0.00, "pnl_pct": 0.0, 
            "count": count, "active_trades": active_trades
        }

    def execute_trade(self, symbol, side):
        """Checks limits and saves trade to DB"""
        stats = self.get_session_stats()
        if stats['count'] >= self.limit:
            return False, f"Limit Reached ({self.limit}/{self.limit}). Discipline first!"

        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        try:
            # For now, we use a mock price of 0.00. 
            # In live v9, we would fetch ltp from self.fyers.get_quotes()
            now = datetime.now().strftime("%H:%M:%S")
            cursor.execute("INSERT INTO trades (symbol, side, entry_price, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                           (symbol, side, 0.00, "MONITORING", now))
            conn.commit()
            return True, f"Monitoring {symbol} for {side} breakout"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()