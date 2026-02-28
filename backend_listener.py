from fastapi import FastAPI, Request
from database import SessionLocal, StagedStock
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def handle_chartink(request: Request):
    data = await request.json()
    stocks = [x.strip() for x in data.get('stocks', '').split(',')]
    db = SessionLocal()
    for s in stocks:
        if not db.query(StagedStock).filter(StagedStock.symbol == s).first():
            # Add ranking logic here later
            db.add(StagedStock(symbol=s, rank_score=1.0))
    db.commit()
    db.close()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
