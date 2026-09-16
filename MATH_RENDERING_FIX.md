# Math rendering compatibility fix

This presentation-only change fixes two README formulas rejected by GitHub's math renderer.

- The equity-weight mapping replaced the unsupported `operatorname` form of `clip` with the mathematically equivalent nested $\min$ / $\max$ expression. The long-only, no-leverage interval remains $[0,1]$.
- The initial risk-budget calibration replaced the unsupported `operatorname` form of `median` with $Q_{0.5}$ and moved the definition of the median into ordinary Markdown text.
- Mathematical meaning changed: **NO**.
- Model definitions, risk budget, strategy logic, result numbers and canonical outputs changed: **NO**.
- Unsupported macro count in public Markdown before: **2**.
- Unsupported macro count in public Markdown after: **0**.
- Public audit now fails with a file and line number if public Markdown contains the unsupported `operatorname`, `DeclareMathOperator` or `newcommand` macro forms.
- A follow-up GitHub check showed that Markdown preprocessing also stripped the escape from brace delimiters, turning the intended left-brace delimiter into an invalid command. Both affected formulas now use ordinary parentheses and no escaped brace delimiters. The audit rejects those fragile left-brace and right-brace delimiter forms as well.
- The same preprocessing converts punctuation-based spacing commands into visible punctuation. All such spacing commands were removed from README math and replaced with ordinary source spaces; the audit now prevents their return.

Validation status: **PASS**. The generated README exactly matches the checked-in README; unsupported macro count is zero; all 22 tests pass; public audit, presentation audit, 61 local links and seven README image links pass.
