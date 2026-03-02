import sqlite3

def setup_database():
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    # 1. Table for incoming Chartink Alerts (for data_manager)
    cursor.execute('''CREATE TABLE IF NOT EXISTS staged_stocks (
                        symbol TEXT, 
                        sentiment TEXT, 
                        timestamp DATETIME)''')
    
    # 2. Table for Strategy Execution (for pro_simulator)
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                        symbol TEXT, 
                        side TEXT, 
                        entry_price REAL DEFAULT 0.0, 
                        status TEXT, 
                        timestamp DATETIME)''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    setup_database()