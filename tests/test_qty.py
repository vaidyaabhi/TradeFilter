from engine import compute_order_qty


def test_compute_order_qty_normal():
    qty, expected_max_loss, qty_by_risk, qty_by_cash, loss_per_unit = compute_order_qty(ltp=100.0, st_sl=98.0, risk_val=200.0, wallet_balance=10000.0, side='BUY')
    # loss_per_unit = entry - sl = 2.0 -> qty_by_risk = 100, qty_by_cash = 100 -> qty = 100
    assert qty == 100
    assert loss_per_unit == 2.0
    assert expected_max_loss == loss_per_unit * qty


def test_compute_order_qty_zero_diff():
    qty, expected_max_loss, _, _, loss_per_unit = compute_order_qty(ltp=100.0, st_sl=100.0, risk_val=500.0, wallet_balance=1000.0, side='BUY')
    assert qty == 1
    assert loss_per_unit == 0.0
    assert expected_max_loss == 0.0


def test_compute_order_qty_caps_by_cash():
    # large risk but small wallet should cap qty
    qty, expected_max_loss, qty_by_risk, qty_by_cash, loss_per_unit = compute_order_qty(ltp=50.0, st_sl=40.0, risk_val=10000.0, wallet_balance=200.0, side='BUY')
    # loss_per_unit = 50-40=10 -> qty_by_risk = int(10000/10)=1000, qty_by_cash = int(200/50)=4 -> qty=4
    assert qty == 4
    assert qty_by_cash == 4
