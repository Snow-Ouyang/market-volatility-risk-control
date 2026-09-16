# Post-convergence cleanup report

**Completed: 22 explicitly audited roots; 11,530 files; 8,945,400,794 logical bytes (8.33 GiB). All listed targets were verified absent.**

Deletion followed the latest cleanup request, the four required evidence/dependency gates, independent review and the user's explicit approval of the concrete 22-item manifest. Decisions and provenance were installed before deletion. The removal is intentional: compact branch summaries do not reproduce deleted branch ledgers.

## Removed

| Scope | Roots | Contents retired |
| --- | ---: | --- |
| Closed research directories | 5 | Defensive parking; compact duplicate Gold archive; Full VOL bands / 21D; adaptive 21D; 5D–21D term-structure accounts |
| Session staging / reproduction copies | 6 | Duplicate horizon, adaptive and term-structure implementations and outputs |
| Old Gold delivery helper | 1 | Obsolete staging helper |
| Old canonical verification / presentation outputs | 8 | Former parity/clone outputs, duplicate rendered figures and presentation reproductions |
| Duplicate private evidence directories | 2 | Superseded branch-evidence / presentation-refinement copies |

No unclassified directory was removed. Exact former paths, counts, byte sizes, uses, retained conclusion locations and the four deletion gates are in the local gitignored POST_CONVERGENCE_DELETE_MANIFEST.md; POST_CONVERGENCE_DELETION_RECEIPT.json records the completed removal. The old pytest-cache enumeration limitation was resolved before deletion.

## Kept

- The canonical 5D HAR/GARCH forecasts, FHS, Full VOL accounts, matched-exposure controls, cost/cash conventions, numerical code, tests and reproduction entry.
- All 80 manifest-bound OHLC/cash/reference inputs, input hashes, final public tables and 13 figures, and artifacts/canonical_final.
- [Six-branch summary](POST_CONVERGENCE_RESEARCH_SUMMARY.md), [final decision](FINAL_POST_CONVERGENCE_SUMMARY.md), the compact [history table](RESEARCH_HISTORY_SUMMARY.md), and the three new private decisions/index/delete-manifest documents.
- Compact cleanup/audit provenance; no large branch ledgers, bootstrap grids or training vintages were moved into the private archive.

The entire existing prospective shadow and unrelated research laboratories were excluded from this cleanup.

## Verification after removal

| Check | Result |
| --- | --- |
| Full frozen-specification reproduction from empty output | PASS |
| Original scientific hashes before vs after | Unchanged |
| Scientific files vs new full reproduction | 673/673 exact SHA-256 matches |
| Isolated public-tree frozen replay | 671/671 expected files exact; two fit-only diagnostics intentionally not generated |
| Canonical / isolated tests | 22/22 and 22/22 PASS |
| Input / import / path / README numbers and image audits | PASS |
| Broken references | 0 |
| Private archive gitignored | YES |
| Unresolved deletion-scope files | 0 |
| Canonical Git index | Original 99 entries unchanged |

The fresh-clone-style test used the installed environment and locally provided hash-matching inputs; it was not a remote clone or data redistribution test. The original FULL_HAR prospective shadow was not changed by cleanup. See [final audit](FINAL_REPO_AUDIT.md).

The six temporary output directories created by this cleanup itself were also removed after their successful checks: 1,809 reproducible duplicate files / 933,547,624 bytes. This is separate from the 22-root user-approved historical deletion. Only compact verification logs, completion seals and hash comparisons were retained; no new duplicate ledger archive was left behind.

## Stop

The final architecture is **5D_FULL_VOL**. Gold and long-horizon work remain summarized findings, and the term-structure portfolio was not promoted. No model, parameter, account, optimizer, portfolio experiment, scheduler, order, deployment or push was added.
