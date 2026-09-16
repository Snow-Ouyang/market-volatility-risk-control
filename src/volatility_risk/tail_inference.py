"""Frozen paired FHS-vs-HS inference family; no new model comparisons."""

import numpy as np
import pandas as pd
from .fhs import masks, SCORES

BLOCKS = [21, 42]
SEED = 20260914
B = 1999


def draw(n, block, rng):
    starts = rng.integers(0, n, size=(n + block - 1) // block)
    return ((starts[:, None] + np.arange(block)) % n).ravel()[:n]


def weights(n, block):
    rng = np.random.default_rng(SEED)
    return np.stack(
        [np.bincount(draw(n, block, rng), minlength=n) for _ in range(B)]
    ).astype(np.float32)


def avg(w, y, g):
    den = w @ g.astype(float)
    return np.divide(
        w @ (np.nan_to_num(y) * g), den, out=np.full(len(w), np.nan), where=den > 0
    )


def bounds(point, rep, labels, period, block, family):
    sd = np.nanstd(rep, axis=0, ddof=1)
    ok = np.isfinite(point) & np.isfinite(sd) & (sd > 0)
    zz = abs((rep[:, ok] - point[ok]) / sd[ok])
    crit = (
        np.quantile(np.where(np.isfinite(zz), zz, 0).max(axis=1), 0.95)
        if ok.any()
        else np.nan
    )
    rows = []
    for j, label in enumerate(labels):
        a = rep[:, j]
        valid = np.isfinite(a)
        enough = valid.mean() >= 0.95
        rows.append(
            dict(
                period=period,
                block=block,
                contrast=label,
                family=family,
                point=point[j],
                valid_fraction=valid.mean(),
                ci_low=np.quantile(a[valid], 0.025) if enough else np.nan,
                ci_high=np.quantile(a[valid], 0.975) if enough else np.nan,
                sim_low=point[j] - crit * sd[j] if enough else np.nan,
                sim_high=point[j] + crit * sd[j] if enough else np.nan,
            )
        )
    return rows


def scorearray(d, f, specs, m):
    aligned = {
        model: z.set_index("origin_index").reindex(d.origin_index)
        for model, z in f.groupby("model")
    }
    vals = []
    den = []
    valid = []
    for candidate, reference, k in specs:
        c = aligned[candidate][k].to_numpy()
        r = aligned[reference][k].to_numpy()
        g = m & np.isfinite(c) & np.isfinite(r)
        vals.append(np.nan_to_num(r - c) * g)
        den.append(np.nan_to_num(r) * g)
        valid.append(g)
    return np.array(vals).T, np.array(den).T, np.array(valid).T


def means(w, arr, g):
    n = w @ g.astype(float)
    return np.divide(w @ arr, n, out=np.full_like(n, np.nan), where=n > 0)


def forecast_inference(d, f, out):
    one = np.ones((1, len(d)))
    rows = []
    calrows = []
    ps = masks(d)
    for block in BLOCKS:
        w = weights(len(d), block)
        for period, m in ps.items():
            for family, specs in families(f).items():
                vals, den, g = scorearray(d, f, specs, m)
                pt = means(one, vals, g)[0]
                ref = means(one, den, g)[0]
                z = bounds(
                    pt,
                    means(w, vals, g),
                    ["|".join(x) for x in specs],
                    period,
                    block,
                    family,
                )
                for j, r in enumerate(z):
                    r.update(
                        candidate=specs[j][0],
                        reference=specs[j][1],
                        score=specs[j][2],
                        n=int(g[:, j].sum()),
                        fractional_gain=(
                            pt[j] / ref[j] if specs[j][2] != "FZ0" else np.nan
                        ),
                    )
                rows += z
            for model, a in f.groupby("model", sort=False):
                aa = a.set_index("origin_index").reindex(d.origin_index)
                columns = {
                    "VAR_BIAS": aa.hit - 0.05,
                    "ES_IDENTIFICATION": aa.ES_moment,
                    "P2_BIAS": aa.p2 - (aa.R5 < -0.02).astype(float),
                    "P5_BIAS": aa.p5 - (aa.R5 < -0.05).astype(float),
                    "DD_BIAS": aa.dd - aa.D,
                }
                for name, x in columns.items():
                    v = x.to_numpy()
                    g = m & np.isfinite(v) & aa.R5.notna().to_numpy()
                    point = avg(one, v, g)
                    rep = avg(w, v, g)
                    rr = bounds(
                        point,
                        rep[:, None],
                        [name],
                        period,
                        block,
                        "calibration_descriptive",
                    )[0]
                    rr["model"] = model
                    calrows.append(rr)
        print("FORECAST_INFERENCE", out.name, block, flush=True)
    pd.DataFrame(rows).to_csv(out / "PAIRED_INTERVALS.csv", index=False)
    pd.DataFrame(calrows).to_csv(out / "CALIBRATION_INTERVALS.csv", index=False)


def families(f):
    return {"FHS_VALUE": [("FHS", "HS", k) for k in SCORES]}
