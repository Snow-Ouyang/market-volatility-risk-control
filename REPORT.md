# Final canonical research report

**Market Volatility Forecasting & Risk Control** — finished historical research, EXPOSED_HISTORY.

The supported chain is daily GK-plus-gap measurement, marginal risk prediction, scale-conditioned FHS and a transparent Full VOL/cash application. Directional prediction, complex allocation and duration parking did not earn promotion. Selecting Full VOL as the explanatory canonical application does not overturn the prior preference for static exposure under a strict cross-regime deployment gate.

## Forecast evidence

| symbol   | baseline   |   MSE |   QLIKE |
|:---------|:-----------|------:|--------:|
| QQQ      | GARCH      | 10.79 |   10.89 |
| QQQ      | ROLLING22  | 22.99 |   21.19 |
| SPY      | GARCH      | 10.89 |   12.09 |
| SPY      | ROLLING22  | 26.04 |   24.51 |

The frozen GARCH joint status is WEAK. Full period, calibration and simultaneous-interval tables are retained under results/forecast.

## Tail evidence

| asset   | model   |    n |   PINBALL |       FZ0 |   BRIER2 |   BRIER5 |   DD_MSE |   var_hit_rate |
|:--------|:--------|-----:|----------:|----------:|---------:|---------:|---------:|---------------:|
| SPY     | HS      | 6616 |  0.003022 | -2.832151 | 0.119432 | 0.023646 | 0.000331 |       0.044135 |
| SPY     | FHS     | 6616 |  0.002633 | -3.056328 | 0.114126 | 0.022242 | 0.000250 |       0.049123 |
| QQQ     | HS      | 5087 |  0.003490 | -2.707618 | 0.141896 | 0.034242 | 0.000414 |       0.042068 |
| QQQ     | FHS     | 5087 |  0.003138 | -2.873917 | 0.136804 | 0.032682 | 0.000334 |       0.051897 |

## Final accounts

Application coverage is shorter than the price/forecast history because FHS needs mature residual history and the frozen cash rule rejects stale quotes. The SPY prefix excludes the existing September-2001 stale-quote break; the risk-budget calibration is not reset. Dates below are the actual primary account endpoints.

| asset   | first_origin        | last_origin         |   eligible_origins |   excluded_prefix | offset0_entry   | offset0_exit   |
|:--------|:--------------------|:--------------------|-------------------:|------------------:|:----------------|:---------------|
| SPY     | 2001-09-19 00:00:00 | 2026-08-20 00:00:00 |               6270 |               346 | 2001-09-25      | 2026-08-27     |
| QQQ     | 2006-06-01 00:00:00 | 2026-08-20 00:00:00 |               5087 |                 0 | 2006-06-06      | 2026-08-24     |

| asset   | rule    |   CAGR |   Return_Retention |   annual_vol |   ES95_5D |   MaxDD |   average_exposure |   annual_turnover |   annual_fee_drag |
|:--------|:--------|-------:|-------------------:|-------------:|----------:|--------:|-------------------:|------------------:|------------------:|
| SPY     | BUYHOLD |  10.46 |             100.00 |        18.50 |      5.49 |   55.42 |             100.00 |              4.02 |              0.00 |
| SPY     | VOL     |   9.08 |              86.81 |        12.16 |      3.47 |   31.84 |              84.62 |            266.04 |              0.03 |
| QQQ     | BUYHOLD |  16.35 |             100.00 |        21.86 |      6.74 |   52.28 |             100.00 |              4.96 |              0.00 |
| QQQ     | VOL     |  13.62 |              83.25 |        15.22 |      4.91 |   30.76 |              83.18 |            328.95 |              0.03 |

## Return and matched-exposure risk attribution

First five component columns are CAGR percentage points; the final three are relative percent risk gains versus equal-average-exposure static controls. Exact additive return identities are evaluated before rounding.

| asset   | rule   |   CAGR_exposure_opportunity |   CAGR_dynamic_timing |   CAGR_cash |   CAGR_cost |   CAGR_interaction |   annual_vol_dynamic_fraction |   ES95_5D_dynamic_fraction |   MaxDD_dynamic_fraction |
|:--------|:-------|----------------------------:|----------------------:|------------:|------------:|-------------------:|------------------------------:|---------------------------:|-------------------------:|
| SPY     | VOL    |                       -1.51 |                 -0.07 |        0.23 |       -0.03 |              -0.00 |                         22.23 |                      25.16 |                    34.91 |
| QQQ     | VOL    |                       -2.63 |                 -0.40 |        0.32 |       -0.04 |               0.00 |                         16.20 |                      12.36 |                    32.07 |

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
