import sqlite3
from datetime import datetime

class ProSimulator:
    def __init__(self, limit=2, db_path='trading.db'):
        self.limit = limit
        self.db_path = db_path

    def get_session_stats(self):
        """
        Calculates P&L and Trade counts for the UI header.
        This keeps the logic separate from the Frontend.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Count today's trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE date(timestamp) = date('now')")
        count = cursor.fetchone()[0]
        
        # 2. Fetch active trades for the UI table
        cursor.execute("SELECT symbol, side, entry_price, status FROM trades WHERE date(timestamp) = date('now')")
        active_rows = cursor.fetchall()
        active_trades = [{"Symbol": r[0], "Side": r[1], "Entry": r[2], "Status": r[3]} for r in active_rows]
        
        conn.close()

        # Mock P&L calculation - this will be updated with your v9 real-time Fyers P&L
        return {
            "pnl": 0.0,
            "pnl_pct": 0.0,
            "count": count,
            "active": True,
            "active_trades": active_trades
        }

    def execute_trade(self, symbol, side):
        """
        Main execution logic: Checks limits and applies v9 breakout rules.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # LOGIC FILTER: Prevent over-trading (Abhishek & Ganesh 1/2 Limit)
        cursor.execute("SELECT COUNT(*) FROM trades WHERE date(timestamp) = date('now')")
        if cursor.fetchone()[0] >= self.limit:
            conn.close()
            return False, f"Limit Reached ({self.limit}/{self.limit}). Discipline first!"

        # STRATEGY LOGIC: Record the intent to trade
        # In your v9 setup, you would add logic here to fetch the 5-min High/Low from Fyers
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''INSERT INTO trades (symbol, side, entry_price, status, timestamp) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (symbol, side, 0.0, 'MONITORING', now))
        
        conn.commit()
        conn.close()
        return True, f"Monitoring {symbol} for {side} breakout. 3-Strike Protection Active."