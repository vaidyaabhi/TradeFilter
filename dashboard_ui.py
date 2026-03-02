import streamlit as st
from data_manager import get_live_alerts
from pro_simulator import ProSimulator
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TradeFilter Terminal", page_icon="🛡️")

# 2. Live Refresh (2 Seconds)
st_autorefresh(interval=2000, key="datarefresh")

# 3. Initialize Components
sim = ProSimulator(limit=2)

# --- SECTION 1: HEADER & LIVE METRICS ---
st.title("🛡️ TradeFilter Terminal")

stats = sim.get_session_stats() 
live_balance = sim.get_fyers_balance()

p1, p2, p3, p4 = st.columns(4)
p1.metric("Simulated P&L", f"₹ {stats['pnl']}", f"{stats['pnl_pct']}%")
p2.metric("Today's Trades", f"{stats['count']} / 2")
p3.metric("Fyers Balance", f"₹ {live_balance:,.2f}")
p4.metric("System Status", "🟢 Connected", "Live")

st.divider()

# --- SECTION 2: SIDE-BY-SIDE TABLES ---
col_bull, col_bear = st.columns(2)

def render_scanner_column(sentiment, ui_column):
    with ui_column:
        st.subheader(f"{'🟢' if sentiment == 'Bullish' else '🔴'} {sentiment} Candidates")
        df = get_live_alerts(sentiment)
        
        if df.empty:
            st.info(f"Waiting for {sentiment} signals...")
        else:
            h1, h2 = st.columns([3, 1])
            h1.write("**Symbol**")
            h2.write("**Action**")
            st.divider()

            for _, row in df.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"### {row['symbol']}")
                btn_label = "BUY" if sentiment == "Bullish" else "SELL"
                if c2.button(btn_label, key=f"{sentiment}_{row['symbol']}", use_container_width=True):
                    success, msg = sim.execute_trade(row['symbol'], btn_label)
                    if success: st.toast(msg)
                    else: st.error(msg)

render_scanner_column("Bullish", col_bull)
render_scanner_column("Bearish", col_bear)

# --- SECTION 3: ACTIVE TRADES ---
if stats['active_trades']:
    st.divider()
    st.markdown("### 📊 Active Position Tracking")
    # Using a dataframe view for better scrolling on MacBook Air
    st.dataframe(stats['active_trades'], use_container_width=True)