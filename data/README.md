# Reproduction data

The public project does not redistribute raw Yahoo/FRED observations or vendor data. Exact replay uses the existing reference snapshots in ignored data/local, verified by mainline_inputs.json. reference_inputs.json preserves the original SPY/QQQ fingerprints.

Required daily prices: SPY.csv and QQQ.csv, adjusted OHLCV with Date, Open, High, Low, Close, Volume and available actions. Prices are read-only. The original snapshots end 2026-08-28; a fresh Yahoo retrieval may have revised adjustments and is not exact reference data.

Cash input: volatility_return_distribution/DGS3MO.csv and its source metadata. This inherited folder name is only a local data label, not a dependency on the retired study. The frozen rule uses a quote at least two stock sessions old, maximum age seven calendar days, and simple ACT/365 yield carry locked over five sessions. This is a 3M Treasury cash-carry approximation, not a tradable total-return index. Historical release-vintage coverage is PARTIAL. Missing/stale quotes are not filled; the original common contiguous eligible suffix is used for PROXY and ZERO.

reference/forecast holds canonical HAR/simple/GARCH forecasts, daily features, fit logs and compact regression tables. reference/tail holds final HS/FHS predictions, mature residual panels and inference references. reference/strategy holds original normalization, targets, metrics and selected final account ledgers. These protected reference files validate refactoring; none are an alternative source of newly fitted historical results.

The default reproduction regenerates features, all frozen marginal forecasts, FHS/HS and selected fixed accounts. --frozen-forecast reuses only hash-verified canonical marginal forecasts, and still recomputes tail and account outputs. Neither mode downloads data. Exact replay fails when required fingerprints differ. A public reader must lawfully obtain matching snapshots; numerical reproducibility does not grant redistribution rights or establish executable historical prices.
