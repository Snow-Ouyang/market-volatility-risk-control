# Post-convergence Research Summary

> Post-convergence extensions produced useful forecasting and diversification evidence, but none provided sufficiently stable portfolio-level increment to justify changing the canonical 5D architecture.

这些扩展提供了有用的预测与分散化证据，但没有形成足够稳定的组合增量来改变现有主线。保留简单架构是完成比较后的研究选择，不是遗漏，也不意味着所有后续研究均无效。

最终主线保持：daily adjusted OHLC → regular-session Garman–Klass + overnight gap → whole-day holding-risk alignment → HAR(1,5,22) → future-5D risk → FHS → Full VOL → 3M cash sleeve。SPY primary、QQQ transfer、月度 expanding 参数更新、五交易日调仓、下一开盘执行、无杠杆、不做空，原成本与现金口径不变。

所有结果均为 **EXPOSED_HISTORY**。这里的 OOS 指历史 walk-forward，不是未暴露的 prospective OOS。区间与代码复核不能消除多阶段研究选择偏差；预测改善、经济价值、相对基准增量和前向就绪度分别判断。

本文只摘录已经完成的研究，不重新计算模型或账户。证据编号对应本地 gitignored 决策归档中的 POST_CONVERGENCE_ARTIFACT_INDEX.md：保留原文件路径、SHA-256、表格/字段及少量精确值。公开摘要不依赖已删除研究目录。原路径是清理前的来源记录，不承诺删除后仍可访问；hash 不能恢复已删除内容。下文处置为本次收敛决定，不冒充已经执行的文件删除结果。

## 1. Gold risk and Equity–Gold allocation

### Research question

GLD 风险能否预测；黄金分散化能否改善权益风险架构；动态 ERC/GMV 和额外现金层是否优于简单静态组合？

### Motivation

权益与黄金的长期关系可能提供分散化，避免单资产降仓后完全放弃风险溢价。但黄金不是恒定负相关 hedge，多资产配置也不能由边际波动预测力直接推出。

### Method

冻结权益 GK HAR，GLD 使用已审计的 session-return² + gap² endpoint HAR；训练期尺度桥接后比较固定静态股金配置、ERC、GMV、执行 band 与固定预算 cash scaling。下一开盘、自融资、无杠杆，按固定成本、offset、时期和 matched-average-exposure 门槛评价。Gold 代理不是全球近全天 realized variance；原生风险定义不同，不能混用早期 common-endpoint 与最终 hybrid vintage 的数值。[E01–E03]

### Main evidence

1. **GLD 风险可预测。** endpoint HAR 的历史 OOS R² 为 **32.67%**、高风险 AUC **0.846**；相对 Rolling22 的 MSE/QLIKE 改善为 **8.19%/11.21%**，相对 GARCH 增量仍为 **WEAK**。[E02 §5；E03]
2. **静态分散化具有历史经济价值。** 固定月度 80/20 在主展示 offset0、每边 1bp 下，SPY 组合 CAGR **11.47%**，对应 Buy & Hold **11.19%**；QQQ 为 **15.89%**，对应 **16.46%**。两资产在每边 1bp 与 3bp 均有 **5/5** offset 通过历史经济门槛；这不等于前向就绪。[E02 §1、§6；E03]
3. **漂亮的动态点估计没有变成稳定增量。** SPY monthly ERC/GMV CAGR 为 **11.88%/12.53%**；但相对匹配平均权益/黄金暴露的静态控制，MaxDD 幅度分别恶化 **5.71%/8.31%**；QQQ 相应恶化 **8.90%/15.35%**。动态规则没有通过强晋级 offset，不能按最高收益选架构。[E02 §1–2；E03]
4. **Gold selloff 是真实反例。** 在独立 parking 研究的 QQQ `TAPER2013` 实际现金窗口，GLD 相对滚动现金平均超额 **−3.396%**、五日超额 ES95 **10.774%**，仅 **6** 窗。该小样本不能证明所有时期失效；SPY 同定义窗口均值并不为负，因此也不能写成两资产一致反例。[E06：COMMON/CASH_SLEEVE/offset0/1bp/TAPER2013]
5. **固定预算现金层保护强，但过于保守。** 对固定月度股金锚点缩放后，SPY/QQQ 相对未缩放 80/20 股金组合的 CAGR 保留仅 **65.55%/68.16%**（分母不是权益 Buy & Hold）；波动降低 **51.15%/41.96%**、MaxDD 降低 **63.33%/55.71%**。未通过本轮风险—收益交换标准，不能改写成没有风险保护，也不能调高预算救结果。[E02 §4；E03]
6. **研究有效不代表可部署。** 最终静态经济价值为 SUPPORTED，但 readiness 为 RESEARCH_ONLY；原归档只保留结论、精选指标与来源，不再支持完整 Gold 账本重跑。[E01–E03]

### Verdict

**CLOSED**；其中静态分散化与 GLD 风险预测为 **SUPPORTED**，动态 ERC/GMV 增量为 **WEAK**，bundle cash scaling 为 **NOT_SUPPORTED**。

### Why it did not change the mainline

动态复杂度未在匹配控制、严重回撤和跨资产检验中稳定胜出。Gold 的长期分散化属于可独立研究的多资产问题，不是当前单资产风险控制主线的必要组件。compact archive 未保留完整长期 return-correlation 系数表，因此本摘要不杜撰“低相关”的精确值；保留的是已核实的分散化结果，不把静态收益表现反推成相关系数证明。

### Final disposition

**KEEP SUMMARY ONLY**；**POSSIBLE SEPARATE FUTURE PROJECT** 仅为领域归类，未经新授权不重开。**DO NOT INCLUDE IN CURRENT MAINLINE**。

## 2. Defensive asset parking

### Research question

在 Full VOL 真正留下现金的固定持有窗口，IEF、TLT、GLD 是否比短端现金更值得持有？

### Motivation

直接衡量减仓资金的实现机会成本，而不是构造利率择时模型，或把高收益风险资产误称为安全现金替代。

### Method

冻结权益 target 与原开盘执行窗口；比较同窗 ETF 净收益和 LOCKED_CASH，并以 REALIZED_ROLLING_CASH 做 ex-post 机会成本诊断。主样本为有 residual cash 的 CASH_SLEEVE；真正新增减仓 DE_RISK 单列。资产收益减现金收益的均值、尾部与跨时期门槛独立于安全替代门槛。[E04]

### Main evidence

1. 主样本 COMMON/offset0/每边 1bp、相对滚动现金的五日平均超额：IEF 为 SPY **0.019%**、QQQ **−0.016%**；TLT 为 **0.009%/−0.052%**。没有稳定战胜现金。[E04 §2；E05–E06]
2. GLD 平均超额为 **0.289%/0.216%**，胜现金概率 **53.480%/54.422%**；五日超额 ES95 却达 **6.116%/6.390%**。正均值机会与安全停车资格是不同命题。[E04 §2；E05–E06]
3. GLD/SPY 的 family-95% 均值下界在较短 block 下仅 **0.000212%**；QQQ 未单独通过全部显著性要求。SUPPORTED 来自预登记 SPY 主证据与 QQQ 方向迁移，不是两资产均有强显著性。[E04 §2]
4. 固定时期中三只资产在 **2022** 的平均超额均为负；IEF/TLT 在近期样本亦为负。GLD 在较近期表现较好，仍不能覆盖其窗口损失。[E04 §3；E05–E06]
5. 原现金可用主样本 SPY **546** 窗、QQQ **588** 窗；后续利率刷新使 QQQ 增至 **589** 窗，GLD 均值变为 **0.226%**，并不改方向或安全结论。刷新敏感性没有延长冻结权益信号，不能与主样本混报。[E04 §7]

### Verdict

IEF/TLT **WEAK**；GLD 的平均实现机会 **SUPPORTED**；safe-sleeve 替换 **NOT_SUPPORTED**。`CANONICAL_SAFE_SLEEVE = 3M_TBILL`。[E04 §8]

### Why it did not change the mainline

现金是风险控制之后的安全资金承载，不按风险资产的平均回报排名替换。现金数据仍是历史 DGS3MO carry 代理，LOCKED 为策略记账、ROLLING 为实现诊断；两者都不是实际买入某只 T-bill 的成交总回报证明。尾部与坏年份门槛未通过，不能据此新增配置或 rate filter。

### Final disposition

**KEEP SUMMARY ONLY**；**DELETE ACTIVE ALLOCATION IMPLEMENTATION**。canonical 现金输入、记账约定和 Full VOL 账户保留。

## 3. Full VOL no-trade bands

### Research question

固定 no-trade band 能否减少无谓交易，又不削弱原风险控制？

### Motivation

实施成本值得检查，但交易次数减少不等于交易金额、风险或收益改善。

### Method

只改变执行 band，不变更预测、预算与目标公式；在决策收盘根据实际持仓判断，下一开盘执行，保留风险降低型 override。对固定 **0/2.5/5/10pp** band 检查成本、offset、近期、去危机与配对区间；要求相邻非零 band 形成跨资产区域。[E07–E08]

### Main evidence

1. offset0、每边 1bp 下，SPY 交易次数从无 band 的 **748** 降至 5pp 的 **460**；年换手从 **2.66** 降至 **2.43** 倍 NAV。QQQ 对应 **675→457** 次、**3.29→3.05** 倍。次数下降显著，金额未达到主要经济门槛。[E07 主结果]
2. 小 band 未形成合格区域：两资产 **2.5/5pp** 在每边 1bp 与 3bp 的完整经济 gate 都为 **0/5** offset。[E07 区域为何未晋级]
3. SPY 10pp 有 **4/5** 全历史经济 offset，但近期安全性仅 **3/5**；QQQ 10pp 全历史仅 **2/5**。单点或单资产表现不能替代宽区域。[E07 区域为何未晋级]
4. 主展示下 5pp 的 realized overshoot 为 SPY **21.53%**、QQQ **23.99%**，不能只以少交易宣称风险控制充分；门槛同时约束风险恶化、overshoot 与近期稳定性。[E07 主结果及门槛]
5. 最终两个资产均无 qualified band，`FULL_VOL_BAND_VALUE = WEAK`、`ROBUST_BAND_REGION = NONE`。[E08]

### Verdict

**WEAK**；稳健 band 区域 **NONE**。

### Why it did not change the mainline

没有同时满足交易金额、收益代价、风险、近期及跨资产条件的相邻区域。不从已知历史挑一个看起来最好的 band，也不将此前 Gold ERC 的 band 实施价值移植成单资产 Full VOL 证据。

### Final disposition

**KEEP SUMMARY ONLY**；**DELETE BRANCH IMPLEMENTATION**。无 band 的 canonical 执行保留。

## 4. 21D volatility forecasting

### Research question

未来整月尺度的 holding risk 是否可预测，简单 HAR 是否优于 persistence 与冻结 GARCH？

### Motivation

较长持有期可能降低风险估计噪声，但预测层价值需要与组合层价值分开证明。

### Method

直接预测未来 **21** 个 HOLD 的均值；下一开盘进入、后续第 **22** 个开盘成熟。月度 expanding、成熟训练标签和原 smearing 不变；HAR(1,5,22) 为主，固定 66D 扩展只作比较，Rolling22/63、历史均值和既有 GARCH 为基准。后续 adaptive 阶段另检验约束 HAR 与 training-only selector，不据最终 test 挑结构。[E09–E12]

### Main evidence

1. HAR 相对 Rolling22 的全历史 MSE/QLIKE 改善：SPY **32.62%/24.49%**，QQQ **24.03%/23.24%**；两种 block 的同时下界均为正。[E09 主模型相对基准]
2. OOS R² 为 SPY **0.380**、QQQ **0.571**；成熟评价 origins 为 **7,819/6,284**。这是 walk-forward 风险预测证据，不是收益方向预测。[E09 全样本预测证据]
3. HAR 相对 GARCH 的点改善为 SPY **23.59%/5.34%**、QQQ **14.78%/6.77%**，但 QLIKE 的同时下界跨零；QQQ 近期 QLIKE 相对 GARCH 还出现反向。因此 HAR-vs-GARCH 为 **WEAK**。[E09 主模型相对基准及失败条件；E10]
4. 加入 66D 后 QLIKE 全历史改善为 SPY **−3.59%**、QQQ **−4.65%**；不是稳定结构改进。[E09 66日固定扩展]
5. 后续 training-only selector 相对 HAR122 的全历史 MSE/QLIKE 改善为 SPY **−2.31%/−3.13%**、QQQ **1.93%/−0.69%**；约束版本与原基线几乎相同。没有依据替换简单 HAR122。[E11 初始21D forecast；E12]

### Verdict

长 horizon 风险预测 **SUPPORTED**；HAR 相对 GARCH **WEAK**；QQQ 迁移 **SUPPORTED**。[E10]

### Why it did not change the mainline

简单 HAR122 仍是该长 horizon 研究的基准，但预测更长持有期不意味着改变投资期限更好。不能用不同目标的 MSE 大小直接挑期限；进入组合后仍需独立增量检验。

### Final disposition

**KEEP AS MONITORING RESULT**：保留预测研究结论，不表示启动监控任务。**NOT PART OF PUBLIC PORTFOLIO PIPELINE**；大规模模型选择与训练中间输出不保留为活跃研究。

## 5. Adaptive 21D reforecast

### Research question

在固定持有终点内，风险已经实现一部分后，最新信息是否改善剩余风险预测？是否还需要路径触发或更频繁参数 refit？

### Motivation

区分刷新输入带来的价值与改变模型参数的价值；已经实现的风险不是可以花完的预算，不能只靠把已实现部分加回而制造预测进步。

### Method

分别评价原曲线尾部、最新 direct remaining forecast、机械预算与 surprise-adjusted 更新。主评价只看尚未实现的 remaining risk。参数月度更新为基线，再按固定规则实际完成 weekly/event refit；早期 high/low 与路径 bands 只使用过去成熟信息。[E11–E12]

### Main evidence

1. 最新 direct 相对原曲线尾部，SPY 在 k5 的 MSE/QLIKE 改善 **17.97%/24.10%**，k10 为 **28.82%/40.65%**；QQQ 对应 **18.22%/20.30%**、**29.08%/35.78%**。同一基础模型内更新具有明确价值。[E11 初始曲线、直接更新]
2. 两种 block 下所有上述 direct 主比较的同时下界均为正；该结论没有借助 total risk 中已实现部分的机械降误差。[E11 关键同时区间]
3. Surprise 相对 direct 的 SPY k5 改善仅 **0.88%/1.17%**，同时下界跨零；SPY 近期 k5/k10 QLIKE 改善为 **−4.75%/−3.17%**。整体判定 **WEAK**，不能把完整再校准收益全部归因于 surprise 项。[E11 Surprise、失败条件；E12]
4. 早期 HIGH5 的 phase0 非重叠 origins 在 k5/k10 为 SPY **14/18**、QQQ **28/28**，均未达到每项 **30** 的要求；另外还有方向与区间问题。证据稀少不等于证实效应为零，非重叠亦不等于独立危机事件。[E11 早期异常]
5. weekly refit 相对 monthly 的 k5 MSE/QLIKE 改善为 SPY **−0.18%/0.02%**、QQQ **−0.34%/−0.06%**；weekly 与 event 均已实际运行，最终均 **NOT_SUPPORTED**。[E11 Monthly、weekly与event refit；E12]

### Verdict

**SUPPORTED**：direct remaining-risk reforecast；**WEAK**：surprise、early-high；**NOT_SUPPORTED**：early-low、路径 band 校准、weekly/event 参数 refit。[E12]

### Why it did not change the mainline

这是预测更新机制，不是仓位触发规则。Open checkpoint 的完整 surprise 包含 latest-Close direct 尚未看到的新 gap；CLOSE_KNOWN 敏感性单列了这一边界。模型同时重估 alpha、beta、gamma，缺少 alpha-beta-only 消融，不能声称全部改善来自独立路径信息。较频繁参数估计没有稳定增量。后续期限组合检验也没有支持改动主线。

### Final disposition

**KEEP SUMMARY ONLY**，保留 methodological finding；**DELETE LARGE PATH / REFIT IMPLEMENTATION**；**NO PORTFOLIO RULE**。旧报告的后续研究建议已由下一分支完成，不是仍待自动启动的任务。

## 6. 5D–21D term-structure portfolio

### Research question

同一资产的短期与较长期风险预测，能否通过 slow base + fast override 提供超越单期限的组合价值？

### Motivation

21D 风险可预测且可重估，但两个期限只有在提供足够不同的信息时才值得增加决策复杂度。

### Method

只复用冻结 5D HAR 与 21D HAR122，保持原资产风险预算和现金日历；比较单期限、monthly/rolling 基础、full cap 与固定过去分位阈值 selective override。预先封存 target，再运行账户；与平均暴露匹配的静态、5D 和 21D 控制比较，不能只击败静态少持仓就宣称期限增量。[E13–E15]

### Main evidence

1. SPY/QQQ 的 log-risk 相关为 **0.996097/0.997435**，日度 log-risk 变化相关为 **0.995649/0.996427**；不是足够独立的快慢风险状态。[E15]
2. 主 offset 的 rolling21 平均目标与 full cap 分别为 SPY **83.29%/83.15%**、QQQ **81.42%/81.36%**，新增 cap 实际改变很小；QQQ 两种 rolling override 在有效月份相同，不是两份独立证据。[E13 NAV前规则]
3. 21D monthly 年换手较低：SPY **1.147** 倍、QQQ **1.331** 倍，对应 5D-only **2.660/3.289**；但 MaxDD 为 **32.73%/33.68%**，对应 5D-only **31.84%/30.76%**。低换手不能替代响应与保护检验。[E13 主要结果]
4. Full cap 相对 matched 5D 的波动改善为 SPY **−0.56%**、QQQ **−0.35%**，MaxDD 改善为 **−2.23%/−2.37%**；相对 matched21D 也只有微小变化。相对 matched static 的显著风险改善属于原动态缩放价值，不是新增期限信息。[E13 是否仅仅更低平均仓位]
5. 最终 `TERM_STRUCTURE_PORTFOLIO_INCREMENT = NOT_SUPPORTED`，`RECOMMENDED_ARCHITECTURE = 5D_ONLY`，`NEXT_ACTION = KEEP_5D_FULL_VOL`；历史经济价值与方向性跨时期稳定不等于新增架构晋级。[E14]

### Verdict

期限结构新增组合价值 **NOT_SUPPORTED**；原 5D 风险控制价值 **SUPPORTED**；前向就绪度仍为 **RESEARCH_ONLY**。[E14]

### Why it did not change the mainline

两期限近乎共线，额外规则的相对风险改善很小，未稳定优于匹配单期限控制。每次 rolling21 是新终点预测，亦不能冒充上一阶段固定终点的 remaining-risk 更新任务。保留 5D 是经过这些比较后的选择，不否认 21D 预测层结果。

### Final disposition

**DELETE PORTFOLIO IMPLEMENTATION**；**KEEP COMPACT SUMMARY ONLY**。不把 overlay、阈值或新账户加入公开主线。

## 收敛后的解释边界

| 保留的认识 | 不随之推出的结论 |
|---|---|
| Gold 可预测且静态分散化有历史价值 | Gold 是安全现金替代，或动态配置可部署 |
| no-trade band 可以少交易 | 存在跨资产、跨时期的稳健实施区域 |
| 21D 风险可预测 | 21D 应替换 canonical 5D |
| remaining-risk reforecast 有效 | path surprise 可直接形成仓位触发，或更频繁 refit 必要 |
| 动态风险控制优于相同平均仓位的静态控制 | 5D–21D overlay 优于原单期限动态风险控制 |

最终保留 **5D_FULL_VOL**。这些归档结论记录了合理探索与停止理由；没有新增收益预测、模型、账户或实盘行动。清理后是否成功复现、测试是否通过、实际删掉哪些文件，应由独立清理报告记录，本摘要不提前替其宣告 PASS。
