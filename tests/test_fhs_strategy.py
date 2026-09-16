"""Migrated accounting boundaries plus PIT residual and cash-contract checks."""

import numpy as np
import pandas as pd
from volatility_risk.fhs import empirical, fhs_values, percentiles
from volatility_risk.strategy_account import simulate
from volatility_risk.strategy_evaluation import drawdown, drawdown_reference


def test_empirical_fractional_mass():
    q, e = empirical(np.arange(-10, 11, dtype=float))
    assert q == -9
    assert np.isclose(e, (-10 - 0.05 * 9) / 1.05)


def test_postfee_weights_units_and_cash():
    price = np.array([100, 101, 99, 105, 102, 103, 104, 100, 101, 102, 103], float)
    rc = np.full(10, 0.0001)
    target = np.r_[np.full(5, 0.7), np.full(5, 0.3)]
    reb = np.arange(10) % 5 == 0
    a = simulate(price, rc, target, reb, 0.0003)
    assert np.allclose(a[reb, 6], target[reb])
    assert np.all(a[1:5, 3] == a[0, 3]) and np.all(a[6:, 3] == a[5, 3])
    assert np.all(a[:, 4] >= 0)
    assert np.allclose(a[:, 0] - a[:, 1], a[:, 7])


def test_drift_is_not_target():
    price = np.array([100, 102, 101, 98, 99, 101], float)
    rc = np.array([0.0001, 0.0002, 0.0001, 0.0001, 0.0003])
    q = 0.61
    er = price[:-1] / price[0]
    cr = np.r_[1, np.cumprod(1 + rc[:-1])]
    expected = q * er / (q * er + (1 - q) * cr)
    for fee in [0, 0.0001, 0.0003]:
        a = simulate(
            price, rc, np.full(5, q), np.array([True, False, False, False, False]), fee
        )
        np.testing.assert_allclose(a[:, 6], expected)


def test_segmented_drawdown():
    r = np.array([0.2, -0.1, -0.3, 0.1, 0.5, -0.2, 0.1, -0.3, 0.6])
    for m in [np.ones(9, bool), np.array([1, 1, 0, 0, 1, 1, 1, 1, 1], bool)]:
        a = drawdown(r, m)
        b = drawdown_reference(r, m)
        assert np.isclose(a[0], b[0])
        assert a[1:] == b[1:]


def test_percentile_uses_only_previous_values():
    values = np.arange(300, dtype=float)
    a = percentiles(values)
    values[280:] = -1000
    b = percentiles(values)
    np.testing.assert_array_equal(a[:280], b[:280])


def test_fhs_direct_five_day_residual_scale():
    tr = pd.DataFrame(dict(Z=np.linspace(-3, 3, 1008), H=np.full(1008, 0.5)))
    s = np.array([0.01, 0.02])
    v = fhs_values(tr, s)
    np.testing.assert_allclose(v["q"][1], 2 * v["q"][0])
    np.testing.assert_allclose(v["e"][1], 2 * v["e"][0])
    assert v["p2"][1] > v["p2"][0]
    np.testing.assert_allclose(v["dd"], -np.expm1(-s * 0.5))
