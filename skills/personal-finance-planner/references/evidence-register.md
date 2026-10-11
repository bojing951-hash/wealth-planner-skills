# 证据登记表 / Evidence register

Version 0.2.0 · checked as starter citations in October 2026. Sources should be independently rechecked when the user requests current figures, market data or legal advice. This file does **not** import current interest rates or market histories.

| 主题 | 类型 | 核心观点 | 转化为 Skill 规则 | 边界 / 不可推出 |
|---|---|---|---|---|
| 多元化（Markowitz, 1952） | 数学 + 历史上广泛研究 | 投资组合方差 = wᵀΣw，单资产波动不足以描述组合风险 | 关注相关性、集中度与组合风险 | 历史相关性并非固定；极端时可能趋同 |
| 主动投资算术（Sharpe, 1991） | 数学恒等与成本逻辑 | 总体主动管理成本前是市场的另一面，较高成本降低整体成本后收益 | 比较全成本，避免仅看超额收益宣传 | 不意味着每一个主动策略每一期都差 |
| 低成本、均衡、纪律（Vanguard） | 研究与实践框架 | 分散、成本、长期计划对于普通投资者重要 | 默认分析费用和投资期限 | 不保证任何指数正收益 |
| 自动储蓄（Thaler & Benartzi, 2004） | 特定情境实证 | 预先承诺有助于提高参与者储蓄率 | 用户授权下可建议规则式分账 | 实验参与者结果不等于所有用户的因果效果 |
| 退休提款率（Bengen 等） | 美国历史回测 + 假设 | 提款率受期限、配置、市场路径影响 | 仅使用财务自由数值作初筛，须压力测试 | 4%/3.5%非普适安全年利率，更非无风险收益 |
| CFP Board 财务规划实践流程 | 行业职业标准 | 明确目标、了解情况、评估并持续复核 | 先核事实、建方案、再定期检查 | 职业标准不等于收益保障 |
| 现金储备 6/12 个月 | **启发式** | 收入更不稳定者一般需更大的流动性缓冲 | 作为可修改的默认值 | 不存在精确普适最优月数 |
| 高息债提前还款阈值 8% | **启发式** | 债务成本较高时，优先检查提前还款 | 作为模型的示例触发线 | 不是法规、统计结论，须考虑利率、罚金、税务、信用 |
| -2%/+5%/+8% 年化收益 | **情景假设** | 用不同收益假设检查算术敏感性 | 明确标注情景而非预测或成功概率 | 不代表资产组合未来分布 |

## Primary / authoritative sources

- Harry Markowitz (1952), *Portfolio Selection*: https://doi.org/10.1111/j.1540-6261.1952.tb01525.x
- William F. Sharpe (1991), *The Arithmetic of Active Management*: https://doi.org/10.2469/faj.v47.n1.7
- Richard H. Thaler & Shlomo Benartzi (2004), *Save More Tomorrow*: https://doi.org/10.1086/380085
- Vanguard Principles for Investing Success: https://corporate.vanguard.com/content/corporatesite/us/en/corp/about-our-funds/how-we-invest/principles-for-investing-success.html
- CFP Board Practice Standards: https://www.cfp.net/ethics/compliance-resources/2020/01/financial-planning-and-application-of-the-practice-standards-for-the-financial-planning-process
- SPIVA active vs passive data (region- and period-specific; not hardcoded): https://www.spglobal.com/spdji/en/spiva/
- For retirees and withdrawal risks, use dated primary/technical reports rather than repeating a slogan; record methodology and geographic assumptions.

## Evidence labels for user-facing reports

- **[MATHEMATICAL]**: identity, accounting arithmetic or formula, conditional on defined inputs.
- **[EMPIRICAL]**: research or historical observation, specify place, years and population.
- **[HEURISTIC]**: useful planning convention; explicitly adjustable.
- **[SCENARIO]**: hypothesis only, no implied frequency/probability.
- **[REGULATORY]**: requires applicable jurisdiction and fresh government or professional verification.

Do not infer risk tolerance from a large nominal income. Assess liquidity, economic exposure, horizon, and ability to survive drawdowns separately.

## v0.2 扩展资料

完整的“理论/观测/决策/失效条件”参见 `references/theory-to-policy.md`；长期实际利率、估值、通胀与10/20年期限匹配参见 `references/long-horizon-macro.md`。必须将实时宏观指标与未来长期收益情景**分开存储、验证和表述**。
