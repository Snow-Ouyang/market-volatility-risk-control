"""No-lookahead, likelihood selection, recursion and risk-target alignment tests."""

import numpy as np
import pytest
from arch import arch_model
from volatility_risk.garch import variance_path, fit_vintage, FAMILY


@pytest.mark.parametrize("p,q,dist", FAMILY)
def test_analytic_recursion_matches_library(p, q, dist):
    y = np.random.default_rng(17).standard_t(8, 700)
    fit = arch_model(
        y, mean="Zero", vol="GARCH", p=p, q=q, dist=dist, rescale=False
    ).fit(disp="off")
    own = variance_path(
        fit.params.to_dict(), y**2, np.asarray(fit.conditional_volatility) ** 2, p, q
    )
    expected = fit.forecast(horizon=6, reindex=False).variance.to_numpy()[-1]
    np.testing.assert_allclose(own, expected, rtol=1e-11, atol=1e-11)


def test_future_innovation_cannot_change_prior_forecast_or_selection():
    y = np.random.default_rng(31).standard_t(8, 600)
    task = (
        "TEST",
        "TEST",
        [str(i) for i in range(len(y))],
        y,
        np.full(len(y), 0.00007),
        np.full(len(y), 0.00003),
        ["a", "b", "c"],
        np.array([0.5, -0.4, 0.2]),
    )
    a = fit_vintage(task)
    changed = (*task[:-1], np.array([0.5, -0.4, 9.0]))
    b = fit_vintage(changed)
    assert a[3]["parameters"] == b[3]["parameters"]
    assert a[3]["BIC"] == b[3]["BIC"]
    assert [x["forecast"] for x in a[0][:2]] == [x["forecast"] for x in b[0][:2]]
    assert a[0][-1]["forecast"] != b[0][-1]["forecast"]
    eligible = [r for r in a[1] if r["valid"]]
    assert a[3]["BIC"] == min(r["BIC"] for r in eligible)
    for row in eligible:
        assert row["BIC"] == pytest.approx(
            -2 * row["loglikelihood"] + row["n_parameters"] * np.log(row["n_train"])
        )
    r = a[0][0]
    v = a[3]
    expected = (
        v["a_RTH"] * sum(r[f"h{i}"] for i in range(1, 6))
        + v["a_GAP"] * sum(r[f"h{i}"] for i in range(2, 7))
    ) / 5
    assert r["forecast"] == pytest.approx(expected, abs=1e-16)


def test_gold_predictability_uses_preregistered_paired_bound(tmp_path):
    import pandas as pd
    from volatility_risk.benchmark_evaluation import decide

    rows = []
    for period in ["ALL", "2023_PLUS", "EX_ALL_THREE"]:
        for model, loss in [("HAR", 0.8), ("GARCH", 0.9), ("ROLLING22", 1.0)]:
            rows.append(
                dict(
                    symbol="GLD",
                    model=model,
                    period=period,
                    MSE=loss,
                    QLIKE=loss,
                    OOS_R2=0.3,
                    high_risk_AUC=0.8,
                    tail_AUC=0.7,
                )
            )
    intervals = []
    for model, base in [("HAR", "ROLLING22"), ("GARCH", "ROLLING22"), ("HAR", "GARCH")]:
        for loss in ["MSE", "QLIKE"]:
            intervals.append(
                dict(
                    symbol="GLD",
                    challenger=model,
                    baseline=base,
                    period="ALL",
                    loss=loss,
                    ci_low=0.01,
                    ci_high=0.2,
                    simultaneous_lower95=-0.02,
                )
            )
    pd.DataFrame(
        [
            dict(
                symbol="GLD",
                vintage=v,
                p=1,
                q=1,
                distribution="t",
                selected=True,
                valid=True,
                persistence=0.95,
            )
            for v in ["2007-01", "2007-02"]
        ]
    ).to_csv(tmp_path / "GARCH_MODEL_SELECTION.csv", index=False)
    result = decide(
        pd.DataFrame(rows), None, pd.DataFrame(intervals), tmp_path, gold=True
    )
    assert result["GOLD_VOLATILITY_PREDICTABILITY"] == "SUPPORTED"
    assert result["GOLD_HAR_VS_GARCH"] == "INCONCLUSIVE"
