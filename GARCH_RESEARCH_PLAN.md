# Equity GARCH benchmark and independent gold transfer protocol

Frozen before viewing any GARCH out-of-sample comparison. All history is RETROSPECTIVE / EXPOSED_HISTORY. HAR, GK, horizons, input cutoff (2026-08-28), costs and former portfolio findings are unchanged. No portfolio optimization, bonds, covariance, orders, shadow changes or push.

## Sequence

1. Explain session/gap decomposition and correct next-open alignment in public equity documentation.
2. Fit and audit the equity GARCH baseline, score common origins, revise the equity conclusions.
3. Audit Yahoo-compatible gold representations, freeze the admissible input, then run the same univariate test in `research/gold_volatility/`. Do not assume a gold success before this sequence completes.

## GARCH family and training-only choice

Six candidates: symmetric GARCH orders (p,q) = (1,1), (1,2), (2,1), each with Normal or standardized Student-t innovations. Zero conditional return mean, percentage log adjusted close-to-close returns, no asymmetric/volume/exogenous terms. `arch==7.2.0`; positive intercept, nonnegative ARCH/GARCH coefficients and package stationarity constraints. A boundary persistence estimate is reported, not silently dropped.

Every existing HAR monthly vintage is an origin group. Fit all six candidates to the same expanding returns strictly before the month's first session. A candidate sees all past returns available at that cutoff, not future outcomes. Choose minimum BIC = -2 log likelihood + k log(n); deterministic ties use the declared order, Normal before t. No asset-specific search space. Retry only failed/nonfinite fits at a higher iteration limit (500 then 2000), same model and data; record both attempts. If every candidate fails, retain the failure and stop rather than replacing it with HAR or masking the origin. Ordinary scientific convergence issues may be versioned and repaired without changing the research choices.

After monthly estimation, update the selected GARCH variance state with each newly observed daily return through close t, keeping parameters fixed. Analytic variance recursion produces h[t,1] through h[t,6]. Conditional initialization uses training data only. No full-sample backcast, variance bound or coefficient may leak into earlier states. Check the recurrence independently against the library at each vintage's last training origin.

## Common-target bridge, fixed before results

Classical GARCH predicts close-to-close return variance. The scored target is the existing sum of session GK and gap squared across Open[t+1] → Open[t+6], which is not the same random variable. Do not relabel a five-step close-to-close sum as this target.

Use an explicitly documented training-only proportional component bridge. On valid pre-refit daily rows with observed close-to-close log returns r:

```text
a_RTH = sum(GK_RTH) / sum(r²)
a_GAP = sum(overnight²) / sum(r²)
GARCH_TARGET[t] = (a_RTH * sum(h[t,1:5]) + a_GAP * sum(h[t,2:6])) / 5
```

Variances h are converted from squared percentage returns to squared log returns before this formula. This is moment calibration to the observed risk proxy, not a fitted time-of-day duration weight or an OOS loss optimization. It allows return variance and the GK proxy to differ in level. Save both coefficients and their training dates/row hashes. Include the unscaled native mean(h1..h5) only as a clearly labeled target-mismatch diagnostic, not a second selectable benchmark. Do not select among bridge designs after seeing the comparison.

The bridge assumes session and gap risk share the conditional close-to-close variance dynamics up to training proportions. This restriction and GARCH's return-only dynamics versus HAR's OHLC risk inputs mean a HAR gain is pipeline increment, not a causal identification that 1/5/22 lags alone caused the gain.

## Scoring and uncertainty

Use all common mature dates for HAR, GARCH, Rolling22, Current, EWMA and historical mean. Keep original features, HAR forecasts and common-target labels exact. Apply the same MSE, QLIKE, OOS R² versus mature training mean, mean-ratio and slope calibration, high-risk AUC/precision/recall/lift, tail and drawdown AUC, and strictly prior forecast-percentile buckets. Report coverage and missingness explicitly.

Primary ordering is HAR vs GARCH vs Rolling22; EWMA remains a supplementary control. Preserve full history, common SPY/QQQ dates, decades, 2020–22, 2023+, fixed crises, and score-only exclusion of GFC/COVID/2022 jointly and individually. Gold adds the fixed 2013-01-01 to 2013-12-31 selloff window and preserves the other applicable windows. No post-result episode choice.

Paired circular blocks: 1,999 draws, seed 20260913, block lengths 21/42. Use simultaneous bounds across the five HAR-versus-baseline comparisons within each asset/period/loss. Repeat ALL, 2023_PLUS, COMMON_ALL and EX_COVID. Intervals do not remove retrospective selection bias or turn overlapping target origins into independent crises.

## Predefined interpretation

- EQUITY_HAR_VS_GARCH SUPPORTED: SPY full MSE/QLIKE gains both ≥2% and conservative simultaneous lower bounds >0; QQQ both positive; each asset's recent and joint-crisis-exclusion QLIKE gains positive. WEAK: at least three of the four full-history asset/loss gains positive but the full rule fails. Otherwise NOT_SUPPORTED. Always display all losses and periods.
- GARCH_SPECIFICATION_STABILITY SUPPORTED: complete forecasts, candidate convergence ≥99%, selected-order switching ≤35%, and selected near-unit persistence (sum ≥0.999) in ≤20% of vintages. PARTIAL if complete forecasts but any of those diagnostic thresholds fail; UNSTABLE if complete coverage fails. BIC near-ties (difference <2) and distribution/order frequencies are reported even when the label passes. These are descriptive engineering criteria, not financial laws.
- GOLD_DATA_REPRESENTATION ROBUST requires auditable session and roll/adjustment convention for an appropriate gold series; a sound US-listed gold ETF alone is PROXY_ONLY; unresolved basic OHLC/adjustment or timing validity is INCONCLUSIVE.
- GOLD_VOLATILITY_PREDICTABILITY SUPPORTED if HAR or GARCH beats Rolling22 in both full losses by ≥2%, both paired lower bounds >0, OOS R² >0, long high-risk AUC ≥0.70 and tail AUC ≥0.60, with positive recent QLIKE gain. WEAK if both full losses improve but the joint rule fails; otherwise NOT_SUPPORTED. GARCH-versus-Rolling intervals are a separate two-model contrast, not chosen after seeing results.
- GOLD_HAR_VS_GARCH SUPPORTED if both full gains ≥2%, conservative simultaneous lower bounds >0, and recent/joint-crisis-exclusion QLIKE positive. GARCH_BETTER requires both gains ≤-2% and paired upper bounds <0. SIMILAR requires both losses' paired 95% intervals fully inside ±5%. Otherwise INCONCLUSIVE. Failure to reject is not equivalence.
- CROSS_ASSET_HAR_TRANSFER SUPPORTED requires supported equity and gold HAR increments with a ROBUST gold representation. PARTIAL if a reliable gold proxy/series has predictive value but one of those conditions is absent. Otherwise NOT_SUPPORTED.
- NEXT_ACTION: REVIEW_GOLD_DATA for INCONCLUSIVE representation; STOP_CROSS_ASSET_EXTENSION for unsupported gold predictability; STUDY_TREASURY_VOLATILITY only for reliable representation, supported predictability and a clear supported/similar/GARCH-better comparison; otherwise KEEP_EQUITY_ONLY. This is a proposal only, not permission to start Treasury research.

## Gold representation audit (Part 3 only)

Inventory existing Yahoo daily caches first. Inspect GLD, GC=F and Yahoo-compatible alternative representations without broad asset/model search. Query only necessary daily snapshots/metadata; never minute APIs. Exchange hours are not proof of Yahoo's bar aggregation boundaries. Require evidence of session boundary, close-versus-settlement, contract identity/roll schedule and adjustment before treating continuous futures as canonical. Missing provider roll/session evidence is sufficient to reject that representation even if its numbers appear smooth. Do not fabricate a roll-adjustment algorithm.

GLD can be retained as a tradable US-session proxy after calendar, OHLC geometry, corporate actions/adjustment, missingness, history and opening-gap audit. If only this representation is admissible, test it alone and state that the economic effect of switching to futures is unidentifiable here. Do not select the series based on HAR results.

Deliver immutable input/plan hashes, forecasts, candidate BIC/convergence/parameters, daily states and component-bridge audit, regime/loss tables, independent numerical review, public documentation and one-command replay. Preserve prior public artifacts privately and the existing laboratory/shadow in place. Stop after the three parts.
