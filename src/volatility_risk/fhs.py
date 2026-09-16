"""Frozen direct five-day HS/FHS, using only mature expanding residual history."""

import bisect
import hashlib
import numpy as np
import pandas as pd
from .io import save

ALPHA = 0.05
SCORES = ["PINBALL", "FZ0", "BRIER2", "BRIER5", "DD_MSE"]
SHOCKS = [
    ("2007-01-01", "2009-12-31"),
    ("2020-02-19", "2020-06-30"),
    ("2022-01-01", "2022-12-31"),
]


def empirical(a, alpha=ALPHA):
    a = np.sort(np.asarray(a))
    k = alpha * len(a)
    whole = int(np.floor(k))
    frac = k - whole
    q = a[int(np.ceil(k)) - 1]
    e = (a[:whole].sum() + (frac * a[whole] if frac > 0 else 0)) / k
    return float(q), float(e)


def percentiles(v):
    history = []
    p = np.full(len(v), np.nan)
    for i, x in enumerate(v):
        if i >= 252:
            p[i] = (
                bisect.bisect_left(history, x) + bisect.bisect_right(history, x)
            ) / (2 * i)
        bisect.insort(history, x)
    return p


def masks(d):
    t = pd.to_datetime(d.session)
    m = {"ALL": np.ones(len(d), bool), "PRE2020": (t < "2020-01-01").to_numpy()}
    for k, a, b in [
        ("GFC", "2007-01-01", "2009-12-31"),
        ("2011", "2011-01-01", "2011-12-31"),
        ("2015_2016", "2015-01-01", "2016-12-31"),
        ("2018Q4", "2018-10-01", "2018-12-31"),
        ("COVID", "2020-02-19", "2020-06-30"),
        ("2022", "2022-01-01", "2022-12-31"),
        ("2023_PLUS", "2023-01-01", "2100-01-01"),
        ("2024_PLUS", "2024-01-01", "2100-01-01"),
    ]:
        m[k] = t.between(a, b).to_numpy()
    keep = np.ones(len(d), bool)
    for a, b in SHOCKS:
        keep &= ~((d.entry_session <= b) & (d.exit_session >= a)).to_numpy()
    m["EX_MAJOR_SHOCKS"] = keep
    for offset in range(5):
        m[f"NONOVERLAP5_{offset}"] = d.origin_index.to_numpy() % 5 == offset
    return m


def build(symbol, features, forecasts, data_dir, out):
    f = (
        forecasts[(forecasts.symbol == symbol) & (forecasts.model == "HAR")]
        .sort_values("session")
        .reset_index(drop=True)
        .copy()
    )
    z = (
        features[features.symbol == symbol]
        .sort_values("session")
        .reset_index(drop=True)
    )
    f["p"] = percentiles(f.forecast.to_numpy())
    f["origin_index"] = z.set_index("session").index.get_indexer(f.session)
    i = f.origin_index.to_numpy()
    d = (
        f[(i + 6 < len(z)) & f.p.notna().to_numpy() & f.actual.notna().to_numpy()]
        .copy()
        .reset_index(drop=True)
    )
    i = d.origin_index.to_numpy()
    px = z.Open.to_numpy()[i[:, None] + np.arange(1, 7)]
    nav = px / px[:, [0]]
    lognav = np.log(nav)
    daily = np.diff(lognav, axis=1)
    for h in range(1, 6):
        d[f"R{h}"] = nav[:, h] - 1
        d[f"logR{h}"] = lognav[:, h]
    d["path_min"] = (nav - 1).min(axis=1)
    d["path_maxDD"] = (1 - nav / np.maximum.accumulate(nav, axis=1)).max(axis=1)
    d["entry_session"] = z.session.iloc[i + 1].to_numpy()
    d["exit_session"] = z.session.iloc[i + 6].to_numpy()
    d["scale"] = np.sqrt(5 * d.forecast)
    d["Z"] = d.R5 / d.scale
    d["logZ"] = d.logR5 / d.scale
    d["logDD"] = np.max(np.maximum.accumulate(lognav, axis=1) - lognav, axis=1)
    d["H"] = d.logDD / d.scale
    d["D"] = -np.expm1(-d.logDD)
    d["state"] = np.select([d.p < 0.4, d.p < 0.8], ["LOW", "MID"], default="HIGH")
    d["sqsum"] = (daily**2).sum(axis=1)
    d["cross"] = d.logR5**2 - d.sqsum
    for j in range(5):
        d[f"u{j}"] = daily[:, j]
    cash = pd.read_csv(
        data_dir / "volatility_return_distribution/DGS3MO.csv", parse_dates=["date"]
    )
    cash["yield_percent"] = pd.to_numeric(cash.yield_percent, errors="coerce")
    assert cash.date.is_unique and cash.date.is_monotonic_increasing
    c = cash.dropna(subset=["yield_percent"])
    allowed = z.session.iloc[i - 2].to_numpy()
    ci = np.searchsorted(c.date.to_numpy(), allowed, side="right") - 1
    assert (ci >= 0).all()
    d["cash_allowed_quote_date"] = allowed
    d["cash_quote_date"] = c.date.iloc[ci].to_numpy()
    d["cash_quote_yield"] = c.yield_percent.iloc[ci].to_numpy()
    d["cash_age_days"] = (d.session - d.cash_quote_date).dt.days
    d["cash_calendar_days"] = (d.exit_session - d.entry_session).dt.days
    d["cash5"] = (d.cash_quote_yield / 100 * d.cash_calendar_days / 365).where(
        d.cash_age_days <= 7
    )
    d["evidence"] = "EXPOSED_HISTORY"
    assert np.max(abs(d.R5 - d.future_return5)) < 1e-12
    assert np.max(abs(d.D - d.future_DD5)) < 1e-12
    assert (d.forecast_timestamp < d.next_open_timestamp).all()
    d.to_parquet(out / "DAILY_PANEL.parquet", index=False)
    return d


def fhs_values(tr, s):
    q, e = empirical(tr.Z)
    zz = np.sort(tr.Z.to_numpy())
    hh = tr.H.to_numpy()
    return dict(
        q=s * q,
        e=s * e,
        p2=np.searchsorted(zz, -0.02 / s, side="left") / len(zz),
        p5=np.searchsorted(zz, -0.05 / s, side="left") / len(zz),
        dd=np.mean(-np.expm1(-s[:, None] * hh[None, :]), axis=1),
        impossible_mass=np.searchsorted(zz, -1 / s, side="left") / len(zz),
    )


def fit(d, out):
    rows, logs = [], []
    for month, cur in d.groupby(d.session.dt.strftime("%Y-%m")):
        cut = cur.information_cutoff.iloc[0]
        tr = d[(d.session < cur.session.iloc[0]) & (d.target_end_timestamp <= cut)]
        if len(tr) < 1008:
            continue
        s = cur.scale.to_numpy()
        hq, he = empirical(tr.R5)
        values = {
            "HS": dict(
                q=np.repeat(hq, len(cur)),
                e=np.repeat(he, len(cur)),
                p2=np.repeat((tr.R5 < -0.02).mean(), len(cur)),
                p5=np.repeat((tr.R5 < -0.05).mean(), len(cur)),
                dd=np.repeat(tr.D.mean(), len(cur)),
                impossible_mass=np.zeros(len(cur)),
            ),
            "FHS": fhs_values(tr, s),
        }
        logs.append(
            dict(
                vintage=month,
                n=len(tr),
                first=tr.session.min(),
                last=tr.session.max(),
                latest_target_end=tr.target_end_timestamp.max(),
                cutoff=cut,
                train_hash=hashlib.sha256(
                    "|".join(tr.session.astype(str)).encode()
                ).hexdigest(),
                FHS_q=empirical(tr.Z)[0],
                FHS_e=empirical(tr.Z)[1],
            )
        )
        for model, v in values.items():
            a = cur[
                [
                    "session",
                    "origin_index",
                    "R5",
                    "D",
                    "p",
                    "scale",
                    "information_cutoff",
                    "target_end_timestamp",
                    "entry_session",
                ]
            ].copy()
            (
                a["model"],
                a["vintage"],
                a["n_train"],
                a["fallback"],
                a["path_shared_FHS"],
            ) = (model, month, len(tr), False, False)
            for k, x in v.items():
                a[k] = x
            rows.append(a)
    f = pd.concat(rows, ignore_index=True)
    f["PINBALL"] = (ALPHA - (f.R5 < f.q).astype(float)) * (f.R5 - f.q)
    hit = (f.R5 <= f.q).astype(float)
    f["FZ0"] = -hit * (f.q - f.R5) / (ALPHA * f.e) + f.q / f.e + np.log(-f.e) - 1
    f["BRIER2"] = ((f.R5 < -0.02).astype(float) - f.p2) ** 2
    f["BRIER5"] = ((f.R5 < -0.05).astype(float) - f.p5) ** 2
    f["DD_MSE"] = (f.D - f.dd) ** 2
    f["DD_MAE"] = abs(f.D - f.dd)
    f["hit"] = hit
    f["ES_moment"] = (f.q - f.e - hit * (f.q - f.R5) / ALPHA) / (-f.e)
    f.to_parquet(out / "FORECASTS.parquet", index=False)
    save(out / "TRAINING_VINTAGES.json", logs)
    return f
