# Final repository audit

Completed after the user-approved post-convergence deletion. Historical evidence remains EXPOSED_HISTORY.

| Status | Result |
| --- | --- |
| CANONICAL_MAINLINE | 5D_FULL_VOL |
| GOLD_BRANCH | CLOSED_AND_SUMMARIZED |
| LONG_HORIZON_BRANCH | CLOSED_AND_SUMMARIZED |
| TERM_STRUCTURE_PORTFOLIO | NOT_PROMOTED |
| PUBLIC_REPO_READY | YES — local working tree ready for review, not pushed |
| REPRODUCTION_STATUS | PASS |
| TEST_STATUS | PASS — 22/22 canonical; 22/22 isolated public tree |
| BROKEN_REFERENCE_COUNT | 0 |
| UNRESOLVED_FILE_COUNT | 0 within the audited cleanup scope |

## Reproduction and scientific preservation

- From an empty output, the unchanged frozen specification rebuilt HAR, training-selected GARCH (681 monthly vintages), FHS and the original accounts. No new specification, parameter search or account was introduced.
- All **673** canonical scientific CSV/Parquet files matched their newly reproduced counterparts **byte for byte (SHA-256)**. The isolated frozen-forecast replay matched **671/671 expected files**; its two intentionally ungenerated GARCH fit-attempt/daily-state diagnostics are specific to full re-estimation and were verified in the full run.
- The 869-file protected baseline was checked before and after: **865 unchanged**; only the two report/presentation modules, the public-audit allowlist and the README presentation-provenance file changed. No unexpected protected-file change.
- The canonical parity reviewer confirmed 71,370 HAR/simple rows, 85,644 rows including GARCH, 13,232 SPY and 10,174 QQQ FHS rows, 3,150 account metric rows, and 1,703,550 independent scalar ledger rows. Original frozen numerical tolerances were retained.
- All 80 local input hashes, the GARCH baseline, FHS, cash references, Full VOL accounts and matched-exposure diagnostic remain unchanged. All 13 final public PNG/PDF files are unchanged.

## Public, dependency and isolated-tree checks

The link/import/input audit passed with 61 local links checked after the final documentation refresh, zero broken references and zero retired runtime references. The presentation audit verified 50 displayed numbers, four original accounts, six matched-static risk comparisons, eight forecast-loss ratios and seven README image links.

The fresh-clone-style check copied only the public allowlist and the 80 explicit hash-bound inputs into a new tree, created a temporary local Git index, checked the public index boundary, ran all tests and reproduced FHS/accounts using frozen marginal forecasts. It had no retired-branch or private-archive dependencies. After verification, the six task-created reproduction/preview/test temporary directories were removed (933,547,624 bytes); their completion seals, exact hash comparisons and logs are retained as compact audit evidence. The original canonical output remains intact. This used the installed locked environment: it is not a network clone, a new package installation or a claim that raw data are publicly redistributed.

The private archive is gitignored. The canonical Git index's 99 mode/object/stage/path entries match the pre-cleanup snapshot exactly; source working-tree changes and four new public documents are left for user review. No commit or push.

An initial test invocation hit a Windows permission error in the pre-existing system pytest temporary directory (18 passed; four fixture setup errors). The same tests passed in a fresh task-local temporary directory; no test or scientific code was changed. Fourteen existing dependency deprecation warnings remained non-failing.

## Unchanged Full VOL headline results

Values are generated here from the unchanged canonical HEADLINE_ACCOUNTS.csv; rate/risk columns are percentages. Primary offset 0, 1bp, original cash convention.

| asset   | rule    |   CAGR |   Return_Retention |   annual_vol |   ES95_5D |   MaxDD |
|:--------|:--------|-------:|-------------------:|-------------:|----------:|--------:|
| SPY     | BUYHOLD |  10.46 |             100.00 |        18.50 |      5.49 |   55.42 |
| SPY     | VOL     |   9.08 |              86.81 |        12.16 |      3.47 |   31.84 |
| QQQ     | BUYHOLD |  16.35 |             100.00 |        21.86 |      6.74 |   52.28 |
| QQQ     | VOL     |  13.62 |              83.25 |        15.22 |      4.91 |   30.76 |

The README remained shorter: **13,226 → 13,066 bytes** (13,005 → 12,843 characters). Core rows were removed only from the report's presentation, not overwritten in immutable scientific references or parity checks. No Gold or 21D portfolio section or new figure was introduced.

## Reproduce the retained mainline

```powershell
python -B scripts/reproduce.py --output artifacts/reproduction_after_cleanup --workers 4
python -B -m pytest -q
python -B scripts/audit.py
python -B scripts/audit_presentation.py --source artifacts/canonical_final --public .
```

Use a new/empty output and the hash-bound local inputs. Windows sandbox verification used a fresh writable pytest basetemp. See [branch findings](POST_CONVERGENCE_RESEARCH_SUMMARY.md), [final decision](FINAL_POST_CONVERGENCE_SUMMARY.md) and [cleanup receipt](POST_CONVERGENCE_CLEANUP_REPORT.md).
