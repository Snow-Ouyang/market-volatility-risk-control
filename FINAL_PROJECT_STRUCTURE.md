# Final project structure

```text
src/volatility_risk/
  data.py, measurement.py, forecast.py, garch.py
  evaluation.py, inference.py, benchmark_evaluation.py, benchmark_review.py
  fhs.py, tail_evaluation.py, tail_inference.py
  strategy.py, strategy_account.py, strategy_evaluation.py
  consolidation_review.py, final_reporting.py, presentation.py
  config.py, io.py, utils.py
scripts/
  reproduce.py             # complete frozen mainline, new/empty output only
  audit.py                 # links, imports, public surface, fingerprints
  render_presentation.py, audit_presentation.py
tests/
data/
  README.md, reference_inputs.json, mainline_inputs.json
  local/                   # ignored OHLC, cash and canonical reference files
results/
  forecast/, tail/, strategy/, figures/
research_archive_private/  # ignored timeline, decisions, cleanup/audit provenance
artifacts/canonical_final/ # ignored complete current reproduction
README.md, REPORT.md, VALIDATION.md, REVIEW.md
RESEARCH_HISTORY_SUMMARY.md, CLEANUP_REPORT.md
POST_CONVERGENCE_RESEARCH_SUMMARY.md, FINAL_POST_CONVERGENCE_SUMMARY.md
POST_CONVERGENCE_CLEANUP_REPORT.md, FINAL_REPO_AUDIT.md
REFACTOR_SUMMARY.md
requirements.txt, requirements-lock.txt, pyproject.toml
GARCH_RESEARCH_PLAN.md
```

The public surface has one research chain and one reproduction entry. It has no live dependency on retired exploration, sibling laboratories, private history or the existing prospective shadow. The GARCH plan is retained verbatim as a frozen historical protocol; its former Gold stage is provenance, not an active entry point.

Canonical data are kept locally and identified by portable SHA-256 manifests. The reference forecasts and selected final accounts are retained for exact regression checks, not replaced by README numbers. The audited post-convergence branch implementations and duplicate reproduction directories have been retired after preserving compact decisions. Unrelated laboratories and the existing prospective shadow remain outside that cleanup. See [final cleanup](POST_CONVERGENCE_CLEANUP_REPORT.md) and [verification](FINAL_REPO_AUDIT.md).
