"""Read-only provenance, account arithmetic and README headline audit."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import numpy as np
import pandas as pd


def audit(source, public):
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    folder = public / "results/figures"
    provenance = json.loads(
        (folder / "PRESENTATION_PROVENANCE.json").read_text(encoding="utf-8")
    )
    for name, expected in provenance["sources"].items():
        assert sha(source / name) == expected, name
    for name, expected in provenance["figures"].items():
        assert sha(folder / name) == expected, name
    assert sha(public / "README.md") == provenance["readme_sha256"]
    d = json.loads((folder / "PRESENTATION_DATA.json").read_text(encoding="utf-8"))
    headline = pd.DataFrame(d["accounts"]).set_index(["asset", "rule"])
    expected = {}
    for s in ["SPY", "QQQ"]:
        for rule in ["BUYHOLD", "VOL"]:
            a = pd.read_parquet(
                source / "strategy" / s / "ledgers" / f"PROXY_0_1_{rule}.parquet"
            )
            c = pd.read_parquet(
                source / "strategy" / s / "cycles" / f"PROXY_0_1_{rule}.parquet"
            )
            r = a.net_return.to_numpy()
            nav = np.r_[1.0, a.end_NAV.to_numpy()]
            years = (
                (pd.to_datetime(a.end_session) - pd.to_datetime(a.execution_session))
                .dt.total_seconds()
                .sum()
                / 86400
                / 365.25
            )
            # Fractional empirical ES at the original 5% tail mass; no new estimator.
            returns = np.sort(c.net5.to_numpy())
            mass = 0.05 * len(returns)
            n = int(np.floor(mass))
            fraction = mass - n
            es = (
                -(returns[:n].sum() + (fraction * returns[n] if fraction else 0)) / mass
            )
            values = dict(
                CAGR=np.expm1(np.log1p(r).sum() / years),
                annual_vol=np.std(r, ddof=1) * np.sqrt(252),
                MaxDD=np.max(1 - nav / np.maximum.accumulate(nav)),
                ES95_5D=es,
            )
            for key, value in values.items():
                assert np.isclose(
                    value, headline.loc[(s, rule), key], atol=2e-12, rtol=1e-10
                ), (s, rule, key)
            expected[(s, rule)] = values
        retention = expected[(s, "VOL")]["CAGR"] / expected[(s, "BUYHOLD")]["CAGR"]
        assert np.isclose(
            retention, headline.loc[(s, "VOL"), "Return_Retention"], atol=2e-12
        )
        for key, metric in [
            ("volatility_reduction", "annual_vol"),
            ("drawdown_reduction", "MaxDD"),
            ("ES_reduction", "ES95_5D"),
        ]:
            row = next(z for z in d["reductions"] if z["asset"] == s)
            assert np.isclose(
                row[key],
                1 - expected[(s, "VOL")][metric] / expected[(s, "BUYHOLD")][metric],
                atol=2e-12,
            )
    m = pd.read_csv(source / "forecast/BENCHMARK_METRICS.csv")
    m = m[m.period.eq("ALL")].set_index(["symbol", "model"])
    gains = pd.DataFrame(d["forecast_gains"]).set_index(["symbol", "baseline"])
    for (s, b), row in gains.iterrows():
        for loss in ["MSE", "QLIKE"]:
            assert np.isclose(
                row[loss], 1 - m.loc[(s, "HAR"), loss] / m.loc[(s, b), loss], atol=2e-10
            )
    text = (public / "README.md").read_text(encoding="utf-8")
    rows = [
        [x.strip() for x in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if re.match(r"^\| (SPY|QQQ)\s*\|", line)
    ]
    assert len(rows) == 12, len(rows)
    checks = 0
    matched = pd.DataFrame(d["matched_exposure"]).set_index("asset")
    for s in ["SPY", "QQQ"]:
        source_attribution = pd.read_csv(
            source / "strategy" / s / "RETURN_RISK_ATTRIBUTION.csv"
        )
        source_attribution = source_attribution[
            (source_attribution.rule == "VOL")
            & (source_attribution.cash_mode == "PROXY")
            & (source_attribution.offset == 0)
            & (source_attribution.cost_bps == 1)
            & (source_attribution.period == "ALL")
        ].iloc[0]
        metrics = pd.read_csv(source / "strategy" / s / "PORTFOLIO_RESULTS.csv")
        static = metrics[
            (metrics.rule == "MATCH_VOL")
            & (metrics.cash_mode == "PROXY")
            & (metrics.offset == 0)
            & (metrics.cost_bps == 1)
            & (metrics.period == "ALL")
        ].iloc[0]
        for field, metric in [
            ("annual_vol_dynamic_fraction", "annual_vol"),
            ("ES95_5D_dynamic_fraction", "ES95_5D"),
            ("MaxDD_dynamic_fraction", "MaxDD"),
        ]:
            assert np.isclose(
                matched.loc[s, field], source_attribution[field], atol=2e-12
            )
            assert np.isclose(
                matched.loc[s, field],
                1 - headline.loc[(s, "VOL"), metric] / static[metric],
                atol=2e-12,
            )
        assert np.isclose(
            matched.loc[s, "dynamic_average"],
            static.average_exposure,
            atol=1e-10,
            rtol=0,
        )
        assert f'{s}: **{matched.loc[s,"dynamic_average"]*100:.2f}%**' in text
        checks += 1
    for row_number, row in enumerate(rows):
        s = row[0]
        if row_number >= 10:
            wants = [
                matched.loc[s, k] * 100
                for k in [
                    "annual_vol_dynamic_fraction",
                    "ES95_5D_dynamic_fraction",
                    "MaxDD_dynamic_fraction",
                ]
            ]
            got = row[1:]
        elif len(row) == 3:
            wants = [gains.loc[(s, "GARCH"), k] * 100 for k in ["MSE", "QLIKE"]]
            got = row[1:]
        elif len(row) == 7:
            rule = {"Buy & Hold": "BUYHOLD", "Full VOL": "VOL"}[row[1]]
            wants = [
                headline.loc[(s, rule), k] * 100
                for k in ["CAGR", "Return_Retention", "annual_vol", "ES95_5D", "MaxDD"]
            ]
            got = row[2:]
        elif "→" in row[1]:
            wants = [
                headline.loc[(s, rule), k] * 100
                for k in ["annual_vol", "MaxDD", "ES95_5D"]
                for rule in ["BUYHOLD", "VOL"]
            ]
            got = [v.strip() for cell in row[1:] for v in cell.split("→")]
        else:
            z = next(x for x in d["reductions"] if x["asset"] == s)
            wants = [
                z[k] * 100
                for k in ["volatility_reduction", "drawdown_reduction", "ES_reduction"]
            ]
            got = row[1:]
        assert got == [f"{v:.2f}" for v in wants], (row, wants)
        checks += len(got)
    image_links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(image_links) == 7
    for path in image_links:
        assert (public / path).is_file(), path
    assert "Core" not in text and "CORE_VOL" not in text
    assert "EXPOSED_HISTORY" in text and "WEAK" in text
    return dict(
        status="PASS",
        headline_numbers_verified=checks,
        original_accounts_rechecked=4,
        matched_static_comparisons_rechecked=6,
        forecast_loss_ratios_rechecked=8,
        image_links=len(image_links),
        source_hashes=len(provenance["sources"]),
        figure_hashes=len(provenance["figures"]),
        new_research=False,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--public", type=Path, default=Path("."))
    args = p.parse_args()
    print(json.dumps(audit(args.source, args.public), indent=2))
