import streamlit as st
from data_manager import get_live_alerts
from pro_simulator import ProSimulator
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration (Wide mode for side-by-side view)
st.set_page_config(layout="wide", page_title="TradeFilter Terminal", page_icon="🛡️")

# 2. Live Refresh (Refreshes the UI every 2 seconds for a "Live" feel)
st_autorefresh(interval=2000, key="datarefresh")

# 3. Initialize "Diff" Components
# These are imported from your logic files
sim = ProSimulator(limit=2)

# --- SECTION 1: HEADER & P&L ---
st.title("🛡️ TradeFilter Terminal")

# Fetch P&L and stats from the Simulator Logic
stats = sim.get_session_stats() 
p1, p2, p3 = st.columns(3)
p1.metric("Simulated P&L", f"₹ {stats['pnl']}", f"{stats['pnl_pct']}%")
p2.metric("Today's Trades", f"{stats['count']} / 2")
p3.metric("System Status", "🟢 Connected via ngrok")

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
            # Table Header with specific ratio [3, 1] for alignment
            h1, h2 = st.columns([3, 1])
            h1.write("**Symbol**")
            h2.write("**Action**")
            st.divider()

            for _, row in df.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"### {row['symbol']}")
                btn_label = "BUY" if sentiment == "Bullish" else "SELL"
                # use_container_width makes the buttons uniform like in your image
                if c2.button(btn_label, key=f"{sentiment}_{row['symbol']}", use_container_width=True):
                    success, msg = sim.execute_trade(row['symbol'], btn_label)
                    if success: st.toast(msg)
                    else: st.error(msg)

# Draw the two columns side-by-side
render_scanner_column("Bullish", col_bull)
render_scanner_column("Bearish", col_bear)

# --- SECTION 3: ACTIVE TRADES TABLE ---
if stats['active_trades']:
    st.divider()
    st.markdown("### 📊 Active Position Tracking")
    st.table(stats['active_trades'])