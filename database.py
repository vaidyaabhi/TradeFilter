import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional
import config

DB_PATH = config.DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS staged_stocks (symbol TEXT, sentiment TEXT, timestamp TEXT);
        CREATE TABLE IF NOT EXISTS trades (rowid INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, side TEXT, entry_price REAL, sl_price REAL, exit_price REAL, qty INTEGER, status TEXT, timestamp TEXT, expected_max_loss REAL DEFAULT 0.0);
        CREATE TABLE IF NOT EXISTS wallet (balance REAL);
        CREATE TABLE IF NOT EXISTS defense_logs (timestamp TEXT, symbol TEXT, old_sl REAL, new_sl REAL, msg TEXT);
    ''')
    # migration: ensure expected_max_loss column exists on older DBs
    cols = [r[1] for r in conn.execute("PRAGMA table_info(trades)").fetchall()]
    if 'expected_max_loss' not in cols:
        try:
            conn.execute("ALTER TABLE trades ADD COLUMN expected_max_loss REAL DEFAULT 0.0")
        except Exception:
            pass
    cur = conn.execute("SELECT balance FROM wallet")
    if cur.fetchone() is None:
        conn.execute("INSERT INTO wallet VALUES (?)", (config.INITIAL_PAPER_BALANCE,))
    conn.commit()
    conn.close()

def _get_conn():
    return sqlite3.connect(DB_PATH, timeout=30)

def get_wallet_balance() -> float:
    conn = _get_conn(); cur = conn.execute("SELECT balance FROM wallet"); row = cur.fetchone(); conn.close()
    return float(row[0]) if row else 0.0

def get_all_trades():
    conn = _get_conn(); df = pd.read_sql("SELECT rowid, * FROM trades", conn); conn.close(); return df

def get_open_trades():
    conn = _get_conn(); df = pd.read_sql("SELECT rowid, * FROM trades WHERE status='OPEN'", conn); conn.close(); return df

def get_staged_alerts():
    conn = _get_conn(); df = pd.read_sql("SELECT * FROM staged_stocks ORDER BY timestamp DESC", conn); conn.close(); return df

def insert_trade(symbol: str, side: str, entry_price: float, sl_price: float, qty: int, expected_max_loss: float = 0.0, timestamp: Optional[str]=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M:%S")
    conn = _get_conn(); conn.execute("INSERT INTO trades (symbol, side, entry_price, sl_price, qty, status, timestamp, expected_max_loss) VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?)", (symbol, side, entry_price, sl_price, qty, timestamp, expected_max_loss)); conn.commit(); conn.close()

def adjust_wallet(amount: float):
    # amount may be positive or negative
    conn = _get_conn(); conn.execute("UPDATE wallet SET balance = balance + ?", (amount,)); conn.commit(); conn.close()

def update_trade_sl(rowid: int, new_sl: float):
    conn = _get_conn(); conn.execute("UPDATE trades SET sl_price=? WHERE rowid=?", (new_sl, rowid)); conn.commit(); conn.close()

def insert_defense_log(timestamp: str, symbol: str, old_sl: float, new_sl: float, msg: str):
    conn = _get_conn(); conn.execute("INSERT INTO defense_logs VALUES (?, ?, ?, ?, ?)", (timestamp, symbol, old_sl, new_sl, msg)); conn.commit(); conn.close()

def close_trade(rowid: int, exit_price: float):
    conn = _get_conn(); conn.execute("UPDATE trades SET status='CLOSED', exit_price=? WHERE rowid=?", (exit_price, rowid)); conn.commit(); conn.close()

def reset_db(initial_balance: float = None):
    if initial_balance is None:
        initial_balance = config.INITIAL_PAPER_BALANCE
    conn = _get_conn(); conn.executescript("DELETE FROM staged_stocks; DELETE FROM trades; DELETE FROM defense_logs;"); conn.execute("UPDATE wallet SET balance=?", (initial_balance,)); conn.commit(); conn.close()

def get_defense_logs(limit: int = 5):
    conn = _get_conn(); df = pd.read_sql("SELECT * FROM defense_logs ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,)); conn.close(); return df
