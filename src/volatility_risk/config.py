"""Frozen specification. Changing these constants creates a new research vintage."""

MODELS = ["HAR", "CURRENT", "EWMA", "ROLLING22", "HIST_MEAN"]
BASES = MODELS[1:]
DRAWS = 1999
SEED = 20260913
STRESS = {
    "2018Q4": ("2018-10-01", "2018-12-31"),
    "COVID": ("2020-02-19", "2020-06-30"),
    "2022": ("2022-01-01", "2022-12-31"),
    "2025_SPRING": ("2025-02-01", "2025-05-30"),
}
EPISODES = {
    "DOTCOM": ("2000-01-01", "2002-12-31"),
    "GFC": ("2007-01-01", "2009-12-31"),
    "2011": ("2011-01-01", "2011-12-31"),
    "2015_2016": ("2015-01-01", "2016-12-31"),
    **STRESS,
}
PERIODS = {
    "ALL": (None, None),
    "PRE2000": (None, "1999-12-31"),
    "2000_2009": ("2000-01-01", "2009-12-31"),
    "2010_2019": ("2010-01-01", "2019-12-31"),
    "2020_2022": ("2020-01-01", "2022-12-31"),
    "2023_PLUS": ("2023-01-01", None),
    "2020_PLUS": ("2020-01-01", None),
}
CUTOFF = "2026-08-28"
SYMBOLS = ("SPY", "QQQ")
MIN_TRAIN = 504
FEATURE_WINDOWS = (1, 5, 22)
EWMA_DECAY = 0.94
VARIANCE_FLOOR = 1e-12
