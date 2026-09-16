"""Redraw the public presentation from existing canonical outputs, without research."""

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from volatility_risk.final_reporting import render


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        p.error("Use a new or empty presentation output directory")
    args.output.mkdir(parents=True, exist_ok=True)
    render(args.source, args.output)
    print("PRESENTATION_COMPLETE", args.output)


if __name__ == "__main__":
    main()
