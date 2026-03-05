import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import os
from fyers_apiv3 import fyersModel
import config, database, os

_defense_thread_started = False
_auto_trail_thread_started = False

# A lightweight scans store (used by the ported auto_trail_sl)
SCANS_DATA = {}

# cached fyers client
_fyers_client = None

def get_fyers_client():
    """Return a cached fyers client or create one if missing.

    Uses the FYERS_ACCESS_ENV variable from `config` to read the access token from env/.env.
    Returns None if token or client creation fails.
    """
    global _fyers_client
    try:
        if _fyers_client is not None:
            return _fyers_client
        token = os.getenv(getattr(config, 'FYERS_ACCESS_ENV', 'FYERS_ACCESS_TOKEN'))
        if not token:
            return None
        _fyers_client = fyersModel.FyersModel(client_id=config.CLIENT_ID, token=token, is_async=False)
        return _fyers_client
    except Exception:
        _fyers_client = None
        return None

def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 1.0):
    """Canonical Supertrend implementation (ported from ProSimulator).

    Returns a tuple: (last_supertrend_value, last_close, last_high, last_low)
    If input is insufficient, returns four zeros.
    """
    if df is None or df.empty or len(df) < period + 1:
        return 0.0, 0.0, 0.0, 0.0

    df = df.copy()
    # ensure required columns exist and have proper dtypes
    for col in ['high', 'low', 'close']:
        if col not in df.columns:
            return 0.0, 0.0, 0.0, 0.0

    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = (df['high'] - df['close'].shift(1)).abs()
    df['l-pc'] = (df['low'] - df['close'].shift(1)).abs()
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    # use the same ATR smoothing as ProSimulator (EWMA with alpha=1/period)
    df['atr'] = df['tr'].ewm(alpha=1.0 / period, adjust=False).mean()

    hl2 = (df['high'] + df['low']) / 2.0
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])

    df['final_upper'] = 0.0
    df['final_lower'] = 0.0
    df['supertrend'] = 0.0

    # initialize previous values to the bands for indices < period
    for i in range(0, len(df)):
        if i < period:
            df.at[i, 'final_upper'] = df.at[i, 'upperband']
            df.at[i, 'final_lower'] = df.at[i, 'lowerband']
            # leave supertrend at 0 for warm-up period
            continue

        # final upper
        if (df.at[i, 'upperband'] < df.at[i-1, 'final_upper']) or (df.at[i-1, 'close'] > df.at[i-1, 'final_upper']):
            df.at[i, 'final_upper'] = df.at[i, 'upperband']
        else:
            df.at[i, 'final_upper'] = df.at[i-1, 'final_upper']

        # final lower
        if (df.at[i, 'lowerband'] > df.at[i-1, 'final_lower']) or (df.at[i-1, 'close'] < df.at[i-1, 'final_lower']):
            df.at[i, 'final_lower'] = df.at[i, 'lowerband']
        else:
            df.at[i, 'final_lower'] = df.at[i-1, 'final_lower']

        # supertrend
        prev_st = df.at[i-1, 'supertrend']
        if prev_st == df.at[i-1, 'final_upper'] and df.at[i, 'close'] < df.at[i, 'final_upper']:
            df.at[i, 'supertrend'] = df.at[i, 'final_upper']
        elif prev_st == df.at[i-1, 'final_upper'] and df.at[i, 'close'] > df.at[i, 'final_upper']:
            df.at[i, 'supertrend'] = df.at[i, 'final_lower']
        elif prev_st == df.at[i-1, 'final_lower'] and df.at[i, 'close'] > df.at[i, 'final_lower']:
            df.at[i, 'supertrend'] = df.at[i, 'final_lower']
        elif prev_st == df.at[i-1, 'final_lower'] and df.at[i, 'close'] < df.at[i, 'final_lower']:
            df.at[i, 'supertrend'] = df.at[i, 'final_upper']
        else:
            if df.at[i, 'close'] <= df.at[i, 'final_upper']:
                df.at[i, 'supertrend'] = df.at[i, 'final_upper']
            else:
                df.at[i, 'supertrend'] = df.at[i, 'final_lower']

    # return last computed values
    last_idx = df.index[-1]
    last_st = df.at[last_idx, 'supertrend']
    last_close = float(df.at[last_idx, 'close'])
    last_high = float(df.at[last_idx, 'high'])
    last_low = float(df.at[last_idx, 'low'])
    return float(last_st), last_close, last_high, last_low


def calculate_supertrend_series(df: pd.DataFrame, period: int = 10, multiplier: float = 1.0):
    """Return full Supertrend series for a dataframe (ported from ProSimulator).

    This mirrors the original ProSimulator behavior so callers that expect a per-candle
    supertrend column can use this helper.
    """
    if df is None or df.empty or len(df) < period + 1:
        return pd.Series([], dtype=float)

    df = df.copy()
    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = (df['high'] - df['close'].shift(1)).abs()
    df['l-pc'] = (df['low'] - df['close'].shift(1)).abs()
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    df['atr'] = df['tr'].ewm(alpha=1.0 / period, adjust=False).mean()

    hl2 = (df['high'] + df['low']) / 2.0
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])

    df['final_upper'] = 0.0
    df['final_lower'] = 0.0
    df['supertrend'] = 0.0

    for i in range(period, len(df)):
        if (df['upperband'].iloc[i] < df['final_upper'].iloc[i-1]) or (df['close'].iloc[i-1] > df['final_upper'].iloc[i-1]):
            df.at[df.index[i], 'final_upper'] = df['upperband'].iloc[i]
        else:
            df.at[df.index[i], 'final_upper'] = df['final_upper'].iloc[i-1]

        if (df['lowerband'].iloc[i] > df['final_lower'].iloc[i-1]) or (df['close'].iloc[i-1] < df['final_lower'].iloc[i-1]):
            df.at[df.index[i], 'final_lower'] = df['lowerband'].iloc[i]
        else:
            df.at[df.index[i], 'final_lower'] = df['final_lower'].iloc[i-1]

        if df['supertrend'].iloc[i-1] == df['final_upper'].iloc[i-1] and df['close'].iloc[i] < df['final_upper'].iloc[i]:
            df.at[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
        elif df['supertrend'].iloc[i-1] == df['final_upper'].iloc[i-1] and df['close'].iloc[i] > df['final_upper'].iloc[i]:
            df.at[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
        elif df['supertrend'].iloc[i-1] == df['final_lower'].iloc[i-1] and df['close'].iloc[i] > df['final_lower'].iloc[i]:
            df.at[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
        elif df['supertrend'].iloc[i-1] == df['final_lower'].iloc[i-1] and df['close'].iloc[i] < df['final_lower'].iloc[i]:
            df.at[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
        else:
            if df['close'].iloc[i] <= df['final_upper'].iloc[i]:
                df.at[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
            else:
                df.at[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]

    return df['supertrend']

def get_market_data(s: str):
    try:
        fyers = get_fyers_client() or fyersModel.FyersModel(client_id=config.CLIENT_ID, token=os.getenv(getattr(config, 'FYERS_ACCESS_ENV', 'FYERS_ACCESS_TOKEN')), is_async=False)
        ltp = fyers.quotes({"symbols": f"NSE:{s}-EQ"})['d'][0]['v']['lp']
        res = fyers.history({
            "symbol": f"NSE:{s}-EQ",
            "resolution": "5",
            "date_format": "1",
            "range_from": (datetime.now()-timedelta(days=2)).strftime("%Y-%m-%d"),
            "range_to": datetime.now().strftime("%Y-%m-%d"),
            "cont_flag": "1"
        })
        df = pd.DataFrame(res['candles'], columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        st_v, last_close, c_h, c_l = calculate_supertrend(df)
        return ltp, st_v, last_close, c_h, c_l
    except Exception:
        return 0.0, 0.0, 0.0, 0.0, 0.0


def get_technical_data(symbol: str, specific_time_str: str | None = None):
    """Ported from ProSimulator.get_technical_data.

    Returns (high, low, st, close, candle_low) for the matched candle.
    If data isn't available, returns five zeros.
    """
    try:
        fy = get_fyers_client()
        if fy is None:
            # fallback: try to create directly
            fy = fyersModel.FyersModel(client_id=config.CLIENT_ID, token=os.getenv(getattr(config, 'FYERS_ACCESS_ENV', 'FYERS_ACCESS_TOKEN')), is_async=False)
        clean = symbol.replace('&', '_').replace("BOSCH", "BOSCHLTD").replace("M_M", "M&M")
        fy_sym = f"NSE:{clean}-EQ"

        target_time = None
        if specific_time_str:
            # use previous 5-minute candle
            target_time = (datetime.strptime(specific_time_str, "%H:%M") - timedelta(minutes=5)).strftime('%H:%M')

        today = datetime.now().strftime('%Y-%m-%d')
        past = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        data = {"symbol": fy_sym, "resolution": "5", "date_format": "1", "range_from": past, "range_to": today, "cont_flag": "1"}
        resp = fy.history(data=data)
        if 'candles' in resp:
            df = pd.DataFrame(resp['candles'], columns=['date', 'open', 'high', 'low', 'close', 'vol'])
            # convert epoch -> IST minute string
            df['time_str'] = pd.to_datetime(df['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.strftime('%H:%M')
            # compute per-candle supertrend series
            st_series = calculate_supertrend_series(df)
            # If series is empty, return zeros
            if st_series.empty:
                return 0.0, 0.0, 0.0, 0.0, 0.0
            df['st'] = st_series
            if target_time:
                match = df[df['time_str'] == target_time]
                if not match.empty:
                    row = match.iloc[-1]
                    return float(row['high']), float(row['low']), float(row['st']), float(row['close']), float(row['low'])
            else:
                row = df.iloc[-2]
                return float(row['high']), float(row['low']), float(row['st']), float(row['close']), float(row['low'])
    except Exception:
        pass
    return 0.0, 0.0, 0.0, 0.0, 0.0

def compute_order_qty(ltp: float, st_sl: float, risk_val: float, wallet_balance: float, side: str = "BUY"):
    """Compute a safe order quantity and expected max loss.

    Directional loss per unit is calculated depending on side:
      - BUY: loss_per_unit = entry_price - sl_price
      - SELL: loss_per_unit = sl_price - entry_price

    Returns (qty, expected_max_loss, qty_by_risk, qty_by_cash, loss_per_unit)
    """
    try:
        entry = float(ltp)
        sl = float(st_sl)
    except Exception:
        entry = float(ltp) if ltp else 0.0
        sl = float(st_sl) if st_sl else 0.0

    # directional per-unit loss
    if side and side.upper() == "SELL":
        loss_per_unit = max(0.0, sl - entry)
    else:
        # default BUY
        loss_per_unit = max(0.0, entry - sl)

    # If loss_per_unit is zero (invalid SL), fallback to absolute diff but warn by returning zero expected loss
    if loss_per_unit <= 0:
        diff_for_risk = abs(entry - sl)
    else:
        diff_for_risk = loss_per_unit

    if diff_for_risk <= 0:
        qty_by_risk = 1
    else:
        qty_by_risk = int(risk_val / diff_for_risk)
        if qty_by_risk < 1:
            qty_by_risk = 1

    try:
        qty_by_cash = int(wallet_balance / entry) if entry > 0 else 1
    except Exception:
        qty_by_cash = 1
    if qty_by_cash < 1:
        qty_by_cash = 1

    qty = min(qty_by_risk, qty_by_cash)
    expected_max_loss = loss_per_unit * qty
    return int(qty), float(expected_max_loss), int(qty_by_risk), int(qty_by_cash), float(loss_per_unit)

def is_api_online():
    try:
        fy = fyersModel.FyersModel(client_id=config.CLIENT_ID, token=os.getenv("FYERS_ACCESS_TOKEN"), is_async=False)
        return fy.get_profile().get('s') == 'ok'
    except Exception:
        return False

def defense_monitor_worker():
    while True:
        try:
            now = datetime.now()
            open_trades = database.get_open_trades()
            if not open_trades.empty:
                for _, t in open_trades.iterrows():
                    _, st_v, last_close, c_h, c_l = get_market_data(t['symbol'])
                    curr_sl = t['sl_price']
                    if t['side'] == "BUY" and last_close < st_v:
                        new_sl = c_l * 0.9995
                        if new_sl > curr_sl:
                            database.update_trade_sl(t['rowid'], new_sl)
                            database.insert_defense_log(now.strftime("%H:%M:%S"), t['symbol'], curr_sl, new_sl, "ST Breach: SL to Low")
                    elif t['side'] == "SELL" and last_close > st_v:
                        new_sl = c_h * 1.0005
                        if new_sl < curr_sl or curr_sl == 0:
                            database.update_trade_sl(t['rowid'], new_sl)
                            database.insert_defense_log(now.strftime("%H:%M:%S"), t['symbol'], curr_sl, new_sl, "ST Breach: SL to High")
        except Exception:
            pass
        time.sleep(60)

def start_defense_monitor():
    global _defense_thread_started
    if not _defense_thread_started:
        threading.Thread(target=defense_monitor_worker, daemon=True).start()
        _defense_thread_started = True


def auto_trail_sl_worker():
    """Ported auto_trail_sl behavior adapted to engine.SCANS_DATA and configurable defaults."""
    SQUARE_OFF_TIME = getattr(config, 'SQUARE_OFF_TIME', '15:15')
    REFRESH_RATE = getattr(config, 'REFRESH_RATE', 60)
    BUFFER_PERCENT = getattr(config, 'BUFFER_PERCENT', 0.5)

    while True:
        try:
            if not SCANS_DATA:
                time.sleep(5)
                continue

            now_str = datetime.now().strftime('%H:%M')
            if now_str >= SQUARE_OFF_TIME:
                time.sleep(10)
                continue

            for scan in list(SCANS_DATA.keys()):
                if scan not in SCANS_DATA:
                    continue
                for stock, d in list(SCANS_DATA[scan].items()):
                    if d.get('status') == 'RUNNING':
                        h, l, st, close, candle_low = get_technical_data(stock)
                        if st and st > 0:
                            d['st_val'] = round(st, 2)
                            if 'reversal_trailed' not in d:
                                d['reversal_trailed'] = False
                            if close > st:
                                d['reversal_trailed'] = False
                            elif close < st:
                                if d['reversal_trailed'] == False:
                                    potential_new_sl = round(candle_low - (candle_low * BUFFER_PERCENT / 100), 2)
                                    if potential_new_sl > d.get('sl', 0):
                                        d['sl'] = potential_new_sl
                                        d['trail_count'] = d.get('trail_count', 0) + 1
                                        # try to send telegram if configured
                                        try:
                                            if getattr(config, 'TELE_TOKEN', None):
                                                import requests
                                                requests.post(f"https://api.telegram.org/bot{config.TELE_TOKEN}/sendMessage", json={"chat_id": config.TELE_CHAT_ID, "text": f"🔄 <b>TRAILING UP: {stock}</b>\n1st Reversal Detected.\nNew SL: {d['sl']}"}, timeout=2)
                                        except Exception:
                                            pass
                                    d['reversal_trailed'] = True
        except Exception:
            pass
        time.sleep(REFRESH_RATE)


def start_auto_trail():
    global _auto_trail_thread_started
    if not _auto_trail_thread_started:
        threading.Thread(target=auto_trail_sl_worker, daemon=True).start()
        _auto_trail_thread_started = True
