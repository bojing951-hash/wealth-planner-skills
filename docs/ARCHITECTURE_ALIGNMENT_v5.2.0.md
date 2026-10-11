# Wealth Planner Skill v5.2.0 — 对照**最初 v0.4 架构**的开发验收与差异报告

> 架构基线：`docs/BASELINE_ORIGINAL_v0.4.md`，SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`，原文未改动。  
> 上一版本：v5.1.0 Skill-First；本次交付：v5.2.0 Persistent Financial Memory。  
> 项目定位不变：**专业 Skill，由 Codex/Claude Code 宿主 Agent 负责推理/研究/工具调用**；本次仅增可选的本地加密状态工具，不是新 Agent/服务/后台调度器。  
> 当前成熟度：**Developer Preview**。以下测试是离线测试，真实 Codex/Claude Code E2E = **NOT_TESTED**。

## A. 本次范围与变更矩阵（相对最初架构）

| 原架构约束/目标 | v5.1 状态 | v5.2 实际证据 | 对照结论与尚存缺口 |
|---|---|---|---|
| **Skill-First**：宿主 Agent 调用工具，Skill 指导 | 是，记忆仅在规约中 | `SKILL.md` 新增记忆路由和授权门槛；`workflows/local-memory.md`；可选 `scripts/memory_cli.py` | **符合**，未新增独立 Agent；真正人类许可仍需宿主正确取得，未真实端到端验证 |
| **D01 个人画像和事实来源** | 简化 JSON/一次性输入 | `lib/wealth_core/local_memory.py` 的 typed/date/source facts；`read` 标记过期和未来日期 | **增强但 PARTIAL**；无账户核验，已保存的用户口述不是验证事实 |
| **D03 现金流** | 算术与规划 | 可选记忆 `income.monthly_*`、`expenses.*`、`assets.*`，月度快照保留原币种 | **增强但 PARTIAL**；不存在真实账单对账或自动读取资产余额 |
| **D09 决策与审批** | Skill 规则和工具调用规范 | 用户审批先于写入的 `preview`/`update`；`change_sha256` + `expected_revision` | **增强但 PARTIAL**；digest 不是用户身份/授权认证；真实 host 审批必须独立验证 |
| **D10 审计与动态管理** | 报告比较，无持久存储 | AES-GCM vault、变更记录、版本快照、`compare`、forget/purge/delete/export | **本次主要实现**；无授权后台监控、正式密钥托管/独立Windows ACL审核/备份擦除 |
| 用户私有 DB/缓存为**可选** | 无持久保存 | 两个 OS 私有根目录（密文与密钥分离）；默认不初始化 | **符合**；无云同步，不在安装Skill目录和Git中存用户数据 |
| L0/L1/L2/L3 权限分界 | 指导性规则 | L1读、L2逐项写/删、无L3；CLI声称已获授权由宿主验证 | **符合设计**；静态 `--consent` 标志本身不保证人类授权 |
| 保留十专业域、十二工作状态 | 10/12 | 原基线与索引不变；记忆通过 `INTAKE` / `FACT_VERIFICATION` / `EXPLAIN_AND_MONITOR` 路由 | **全部保留**；未删旧专业能力或修改原始流程 |
| 必要代码可复算、无自建通用 Agent | 保留可选算术后端 | 小型本地加密文件适配器；不加推理、爬虫、调度循环 | **符合**；引入可选 cryptography 依赖，缺依赖拒绝存明文 |

### v5.2 核心能力与局限

**已实现的本地行为：** 用户明确同意时独立初始化私人存储；用户审批读取；只保存白名单内的日期化事实、简短规划/决策及其修订；存储在本机加密档案；二次进程加载同一档案并对比变化；撤回使用、忘记字段、清理分类、完整本地档案删除；用户明确接受风险后导出 JSON；版本冲突拒绝静默覆盖；Git 路径/符号链接/权限/缺密钥拒绝操作。`SKILL.md` 指导宿主选择可用工具，而不是自己模拟 Codex/Claude Code 的工具调用。

**明确未实现：** 真实客户账户自动同步、跨设备/云端记忆同步、OS硬件密钥存储、Windows ACL独立审计、密钥恢复和加密备份、自动定期复盘、真实宿主客户端授权与加载全流程、保证其他AI对话/旧备份/导出文件彻底删除。

## B. 十个原始专业域逐项对照（D01–D10）

状态说明：`PARTIAL` 是存在一部分代码/方法但尚不具备原始目标的完整端到端能力；文件存在不能算完整实现。

| ID | 原始规定职责 | v5.2 证据/保留 | 状态 | 尚缺失、风险或下一步 |
|---|---|---|---|---|
| **D01** | 画像与数据质量 | `schemas/profile-v5.schema.json`, `lib/wealth_core/profile.py`, **新增 `local_memory.py` 日期/来源事实** | **PARTIAL（增强）** | 真实账单对账、重复账户合并、多数据源冲突核实 |
| **D02** | 地区与法律合规 | `workflows/jurisdiction-tax.md`, `jurisdictions/`, `jurisdiction_v5.py` | **PARTIAL（保留）** | 地方税的现行适用判断、专业审核/税年精算；历史税收居留主张仅事实声明 |
| **D03** | 家庭现金流、债务、流动性 | `finance.py`, `household.py`, **`local_memory.py` 财务快照** | **PARTIAL（增强）** | 多账户现金流流水对账、社保/养老金及负债合同模型 |
| **D04** | 生命周期和长期目标 | `workflows/lifecycle-and-safety.md`, `household.py` | **PARTIAL（保留）** | 婚姻、医疗、教育、退休、继承/信托长期动态现金流 |
| **D05** | 经济与循证理论冲突 | `workflows/theory-evidence-and-conflicts.md`, `policies/theory_graph.json` | **PARTIAL（保留）** | 原始论文系统评价、结论外部效度和更广理论集成 |
| **D06** | 长期宏观慢变量 | `references/long-horizon-macro.md`, `macro_review.py` | **PARTIAL（保留）** | 经检验的人民币/美元长期假设和真实来源联调；禁止把历史记忆当市场现价 |
| **D07** | 投资政策与组合管理 | `portfolio.py`, `workflows/portfolio-and-macro.md` | **PARTIAL（保留）** | 多法域税后组合、产品实际适格性和可执行IPS |
| **D08** | 数学模拟与风险校验 | `simulation.py`, `goal_math.py`, 可选 `wealth_v5.py` | **PARTIAL（保留）** | 现实市场参数/极端尾部校准、样本外风险验证 |
| **D09** | 硬约束/候选方案/执行权限 | `policies/core-decision.md`, **新 `preview`、digest+CAS 写入门槛** | **PARTIAL（增强）** | 宿主真正用户审批与外部研究调用的E2E可信验证 |
| **D10** | 审计、动态监控和纠错 | `workflows/dynamic-review-protocol.md`, **`workflows/local-memory.md`、`local_memory.py`** | **PARTIAL（关键能力实现）** | 有条件持久化已可用；无受授权长期调度与私有连接器；灾备和密钥恢复未生产化 |

**量化对照：D01–D10 共10/10保留；部分实现10/10；不虚报任一专业域完成。** v5.2 仅增强 D01/D03/D09/D10 的指定子能力，不能推断其他6个域自动提高成熟度。

## C. 原始十二状态逐项对照（未更改定义）

| 状态 | 核心责任主体 | v5.2 变化/验证 | 缺口/降级 |
|---|---|---|---|
| `INTAKE` | Host | 可识别用户是否主动要求记忆；默认 memory OFF | 未给授权则按无状态 Skill 完成提问 |
| `CAPABILITY_CHECK` | Host | 判断宿主是否可以访问本地Python/存储/依赖 | 无文件/依赖/许可时退回无状态方式 |
| `FACT_VERIFICATION` | Host + 验证规则 | 保存日期/来源；标记 stale/future | 读取旧事实不代表账户已核验 |
| `JURISDICTION_GATE` | Host 使用官方资料 | 旧法域信息需重新核验时效 | 未核实时 `NOT_VERIFIED` |
| `HOUSEHOLD_SOLVENCY` | Host + Math | 按授权读取历史汇总数据 | 现金与负债仍需新实证核对 |
| `GOAL_AND_LIFECYCLE` | Host | 可保留目标日期/范围 | 大额人生目标变化触发重新规划 |
| `EVIDENCE_RESEARCH` | Host | 可保存短证据ID；不能把存档当最新法规 | 重要来源需要重新访问官方文档 |
| `MACRO_SCENARIOS` | Host + Math | 旧宏观假设不能当新市场报价 | 不自动从当月新闻重配策略 |
| `CANDIDATE_PLANS` | Host | 可保存短规划摘要/状态及假设 | 草稿不能冒充用户确认方案 |
| `DETERMINISTIC_AND_STOCHASTIC_VALIDATION` | Host + optional Math | 模拟/算术模块仍按需可用 | 未校准MC结果不作客观概率 |
| `POLICY_CHECK` | Host | 新增写入授权、隔离文件和安全数据白名单 | 用户授权不能由 `--consent` flag 代替 |
| `EXPLAIN_AND_MONITOR` | Host | 可运行按需 old/new 比较、审计历史、清理和删除 | 未实现自主后台或授权定期监控 |

**状态对照：12/12 名称、顺序、规范保持一致**；与 v0.4 基线无状态机偏离。

## D. 安全/隐私/执行边界

| 原始底线 | v5.2 执行 | 仍有风险 |
|---|---|---|
| L1私有读取、L2写入、L3禁自动交易 | `SKILL.md`, `workflows/local-memory.md`, `memory_cli.py` | CLI flags和校验摘要不验证是否真的由人批准；依赖宿主真实许可流程 |
| 可选本地/私有保存，不上传Git | `default_data_root`, `default_key_root`, `_is_repo_path`, `.gitignore` | 非Git私人目录可被同一OS用户进程读取；云端沙箱不共享本地记忆 |
| 不把真实到账与模拟PF盈利混淆 | `ALLOWED_FACTS` 只允许 `income.monthly_pf_bank_received` | 收款真伪由用户/已授权连接器验证；存档并非凭证 |
| 多币种隔离、元数据记录 | `_fact_valid` 要求 money 有 ISO货币、`as_of`和来源 | 没有自动 FX 折算或跨币种总净值 |
| 避免陈旧法律/市场数据 | `read` stale/future 标记；`SKILL.md`官方来源规则 | 实时法税还是由宿主检索、版本审计 |
| 用户删除 | `forget_field`, `purge`, `delete`；清空派生 free-text 文本 | 无法擦除先前备份、聊天、旧导出；路径锁文件仍可能存在 |
| 禁止自行启动 Agent/后台 | `memory_cli.py` 仅命令行操作 | 真实宿主 E2E 尚未验证，严格标记 NOT_TESTED |

**持久化安全机制：** AES-256-GCM，独立key文件，POSIX私有权限，原子替换、锁与版本控制，无加密库就拒绝明文后退。Windows ACL与Keychain未正式审计。更多见 `docs/LOCAL_MEMORY_SECURITY_v5.2.md`。

## E. 测试与演示记录（本地，2026-10-11）

| 验收项 | 命令/证据 | 结果 |
|---|---|---|
| 保留原始基线SHA | `sha256sum docs/BASELINE_ORIGINAL_v0.4.md` | **PASS** — SHA如上 |
| 结构完整性 | `python tools/check_architecture.py --strict` | **PASS**：10/10专业域、12/12状态、v0.4基线哈希一致 |
| 历史代码回归 | `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | **PASS**：历史46项 |
| v5+架构+记忆回归 | `python -m unittest discover -s tests -p 'test_*.py' -q` | **PASS**：138项（含29项记忆测试与新增架构回归；总计 46+138=184 项） |
| 四城市和跨境PF算术烟测 | `python scripts/wealth_v5.py run --input ...` | **PASS**：深圳、上海、纽约、芝加哥及跨境 PF 共5个虚构案例；仅算术/结构 |
| 多进程记忆回放 | `docs/MEMORY_OFFLINE_DEMO_v5.2.md` | **PASS**：虚构月薪2万→3万、两进程读取、版本比对、删除 |
| JSON Schema 与代码校验 | `schemas/memory-changes-v5.2.schema.json`、`validate_changes` | **PASS**：JSON Schema自检、示例有效和代码校验 |
| 独立 Skill ZIP 可移植 | 临时目录解压，仅基于 Skill 路径运行 `status/init/preview/update/read/delete` | **PASS**：无需仓库根目录，虚构档案加密读写、删除通过 |
| 真正 Codex/Claude Code 联调 | `tests/host_e2e/ACCEPTANCE_MEMORY_v5.2.md` | **NOT_TESTED**，不可冒充成功 |

## F. 偏离审计与剩余风险（不得因功能增加隐藏）

- **新增本地 Python 工具是否偏离 Skill-First？** 否。存储程序只提供可选安全 I/O，不执行LLM推理、互联网搜索、定时任务或资金操作；宿主可不安装它。属于原架构「可选 DB/缓存/私有状态」。
- **性能/可移植性代价：** 启用记忆需 Python 与可选第三方加密依赖，完全隔离的云宿主不能默认访问本地文件；无记忆路径仍可正常完成原有分析。
- **存储边界：** 私有 AES 密文和同一 OS 用户可读的密钥只是局部保护，非硬件安全模块，不能承诺设备中毒下安全；文件导出和宿主对话记录可能泄漏个人信息。
- **潜在监管与财务可信性：** 长期资产收益/全球税务的原有缺口仍然存在，记忆不会提升研究本身的正确性。
- **架构唯一基线：** 原始 v0.4 原文及SHA不可静默更改；任何新功能必须继续满足10领域、12状态和L0—L3批准边界。

## G. 后续优先任务（限于证据与需求驱动）

1. 在**真实本地** Codex和Claude Code中执行 `ACCEPTANCE_MEMORY_v5.2.md` 并保留经脱敏的工具调用与授权记录（不能用模拟 CLI 冒充）。
2. 对 Windows/macOS 存储ACL、密钥系统、并发访问、跨会话安全进行独立验证；必要时改为宿主支持的OS keyring/用户私有加密管理。
3. 增加用户可配置保留期、合法安全的迁移/备份/恢复和跨环境加密同步（默认关闭，逐项独立授权）。
4. 按最初业务域继续推进税务、长期投资模型与概率校准；本次没有跳过这些仍缺失的原始承诺。

**发布结论：本次离线结构、单元、五场景、独立Skill打包验证均通过，允许以“Developer Preview + 本地记忆功能离线验收通过/真实宿主未测”交付。不得称生产级加密保险库或自主金融顾问。**
