"""Common-target six-model comparison; preserves legacy five-model artifacts."""

import hashlib
import numpy as np
import pandas as pd
from .config import DRAWS
from .evaluation import metrics, group_masks
from .inference import indices, counts
from .utils import mask
from .io import csv, save

MODELS = ["HAR", "GARCH", "ROLLING22", "EWMA", "CURRENT", "HIST_MEAN"]


def evaluate(f, data, out, gold=False):
    f = f[f.model.isin(MODELS)].copy()
    f["valid"] = (
        f[["forecast", "actual", "future_DD5", "future_tail5"]].notna().all(axis=1)
    )
    checks = f.groupby(["symbol", "session"]).agg(
        n=("model", "size"), valid=("valid", "sum")
    )
    good = checks[(checks.n == len(MODELS)) & (checks.valid == len(MODELS))].index
    g = f.set_index(["symbol", "session"]).loc[good].reset_index().drop(columns="valid")
    r = g.actual.clip(lower=1e-12) / g.forecast.clip(lower=1e-12)
    g["MSE"] = (g.actual - g.forecast) ** 2
    g["QLIKE"] = r - np.log(r) - 1
    g.to_parquet(out / "COMMON_TARGET_EVALUATION.parquet", index=False)
    nassets = g.symbol.nunique()
    common = g.groupby("session").symbol.nunique()
    common = common[common == nassets].index
    rows = []
    losses = []
    bins = []
    uncertainty = []
    blockplan = []

    def windows(z):
        groups = group_masks(z)
        groups["COMMON_ALL"] = z.session.isin(common).to_numpy()
        if gold:
            groups["GOLD_2013"] = mask(z.session, ("2013-01-01", "2013-12-31"))
        return groups

    for (symbol, model), z in g.groupby(["symbol", "model"]):
        groups = windows(z)
        for period, m in groups.items():
            if m.sum() < 20:
                continue
            rows.append(
                dict(symbol=symbol, model=model, period=period, **metrics(z[m]))
            )
        for period in ["ALL", "2023_PLUS"]:
            a = z[groups[period] & z.forecast_percentile.notna()].copy()
            a["bin"] = np.minimum((a.forecast_percentile * 10).astype(int), 9) + 1
            for b, q in a.groupby("bin"):
                bins.append(
                    dict(
                        symbol=symbol,
                        model=model,
                        period=period,
                        bin=b,
                        n=len(q),
                        future_risk=q.actual.mean(),
                        mean_forecast=q.forecast.mean(),
                        future_tail_frequency=q.future_tail5.mean(),
                        mean_future_DD=q.future_DD5.mean(),
                    )
                )
    met = pd.DataFrame(rows)
    for symbol, z in g.groupby("symbol"):
        har = z[z.model.eq("HAR")].set_index("session")
        groups = windows(har.reset_index())
        for base in MODELS[1:]:
            baseline = z[z.model.eq(base)].set_index("session").reindex(har.index)
            for loss in ["MSE", "QLIKE"]:
                diff = baseline[loss] - har[loss]
                for period, m in groups.items():
                    if m.sum() < 20:
                        continue
                    losses.append(
                        dict(
                            symbol=symbol,
                            baseline=base,
                            period=period,
                            loss=loss,
                            n=int(m.sum()),
                            relative_improvement=1
                            - har.loc[m, loss].mean() / baseline.loc[m, loss].mean(),
                            gain_sum=diff[m].sum(),
                            share_of_total=(
                                diff[m].sum() / diff.sum()
                                if diff.sum() != 0
                                else np.nan
                            ),
                        )
                    )
        calendar = pd.DatetimeIndex(
            data[
                (data.symbol == symbol)
                & data.session.between(z.session.min(), z.session.max())
            ].session
        )
        labels = pd.DataFrame({"session": calendar})
        masks = windows(labels)
        for period in ["ALL", "2023_PLUS", "COMMON_ALL", "EX_COVID"]:
            cal = calendar[masks[period]]
            for length in [21, 42]:
                ix = indices(len(cal), length)
                cc = counts(ix, len(cal))
                blockplan.append(
                    dict(
                        symbol=symbol,
                        period=period,
                        block=length,
                        draws=DRAWS,
                        n_calendar=len(cal),
                        index_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),
                    )
                )
                for loss in ["MSE", "QLIKE"]:
                    x = z.pivot(index="session", columns="model", values=loss).reindex(
                        index=cal, columns=MODELS
                    )
                    valid = x.notna().all(axis=1).to_numpy()
                    means = (
                        cc
                        @ x.fillna(0).to_numpy()
                        / (cc @ valid.astype(float))[:, None]
                    )
                    point = x.mean().to_numpy()
                    gain = 1 - means[:, [0]] / means[:, 1:]
                    pt = 1 - point[0] / point[1:]
                    sd = gain.std(axis=0, ddof=1)
                    student = np.divide(
                        pt - gain, sd, out=np.zeros_like(gain), where=sd > 1e-15
                    )
                    critical = np.quantile(student.max(axis=1), 0.95)
                    lower = pt - critical * sd
                    for j, base in enumerate(MODELS[1:]):
                        lo, hi = np.quantile(gain[:, j], [0.025, 0.975])
                        uncertainty.append(
                            dict(
                                symbol=symbol,
                                challenger="HAR",
                                baseline=base,
                                period=period,
                                block=length,
                                loss=loss,
                                point_improvement=pt[j],
                                ci_low=lo,
                                ci_high=hi,
                                simultaneous_lower95=lower[j],
                                family_size=len(MODELS) - 1,
                            )
                        )
                    if gold:
                        ratio = 1 - means[:, 1] / means[:, 2]
                        lo, hi = np.quantile(ratio, [0.025, 0.975])
                        uncertainty.append(
                            dict(
                                symbol=symbol,
                                challenger="GARCH",
                                baseline="ROLLING22",
                                period=period,
                                block=length,
                                loss=loss,
                                point_improvement=1 - point[1] / point[2],
                                ci_low=lo,
                                ci_high=hi,
                                simultaneous_lower95=np.nan,
                                family_size=1,
                            )
                        )
            print("BENCHMARK_INTERVALS", symbol, period, flush=True)
    csv(out / "BENCHMARK_METRICS.csv", met)
    csv(out / "BENCHMARK_LOSS_GAINS.csv", losses)
    csv(out / "BENCHMARK_PAIRED_INTERVALS.csv", uncertainty)
    csv(out / "BENCHMARK_RISK_BUCKETS.csv", bins)
    save(out / "BENCHMARK_BOOTSTRAP_PLAN.json", blockplan)
    losses = pd.DataFrame(losses)
    intervals = pd.DataFrame(uncertainty)
    csv(out / "HAR_VS_GARCH_RESULTS.csv", losses[losses.baseline.eq("GARCH")])
    return met, losses, intervals


def decide(met, losses, intervals, out, gold=False):
    def gain(symbol, model, base, loss, period="ALL"):
        z = met[(met.symbol == symbol) & (met.period == period)].set_index("model")
        return float(1 - z.loc[model, loss] / z.loc[base, loss])

    def bound(symbol, model, base, loss, column):
        z = intervals[
            (intervals.symbol == symbol)
            & intervals.challenger.eq(model)
            & intervals.baseline.eq(base)
            & intervals.loss.eq(loss)
            & intervals.period.eq("ALL")
        ]
        return float(
            z[column].min()
            if column in ["ci_low", "simultaneous_lower95"]
            else z[column].max()
        )

    candidates = pd.read_csv(out / "GARCH_MODEL_SELECTION.csv")
    selected = candidates[candidates.selected].sort_values(["symbol", "vintage"])
    switches = []
    for symbol, z in selected.groupby("symbol"):
        names = z.p.astype(str) + "_" + z.q.astype(str) + "_" + z.distribution
        switches.append(
            dict(
                symbol=symbol,
                vintages=len(z),
                switch_rate=float(
                    (names.iloc[1:].to_numpy() != names.iloc[:-1].to_numpy()).mean()
                ),
                near_unit_fraction=float((z.persistence >= 0.999).mean()),
                candidate_convergence=float(
                    candidates[candidates.symbol.eq(symbol)].valid.mean()
                ),
            )
        )
    spec_good = all(
        x["switch_rate"] <= 0.35
        and x["near_unit_fraction"] <= 0.20
        and x["candidate_convergence"] >= 0.99
        for x in switches
    )
    specification = "SUPPORTED" if spec_good else "PARTIAL"
    save(
        out / "GARCH_SPECIFICATION_AUDIT.json",
        dict(
            status=specification,
            by_asset=switches,
            criterion="Complete forecast coverage is mandatory; thresholds frozen in plan",
        ),
    )
    if not gold:
        full = [
            gain(s, "HAR", "GARCH", l) for s in ["SPY", "QQQ"] for l in ["MSE", "QLIKE"]
        ]
        supported = (
            all(
                gain("SPY", "HAR", "GARCH", l) >= 0.02
                and bound("SPY", "HAR", "GARCH", l, "simultaneous_lower95") > 0
                for l in ["MSE", "QLIKE"]
            )
            and all(gain("QQQ", "HAR", "GARCH", l) > 0 for l in ["MSE", "QLIKE"])
            and all(
                gain(s, "HAR", "GARCH", "QLIKE", p) > 0
                for s in ["SPY", "QQQ"]
                for p in ["2023_PLUS", "EX_ALL_THREE"]
            )
        )
        state = (
            "SUPPORTED"
            if supported
            else "WEAK" if sum(x > 0 for x in full) >= 3 else "NOT_SUPPORTED"
        )
        result = dict(
            EQUITY_HAR_VS_GARCH=state,
            GARCH_SPECIFICATION_STABILITY=specification,
            evidence="EXPOSED_HISTORY",
        )
    else:
        symbol = met.symbol.iloc[0]
        good = []
        weak = []
        for model in ["HAR", "GARCH"]:
            a = met[(met.model == model) & met.period.eq("ALL")].iloc[0]
            gl = [gain(symbol, model, "ROLLING22", l) for l in ["MSE", "QLIKE"]]
            lower = [
                bound(
                    symbol,
                    model,
                    "ROLLING22",
                    l,
                    "ci_low",
                )
                for l in ["MSE", "QLIKE"]
            ]
            good.append(
                all(x >= 0.02 for x in gl)
                and min(lower) > 0
                and a.OOS_R2 > 0
                and a.high_risk_AUC >= 0.7
                and a.tail_AUC >= 0.6
                and gain(symbol, model, "ROLLING22", "QLIKE", "2023_PLUS") > 0
            )
            weak.append(min(gl) > 0)
        prediction = (
            "SUPPORTED" if any(good) else "WEAK" if any(weak) else "NOT_SUPPORTED"
        )
        gg = [gain(symbol, "HAR", "GARCH", l) for l in ["MSE", "QLIKE"]]
        supported = (
            min(gg) >= 0.02
            and all(
                bound(symbol, "HAR", "GARCH", l, "simultaneous_lower95") > 0
                for l in ["MSE", "QLIKE"]
            )
            and all(
                gain(symbol, "HAR", "GARCH", "QLIKE", p) > 0
                for p in ["2023_PLUS", "EX_ALL_THREE"]
            )
        )
        better = max(gg) <= -0.02 and all(
            bound(symbol, "HAR", "GARCH", l, "ci_high") < 0 for l in ["MSE", "QLIKE"]
        )
        similar = all(
            bound(symbol, "HAR", "GARCH", l, "ci_low") >= -0.05
            and bound(symbol, "HAR", "GARCH", l, "ci_high") <= 0.05
            for l in ["MSE", "QLIKE"]
        )
        result = dict(
            GOLD_VOLATILITY_PREDICTABILITY=prediction,
            GOLD_HAR_VS_GARCH=(
                "SUPPORTED"
                if supported
                else (
                    "GARCH_BETTER"
                    if better
                    else "SIMILAR" if similar else "INCONCLUSIVE"
                )
            ),
            GARCH_SPECIFICATION_STABILITY=specification,
            evidence="EXPOSED_HISTORY",
        )
    save(out / "BENCHMARK_STATUS.json", result)
    return result
