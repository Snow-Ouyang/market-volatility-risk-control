"""Generate every public headline number from the canonical replay outputs."""

import shutil
import pandas as pd
from .io import save, sha


def pct_table(d, columns):
    d = d.copy()
    for c in columns:
        d[c] *= 100
    return d.to_markdown(index=False, floatfmt=".2f")


def render(out, public=None):
    public = public if public is not None else out / "public"
    r = public / "results"
    for folder in ["forecast", "tail", "strategy", "figures"]:
        (r / folder).mkdir(parents=True, exist_ok=True)
    for name in [
        "DATA_COVERAGE.csv",
        "BENCHMARK_METRICS.csv",
        "BENCHMARK_LOSS_GAINS.csv",
        "BENCHMARK_PAIRED_INTERVALS.csv",
        "BENCHMARK_RISK_BUCKETS.csv",
        "GARCH_MODEL_SELECTION.csv",
        "BENCHMARK_STATUS.json",
    ]:
        shutil.copy2(out / "forecast" / name, r / "forecast" / name)
    application = []
    application_coverage = []
    attribution = []
    tail = []
    ranges = []
    for s in ["SPY", "QQQ"]:
        t = out / "tail" / s
        st = out / "strategy" / s
        import json

        coverage_audit = json.loads((st / "DATA_COVERAGE_AUDIT.json").read_text())
        first_account = pd.read_parquet(st / "ledgers/PROXY_0_1_VOL.parquet")
        application_coverage.append(
            dict(
                asset=s,
                first_origin=coverage_audit["first_eligible"],
                last_origin=coverage_audit["last_eligible"],
                eligible_origins=coverage_audit["eligible_origins"],
                excluded_prefix=coverage_audit["excluded_prefix"],
                offset0_entry=str(first_account.execution_session.iloc[0].date()),
                offset0_exit=str(first_account.end_session.iloc[-1].date()),
            )
        )
        for group, source, names in [
            (
                "tail",
                t,
                [
                    "FORECAST_METRICS.csv",
                    "CALIBRATION.csv",
                    "NONOVERLAP_COVERAGE.csv",
                    "PAIRED_INTERVALS.csv",
                    "SHOCK_CONTRIBUTIONS.csv",
                ],
            ),
            (
                "strategy",
                st,
                [
                    "PORTFOLIO_RESULTS.csv",
                    "RETURN_RISK_ATTRIBUTION.csv",
                    "PERIOD_STATIC_CONTROLS.csv",
                    "OPPORTUNITY_COST.csv",
                    "NORMALIZATION.json",
                    "DATA_COVERAGE_AUDIT.json",
                ],
            ),
        ]:
            target = r / group / s
            target.mkdir()
            for name in names:
                shutil.copy2(source / name, target / name)
        p = pd.read_csv(st / "PORTFOLIO_RESULTS.csv")
        primary = p[(p.cash_mode == "PROXY") & (p.cost_bps == 1) & (p.period == "ALL")]
        application.append(
            primary[
                (primary.offset == 0)
                & primary.rule.isin(["BUYHOLD", "VOL", "CORE_VOL"])
            ].assign(asset=s)
        )
        for rule, z in primary.groupby("rule"):
            for metric in [
                "CAGR",
                "Return_Retention",
                "annual_vol",
                "ES95_5D",
                "MaxDD",
                "average_exposure",
            ]:
                ranges.append(
                    dict(
                        asset=s,
                        rule=rule,
                        metric=metric,
                        minimum=z[metric].min(),
                        maximum=z[metric].max(),
                    )
                )
        a = pd.read_csv(st / "RETURN_RISK_ATTRIBUTION.csv")
        attribution.append(
            a[
                (a.cash_mode == "PROXY")
                & (a.cost_bps == 1)
                & (a.period == "ALL")
                & (a.offset == 0)
            ].assign(asset=s)
        )
        m = pd.read_csv(t / "FORECAST_METRICS.csv")
        tail.append(m[m.period == "ALL"].assign(asset=s))
    app = pd.concat(application)
    att = pd.concat(attribution)
    tm = pd.concat(tail)
    app.to_csv(r / "strategy/HEADLINE_ACCOUNTS.csv", index=False)
    pd.DataFrame(application_coverage).to_csv(
        r / "strategy/APPLICATION_COVERAGE.csv", index=False
    )
    att.to_csv(r / "strategy/HEADLINE_ATTRIBUTION.csv", index=False)
    pd.DataFrame(ranges).to_csv(r / "strategy/OFFSET_RANGES.csv", index=False)
    tm.to_csv(r / "tail/HEADLINE_METRICS.csv", index=False)
    loss = pd.read_csv(out / "forecast/BENCHMARK_LOSS_GAINS.csv")
    gain = (
        loss[(loss.period == "ALL") & loss.baseline.isin(["GARCH", "ROLLING22"])]
        .pivot(
            index=["symbol", "baseline"], columns="loss", values="relative_improvement"
        )
        .reset_index()
    )
    gain.to_csv(r / "forecast/HEADLINE_GAINS.csv", index=False)
    coverage = pd.read_csv(out / "forecast/DATA_COVERAGE.csv")
    cols = [
        "CAGR",
        "Return_Retention",
        "annual_vol",
        "ES95_5D",
        "MaxDD",
        "average_exposure",
        "annual_turnover",
        "annual_fee_drag",
    ]
    app_table = pct_table(app.loc[app.rule.isin(["BUYHOLD", "VOL"]), ["asset", "rule"] + cols], cols)
    app_table = (
        "Application coverage is shorter than the price/forecast history because FHS needs mature residual history and the frozen cash rule rejects stale quotes. The SPY prefix excludes the existing September-2001 stale-quote break; the risk-budget calibration is not reset. Dates below are the actual primary account endpoints.\n\n"
        + pd.DataFrame(application_coverage).to_markdown(index=False)
        + "\n\n"
        + app_table
    )
    gain_table = pct_table(gain, ["MSE", "QLIKE"])
    tail_table = tm[
        [
            "asset",
            "model",
            "n",
            "PINBALL",
            "FZ0",
            "BRIER2",
            "BRIER5",
            "DD_MSE",
            "var_hit_rate",
        ]
    ].to_markdown(index=False, floatfmt=".6f")
    acols = [
        "CAGR_exposure_opportunity",
        "CAGR_dynamic_timing",
        "CAGR_cash",
        "CAGR_cost",
        "CAGR_interaction",
        "annual_vol_dynamic_fraction",
        "ES95_5D_dynamic_fraction",
        "MaxDD_dynamic_fraction",
    ]
    att_table = pct_table(att.loc[att.rule.eq("VOL"), ["asset", "rule"] + acols], acols)
    report = (
        """# Final canonical research report

**Market Volatility Forecasting & Risk Control** — finished historical research, EXPOSED_HISTORY.

The supported chain is daily GK-plus-gap measurement, marginal risk prediction, scale-conditioned FHS and a transparent Full VOL/cash application. Directional prediction, complex allocation and duration parking did not earn promotion. Selecting Full VOL as the explanatory canonical application does not overturn the prior preference for static exposure under a strict cross-regime deployment gate.

## Forecast evidence

"""
        + gain_table
        + "\n\nThe frozen GARCH joint status is WEAK. Full period, calibration and simultaneous-interval tables are retained under results/forecast.\n\n## Tail evidence\n\n"
        + tail_table
        + "\n\n## Final accounts\n\n"
        + app_table
        + "\n\n## Return and matched-exposure risk attribution\n\nFirst five component columns are CAGR percentage points; the final three are relative percent risk gains versus equal-average-exposure static controls. Exact additive return identities are evaluated before rounding.\n\n"
        + att_table
        + """

Matched controls use future full-period average exposure by design and are strictly ex-post. Removing crisis periods preserves separate drawdown segments, rather than splicing them into an investable account. Full accounts and all 0/1/3bp, PROXY/ZERO, five-offset fixed sensitivities reproduce the original selected accounts. No additional target/core parameter was tested.

## Post-convergence decision

Post-convergence extensions produced useful forecasting and diversification evidence, but none provided sufficiently stable portfolio-level increment to justify changing the canonical 5D architecture.

**Supported mainline:** 5D risk forecasting, FHS tail translation, Full VOL risk control and the frozen 3M cash sleeve. Cash remains a yield-carry approximation with PARTIAL release-vintage provenance.

**Useful but noncanonical:** Gold strategic diversification, 21D risk forecasting and sequential remaining-risk reforecasting.

**Not promoted:** dynamic Gold allocation, Gold/cash scaling, Full VOL no-trade bands, path-surprise triggers, weekly/event parameter refits and 5D–21D portfolio overlays.

The public application remains 5D Full VOL. Previously frozen secondary-account rows remain only in immutable reference tables and parity checks; they are not promoted back into the mainline. See [post-convergence evidence and dispositions](POST_CONVERGENCE_RESEARCH_SUMMARY.md). No new parameter, account or research comparison was introduced by this cleanup.

## Interpretation and stop

Volatility describes distribution width and tail scale more reliably than return direction. Cash is a short-duration carry proxy with known provenance limits; IEF's rate sensitivity is not part of that safe sleeve. No new forward vintage, scheduler, order, deployment or push was performed. The mainline is reproducible research, not prospective deployment evidence.

![Forecast](results/figures/FORECAST_ACCURACY.png)

![QQQ application](results/figures/QQQ_RISK_CONTROL.png)

See [README](README.md), [history](RESEARCH_HISTORY_SUMMARY.md), [validation](VALIDATION.md) and [cleanup](CLEANUP_REPORT.md).
"""
    )
    (public / "REPORT.md").write_text(report, encoding="utf-8")
    save(
        public / "results/HEADLINE_PROVENANCE.json",
        dict(
            generated_by="volatility_risk.final_reporting.render",
            history="EXPOSED_HISTORY",
            configuration=dict(
                cash="PROXY", cost_bps=1, offset=0, rebalance_sessions=5
            ),
            source_files={
                p.relative_to(out).as_posix(): sha(p)
                for p in [
                    out / "forecast/DATA_COVERAGE.csv",
                    out / "forecast/BENCHMARK_LOSS_GAINS.csv",
                ]
                + [
                    out / k / s / n
                    for s in ["SPY", "QQQ"]
                    for k, n in [
                        ("tail", "FORECAST_METRICS.csv"),
                        ("strategy", "PORTFOLIO_RESULTS.csv"),
                        ("strategy", "RETURN_RISK_ATTRIBUTION.csv"),
                    ]
                ]
            },
        ),
    )

    from .presentation import render as render_presentation

    render_presentation(out, public)
