"""Validated adjusted Yahoo daily snapshots; no implicit fills or downloads."""

from pathlib import Path
import numpy as np
import pandas as pd
import exchange_calendars as xcals
from .config import SYMBOLS, CUTOFF
from .io import csv, save, sha, read
from .measurement import transform


def build(data_dir, out, reference_manifest=None, symbols=SYMBOLS):
    frames, audits = [], []
    reference = read(reference_manifest) if reference_manifest else {}
    for symbol in symbols:
        path = Path(data_dir) / f"{symbol}.csv"
        z = pd.read_csv(path, parse_dates=["Date"]).rename(
            columns={"Date": "session", "Stock Splits": "Stock_Splits"}
        )
        required = {"session", "Open", "High", "Low", "Close", "Volume"}
        if not required.issubset(z.columns):
            raise ValueError(f"{symbol}: missing required OHLCV columns")
        if not z.session.is_unique or not z.session.is_monotonic_increasing:
            raise ValueError(f"{symbol}: duplicate or unsorted sessions")
        z = z[z.session <= pd.Timestamp(CUTOFF)].copy()
        for column in ["Dividends", "Stock_Splits"]:
            if column not in z:
                z[column] = 0.0
        cal = xcals.get_calendar(
            "XNYS", start=str(z.session.min().date()), end=str(z.session.max().date())
        )
        expected = cal.sessions_in_range(z.session.min(), z.session.max()).tz_localize(
            None
        )
        missing = expected.difference(z.session)
        extra = pd.DatetimeIndex(z.session).difference(expected)
        if len(extra) or len(missing):
            raise ValueError(
                f"{symbol}: {len(missing)} missing and {len(extra)} extra sessions; no repair performed"
            )
        z = (
            z.set_index("session")
            .reindex(expected)
            .rename_axis("session")
            .reset_index()
        )
        z["symbol"] = symbol
        schedule = cal.schedule.reindex(expected)
        z["open_ts"] = schedule["open"].to_numpy()
        z["close_ts"] = schedule["close"].to_numpy()
        ohlc = z[["Open", "High", "Low", "Close"]]
        finite = np.isfinite(ohlc).all(axis=1) & (ohlc > 0).all(axis=1)
        geometry = np.maximum(
            ohlc[["Open", "Close", "Low"]].max(axis=1) - z.High,
            z.Low - ohlc[["Open", "Close", "High"]].min(axis=1),
        )
        valid = (
            finite
            & (geometry <= 1e-7 * z.Close)
            & z.Volume.ge(0)
            & np.isfinite(z.Volume)
        )
        z = transform(z, valid)
        if not z.quality_valid.all():
            raise ValueError(f"{symbol}: invalid OHLCV; no silent clipping or deletion")
        audits.append(
            dict(
                symbol=symbol,
                file=path.name,
                sha256=sha(path),
                reference_match=sha(path) == reference.get(symbol, {}).get("sha256"),
                start=z.session.min(),
                end=z.session.max(),
                calendar_rows=len(z),
                missing_sessions=len(missing),
                invalid_OHLC=0,
                mature_target_n=int(z.Y5.notna().sum()),
                auto_adjust=True,
            )
        )
        frames.append(z)
    d = pd.concat(frames, ignore_index=True)
    d["evidence"] = "EXPOSED_HISTORY"
    d.to_parquet(out / "DAILY_FEATURES.parquet", index=False)
    csv(out / "DATA_COVERAGE.csv", audits)
    save(out / "INPUT_FINGERPRINTS.json", audits)
    return d


def fetch(data_dir):
    """Explicit optional daily fetch. Refuse to replace any existing input file."""
    import yfinance as yf

    destination = Path(data_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if any((destination / f"{s}.csv").exists() for s in SYMBOLS):
        raise FileExistsError("Use a new data directory; existing inputs are immutable")
    receipts = []
    for symbol in SYMBOLS:
        z = yf.download(
            symbol,
            period="max",
            interval="1d",
            auto_adjust=True,
            actions=True,
            repair=False,
            keepna=True,
            progress=False,
            threads=False,
            multi_level_index=False,
        )
        if z.empty:
            raise RuntimeError(f"Yahoo returned no rows for {symbol}")
        z.index = pd.to_datetime(z.index).tz_localize(None)
        z = z.loc[z.index <= pd.Timestamp(CUTOFF)].rename(
            columns={"Stock Splits": "Stock_Splits"}
        )
        z.index.name = "Date"
        path = destination / f"{symbol}.csv"
        z.to_csv(path, encoding="utf-8")
        receipts.append(
            dict(
                symbol=symbol,
                file=path.name,
                sha256=sha(path),
                retrieved_utc=str(pd.Timestamp.now(tz="UTC")),
                provider="Yahoo via yfinance",
                interval="1d",
                auto_adjust=True,
                cutoff=CUTOFF,
                revision_status="NEW_SNAPSHOT_NOT_REFERENCE_VINTAGE",
            )
        )
    save(destination / "retrieval.json", receipts)
