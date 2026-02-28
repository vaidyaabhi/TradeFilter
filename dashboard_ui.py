import streamlit as st
import pandas as pd
from database import SessionLocal, StagedStock, ActiveTrade

st.set_page_config(layout="wide", page_title="TradeFilter Dashboard")
st.title("🛡️ TradeFilter Terminal")

db = SessionLocal()

# Layout: Ranked Stocks and Live Simulator
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Ranked Candidates")
    stocks = db.query(StagedStock).filter(StagedStock.status == "AWAITING_REVIEW").all()
    if stocks:
        df = pd.DataFrame([{"Symbol": s.symbol, "Rank": s.rank_score} for s in stocks])
        st.table(df)
        selected_stock = st.selectbox("Select Stock to View", [s.symbol for s in stocks])
        if st.button("🚀 Execute Trade"):
            # Move to ActiveTrade logic here
            st.success(f"Trade triggered for {selected_stock}")

with col2:
    st.subheader("Live Pro-Simulator")
    active = db.query(ActiveTrade).all()
    if active:
        st.write(active)
    else:
        st.info("No active trades running.")

db.close()
