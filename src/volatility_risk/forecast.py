"""Monthly expanding log-HAR with mature targets and training-only smearing."""

import hashlib
import numpy as np
import pandas as pd
from .config import MIN_TRAIN, VARIANCE_FLOOR
from .io import save


def design(z):
    return np.c_[
        np.ones(len(z)),
        np.log(z[["GK_1", "GK_5", "GK_22"]].to_numpy().clip(min=VARIANCE_FLOOR)),
    ]


def run(d, out):
    rows = []
    vintages = []
    for sym, z in d.groupby("symbol"):
        z = z.sort_values("session").reset_index(drop=True)
        for month, cur0 in z.groupby(z.session.dt.strftime("%Y-%m")):
            first = cur0.session.iloc[0]
            tr = z[(z.session < first) & (z.target_end <= first)].dropna(
                subset=["GK_1", "GK_5", "GK_22", "Y5"]
            )
            cur = cur0.dropna(subset=["GK_1", "GK_5", "GK_22"])
            if len(tr) < MIN_TRAIN:
                continue
            x = design(tr)
            y = np.log(tr.Y5.clip(lower=VARIANCE_FLOOR).to_numpy())
            beta = np.linalg.lstsq(x, y, rcond=None)[0]
            smear = np.exp(y - x @ beta).mean()
            pred = np.exp(design(cur) @ beta) * smear
            rowhash = hashlib.sha256(
                "|".join(tr.session.dt.strftime("%Y-%m-%d")).encode()
            ).hexdigest()
            q90 = tr.Y5.quantile(0.9)
            dq = tr.future_DD5.quantile(0.9)
            vintages.append(
                dict(
                    symbol=sym,
                    vintage=month,
                    cutoff=first,
                    n_train=len(tr),
                    train_first=tr.session.min(),
                    train_origin_last=tr.session.max(),
                    latest_target_end=tr.target_end.max(),
                    row_hash=rowhash,
                    beta=beta,
                    smearing=smear,
                    target_mean=tr.Y5.mean(),
                    target_q90=q90,
                    DD_q90=dq,
                )
            )
            ts = z.set_index("session")
            for r, p in zip(cur.itertuples(), pred):
                common = dict(
                    symbol=sym,
                    session=r.session,
                    vintage=month,
                    n_train=len(tr),
                    target_end=r.target_end,
                    actual=r.Y5,
                    benchmark_mean=tr.Y5.mean(),
                    target_q90=q90,
                    DD_q90=dq,
                    future_DD5=r.future_DD5,
                    future_tail5=r.future_tail5,
                    future_return5=r.future_return5,
                    OO_SQ5=r.OO_SQ5,
                    information_session=r.session,
                    prediction_available="AFTER_CLOSE_NEXT_OPEN",
                    training_target_end=tr.target_end.max(),
                )
                pos = int(z.index[z.session == r.session][0])
                common.update(
                    information_cutoff=r.close_ts,
                    forecast_timestamp=r.close_ts + pd.Timedelta(minutes=1),
                    refit_cutoff=ts.loc[first, "close_ts"],
                    training_target_end_timestamp=ts.loc[
                        tr.target_end.max(), "open_ts"
                    ],
                    target_end_timestamp=(
                        ts.loc[r.target_end, "open_ts"]
                        if pd.notna(r.target_end)
                        else pd.NaT
                    ),
                    next_open_timestamp=(
                        z.open_ts.iloc[pos + 1] if pos + 1 < len(z) else pd.NaT
                    ),
                )
                for model, v in [
                    ("HAR", p),
                    ("CURRENT", r.GK_1),
                    ("EWMA", r.EWMA),
                    ("ROLLING22", r.GK_22),
                    ("HIST_MEAN", tr.Y5.mean()),
                ]:
                    rows.append(dict(**common, model=model, forecast=v))
        print("DAILY_FORECAST", sym, flush=True)
    f = pd.DataFrame(rows)
    parts = []
    for (sym, model), z in f.groupby(["symbol", "model"], sort=False):
        z = z.sort_values("session").copy()
        prior = z.forecast.shift()
        z["forecast_q90"] = prior.expanding(252).quantile(0.9)
        z["forecast_percentile"] = np.nan
        pp = z.forecast.to_numpy()
        rank = np.full(len(z), np.nan)
        for i in range(252, len(z)):
            rank[i] = ((pp[:i] < pp[i]).sum() + 0.5 * (pp[:i] == pp[i]).sum()) / i
        z["forecast_percentile"] = rank
        parts.append(z)
    f = pd.concat(parts, ignore_index=True)
    f["evidence"] = "EXPOSED_HISTORY"
    f.to_parquet(out / "FORECASTS.parquet", index=False)
    save(out / "VINTAGES.json", vintages)
    return f
