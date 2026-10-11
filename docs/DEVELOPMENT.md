# Wealth Planner Skill v5.1.0 — 以最初架构为唯一基线的 Skill-First 重构

**产品形态**：安装给 **Codex / Claude Code** 等宿主 Agent 使用的循证个人财富规划 **Skill**，不是第二套Agent或自动运行的投资平台。宿主负责推理、外部资料研究、执行工具；Skill规定经济学/金融学/行为金融/税法/法律/生命周期规划的研究和决策流程；可选 Python 仅做可复算数学。项目仅供研究/教育与决策支持，不构成已核定的税务、律师或持牌投资意见。

**最高架构约束**：原始《总体架构与能力缺口》v0.4 规划稿，完整原文存于 [docs/BASELINE_ORIGINAL_v0.4.md](docs/BASELINE_ORIGINAL_v0.4.md)。每次发布**必须**交付逐项对照报告；本次报告：[docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md](docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md)。

## v5.1 到底修正了什么？

上一版 v5.0 的宿主任务清单、理论规则图和数学代码已经存在，但容易被理解成由 Skill 自己执行研究。**本版把 Skill 恢复为“专业知识 + 决策规则 + 执行指导”，不再要求先运行自有 `host-queue`**。宿主直接根据当前的实际工具和权限开展研究；可选脚本仅用于重现计算与检查数据。不因为自带 132 项旧测试，就宣称真正通过 Claude/Codex 客户端测试。

```
用户 → Codex / Claude Code（宿主真正执行）
               ↓ 加载
       personal-finance-planner / SKILL.md
         ├─ 十大专业模块的条件性研究规范
         ├─ 十二状态工作流 + 法税/现金硬门槛
         ├─ 金融理论/经典书籍 + 命题级循证冲突流程
         ├─ 宏观慢变量与长周期情景方法
         ├─ 自主使用宿主现成能力的工具协议
         ├─ 动态复核规则（宿主具备调度才可周期运行）
         └─ 可选确定性计算辅助程序
               ↓
   官方来源（若宿主真的检索到）+ 假设计算（若可运行）
               ↓
          可靠性与约束检查 → 有条件的财务方案
```

## 安装：复制完整 Skill 文件夹

- Codex 用户级：`~/.agents/skills/personal-finance-planner/`
- Claude Code 用户级：`~/.claude/skills/personal-finance-planner/`

**请复制整个 `skills/personal-finance-planner/` 文件夹，而不是只复制 `SKILL.md`。** 具体目录以宿主当前官方文档和实际版本为准。安装之后可以说：

> 使用 personal-finance-planner 研究我在深圳、税后月收入2万元的10年财富规划。请先按我的财务目标和现金储备识别缺失信息；必要时查官方法税，分析相关金融理论冲突，使用宿主已有的 Python 计算并验证。不要猜测最新政策或把情景概率当作真实概率。

## 运行方式

**默认：不需要启动任何本地 CLI**。宿主读取 `SKILL.md`、选择最小相关工作流、调用本身实际可用的工具。无 Python 时，仍可执行定性研究和条件规划，并标明数理限制。

**可选：仅当需要重复验算的本地算术**，Python 3.10+：

```bash
python3 skills/personal-finance-planner/scripts/wealth_v5.py validate --input skills/personal-finance-planner/examples/v5-shenzhen.json
python3 skills/personal-finance-planner/scripts/wealth_v5.py run --input skills/personal-finance-planner/examples/v5-shenzhen.json --format md
```

这些演示使用**虚构数据**；`run` 不查询真实法规、市场数据或账户。旧 `host-queue` 可作开发调试，不是 AI 自主工具调用的实现。

## 关键约束与限制

- 银行收到的实际收入、工资税前收入、PF模拟利润、持仓名义资金、养老金/公积金与本人可用净金融资产严格区分；币种未经有日期的 FX 不可合并。
- 司法辖区必须具体到可能涉及的国家/州/省/市及税年；不能因香港收款就认定内地免税。没有核实当前法律就不计算“真实精准税额”。
- 历史收益、常态市场假设、贝叶斯/随机模型、实证论文与法律规定不能混为一种“科学证据”。随机模拟没有校准时只描述**假设条件下的路径**。
- **不自动交易、转账、开户、报税、上传个人银行记录或启动后台监控。** 连接只读银行服务、私有保存和定时运行均必须由宿主能力与用户授权支持。
- **真实 Claude Code/Codex 端到端联网调用：尚未验收。** 本项目当前为 Developer Preview。

## 开发后的强制对照流程

```bash
python3 tools/check_architecture.py --strict
python3 -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

`tools/check_architecture.py` 只检查原始基线 SHA256、十模块/十二工作流结构、Skill链接和发布对照文件；不能代替实际投资、税法、模型正确性和客户端 E2E 评审。

- [每次必须执行的发布审查](docs/DEVELOPMENT_RELEASE_GATE.md)
- [v5.1 逐域/逐阶段差异报告](docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md)
- [本次测试日志](docs/TEST_REPORT_v5.1.md)
- [持续存在的缺口](docs/MATURITY_AND_GAPS.md)
- [真实宿主 E2E 待测清单](tests/host_e2e/ACCEPTANCE_v5.1.md)

**兼容性**：v5 CLI 的模型 JSON schema 标识仍为 `5.0.0`（有意保持输入兼容）；**Skill 发布版本为 `5.1.0`**；可选计算模块自身代码版本仍 `5.0.0`。两者是不同版本维度。

MIT 许可。开源仓库只放研究规范、代码和合成示例，**不放真实财务资料**。尚未推送 GitHub。
