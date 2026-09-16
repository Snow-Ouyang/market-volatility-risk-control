# Validation

Final consolidation validation completed on 2026-09-14. This is an exact-specification reproduction and refactor audit, not a new experiment or prospective result.

## Reproduction after deletion

The full default command ran successfully from a new output directory after the retired laboratory and artifacts were removed:

```powershell
python -B scripts/reproduce.py --output artifacts/canonical_final --workers 4
```

It regenerated daily features, frozen monthly HAR and training-selected GARCH forecasts, benchmark inference, HS/FHS forecasts and inference, and the existing five-session accounts. All input hashes passed. The output includes PARITY_REVIEW.json, a GARCH independent-calculation review, ENVIRONMENT.json and COMPLETION_SEAL.json. These full outputs are local and ignored; compact evidence is published in [validation results](results/validation.json).

| Check | Observations checked | Result |
| --- | ---: | --- |
| HAR and simple forecast table | 71,370 | Exact numeric match |
| Forecast table including GARCH | 85,644 | Exact numeric match |
| GARCH monthly vintages / daily forecasts | 681 / 14,274 | PASS; forecast and target-bridge error zero |
| SPY HS/FHS prediction rows | 13,232 | Exact numeric match |
| QQQ HS/FHS prediction rows | 10,174 | Exact numeric match |
| Strategy metric rows, across periods and fixed cases | 3,150 | Maximum absolute error 1.23e-15 |
| Independently recomputed scalar account rows | 1,703,550 | Maximum cash-flow error 3.56e-15 |
| Target weights, both cash cases | SPY 6,270; QQQ 5,087 per case | Exact numeric match |

The GARCH BIC comparison differs by at most 7.28e-12; direct interval recalculation differs by at most 8.89e-15. FHS inference differs by at most 1.56e-15. These are numerical round-off, not revised research results. Selected final account ledgers are also compared directly with protected canonical references.

## Tests and isolated public tree

All **22 mainline tests pass** in the cleaned project and again in an isolated public-file-only tree. The latter contains only the public allowlist plus the 80 explicit, hash-checked local input/reference files; no retired laboratory, old artifacts or private research archive was supplied. Every package module imports from that isolated tree. Its Git index/public audit and complete `--frozen-forecast` replay pass. Generated reports, numerical tables and figures match the full default run byte for byte.

This is a **fresh-clone-style source and dependency audit**, using the same pinned Python environment. It is not a network clone or an independent clean dependency installation. Local licensed/reference snapshots must be provided separately; see [data requirements](data/README.md). Fourteen Matplotlib/Pyparsing deprecation warnings remain in the test run; they are not test failures.

## Public and scientific boundaries

`python -B scripts/audit.py --index` checks public file limits, local Markdown links, imports, retired runtime paths, credential/private-path patterns, input hashes and the staged Git boundary. The private archive, raw data, complete accounts and generated runtime artifacts are ignored. The original measurement, HAR, GARCH and inference implementations remain unchanged; extraction of FHS/accounts is covered by numerical parity.

README and REPORT are produced by final_reporting from canonical results. [Headline provenance](results/HEADLINE_PROVENANCE.json) identifies the underlying files and hashes; the primary account is original offset 0, PROXY cash and 1bp. All five original offsets, ZERO cash and 0/1/3bp costs are retained. No result was selected by highest Sharpe.

All evidence remains EXPOSED_HISTORY. Cash is the frozen lagged 3M Treasury yield-carry approximation, with PARTIAL release-vintage provenance, not an executable Treasury total-return instrument. Application history starts after the original FHS/cash eligibility checks, not at ETF inception. The existing prospective shadow was neither an input nor a modification target.
