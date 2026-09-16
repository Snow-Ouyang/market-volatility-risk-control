# Final research consolidation and cleanup

Completed on 2026-09-14. The public project now follows one frozen daily-risk/FHS/Full VOL chain. This work changes organization, dependencies and presentation; it does not add models, parameters or research experiments.

## What was removed

The research retirement deleted **11,346 files / 7,034,254,459 bytes** (7.03 GB decimal). These include obsolete exploration code; duplicate and superseded forecasts/reports; old tail/decision versions; retired Gold, Treasury, stock–bond dependence, covariance and parking outputs; old account ledgers; and temporary inference/figure artifacts. Canonical implementations and required final data were extracted and protected before their original duplicate locations were removed.

A separate follow-up cleanup removed **1,699 files / 917,203,500 bytes** created during this consolidation: the transition replay, isolated public-tree replay, Python/test caches and one-time migration helpers. Compact verification evidence remains. These are validation duplicates, not an additional 0.92 GB reduction in the original research lab.

Every deletion had a prior file-level path, size and SHA-256 manifest, a recorded purpose/retirement reason, a decision-history reference, and a no-mainline-dependency conclusion. All hashes were checked again before native PowerShell single-file removal; only empty directories were removed afterward. No broad cross-shell recursive deletion was used.

## What was retained and why

- **Canonical research:** adjusted SPY/QQQ inputs and original hashes; unchanged measurement/HAR/GARCH/inference; final HS/FHS logic; the original Full VOL cash/units account; cost/cash/offset sensitivities; compact current tables, charts and tests.
- **Exact regression evidence:** protected canonical forecasts, fit logs, FHS predictions and selected final ledgers in ignored local reference storage. The complete successful current run remains in ignored `artifacts/canonical_final`.
- **Private history:** 23 structured decision records covering question, motivation, method, evidence, verdict, stopping reason and former artifact identity. Timeline, retired-branch index, original inventory, dependency graph, deletion receipts and audit logs are retained in ignored `research_archive_private`.
- **Public narrative:** [README](README.md), [report](REPORT.md), [concise history](RESEARCH_HISTORY_SUMMARY.md), [structure](FINAL_PROJECT_STRUCTURE.md) and [refactor summary](REFACTOR_SUMMARY.md). The GARCH protocol remains verbatim historical provenance. The requested alternative spelling [REFRACTOR_SUMMARY](REFRACTOR_SUMMARY.md) points to the substantive summary.

The sibling original laboratories and existing FULL_HAR prospective shadow are outside this repository cleanup scope and were not modified. No raw minute/vendor files or old full ledgers enter the public index. The private archive is Git-ignored, not merely hidden from the README.

## Verification after retirement

| Requirement | Measured result |
| --- | --- |
| Full mainline from empty output | PASS; refit 681 frozen GARCH monthly vintages and regenerate forecasts/FHS/accounts |
| Frozen numerical parity | PASS; 85,644 combined forecast rows, 23,406 HS/FHS rows, 3,150 account metric rows |
| Separate scalar accounting | PASS; 1,703,550 rows, maximum cash-flow error below 3.56e-15 |
| Mainline tests | PASS; 22 tests in the cleaned tree and 22 in the isolated public tree |
| Fresh-clone-style replay | PASS; 19 isolated module imports and 41 generated public artifacts identical to the full refit |
| README/REPORT numbers | Generated from canonical accounts and forecast results; source hashes published |
| Links/imports/stale runtime paths | PASS; zero broken local references or retired runtime dependencies |
| Local data/reference hashes | PASS |
| Git public/private boundary | PASS; only the finished public allowlist staged |

See [validation](VALIDATION.md), [numerical review](REVIEW.md) and [machine-readable evidence](results/validation.json). Fresh-clone-style validation used the same pinned environment and explicitly provisioned local snapshots; it is not a claim of a fresh dependency installation or data redistribution.

## Final status

```text
MAINLINE_STATUS: COMPLETE_FROZEN
REPRODUCTION_STATUS: PASS
TEST_STATUS: PASS (22)
PUBLIC_REPO_READY: YES_FOR_USER_REVIEW
PRIVATE_ARCHIVE_GITIGNORED: YES
BROKEN_REFERENCE_COUNT: 0
UNRESOLVED_FILES: 0
```

There are no unresolved deletion decisions within the named repository. Scientific limitations remain explicit: EXPOSED_HISTORY, weak uniform HAR/GARCH and dynamic/static increments, and PARTIAL cash release-vintage provenance. Public readiness means a reviewable finished source/results project with documented local-data prerequisites, not deployment readiness.

The final public index is staged for inspection; the original pre-cleanup index snapshot is retained privately. No commit, push, order, deployment or new shadow was made. The fixed consolidation is complete.
