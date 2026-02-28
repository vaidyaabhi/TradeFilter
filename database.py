from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///trading.db', connect_args={"check_same_thread": False})
Base = declarative_base()

class StagedStock(Base):
    __tablename__ = 'staged_stocks'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    rank_score = Column(Float, default=0.0)
    status = Column(String, default="AWAITING_REVIEW") 
    timestamp = Column(DateTime, default=datetime.now)

class ActiveTrade(Base):
    __tablename__ = 'active_trades'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    entry_price = Column(Float)
    stop_loss = Column(Float)
    pnl = Column(Float, default=0.0)
    status = Column(String, default="RUNNING")

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
