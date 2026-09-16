"""Reproduce the frozen canonical forecast, FHS and Full VOL application."""

from pathlib import Path
import sys, os, argparse, json, shutil, importlib.metadata

for name in [
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[name] = "1"
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from volatility_risk import (
    data,
    forecast,
    garch,
    benchmark_evaluation,
    benchmark_review,
    fhs,
    tail_evaluation,
    tail_inference,
    strategy,
)
from volatility_risk.io import save, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data/local")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument(
        "--frozen-forecast",
        action="store_true",
        help="Replay from hash-verified canonical forecast files, without re-estimation",
    )
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        p.error("Output must be empty; no overwriting")
    a.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "data/mainline_inputs.json").read_text())
    required = ["SPY.csv", "QQQ.csv", "volatility_return_distribution/DGS3MO.csv"]
    for n in required:
        assert sha(a.data_dir / n) == manifest[n], n
    fo = a.output / "forecast"
    fo.mkdir()
    d = data.build(a.data_dir, fo, ROOT / "data/reference_inputs.json")
    if a.frozen_forecast:
        import pandas as pd

        for n in [
            "FORECASTS.parquet",
            "FORECASTS_WITH_GARCH.parquet",
            "VINTAGES.json",
            "GARCH_VINTAGES.json",
            "GARCH_MODEL_SELECTION.csv",
        ]:
            q = a.data_dir / "reference/forecast" / n
            assert sha(q) == manifest[q.relative_to(a.data_dir).as_posix()]
            shutil.copy2(q, fo / n)
        f = pd.read_parquet(fo / "FORECASTS.parquet")
        allf = pd.read_parquet(fo / "FORECASTS_WITH_GARCH.parquet")
    else:
        f = forecast.run(d, fo)
        allf = garch.run(d, f, fo, a.workers)
    met, losses, ci = benchmark_evaluation.evaluate(allf, d, fo)
    benchmark_evaluation.decide(met, losses, ci, fo)
    if not a.frozen_forecast:
        benchmark_review.run(fo)
    for symbol in ["SPY", "QQQ"]:
        out = a.output / "tail" / symbol
        out.mkdir(parents=True)
        panel = fhs.build(symbol, d, f, a.data_dir, out)
        tf = fhs.fit(panel, out)
        tail_evaluation.evaluate(panel, tf, out)
        tail_inference.forecast_inference(panel, tf, out)
        so = a.output / "strategy" / symbol
        so.mkdir(parents=True)
        strategy.run(
            symbol,
            panel,
            tf,
            d,
            json.loads((out / "TRAINING_VINTAGES.json").read_text()),
            so,
        )
    from volatility_risk.consolidation_review import validate

    validate(a.output, a.data_dir)
    from volatility_risk.final_reporting import render

    render(a.output)
    save(
        a.output / "ENVIRONMENT.json",
        {
            n: importlib.metadata.version(n)
            for n in [
                "numpy",
                "pandas",
                "scipy",
                "arch",
                "numba",
                "llvmlite",
                "exchange-calendars",
                "pyarrow",
            ]
        },
    )
    save(
        a.output / "COMPLETION_SEAL.json",
        dict(
            status="PASS",
            mode=(
                "FROZEN_FORECAST_REPLAY"
                if a.frozen_forecast
                else "FULL_FROZEN_SPECIFICATION_REPRODUCTION"
            ),
            history="EXPOSED_HISTORY",
            files={
                p.relative_to(a.output).as_posix(): sha(p)
                for p in a.output.rglob("*")
                if p.is_file()
            },
        ),
    )
    print("CANONICAL_COMPLETE", a.output, flush=True)


if __name__ == "__main__":
    main()
