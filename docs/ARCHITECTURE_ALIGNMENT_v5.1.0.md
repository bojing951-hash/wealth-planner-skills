# v5.1.0 开发完成后架构逐项对照及验收记录

**总体结论：结构回归原始 v0.4 设计；当前仍是 Developer Preview，不等于十个模块已全部实现。**

- 架构唯一基线：[`BASELINE_ORIGINAL_v0.4.md`](BASELINE_ORIGINAL_v0.4.md)，2026-10-11 原稿原文，SHA256：`552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`。
- 对照对象：上一工程版本 v5.0.0 → 本次 v5.1.0 **Skill-First 架构回归**。不引入未经核验的当地税率/资本市场预测。
- 版本关系：`Skill = 5.1.0`；保留并复用 `wealth_core` v5.0 数学后端（仍为开发预览），不将“更新 Skill 指令”等同于“升级金融模型”。
- **宿主执行**：联网、论文与法规搜索、文件操作、推理、工具调用、用户报告；**Skill 提供规范**：研究流程/证据裁决/规则/权限；**可选算术程序**：确定性计算、输入核验、用户情景，不自行启动独立 Agent。
- **工具联调真实状态：NOT_TESTED。** 未在真实 Codex / Claude Code 会话执行并记录宿主对官方原始法律文档的实际检索；仅本地文本/程序和离线示例测试。

## A. 相对于原始架构，v5.0 → v5.1 究竟改变什么？

| 架构要素 | 最初 v0.4 规划要求 | v5.0 实际偏离/保留 | v5.1 本次修正及文件 | 是否符合 / 未解决 |
|---|---|---|---|---|
| 执行主体 | 宿主 Codex/Claude 执行研究和工具调用；Skill 非独立 Agent | 主集成 CLI 把若干研究决策编排固化为流程，易被误认作独立 Agent | `SKILL.md` 明确 **host-native 执行优先**，`host-queue` 降级为非必需兼容工具；`workflows/host-research-protocol.md` | **设计符合**；真实宿主调用未 E2E |
| 专业知识 | 证据分类、理论间条件性冲突，不以人物权威代替方法 | 已有理论关系 JSON 和条件匹配代码，但与开放式研究有缝隙 | `workflows/theory-evidence-and-conflicts.md` 把可验证 claim 作为单位、要求原始来源和外部有效性分析，保持争议 | **研究规约已强化**；尚无实证系统文献评价流水线 |
| 财务决策 | 法律与权限 → 家庭可生存 → 目标期限 → 模型证据 → 风险成本优化 | 有局部代码和声明，但入口强调 CLI | `policies/core-decision.md` 与 `workflows/skill-first-execution.md` 恢复硬约束顺序 | **流程定义符合**；决策质量未真实宿主验证 |
| 长期宏观 | 本币真实利率、通胀、估值慢变量；不短线择时 | 现有宏观校验工具但没有实时宏观调用证明 | `SKILL.md` 和原 `references/long-horizon-macro.md` 明确宿主取官方数据、慢变量低频 | **规约符合**；长期预测校准未实现 |
| 数学计算 | 可复算程序、假设明确、与 LLM/宿主解耦 | v5.0 Python 代码较重，但有可测试性 | 保留 `scripts/wealth_v5.py` 为**可选工具**；不要求每个问题强制调用；保留数学行为回归 | **兼容保留**；后端拆减属未来技术债 |
| 法税合规 | 国内外分法域与税年、有效法律原文、拒绝推测确定税额 | 仅预检与用户虚构税档算术 | `workflows/host-research-protocol.md`、`workflows/jurisdiction-tax.md` 强制现实宿主原始来源与 `NOT_VERIFIED` | **规约符合**；正式准确税负引擎缺失 |
| 动态复盘 | 条件驱动按需/外部授权调度；保持历史审计 | 有旧新报告比对，不存在后台自主运行 | `workflows/dynamic-review-protocol.md` 明确触发、分类、原因与授权状态；不因新闻自动交易 | **按需协议符合**；持续管理需私有存储/授权调度 |
| 安全与审计 | 可复算、区分真实资产/模拟利润、敏感数据不外传 | 现有测试和有条件阻断 | 加 `tools/check_architecture.py` 守卫、精确保留原稿 SHA、每次发布强制对照文档、CI 审核 | **结构守卫完成**；缺专业复核及真实 host E2E |

## B. 十个专业域（D01–D10）逐项对照

> **状态解释：** 此处 `PARTIAL` 表示存在程序和/或规约，但尚未达到原始总体架构所描述的端到端能力。不能把文件存在视为业务已实现。

| ID | 原始规定能力 | v5.1 现有实现证据 | 当前成熟度 | 未完成/偏差及风险 | 下一阶段的检验或补齐 |
|---|---|---|---|---|---|
| D01 | `profile_and_data_quality` 数据真实性、归属、币种 | `schemas/profile-v5.schema.json`; `lib/wealth_core/profile.py`; `references/architecture-10-domains.md` | **PARTIAL** | 银行流水无授权自动对账；用户口述与已验证文件不能等同 | 测试数据冲突/所有权/重复账户；未来只读连接器 |
| D02 | `jurisdiction_and_compliance` 地区身份/合同/税务/资产法 | `workflows/jurisdiction-tax.md`; `lib/wealth_core/jurisdiction_v5.py`; `workflows/host-research-protocol.md` | **PARTIAL** | 无完整年度地方税引擎；官方法规当前有效期未有宿主实机核验 | 先验收深圳上海纽约芝加哥官方法条获取与准确身份边界 |
| D03 | `personal_cashflow` 到账/支出/债务/现金池 | `lib/wealth_core/finance.py`; `lib/wealth_core/household.py` | **PARTIAL** | 非银行核验的税后可投资额为条件金额；社保养老金和债务多合同摊销不全 | 现金流勾稽；净资产与受限权益不得重复入账 |
| D04 | `life_cycle_and_goals` 家庭与10–30年生命周期 ALM | `lib/wealth_core/household.py`; `workflows/lifecycle-and-safety.md` | **PARTIAL** | 婚姻/继承/保险/跨境移居/退休制度尚未形成完整数值模型 | 期限与负债匹配、养老/保障合规案例 |
| D05 | `economics_and_evidence` 数学/实证/经验/法律分开、冲突裁决 | `policies/theory_graph.json`; `lib/wealth_core/evidence.py`; **新增** `workflows/theory-evidence-and-conflicts.md`; `assets/claim-card-example.json` | **PARTIAL** | 12项理论/7组关系非全面系统综述；真实论文检索和质量分级需宿主完成 | 真实研究 source→claim→decision 链抽样核验，反例测试 |
| D06 | `long_term_macro` 真实利率、本币通胀、估值慢变量 | `references/long-horizon-macro.md`; `lib/wealth_core/macro_review.py` | **PARTIAL** | 无校准资本市场长期收益分布；来源数据不自动变成预测 | 宿主真实官方宏观抓取、货币匹配、情景敏感性 |
| D07 | `investment_policy` 费用/资产配置/风险预算和税务位置 | `lib/wealth_core/portfolio.py`; `workflows/portfolio-and-macro.md`; `policies/core-decision.md` | **PARTIAL** | 实际各地适格投资渠道与净税后组合尚未建成 | 先建立 IPS 模板，测费用、税、流动性和可访问性 |
| D08 | `simulation_and_risk` 现金流、真实复利、冲击和概率 | `lib/wealth_core/simulation.py`; `lib/wealth_core/goal_math.py`; `workflows/models-and-reporting.md` | **PARTIAL** | MC仅用户输入假设/种子；样本份额不是校准现实概率 | 资产/收入相关冲击、历史重放和样本外校准 |
| D09 | `decision_and_execution` 硬约束→多个候选→审批与比较 | **新增** `policies/core-decision.md`; `workflows/skill-first-execution.md`; 原 `lib/wealth_core/integrated.py` 仅计算辅助 | **PARTIAL** | 真实宿主调用和最终报告流程未 E2E；缺多方案质量评估 | 手工 rubric + 两客户端真实执行核查 |
| D10 | `audit_and_monitoring` 来源/版本/触发/纠错 | **新增** `workflows/dynamic-review-protocol.md`; `workflows/report-contract.md`; `lib/wealth_core/dynamic.py`; 架构审查脚本 | **PARTIAL** | 无经同意的安全存储/定时工作流；守卫只查结构 | 真实前后计划差异记录、数据删除验证、授权调度验收 |

## C. 12 个原始工作流状态逐项对照

| 状态 | 执行责任 | v5.1 规范/实现 | 验收结论 |
|---|---|---|---|
| `INTAKE` | Host | `workflows/intake.md` + `workflows/skill-first-execution.md` | **规约具备**，只取相关财务事实 |
| `CAPABILITY_CHECK` | Host | `workflows/host-research-protocol.md` | **规约具备**；真实能力清单未宿主实机核验 |
| `FACT_VERIFICATION` | Host + 可选计算 | `SKILL.md`; `lib/wealth_core/profile.py` | **部分**；只能检查提供的数据，不能验证银行真伪 |
| `JURISDICTION_GATE` | Host 使用官方来源 | `workflows/jurisdiction-tax.md`; `policies/core-decision.md` | **部分**；法律实质尚未通过当前资料的独立认证 |
| `HOUSEHOLD_SOLVENCY` | Host + Math | `workflows/lifecycle-and-safety.md`; `lib/wealth_core/finance.py` | **部分**；保险/负债覆盖不足 |
| `GOAL_AND_LIFECYCLE` | Host | `workflows/lifecycle-and-safety.md`; `lib/wealth_core/household.py` | **部分**；正式长期负债匹配模型不足 |
| `EVIDENCE_RESEARCH` | Host 查原始来源，Skill定方法 | `workflows/theory-evidence-and-conflicts.md` | **规约已加强**；真实文献研究未 E2E |
| `MACRO_SCENARIOS` | Host + Math | `references/long-horizon-macro.md`; `lib/wealth_core/macro_review.py` | **部分**；模型无历史校准 |
| `CANDIDATE_PLANS` | Host | `policies/core-decision.md` + `workflows/models-and-reporting.md` | **规约具备**；报告质量需 E2E |
| `DETERMINISTIC_AND_STOCHASTIC_VALIDATION` | 可选 Math + Host复核 | `scripts/wealth_v5.py`; `lib/wealth_core/simulation.py` | **算术测试通过**；概率校准未实现 |
| `POLICY_CHECK` | Host 遵守 Skill 规则 | `policies/core-decision.md` + `SKILL.md` | **规约具备**；实际不同工具权限需 E2E |
| `EXPLAIN_AND_MONITOR` | Host + 用户审批，调度可选 | `workflows/report-contract.md`; `workflows/dynamic-review-protocol.md` | **按需复核规约具备**，后台监控不存在 |

**流程分支**：对“月薪 2 万元如何做预算”等问题可略过无关的复杂宏观/跨境研究；但任何实际法税决策均不能绕过适用法域与有效来源核验。`NOT_APPLICABLE` 应说明原因，不能随意删除状态定义。

## D. 边界、安全和证据核对

| 原始硬约束 | v5.1 处理 | 仍有何风险 |
|---|---|---|
| L0–L3 权限与宿主工具能力 | `workflows/host-research-protocol.md`；L1/2需明示授权，L3金融/税务动作**默认不执行** | 真实宿主权限行为待端到端测试 |
| 不把 PF 模拟收益或名义资金算作个人资产 | `SKILL.md`; `lib/wealth_core/finance.py`；跨境 PF 测试输入 | 无法核验真实平台/银行流水；仅对合成数据校验 |
| 不混合 CNY/USD，除非注明日期和汇率 | `lib/wealth_core/fx.py`; `references/architecture-10-domains.md` | 用户需要提供可信估值及汇率来源 |
| 当前法律与税率必须来自有效官方资料 | `workflows/host-research-protocol.md`; 法域预检仅给问题清单 | 没有联网/许可时输出 `NOT_VERIFIED` 而非精准税额 |
| 不将模拟达标样本比率当成校准概率 | `SKILL.md`; `lib/wealth_core/simulation.py` | 用户输入收益分布未经科学校准 |
| 不因单月宏观新闻触发自动交易 | `workflows/dynamic-review-protocol.md`; `references/long-horizon-macro.md` | 模拟假设更新仍需人工判断 |
| 不在没有存储/定时权限时宣称持续监控 | `workflows/dynamic-review-protocol.md` | 真实持续监控未实现 |
| 版权和隐私 | 存**索引/命题**而非受版权保护书籍全文；只用虚构例子、禁传私人数据 | 公开发布前仍需手动安全检查 |

## E. 本次测试与执行记录（2026-10-11）

| 测试 | 运行命令或文件 | 状态 |
|---|---|---|
| 架构结构守卫 | `python3 tools/check_architecture.py --strict` | `PASS`（10/10 域，12/12 状态，原稿哈希一致，须有本报告） |
| 旧版回归 | `python3 -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | `PASS`（46项） |
| v5 原有功能 + 本版架构守卫负例测试 | `python3 -m unittest discover -s tests -p 'test_*.py' -q` | `PASS`（原86项 + 两组架构守卫测试共22项 = 108项，合计 154 项） |
| 五案例离线试运行 | 深圳、上海、纽约、芝加哥、跨境 PF，`wealth_v5.py run --format json` | `PASS`（仅用户输入与模型约束核查，不核验真实税额） |
| 断网、跨宿主权限和直接研究 | 手工宿主测试文档 `tests/host_e2e/ACCEPTANCE_v5.1.md` | **NOT_TESTED**：没有 Codex/Claude 实机记录 |
| 正式全球税务/宏观数据的实质正确性 | 独立专业验证 | **NOT_TESTED/NOT_IMPLEMENTED** |

> 测试总数以执行日志为准；增加或修订测试后必须同步更新本节。守卫检测的是架构一致性和必要资料**存在性**，不验证实际研究质量。

## F. 技术债、偏离与下一阶段顺序

1. **v5.0 主集成代码仍较大**：目前作为兼容的辅助程序保留，不能把其 `host-queue` 输出看成宿主已执行。下一阶段择机将宿主规划逻辑与确定性数学计算拆开，不应影响用户可复算性。
2. **循证动态研究未形成现实宿主闭环**：指令已存在，须先通过 Codex 和 Claude Code 各自实机工具链测试，完整留存检索的官方文本、日期、逻辑、降级及报告证据。
3. **跨法域税法范围太大**：以四城市 + 跨境 PF 五个标准案例为有限范围验收，不可直接宣布全球覆盖；优先官方有效规则、家庭身份、收入性质。
4. **长期实际收益分布未科学校准**：先抓取真实且许可使用的长期市场数据，再做资本市场假设、敏感性、历史重放和失效边界研究。
5. **缺安全数据持久化和自动复核**：在获用户授权、完成威胁建模及数据生命周期设计前，不增加默认后台功能。

**结论：** v5.1.0 回归并保留原始 v0.4 的十域十二态、Skill/Host职责、法税和现金安全硬门槛以及可复算性；所有领域成熟度仍为**PARTIAL**。本次完成的是架构对齐和发布治理工程，不得宣称“完整财务规划 Agent 已完成”。
