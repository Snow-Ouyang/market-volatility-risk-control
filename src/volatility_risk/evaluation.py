"""Common-date losses, calibration, risk ranking and fixed regime diagnostics."""

import numpy as np
import pandas as pd
from .config import MODELS, BASES, PERIODS, EPISODES
from .io import csv
from .utils import mask, auc


def group_masks(z):
    dates = z.session
    out = {k: mask(dates, v) for k, v in PERIODS.items()}
    out.update({k: mask(dates, v) for k, v in EPISODES.items()})
    for year in sorted(dates.dt.year.unique()):
        out[f"YEAR_{year}"] = dates.dt.year.eq(year).to_numpy()
    excluded = np.zeros(len(z), bool)
    for key in ["GFC", "COVID", "2022"]:
        out["EX_" + key] = ~out[key]
        excluded |= out[key]
    out["EX_ALL_THREE"] = ~excluded
    return out


def metrics(z):
    y = z.actual.to_numpy()
    p = z.forecast.to_numpy()
    ratio = y.clip(min=1e-12) / p.clip(min=1e-12)
    mse = (y - p) ** 2
    ql = ratio - np.log(ratio) - 1
    beta = np.linalg.lstsq(np.c_[np.ones(len(p)), p], y, rcond=None)[0]
    event = y >= z.target_q90.to_numpy()
    high = p > z.forecast_q90.to_numpy()
    ok = z.forecast_q90.notna().to_numpy()
    den = np.sum(event & ok)
    hi = np.sum(high & ok)
    base = event[ok].mean() if ok.any() else np.nan
    precision = np.sum(event & high & ok) / hi if hi else np.nan
    return dict(
        n=len(z),
        start=z.session.min(),
        end=z.session.max(),
        MSE=mse.mean(),
        QLIKE=ql.mean(),
        OOS_R2=1 - mse.sum() / np.square(y - z.benchmark_mean).sum(),
        calibration_ratio=p.mean() / y.mean(),
        calibration_intercept=beta[0],
        calibration_slope=beta[1],
        high_risk_AUC=auc(event, p),
        high_risk_events=event.sum(),
        high_forecast_n=hi,
        eligible_n=ok.sum(),
        precision=precision,
        recall=np.sum(event & high & ok) / den if den else np.nan,
        base_rate=base,
        lift=precision / base if base > 0 else np.nan,
        DD_AUC=auc(z.future_DD5 >= z.DD_q90, p),
        DD_events=(z.future_DD5 >= z.DD_q90).sum(),
        tail_AUC=auc(z.future_tail5 > 0, p),
        tail_events=(z.future_tail5 > 0).sum(),
        negative5D_AUC=auc(z.future_return5 < 0, p),
        OO_SQ_spearman=pd.Series(p).corr(
            pd.Series(z.OO_SQ5.to_numpy()), method="spearman"
        ),
    )


def evaluate(f, out):
    good = f.groupby(["symbol", "session"]).apply(
        lambda x: len(x) == 5
        and x[["forecast", "actual", "future_DD5", "future_tail5"]].notna().all().all(),
        include_groups=False,
    )
    keys = good[good].index
    g = f.set_index(["symbol", "session"]).loc[keys].reset_index()
    rr = g.actual.clip(lower=1e-12) / g.forecast.clip(lower=1e-12)
    g["MSE"] = (g.actual - g.forecast) ** 2
    g["QLIKE"] = rr - np.log(rr) - 1
    g.to_parquet(out / "FORECAST_EVALUATION.parquet", index=False)
    common = g.groupby("session").symbol.nunique()
    common = common[common == 2].index
    rows = []
    bins = []
    conc = []
    for (sym, model), z in g.groupby(["symbol", "model"]):
        groups = group_masks(z)
        groups["COMMON_ALL"] = z.session.isin(common).to_numpy()
        for name, m in groups.items():
            if m.sum() < 20:
                continue
            rows.append(dict(symbol=sym, model=model, period=name, **metrics(z[m])))
        for period in ["ALL", "2023_PLUS"]:
            v = z[groups[period] & z.forecast_percentile.notna().to_numpy()].copy()
            v["bin"] = np.minimum((v.forecast_percentile * 10).astype(int), 9) + 1
            for b, q in v.groupby("bin"):
                bins.append(
                    dict(
                        symbol=sym,
                        model=model,
                        period=period,
                        bin=b,
                        n=len(q),
                        future_risk=q.actual.mean(),
                        future_tail_frequency=q.future_tail5.mean(),
                        mean_future_DD=q.future_DD5.mean(),
                        negative5D_frequency=(q.future_return5 < 0).mean(),
                        mean_forecast=q.forecast.mean(),
                    )
                )
    met = pd.DataFrame(rows)
    csv(out / "FORECAST_METRICS.csv", met)
    csv(out / "PIT_RISK_BUCKETS.csv", bins)
    for sym in ["SPY", "QQQ"]:
        a = g[(g.symbol == sym) & (g.model == "HAR")].set_index("session")
        groups = group_masks(a.reset_index())
        for base in BASES:
            b = (
                g[(g.symbol == sym) & (g.model == base)]
                .set_index("session")
                .reindex(a.index)
            )
            for loss in ["MSE", "QLIKE"]:
                diff = b[loss] - a[loss]
                for name, m in groups.items():
                    if m.sum() < 20:
                        continue
                    conc.append(
                        dict(
                            symbol=sym,
                            baseline=base,
                            loss=loss,
                            period=name,
                            n=int(m.sum()),
                            relative_improvement=1
                            - a.loc[m, loss].mean() / b.loc[m, loss].mean(),
                            improvement_sum=diff[m].sum(),
                            share_of_total=(
                                diff[m].sum() / diff.sum()
                                if abs(diff.sum()) > 1e-18
                                else np.nan
                            ),
                        )
                    )
    csv(out / "LOSS_CONCENTRATION.csv", conc)
    return g
