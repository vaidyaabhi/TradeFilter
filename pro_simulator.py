import os
import sqlite3
import pandas as pd  # Added this to fix the error
from datetime import datetime
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

load_dotenv(override=True)

class ProSimulator:
    def __init__(self, db_path="trading.db"):
        self.db_path = db_path
        self.client_id = os.getenv("FYERS_CLIENT_ID")
        self.access_token = os.getenv("FYERS_ACCESS_TOKEN")
        # Initialize Fyers
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id, 
            token=self.access_token, 
            is_async=False, 
            log_path="/tmp"
        )
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades 
                        (symbol TEXT, side TEXT, entry_price REAL, exit_price REAL, status TEXT, timestamp TEXT)''')
        
        # Schema migration to ensure all columns exist
        cursor.execute("PRAGMA table_info(trades)")
        columns = [column[1] for column in cursor.fetchall()]
        for col in ['entry_price', 'exit_price']:
            if col not in columns:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {col} REAL DEFAULT 0.0")
        if 'status' not in columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN status TEXT DEFAULT 'OPEN'")
        conn.commit()
        conn.close()

    def get_balance(self):
        try:
            funds = self.fyers.funds()
            if funds.get('s') == 'ok':
                for item in funds.get('fund_limit', []):
                    # Fixed for your specific account structure
                    if item.get('title') == 'Available Balance':
                        return float(item.get('equityAmount', 0.0))
        except:
            pass
        return 0.0

    def get_ltp(self, symbol):
        try:
            data = {"symbols": f"NSE:{symbol}-EQ"}
            res = self.fyers.quotes(data)
            if res.get('s') == 'ok':
                return res['d'][0]['v']['lp']
        except:
            pass
        return 0.0

    def execute_trade(self, symbol, side):
        price = self.get_ltp(symbol)
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO trades (symbol, side, entry_price, status, timestamp) VALUES (?, ?, ?, ?, ?)", 
                     (symbol, side, price, "OPEN", datetime.now().strftime("%H:%M:%S")))
        conn.commit()
        conn.close()
        return price

    def exit_trade(self, rowid, symbol):
        price = self.get_ltp(symbol)
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE trades SET status='CLOSED', exit_price=? WHERE rowid=?", (price, rowid))
        conn.commit()
        conn.close()

    def get_performance(self):
        conn = sqlite3.connect(self.db_path)
        # Using rowid for unique button keys
        df = pd.read_sql("SELECT rowid, * FROM trades ORDER BY timestamp DESC", conn)
        conn.close()
        
        total_pnl = 0.0
        wins = 0
        closed_count = 0
        processed = []
        
        for _, t in df.iterrows():
            if t['status'] == "OPEN":
                ltp = self.get_ltp(t['symbol'])
                pnl = (ltp - t['entry_price']) if t['side'] == "BUY" else (t['entry_price'] - ltp)
            else:
                ltp = t['exit_price']
                pnl = (t['exit_price'] - t['entry_price']) if t['side'] == "BUY" else (t['entry_price'] - t['exit_price'])
                closed_count += 1
                if pnl > 0: wins += 1
            
            total_pnl += pnl
            processed.append({**t, 'ltp': ltp, 'pnl': pnl})
            
        win_rate = (wins / closed_count * 100) if closed_count > 0 else 0
        return processed, total_pnl, win_rate, len(df)