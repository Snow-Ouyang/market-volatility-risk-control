# Final consolidation review

**PASS for structural consolidation and numerical preservation.** This review does not upgrade scientific evidence or authorize deployment.

The final mainline is daily adjusted OHLC → GK plus aligned gap risk → frozen HAR/GARCH/simple controls → five-day FHS → Full VOL and short-duration cash proxy. Core50 remains a secondary preference example. The same mature-target timing, training-only smearing/BIC selection, five-session execution, cash-rate lag, fee treatment and self-financing cash/units equations are retained.

Review used three complementary checks: immutable forecast/account reference comparisons; separate scalar cash-flow and direct block-index calculations; and complete post-deletion reproduction plus isolated-source replay. The GARCH review uses library refiltering and separate recursions. These are independent calculations by the same researcher, **not external peer review**. See [measured evidence](results/validation.json) and [validation](VALIDATION.md).

## Interpretations deliberately preserved

- Equity risk predictability is supported, but the joint HAR-versus-GARCH increment remains WEAK despite positive average MSE and QLIKE improvements.
- Full VOL materially reduces long-run volatility, ES and drawdown, with a cost to equity participation. Matched-exposure gains are not stable in every regime; the historical promotion gate remains WEAK, with no prospective candidate.
- FHS scale information is useful. Rarer >5% losses have weaker inference than >2% events. CAViaR/EVT and a dynamic residual-shape model were not tested after their gate failed; they are not falsely described as empirically defeated.
- cDCC's SPY fixed-portfolio stage was NOT RUN after its gate closed; QQQ fixed-portfolio evidence was WEAK. Neither allocation stage ran. Better correlation accuracy is not equivalent to useful covariance or portfolio risk forecasting.
- IEF can earn duration returns but is not risk-free cash. Conditional parking did not establish stable value over Always IEF, and 2022 remains adverse evidence.
- Daily adjusted prices, the partial-vintage yield carry approximation and retrospective sample selection limit executability and prospective claims.

## Scope closure

Twenty-three research decisions retain questions, motivations, methods, evidence, verdicts, stopping reasons and former artifact identities. Deletion was authorized by the cleanup request, preceded by dependency/manifests and hash preflight, and followed by successful reproduction. Canonical raw data, forecast references, selected final accounts, current outputs and tests were preserved. Original sibling research laboratories and FULL_HAR prospective shadow remain outside scope and untouched.

No new model, parameter, backtest definition or rescue experiment was introduced. No commit, push, order, deployment or new shadow was performed.
