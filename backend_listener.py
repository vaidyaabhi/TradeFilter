from fastapi import FastAPI, Request, Query, BackgroundTasks
import sqlite3
from datetime import datetime
import uvicorn

app = FastAPI()

def save_to_db(stocks, sentiment):
    """Background task to handle DB writes without blocking the API response"""
    try:
        # Added timeout to prevent "database is locked" during high volatility
        conn = sqlite3.connect('trading.db', timeout=10)
        cursor = conn.cursor()
        
        # Prepare data for bulk insertion
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_insert = [(s.strip(), sentiment, now) for s in stocks if s.strip()]
        
        if data_to_insert:
            # executemany is 20x-100x faster than a for-loop for multiple stocks
            cursor.executemany("INSERT INTO staged_stocks VALUES (?, ?, ?)", data_to_insert)
            conn.commit()
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        conn.close()

@app.post("/alert")
async def handle_alert(request: Request, background_tasks: BackgroundTasks, tag: str = Query(...)):
    data = await request.json()
    stocks_list = data.get("stocks", "").split(",")
    sentiment = tag.capitalize()

    # Use BackgroundTasks so ngrok/Chartink gets a "200 OK" immediately
    # while the database write happens in the background.
    background_tasks.add_task(save_to_db, stocks_list, sentiment)
    
    return {"status": "success", "count": len(stocks_list)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)