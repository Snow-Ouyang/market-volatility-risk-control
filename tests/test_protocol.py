"""Protocol tests: labels, lookahead, self-financing and public data adapter."""

import sys
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from volatility_risk.measurement import transform
from volatility_risk.forecast import run
from volatility_risk.strategy_account import simulate, COLS
from volatility_risk.data import fetch, build
from volatility_risk.inference import counts


def sample(n=670):
    rng = np.random.default_rng(72)
    dates = pd.bdate_range("2010-01-01", periods=n)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    opening = np.r_[close[0], close[:-1]] * np.exp(rng.normal(0, 0.003, n))
    return pd.DataFrame(
        dict(
            session=dates,
            Open=opening,
            Close=close,
            High=np.maximum(opening, close) * 1.005,
            Low=np.minimum(opening, close) * 0.995,
            Volume=1000,
            symbol="SPY",
            open_ts=dates.tz_localize("UTC") + pd.Timedelta(hours=14),
            close_ts=dates.tz_localize("UTC") + pd.Timedelta(hours=21),
        )
    )


def test_target_excludes_preentry_overnight():
    z = sample(40)
    result = transform(z.copy(), pd.Series(True, index=z.index))
    t = 24
    expected = np.mean(
        [result.GK_RTH.iloc[j] + result.OVN2.iloc[j + 1] for j in range(t + 1, t + 6)]
    )
    assert result.Y5.iloc[t] == pytest.approx(expected, abs=1e-15)
    assert result.target_end.iloc[t] == z.session.iloc[t + 6]
    assert result.Y5.tail(6).isna().all()
    assert np.isnan(result.GK_FULL.iloc[0])
    assert not np.isclose(
        expected, result.GK_FULL.iloc[t + 1 : t + 6].mean(), rtol=1e-5
    )


def test_future_prices_do_not_change_available_forecasts(tmp_path):
    z = sample()
    cutoff = z.session.iloc[590]
    base = transform(z.copy(), pd.Series(True, index=z.index))
    a = tmp_path / "a"
    a.mkdir()
    f = run(base, a)
    changed = z.copy()
    changed.loc[changed.session >= cutoff, ["Open", "High", "Low", "Close"]] *= 1.7
    other = transform(changed, pd.Series(True, index=z.index))
    b = tmp_path / "b"
    b.mkdir()
    g = run(other, b)
    left = f[(f.session < cutoff) & (f.model == "HAR")].forecast.to_numpy()
    right = g[(g.session < cutoff) & (g.model == "HAR")].forecast.to_numpy()
    np.testing.assert_array_equal(left, right)
    assert (f.training_target_end_timestamp <= f.refit_cutoff).all()


@pytest.mark.parametrize("bp", [0, 1, 3])
def test_self_financing_drift_and_initial_cost(bp):
    p = np.array([100.0, 120.0, 80.0, 115.0])
    a = pd.DataFrame(
        simulate(p, np.zeros(3), np.full(3, 0.5), np.ones(3, dtype=bool), bp / 10000),
        columns=COLS,
    )
    np.testing.assert_allclose(a.post_NAV, a.pre_NAV - a.fee, atol=1e-15)
    np.testing.assert_allclose(a.end_NAV, a.cash + a.units * p[1:], atol=1e-15)
    assert a.drift.iloc[1] > 0.5
    assert a.signed_notional.iloc[1] < 0
    assert a.signed_notional.iloc[2] > 0
    assert (a.cash >= -1e-14).all() and (a.units >= 0).all()
    assert a.fee.iloc[0] == pytest.approx(bp / 10000 * 0.5 / (1 + bp / 10000 * 0.5))
    bh = pd.DataFrame(
        simulate(p, np.zeros(3), np.ones(3), np.ones(3, dtype=bool), bp / 10000, True),
        columns=COLS,
    )
    assert (bh.fee.iloc[1:] == 0).all()
    assert bh.units.nunique() == 1


def test_count_matrix_matches_direct_block_sampling():
    ix = np.array([[0, 1, 2, 2], [2, 0, 0, 1]])
    values = np.array([[1.0, 2.0], [5.0, 3.0], [-1.0, 7.0]])
    np.testing.assert_array_equal(counts(ix, 3) @ values, values[ix].sum(axis=1))


def test_fetch_contract_and_overwrite_guard(tmp_path, monkeypatch):
    calls = []

    def fake(symbol, **kwargs):
        calls.append(kwargs)
        return pd.DataFrame(
            {
                "Open": [10.0, 11.0],
                "High": [12.0, 13.0],
                "Low": [9.0, 10.0],
                "Close": [11.0, 12.0],
                "Volume": [100.0, 200.0],
                "Stock Splits": [0.0, 0.0],
            },
            index=pd.DatetimeIndex(["2026-08-28", "2026-08-31"], name="Date"),
        )

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(download=fake))
    fetch(tmp_path)
    assert all(
        c["auto_adjust"] and c["interval"] == "1d" and not c["repair"] for c in calls
    )
    assert len(pd.read_csv(tmp_path / "SPY.csv")) == 1
    with pytest.raises(FileExistsError):
        fetch(tmp_path)


def test_data_rejects_duplicates(tmp_path):
    z = pd.DataFrame(
        dict(
            Date=["2026-08-27", "2026-08-27"],
            Open=[1, 1],
            High=[1, 1],
            Low=[1, 1],
            Close=[1, 1],
            Volume=[1, 1],
        )
    )
    z.to_csv(tmp_path / "SPY.csv", index=False)
    with pytest.raises(ValueError, match="duplicate"):
        build(tmp_path, tmp_path)
