"""Parity against frozen final outputs and independent scalar cash-flow checks."""

import numpy as np
import pandas as pd
from .io import save, read, sha


def compare(a, b, keys, columns):
    a = a.sort_values(keys).reset_index(drop=True)
    b = b.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(a[keys], b[keys], check_dtype=False)
    largest = 0.0
    for c in columns:
        if pd.api.types.is_numeric_dtype(a[c]):
            x = a[c].to_numpy(dtype=float)
            y = b[c].to_numpy(dtype=float)
            np.testing.assert_allclose(
                x, y, rtol=2e-9, atol=2e-11, equal_nan=True, err_msg=c
            )
            err = np.abs(x - y)
            if np.isfinite(err).any():
                largest = max(largest, float(np.nanmax(err)))
        else:
            pd.testing.assert_series_equal(
                a[c], b[c], check_names=False, check_dtype=False
            )
    return dict(rows=len(a), columns=len(columns), max_absolute_numeric_error=largest)


def validate(out, data_dir):
    ref = data_dir / "reference"
    checks = {}
    for file in ["FORECASTS.parquet", "FORECASTS_WITH_GARCH.parquet"]:
        a = pd.read_parquet(out / "forecast" / file)
        b = pd.read_parquet(ref / "forecast" / file)
        checks[file] = compare(
            a,
            b,
            ["symbol", "session", "model"],
            [
                "forecast",
                "actual",
                "n_train",
                "target_end_timestamp",
                "information_cutoff",
                "forecast_timestamp",
            ],
        )
    for symbol in ["SPY", "QQQ"]:
        t = out / "tail" / symbol
        r = ref / "tail" / symbol
        a = pd.read_parquet(t / "FORECASTS.parquet")
        b = pd.read_parquet(r / "FORECASTS.parquet")
        checks[symbol + "_FHS"] = compare(a, b, ["session", "model"], list(b.columns))
        x = pd.read_csv(t / "FORECAST_METRICS.csv")
        y = pd.read_csv(r / "FORECAST_METRICS.csv")
        y = y[y.model.isin(["HS", "FHS"])]
        checks[symbol + "_tail_metrics"] = compare(
            x, y, ["period", "model"], [c for c in x if c not in ["first", "last"]]
        )
        x = pd.read_csv(t / "PAIRED_INTERVALS.csv")
        y = pd.read_csv(r / "PAIRED_INTERVALS.csv")
        y = y[y.family == "FHS_VALUE"]
        checks[symbol + "_tail_intervals"] = compare(
            x, y, ["period", "block", "contrast"], list(x.columns)
        )
        s = out / "strategy" / symbol
        r = ref / "strategy" / symbol
        p = pd.read_csv(s / "PORTFOLIO_RESULTS.csv")
        q = pd.read_csv(r / "PORTFOLIO_RESULTS.csv")
        q = q[
            q.rule.isin(["BUYHOLD", "VOL", "CORE_VOL", "MATCH_VOL", "MATCH_CORE_VOL"])
        ]
        checks[symbol + "_strategy_metrics"] = compare(
            p, q, ["cash_mode", "offset", "cost_bps", "rule", "period"], list(p.columns)
        )
        a = read(s / "NORMALIZATION.json")
        b = read(r / "NORMALIZATION.json")
        for cash in ["PROXY", "ZERO"]:
            for k in b["budgets"][cash]:
                np.testing.assert_allclose(
                    a["budgets"][cash][k], b["budgets"][cash][k], atol=1e-14, rtol=1e-12
                )
        n = 0
        error = 0.0
        for f in (s / "ledgers").glob("*.parquet"):
            d = pd.read_parquet(f)
            px = d.price.to_numpy()
            up = d.units.to_numpy()
            cash = d.cash_next.to_numpy()
            prev_units = np.r_[0, up[:-1]]
            prev_cash = np.r_[1, cash[:-1]]
            before = prev_units * px + prev_cash
            delta = (up - prev_units) * px
            fees = d.fee.to_numpy()
            expected_cash = prev_cash - delta - fees
            expected_end = up * d.next_price.to_numpy() + expected_cash * (
                1 + d.cash_return.to_numpy()
            )
            e = max(
                float(np.max(abs(before - d.pre_NAV))),
                float(np.max(abs(expected_cash - d.cash))),
                float(np.max(abs(expected_end - d.end_NAV))),
            )
            assert e < 1e-9
            error = max(error, e)
            n += len(d)
            old = r / "ledgers" / f.name
            if old.exists():
                original = pd.read_parquet(old)
                compare(d, original, ["origin_index"], list(original.columns))
        checks[symbol + "_independent_ledger"] = dict(rows=n, max_cashflow_error=error)
        for cash in ["PROXY", "ZERO"]:
            w = pd.read_csv(s / f"DECISION_WEIGHTS_{cash}.csv")
            v = pd.read_csv(r / f"DECISION_WEIGHTS_{cash}.csv")
            checks[symbol + "_weights_" + cash] = compare(
                w, v, ["origin_index"], ["session", "VOL", "CORE_VOL"]
            )
    save(
        out / "PARITY_REVIEW.json",
        dict(
            status="PASS",
            scope="Frozen canonical numerical replay; separate scalar accounting; no claim of external peer review",
            checks=checks,
        ),
    )
    print("MAINLINE_PARITY_PASS", flush=True)
