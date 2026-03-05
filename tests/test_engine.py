import pandas as pd
from engine import calculate_supertrend


def test_calculate_supertrend_returns_tuple_and_last_close_matches():
    # create synthetic data with at least 12 rows
    data = {
        'time': list(range(12)),
        'open': [100 + i for i in range(12)],
        'high': [101 + i for i in range(12)],
        'low': [99 + i for i in range(12)],
        'close': [100 + i for i in range(12)],
        'vol': [1000 for _ in range(12)],
    }
    df = pd.DataFrame(data)
    st_val, last_close, c_h, c_l = calculate_supertrend(df)

    # check types
    assert isinstance(st_val, float)

    # last_close/high/low should match the last values in the df
    assert last_close == df['close'].iloc[-1]
    assert c_h == df['high'].iloc[-1]
    assert c_l == df['low'].iloc[-1]


def test_calculate_supertrend_short_df_returns_zeros():
    df = pd.DataFrame(columns=['time','open','high','low','close','vol'])
    st_val, last_close, c_h, c_l = calculate_supertrend(df)
    assert (st_val, last_close, c_h, c_l) == (0.0, 0.0, 0.0, 0.0)
