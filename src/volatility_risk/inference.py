"""Paired circular calendar-block intervals; frozen four-baseline comparison families."""

import hashlib
import numpy as np
import pandas as pd
from .config import MODELS, BASES, DRAWS, SEED
from .io import csv, save
from .evaluation import group_masks


def indices(n, L, salt=0):
    rng = np.random.default_rng(SEED + L + salt)
    starts = rng.integers(0, n, size=(DRAWS, int(np.ceil(n / L))))
    return (
        ((starts[:, :, None] + np.arange(L)) % n)
        .reshape(DRAWS, -1)[:, :n]
        .astype(np.int32)
    )


def counts(ix, n):
    c = np.zeros((len(ix), n))
    np.add.at(c, (np.arange(len(ix))[:, None], ix), 1)
    return c


def inference(g, d, out):
    rows = []
    plan = []
    common = g.groupby("session").symbol.nunique()
    common = common[common == 2].index
    for sym, z in g.groupby("symbol"):
        calendar = pd.DatetimeIndex(
            d[
                (d.symbol == sym) & d.session.between(z.session.min(), z.session.max())
            ].session
        )
        labels = pd.DataFrame({"session": calendar})
        masks = group_masks(labels)
        # Common-date analysis still retains intervening unavailable calendar rows.
        masks["COMMON_ALL"] = (calendar >= common.min()) & (calendar <= common.max())
        for period in ["ALL", "2023_PLUS", "COMMON_ALL", "EX_COVID"]:
            cal = calendar[masks[period]]
            for L in [21, 42]:
                ix = indices(len(cal), L)
                cc = counts(ix, len(cal))
                plan.append(
                    dict(
                        symbol=sym,
                        period=period,
                        block=L,
                        draws=DRAWS,
                        n_calendar=len(cal),
                        index_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),
                    )
                )
                for loss in ["MSE", "QLIKE"]:
                    x = (
                        z.pivot(index="session", columns="model", values=loss)
                        .reindex(cal)
                        .reindex(columns=MODELS)
                    )
                    if period == "COMMON_ALL":
                        x.loc[~x.index.isin(common)] = np.nan
                    valid = x.notna().all(axis=1).to_numpy()
                    means = (
                        cc
                        @ x.fillna(0).to_numpy()
                        / (cc @ valid.astype(float))[:, None]
                    )
                    pt = x.mean().to_numpy()
                    gain = 1 - means[:, [0]] / means[:, 1:]
                    point = 1 - pt[0] / pt[1:]
                    sd = gain.std(axis=0, ddof=1)
                    err = np.divide(
                        point - gain, sd, out=np.zeros_like(gain), where=sd > 1e-15
                    )
                    crit = np.quantile(err.max(axis=1), 0.95)
                    lower = point - crit * sd
                    for j, base in enumerate(BASES):
                        lo, hi = np.quantile(gain[:, j], [0.025, 0.975])
                        rows.append(
                            dict(
                                symbol=sym,
                                period=period,
                                block=L,
                                loss=loss,
                                baseline=base,
                                n=int(valid.sum()),
                                point_improvement=point[j],
                                ci_low=lo,
                                ci_high=hi,
                                simultaneous_lower95=lower[j],
                                family_size=4,
                            )
                        )
            print("DAILY_INTERVALS", sym, period, flush=True)
    csv(out / "PAIRED_INTERVALS.csv", rows)
    save(out / "BOOTSTRAP_PLAN.json", plan)
