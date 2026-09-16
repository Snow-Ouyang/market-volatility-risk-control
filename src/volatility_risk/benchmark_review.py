"""Independent GARCH state/bridge, selection and paired-interval audit."""

import hashlib
import numpy as np
import pandas as pd
from arch import arch_model
from .io import read, save
from .config import DRAWS, SEED
from .benchmark_evaluation import MODELS


def run(out):
    data = pd.read_parquet(out / "DAILY_FEATURES.parquet")
    states = pd.read_parquet(out / "GARCH_DAILY_STATE.parquet")
    vintages = read(out / "GARCH_VINTAGES.json")
    selection = pd.read_csv(out / "GARCH_MODEL_SELECTION.csv")
    native = pd.read_parquet(out / "FORECASTS.parquet")
    allf = pd.read_parquet(out / "FORECASTS_WITH_GARCH.parquet")
    pd.testing.assert_frame_equal(
        native.reset_index(drop=True),
        allf[allf.model.ne("GARCH")].reset_index(drop=True)[native.columns],
        check_exact=True,
    )
    largest = 0.0
    bridge_error = 0.0
    bic_error = 0.0
    reviewed = 0
    for v in vintages:
        z = data[data.symbol.eq(v["symbol"])].copy()
        z["returns"] = 100 * np.log(z.Close / z.Close.shift())
        tr = z[
            z.session.between(
                pd.Timestamp(v["train_first"]), pd.Timestamp(v["train_last"])
            )
        ].dropna(subset=["returns", "GK_RTH", "OVN2"])
        digest = hashlib.sha256(
            "|".join(tr.session.dt.strftime("%Y-%m-%d")).encode()
        ).hexdigest()
        assert digest == v["training_row_hash"] and len(tr) == v["n_train"]
        group = selection[
            selection.symbol.eq(v["symbol"]) & selection.vintage.eq(v["vintage"])
        ]
        winner = group[group.valid].sort_values(["BIC", "order"]).iloc[0]
        assert winner["order"] == v["order"] and group.selected.sum() == 1
        for r in group[group.valid].itertuples():
            bic_error = max(
                bic_error,
                abs(
                    r.BIC - (-2 * r.loglikelihood + r.n_parameters * np.log(r.n_train))
                ),
            )
        p, q = int(v["p"]), int(v["q"])
        params = v["parameters"]
        model = arch_model(
            tr.returns.to_numpy(),
            mean="Zero",
            vol="GARCH",
            p=p,
            q=q,
            dist=v["distribution"],
            rescale=False,
        )
        fixed = model.fix(pd.Series(params))
        variance = list(np.asarray(fixed.conditional_volatility) ** 2)
        shock = list(tr.returns.to_numpy() ** 2)
        a = np.array([params[f"alpha[{i}]"] for i in range(1, p + 1)])
        b = np.array([params[f"beta[{i}]"] for i in range(1, q + 1)])
        a_rth = tr.GK_RTH.sum() / np.square(tr.returns / 100).sum()
        a_gap = tr.OVN2.sum() / np.square(tr.returns / 100).sum()
        bridge_error = max(
            bridge_error, abs(a_rth - v["a_RTH"]), abs(a_gap - v["a_GAP"])
        )
        cur = states[
            states.symbol.eq(v["symbol"]) & states.vintage.eq(v["vintage"])
        ].sort_values("session")
        lookup = z.set_index("session")
        assert pd.Timestamp(v["train_last"]) < cur.session.min()
        for row in cur.itertuples():
            observed_variance = (
                params["omega"]
                + a @ np.asarray(shock[-p:][::-1])
                + b @ np.asarray(variance[-q:][::-1])
            )
            variance.append(observed_variance)
            shock.append(lookup.loc[row.session, "returns"] ** 2)
            expected_shocks = shock[-p:].copy()
            expected_variances = variance[-q:].copy()
            future = []
            for h in range(6):
                expected = (
                    params["omega"]
                    + a @ np.asarray(expected_shocks[-p:][::-1])
                    + b @ np.asarray(expected_variances[-q:][::-1])
                )
                future.append(expected / 10000)
                expected_shocks.append(expected)
                expected_variances.append(expected)
            risk = (a_rth * np.sum(future[:5]) + a_gap * np.sum(future[1:])) / 5
            largest = max(
                largest,
                abs(risk / row.forecast - 1),
                float(
                    np.max(
                        abs(
                            np.array(future)
                            / np.array([getattr(row, f"h{i}") for i in range(1, 7)])
                            - 1
                        )
                    )
                ),
            )
            reviewed += 1
    intervals = pd.read_csv(out / "BENCHMARK_PAIRED_INTERVALS.csv")
    g = pd.read_parquet(out / "COMMON_TARGET_EVALUATION.parquet")
    interval_error = 0.0
    for symbol, z in g.groupby("symbol"):
        for length in [21, 42]:
            dates = sorted(z.session.unique())
            n = len(dates)
            rng = np.random.default_rng(SEED + length)
            starts = rng.integers(0, n, size=(DRAWS, int(np.ceil(n / length))))
            ix = ((starts[:, :, None] + np.arange(length)) % n).reshape(DRAWS, -1)[
                :, :n
            ]
            for loss in ["MSE", "QLIKE"]:
                x = (
                    z.pivot(index="session", columns="model", values=loss)
                    .reindex(index=dates, columns=MODELS)
                    .to_numpy()
                )
                means = []
                for start in range(0, DRAWS, 100):
                    means.append(x[ix[start : start + 100]].mean(axis=1))
                means = np.concatenate(means)
                gain = 1 - means[:, [0]] / means[:, 1:]
                pt = 1 - x.mean(axis=0)[0] / x.mean(axis=0)[1:]
                sd = gain.std(axis=0, ddof=1)
                critical = np.quantile(((pt - gain) / sd).max(axis=1), 0.95)
                lower = pt - critical * sd
                for j, base in enumerate(MODELS[1:]):
                    row = intervals[
                        (intervals.symbol == symbol)
                        & intervals.period.eq("ALL")
                        & intervals.loss.eq(loss)
                        & intervals.block.eq(length)
                        & intervals.baseline.eq(base)
                        & intervals.challenger.eq("HAR")
                    ].iloc[0]
                    lo, hi = np.quantile(gain[:, j], [0.025, 0.975])
                    interval_error = max(
                        interval_error,
                        abs(lo - row.ci_low),
                        abs(hi - row.ci_high),
                        abs(lower[j] - row.simultaneous_lower95),
                    )
    assert (
        largest < 1e-9
        and bridge_error < 1e-12
        and bic_error < 1e-7
        and interval_error < 1e-9
    )
    result = dict(
        status="PASS",
        vintages=len(vintages),
        daily_forecasts=reviewed,
        maximum_forecast_relative_error=largest,
        maximum_bridge_error=bridge_error,
        maximum_BIC_error=bic_error,
        maximum_interval_error=interval_error,
        old_model_forecasts_unchanged=True,
        reviewer="Same agent using independent library refiltering, vector recursion and direct block-index sampling; not external peer review",
    )
    save(out / "GARCH_INDEPENDENT_REVIEW.json", result)
    (out / "GARCH_REVIEW.md").write_text(
        "# GARCH independent numerical review\n\n"
        + pd.DataFrame([result]).to_markdown(index=False)
        + "\n\nAll monthly choices use pre-origin data; original HAR and simple-model values are unchanged. Daily state/target conversion and full-history paired/simultaneous interval endpoints were independently recomputed. This is retrospective numerical verification, not prospective or external validation.\n",
        encoding="utf-8",
    )
    return result
