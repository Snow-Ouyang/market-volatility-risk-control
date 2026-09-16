# Presentation refinement

Completed 2026-09-15. This update changes presentation only. Models, parameters, inputs, risk budgets, accounts, scores and research conclusions remain frozen.

## README: results before methods

The first screen now gives the thesis, HAR-versus-GARCH loss reductions and Buy & Hold-to-Full VOL risk changes for both SPY and QQQ. It then shows forecast accuracy, the two historical equity/cash applications, and their return/risk tradeoff. Session/gap alignment and formulas follow the results; forecast-state calibration, FHS, retired extensions, limitations and reproduction remain available below.

Only Buy & Hold and Full VOL appear in the headline tables and account figures. Core50 remains unchanged in REPORT and canonical result tables as an investor-preference example. IEF, correlation, alternate ES/probability mappings and optimizers are confined to the compact research-history discussion. No positive inference claim was substituted for the original WEAK HAR/GARCH or dynamic/static promotion verdicts.

## Six figures, each PNG and PDF

| Figure | Purpose | Frozen source |
| --- | --- | --- |
| FORECAST_ACCURACY | Paired horizontal MSE/QLIKE loss reductions | BENCHMARK_LOSS_GAINS; checked against BENCHMARK_METRICS |
| FORECAST_VS_REALIZED | Past-only forecast-risk buckets versus realized risk | Existing HAR / ALL BENCHMARK_RISK_BUCKETS |
| SPY_RISK_CONTROL | Log wealth, underwater drawdown, actual equity exposure | SPY PROXY / offset 0 / 1bp Buy & Hold and VOL ledgers |
| QQQ_RISK_CONTROL | Same framework and account view for historical transfer | QQQ, same configuration |
| RISK_RETURN_TRADEOFF | CAGR, volatility, MaxDD and 5D ES95 | The same four canonical accounts |
| SESSION_HOLDING_TIMELINE | Distinguish state and open-to-open holding alignment | Frozen measurement definitions; conceptual diagram |

All figures use a restrained navy/teal/gray palette, explicit units, sample qualifications and readable legends. Account figures show daily marks without smoothing, initial funding and natural weight drift. Wealth uses a labeled log scale; drawdown includes the initial $1 observation. Crisis shading uses the existing GFC/COVID/2022 windows. Risk-bucket curves use `100 * sqrt(252 * bucket mean daily variance proxy)`, not an average of volatilities, endpoint-return volatility or a new risk estimator. No future-based regrouping, smoothing, interval estimation or new scoring was introduced.

The three former presentation PNGs were superseded, after recording their hashes privately. Original canonical outputs and all numerical research tables remain unchanged.

## Headline provenance and checks

The renderer reads canonical results; no measured headline value is hard-coded. [Presentation data](results/figures/PRESENTATION_DATA.json) carries the display inputs; [provenance](results/figures/PRESENTATION_PROVENANCE.json) records source and figure hashes. The read-only presentation auditor checks 42 rounded README headline numbers, recalculates the four accounts' CAGR/volatility/MaxDD/ES from their ledgers and cycles, checks eight HAR loss ratios against baseline scores, and validates all six image links.

Full default frozen-specification reproduction passed in a new output directory. **659 forecast, tail and strategy output files are byte-identical to the previous canonical run**, including all final account files. Mainline tests: **22 passed**; 14 existing Matplotlib/Pyparsing deprecation warnings remain. All six PDF exports were rendered and visually inspected. Public link/import/hash audit passed. These checks preserve the original research, not certify a new strategy.

## Reproduce presentation without research

```powershell
python -B scripts/render_presentation.py --source artifacts/canonical_final --output artifacts/presentation_preview
python -B scripts/audit_presentation.py --source artifacts/canonical_final --public artifacts/presentation_preview
```

Use a new or empty destination. Full `scripts/reproduce.py` also invokes the same reporting/presentation functions after completing the frozen pipeline. The normal public audit checks the final repository; the presentation audit can check either an isolated generated public directory or the repository root.

Backtrader was not introduced. The existing self-financing engine already defines execution timing, units/cash, drift, costs, cash accrual, five-session rebalancing and offsets. A second implementation would create accounting differences without adding research evidence.

All results remain EXPOSED_HISTORY. The Treasury sleeve is the original partial-vintage yield-carry proxy, not an executable T-bill total-return series. No model change, new research, shadow update, commit, push or deployment was performed.
