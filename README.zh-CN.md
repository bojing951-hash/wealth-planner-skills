# Wealth Planner Skills v5.1.0｜架构回归版

这是一个**安装到 Codex / Claude Code 的专业财务规划 Skill**，不是自行运行的 Agent，更不是已经验证的跨国税务申报系统。

**职责划分：**

- **宿主 Agent**：使用其现实可用、获授权的搜索/浏览、文献阅读、文件分析、计算工具和安全连接器；执行完整研究并向用户解释。
- **Skill**：定义十个专业财务域、十二个工作流状态、法律与现金安全硬约束、理论证据与冲突处理、长期宏观研究、工具调用权限及报告规范。
- **可选脚本**：只做可复算的财务数学、数据校验和条件情景模拟。不是额外的 Agent，不会独立联网或交易。
- **外部来源**：当前有效法条、税局数据、原始论文、中央银行/监管机构及合法可访问的金融数据，由宿主查找并核验。

## 本次核心变更

v5.1 保留了 v5.0 的必要算术工具，但将**宿主自主研究**恢复为默认流程。原 `host-queue` 只属于可选开发/兼容工具，不是每次分析必须经过的独立调度器。

**架构基线不可静默修改：**`docs/BASELINE_ORIGINAL_v0.4.md`。每次发布必须附上逐项对照报告（`docs/ARCHITECTURE_ALIGNMENT_v版本号.md`），检查十个业务域、十二个状态、四类权限、财务/法税/证据边界、测试和未完成项。

## 安装

复制 `skills/personal-finance-planner/` 整个目录：

- Codex：`~/.agents/skills/personal-finance-planner/`
- Claude Code：`~/.claude/skills/personal-finance-planner/`

Skill 在当前宿主实际有工具和权限时才可以调用，安装 Skill 并不会安装外部金融账户接口或创建后台任务。

## 开发/验收

```bash
python3 tools/check_architecture.py --strict
python3 -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

**现状：Developer Preview。** 部分地区税法的实际税负计算、校准的投资风险模型、真实 Codex/Claude Code 端到端调用、用户授权连接器及后台监控尚未完成，不以现有代码测试替代专业法律税务校验。

阅读：[`逐项架构对照`](docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md)、[`开发发布门禁`](docs/DEVELOPMENT_RELEASE_GATE.md)、[`完整英文说明`](README.md)。
