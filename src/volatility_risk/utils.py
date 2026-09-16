"""Calendar masks and rank-based event discrimination."""

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def mask(dates, window):
    d = pd.DatetimeIndex(dates)
    lo, hi = window
    return ((d >= pd.Timestamp(lo)) if lo else np.ones(len(d), bool)) & (
        (d <= pd.Timestamp(hi)) if hi else np.ones(len(d), bool)
    )


def auc(y, p):
    y = np.asarray(y, bool)
    p = np.asarray(p)
    a = y.sum()
    b = len(y) - a
    return (rankdata(p)[y].sum() - a * (a + 1) / 2) / (a * b) if a * b else np.nan
