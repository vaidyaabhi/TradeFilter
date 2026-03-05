import streamlit as st
import pandas as pd
from datetime import datetime, time as dt_time, timedelta
import os
import time
import webbrowser
import threading
from flask import Flask, request
from fyers_apiv3 import fyersModel
import config, database, engine

# --- 1. INITIAL SETUP ---
# config.py handles .env loading and secrets

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.error("Missing dependency: Run 'pip install streamlit-autorefresh'")

st.set_page_config(page_title="TradeFilter Elite Cockpit", layout="wide", initial_sidebar_state="collapsed")

DB_PATH = config.DB_PATH
INITIAL_PAPER_BALANCE = config.INITIAL_PAPER_BALANCE
CLIENT_ID = config.CLIENT_ID
SECRET_KEY = config.SECRET_KEY
REDIRECT_URI = config.REDIRECT_URI

# --- 2. DATABASE INIT ---
database.init_db()

# --- 3. LOGIN & AUTH LOGIC (RESTORED AS PER YOUR REQUEST) ---
captured_auth_code = None
login_app = Flask(__name__ + "_login")

@login_app.route('/login')
def callback_handler():
    global captured_auth_code
    code = request.args.get('auth_code')
    if code:
        captured_auth_code = code
        return "<h1>✅ Login Successful!</h1><p>You can close this tab.</p>"
    return "❌ No code found"

def run_login_server():
    try:
        login_app.run(port=5000, debug=False, use_reloader=False)
    except:
        pass # Port already in use

def perform_fyers_login():
    global captured_auth_code
    captured_auth_code = None
    session = fyersModel.SessionModel(client_id=CLIENT_ID, secret_key=SECRET_KEY, redirect_uri=REDIRECT_URI, response_type="code", grant_type="authorization_code")
    
    # Start server in background
    threading.Thread(target=run_login_server, daemon=True).start()
    webbrowser.open(session.generate_authcode())
    
    # Wait for captured code
    wait_start = time.time()
    while not captured_auth_code and (time.time() - wait_start) < 60:
        time.sleep(1)
    
    if captured_auth_code:
        session.set_token(captured_auth_code)
        response = session.generate_token()
        if "access_token" in response:
            # write back to .env using config helper
            config.set_env_key("FYERS_ACCESS_TOKEN", response["access_token"])
            return True
    return False

# --- 4. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top left, #1a1c24, #0f1117); color: #e2e8f0; }
    [data-testid="stSidebar"] { display: none; }
    .tv-link { color: #3b82f6 !important; text-decoration: none !important; font-weight: 900 !important; font-size: 20px !important; }
    .tv-link:hover { color: #60a5fa !important; text-decoration: underline !important; }
    .glass-card { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; }
    .metric-label { color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; }
    .metric-value { font-size: 26px; font-weight: 900; font-family: 'JetBrains Mono', monospace; }
    .status-pill { padding: 4px 12px; border-radius: 50px; font-size: 10px; font-weight: 900; text-transform: uppercase; margin-right: 5px; }
    .online-neon { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid #10b981; box-shadow: 0 0 8px #10b98144; }
    .offline-neon { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid #ef4444; }
    .exec-row { background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #3b82f6; }
    .bull-border { border-left: 6px solid #10b981; }
    .bear-border { border-left: 6px solid #ef4444; }
    .stButton>button { border-radius: 10px; height: 3.5em; font-weight: 800; }
    div.stButton > button[key*="buy_btn"] { background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important; color: white !important; }
    div.stButton > button[key*="sell_btn"] { background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important; color: white !important; }
    .log-container { background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; font-family: 'JetBrains Mono'; font-size: 12px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5000, key="refresh")

# --- 5. ENGINE CORE ---
# engine.py handles Supertrend math and market data fetch

# --- 6. DEFENSE THREAD ---
if 'defense_active' not in st.session_state:
    # start background defense monitor from engine
    engine.start_defense_monitor()
    st.session_state['defense_active'] = True
if 'auto_trail_active' not in st.session_state:
    # start auto trailing worker from engine
    engine.start_auto_trail()
    st.session_state['auto_trail_active'] = True

# --- 7. RENDER LOGIC ---
wallet_bal = database.get_wallet_balance()
trades_df = database.get_all_trades()

total_pnl = 0.0
for _, t in trades_df.iterrows():
    if t['status'] == 'OPEN':
        p, _, _, _, _ = engine.get_market_data(t['symbol'])
        total_pnl += (p - t['entry_price']) * t['qty'] if t['side'] == "BUY" else (t['entry_price'] - p) * t['qty']
    else:
        total_pnl += (t['exit_price'] - t['entry_price']) * t['qty'] if t['side'] == "BUY" else (t['entry_price'] - t['exit_price']) * t['qty']

# --- 8. HEADER ---
st.write("")
h1, h2, h3, h4 = st.columns([2.5, 1, 1, 0.8])
with h1:
    try: online = engine.is_api_online()
    except: online = False
    def_armed = st.session_state.get('defense_active', False)
    st.markdown(f'# <span style="color:#3b82f6;">TF</span> ELITE', unsafe_allow_html=True)
    st.markdown(f'<span class="status-pill {"online-neon" if online else "offline-neon"}">{"● API ONLINE" if online else "● API OFFLINE"}</span>'
                f'<span class="status-pill {"online-neon" if def_armed else "offline-neon"}">{"● DEFENSE ARMED" if def_armed else "● DEFENSE IDLE"}</span>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<div class="glass-card" style="padding:15px;"><div class="metric-label">Liquidity</div><div class="metric-value">₹{wallet_bal:,.2f}</div></div>', unsafe_allow_html=True)
with h3:
    p_color = "#10b981" if total_pnl >= 0 else "#ef4444"
    st.markdown(f'<div class="glass-card" style="padding:15px; border-bottom: 3px solid {p_color};"><div class="metric-label">Today P&L</div><div class="metric-value" style="color:{p_color};">₹{total_pnl:,.2f}</div></div>', unsafe_allow_html=True)
with h4:
    if st.button("🔑 LOGIN", use_container_width=True):
        with st.spinner("Authorizing..."):
            if perform_fyers_login():
                st.success("Authenticated!")
                time.sleep(1)
                st.rerun()
    if st.button("🚨 RESET", use_container_width=True):
        database.reset_db(INITIAL_PAPER_BALANCE); st.rerun()

# --- 9. TABS ---
t1, t2 = st.tabs(["📡 RADAR ALERTS", "🕹️ COMMAND CENTER"])

with t1:
    risk_val = st.select_slider("Risk Amount (₹)", options=[100, 250, 500, 1000, 2000, 5000], value=500)
    c_l, c_r = st.columns(2)
    alerts = database.get_staged_alerts()
    for sent, col, side_color in [('bull', c_l, 'bull-border'), ('bear', c_r, 'bear-border')]:
        with col:
            st.markdown(f"### {'❇️ BULLISH' if sent == 'bull' else '🛑 BEARISH'}")
            for idx, row in alerts[alerts['sentiment'].str.contains(sent, case=False)].iterrows():
                st.markdown(f'<div class="exec-row {side_color}">', unsafe_allow_html=True)
                l, r = st.columns([3, 1.2])
                tv_url = f"https://www.tradingview.com/chart/?symbol=NSE:{row['symbol']}"
                l.markdown(f'<a href="{tv_url}" target="_blank" class="tv-link">{row["symbol"]}</a><br><small>Detected: {row["timestamp"]}</small>', unsafe_allow_html=True)
                btn_txt = "BUY" if sent == 'bull' else "SELL"
                if r.button(btn_txt, key=f"buy_btn_{idx}_{row['symbol']}", use_container_width=True):
                    # Immediate market execution (simple behaviour like ProSimulator):
                    # Unpack full market data: (ltp, supertrend, last_close, last_high, last_low)
                    ltp, st_val, last_close, last_high, last_low = engine.get_market_data(row['symbol'])
                    # Compute SL from the candle extreme using configured BUFFER_PERCENT to match ProSimulator
                    try:
                        buf = float(getattr(config, 'BUFFER_PERCENT', 0.5)) / 100.0
                    except Exception:
                        buf = 0.005
                    if btn_txt == 'BUY':
                        # SL should be below entry -> use candle low minus buffer
                        st_sl = round(last_low - (last_low * buf), 2) if last_low and last_low > 0 else float(st_val or 0)
                    else:
                        # For SELL, SL should be above entry -> use candle high plus buffer
                        st_sl = round(last_high + (last_high * buf), 2) if last_high and last_high > 0 else float(st_val or 0)
                    wallet_now = database.get_wallet_balance()
                    qty, expected_max_loss, qty_by_risk, qty_by_cash, loss_per_unit = engine.compute_order_qty(ltp, st_sl, risk_val, wallet_now, side=btn_txt)

                    # Cap qty by available cash to ensure the order can be placed
                    try:
                        max_qty_cash = int(wallet_now / ltp) if ltp > 0 else 0
                    except Exception:
                        max_qty_cash = qty_by_cash
                    final_qty = max(0, min(qty, max_qty_cash))

                    if final_qty < 1:
                        st.error(f"Insufficient funds to place even 1 unit (available ₹{wallet_now:,.2f}, price ₹{ltp:.2f}).")
                    else:
                        # perform immediate market trade
                        database.adjust_wallet(-ltp * final_qty)
                        database.insert_trade(row['symbol'], btn_txt, float(ltp), float(st_sl), int(final_qty), float(expected_max_loss), datetime.now().strftime("%H:%M:%S"))
                        # ensure SCANS_DATA monitors it as RUNNING
                        try:
                            if 'PRO' not in engine.SCANS_DATA:
                                engine.SCANS_DATA['PRO'] = {}
                            engine.SCANS_DATA['PRO'][row['symbol']] = {
                                'time': datetime.now().strftime('%H:%M'),
                                'entry': float(ltp),
                                'sl': float(st_sl),
                                'orig_sl': float(st_sl),
                                'qty': int(final_qty),
                                'status': 'RUNNING',
                                'st_val': float(0),
                                'trail_count': 0
                            }
                        except Exception:
                            pass
                        st.success(f"Market order placed: {row['symbol']} {btn_txt} QTY:{final_qty} @ ₹{ltp:.2f}")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # Confirmation panel for pending order
    if 'pending_order' in st.session_state:
        po = st.session_state['pending_order']
        with st.expander(f"Confirm Order: {po['symbol']} {po['side']}", expanded=True):
            st.write(f"QTY: {po['qty']} @ ₹{po['ltp']:.2f}")
            st.write(f"SL: ₹{po['st_sl']:.2f}")
            st.write(f"Expected max loss: ₹{po['expected_max_loss']:,.2f} (requested ₹{po['risk_val']:,})")
            st.write(f"Qty by risk: {po['qty_by_risk']} | Qty by cash: {po['qty_by_cash']}")
            c1, c2 = st.columns([1,1])
            if c1.button("Confirm Order", key="confirm_order"):
                # re-check wallet sufficiency at confirm time
                current_balance = database.get_wallet_balance()
                cost = po['ltp'] * po['qty']
                if current_balance < cost:
                    st.error(f"Insufficient balance: available ₹{current_balance:,.2f}, required ₹{cost:,.2f}.")
                    # offer to adjust to available qty
                    if c1.button("Adjust to available qty", key="adjust_qty"):
                        max_qty_cash = int(database.get_wallet_balance() / po['ltp']) if po['ltp'] > 0 else 1
                        if max_qty_cash < 1:
                            st.error("No available cash to buy even 1 unit.")
                        else:
                            po['qty'] = int(max_qty_cash)
                            po['expected_max_loss'] = float(abs(po['ltp'] - po['st_sl']) * po['qty'])
                            st.session_state['pending_order'] = po
                            # update SCANS_DATA qty/expected loss if present
                            try:
                                if 'PRO' in engine.SCANS_DATA and po['symbol'] in engine.SCANS_DATA['PRO']:
                                    engine.SCANS_DATA['PRO'][po['symbol']]['qty'] = int(po['qty'])
                                    engine.SCANS_DATA['PRO'][po['symbol']]['entry'] = float(po['ltp'])
                                    engine.SCANS_DATA['PRO'][po['symbol']]['sl'] = float(po['st_sl'])
                                    engine.SCANS_DATA['PRO'][po['symbol']]['orig_sl'] = float(po['st_sl'])
                            except Exception:
                                pass
                            st.success(f"Adjusted qty to {po['qty']} based on available balance")
                            st.rerun()
                    if c2.button("Cancel", key="cancel_order"):
                        # remove from SCANS_DATA if we added earlier
                        try:
                            if 'PRO' in engine.SCANS_DATA and po['symbol'] in engine.SCANS_DATA['PRO']:
                                del engine.SCANS_DATA['PRO'][po['symbol']]
                        except Exception:
                            pass
                        del st.session_state['pending_order']
                        st.info("Order cancelled")
                        st.rerun()
                else:
                    # perform the trade
                    database.adjust_wallet(-po['ltp'] * po['qty'])
                    database.insert_trade(po['symbol'], po['side'], po['ltp'], po['st_sl'], po['qty'], po['expected_max_loss'], datetime.now().strftime("%H:%M:%S"))
                    st.success(f"Order placed: {po['symbol']} {po['side']} QTY:{po['qty']}")
                    # mark SCANS_DATA entry as RUNNING so auto-trail treats it as an active trade
                    try:
                        if 'PRO' in engine.SCANS_DATA and po['symbol'] in engine.SCANS_DATA['PRO']:
                            engine.SCANS_DATA['PRO'][po['symbol']]['status'] = 'RUNNING'
                            engine.SCANS_DATA['PRO'][po['symbol']]['entry'] = float(po['ltp'])
                            engine.SCANS_DATA['PRO'][po['symbol']]['qty'] = int(po['qty'])
                    except Exception:
                        pass
                    del st.session_state['pending_order']
                    st.rerun()
            if c2.button("Cancel", key="cancel_order"):
                # remove SCANS_DATA entry if we created it
                try:
                    if 'pending_order' in st.session_state:
                        sym = st.session_state['pending_order']['symbol']
                        if 'PRO' in engine.SCANS_DATA and sym in engine.SCANS_DATA['PRO']:
                            del engine.SCANS_DATA['PRO'][sym]
                except Exception:
                    pass
                if 'pending_order' in st.session_state:
                    del st.session_state['pending_order']
                st.info("Order cancelled")
                st.rerun()

with t2:
    active_list = database.get_open_trades()
    if active_list.empty: st.info("NO ACTIVE POSITIONS")
    else:
        for _, t in active_list.sort_values('timestamp', ascending=False).iterrows():
            st.markdown(f'<div class="exec-row {"bull-border" if t["side"]=="BUY" else "bear-border"}">', unsafe_allow_html=True)
            m1, m2, m3, m4, m5 = st.columns([1.5, 2, 1, 1.5, 1])
            t_url = f"https://www.tradingview.com/chart/?symbol=NSE:{t['symbol']}"
            m1.markdown(f'<a href="{t_url}" target="_blank" class="tv-link" style="font-size:18px;">{t["symbol"]}</a><br><small>{t["side"]} | QTY: {t["qty"]}</small>', unsafe_allow_html=True)
            expected_loss = t.get('expected_max_loss', 0.0) if hasattr(t, 'get') else (t['expected_max_loss'] if 'expected_max_loss' in t.index else 0.0)

            # Retrieve original SL from engine.SCANS_DATA if available
            original_sl_display = "N/A"
            if 'PRO' in engine.SCANS_DATA and t['symbol'] in engine.SCANS_DATA['PRO']:
                original_sl_value = engine.SCANS_DATA['PRO'][t['symbol']].get('orig_sl')
                if original_sl_value is not None:
                    original_sl_display = f"₹{original_sl_value:,.2f}"

            m2.markdown(f"Entry: ₹{t['entry_price']:.2f}<br>"
                        f"Current SL: ₹{t['sl_price']:.2f}<br>"
                        f"Original SL: {original_sl_display}<br>" # Added this line
                        f"Est Loss: ₹{expected_loss:,.2f}", unsafe_allow_html=True)
            # fetch market data including the Supertrend (10,1) value
            p, st10_1, _, _, _ = engine.get_market_data(t['symbol'])
            pnl = (p - t['entry_price']) * t['qty'] if t['side'] == "BUY" else (t['entry_price'] - p) * t['qty']
            m3.markdown(f"LTP: ₹{p:.2f}<br>ST(10,1): ₹{st10_1:.2f}", unsafe_allow_html=True)
            pnl_c = "#10b981" if pnl >= 0 else "#ef4444"
            m4.markdown(f"<span style='color:{pnl_c}; font-weight:900;'>₹{pnl:,.2f}</span>", unsafe_allow_html=True)
            if m5.button("EXIT", key=f"ex_{t['rowid']}", use_container_width=True):
                database.adjust_wallet(p * t['qty'])
                database.close_trade(t['rowid'], p)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🛡️ DEFENSE PROTOCOL LOGS")
logs = database.get_defense_logs(limit=5)
for _, log in logs.iterrows():
    st.markdown(f'<div class="log-container">[{log["timestamp"]}] <b>{log["symbol"]}</b>: {log["msg"]} (QTY: {log["old_sl"]:.2f} → {log["new_sl"]:.2f})</div>', unsafe_allow_html=True)