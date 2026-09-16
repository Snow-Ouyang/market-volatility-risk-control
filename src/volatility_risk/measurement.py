"""GK session variance plus overnight squared return and next-open aligned targets."""

import numpy as np
import pandas as pd
from .config import FEATURE_WINDOWS, EWMA_DECAY


def transform(z, valid):
    """Input chronological calendar rows; never fill a missing price or risk label."""
    o = np.log(z.Open / z.Close.shift(1))
    c = np.log(z.Close / z.Open)
    rth = 0.5 * np.log(z.High / z.Low) ** 2 - (2 * np.log(2) - 1) * c**2
    valid &= rth >= -1e-12
    z["quality_valid"] = valid
    z["GK_RTH"] = rth.where(valid)
    z["overnight"] = o.where(valid & valid.shift(1, fill_value=False))
    z["OVN2"] = z.overnight**2
    z["GK_FULL"] = z.GK_RTH + z.OVN2
    for w in FEATURE_WINDOWS:
        z[f"GK_{w}"] = (
            z.GK_FULL
            if w == 1
            else z.GK_FULL.dropna().rolling(w, min_periods=w).mean().reindex(z.index)
        )
    state = np.nan
    values = []
    for x in z.GK_FULL:
        if np.isfinite(x):
            state = x if not np.isfinite(state) else EWMA_DECAY * state + 0.06 * x
            values.append(state)
        else:
            values.append(np.nan)
    z["EWMA"] = values
    z["HOLD"] = z.GK_RTH + z.OVN2.shift(-1)
    z["Y5"] = pd.concat([z.HOLD.shift(-j) for j in range(1, 6)], axis=1).mean(
        axis=1, skipna=False
    )
    z["target_end"] = z.session.shift(-6)
    # Open-only market outcomes are independent diagnostics, not replacement risk labels.
    oo = z.Open.shift(-1) / z.Open - 1
    z["oo_return"] = oo
    fret = pd.concat([oo.shift(-j) for j in range(1, 6)], axis=1)
    validfuture = fret.notna().all(axis=1)
    z["future_return5"] = z.Open.shift(-6) / z.Open.shift(-1) - 1
    z["future_tail5"] = fret.min(axis=1).lt(-0.02).astype(float).where(validfuture)
    futureprices = np.column_stack([z.Open.shift(-j) for j in range(1, 7)])
    nav = futureprices / futureprices[:, [0]]
    dd = 1 - nav / np.maximum.accumulate(nav, axis=1)
    z["future_DD5"] = np.max(dd, axis=1)
    z["OO_SQ5"] = (fret**2).mean(axis=1, skipna=False)
    return z
