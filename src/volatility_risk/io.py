"""Portable artifact IO; no workspace or private archive dependencies."""

from pathlib import Path
import json, hashlib, datetime
import numpy as np
import pandas as pd


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [clean(v) for v in x]
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, (pd.Timestamp, datetime.datetime, datetime.date, Path)):
        return str(x)
    return x


def save(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(
        json.dumps(clean(obj), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def csv(p, x):
    z = x.copy() if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
    z["evidence"] = "EXPOSED_HISTORY"
    z.to_csv(p, index=False, encoding="utf-8")
