import sqlite3
import pandas as pd

def get_live_alerts(sentiment):
    """
    Handles all SORTING and FILTERING.
    UI calls this to get a clean list of today's stocks.
    """
    conn = sqlite3.connect('trading.db')
    
    # FILTER: Today only AND specific sentiment (Bullish/Bearish)
    # SORT: Newest alerts at the top (DESC)
    query = f"""
        SELECT symbol, timestamp 
        FROM staged_stocks 
        WHERE sentiment = '{sentiment}' 
        AND date(timestamp) = date('now') 
        ORDER BY timestamp DESC
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        # Returns empty dataframe if table doesn't exist yet
        df = pd.DataFrame(columns=['symbol', 'timestamp'])
    
    conn.close()
    return df