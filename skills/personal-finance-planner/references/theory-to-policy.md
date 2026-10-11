# 从理论到可执行规则：证据分级与反例

> 规则不是大师语录。每次给建议先回答：**决策是什么 → 理论机制 → 可观测变量 → 可运行检验 → 适用边界 → 最终是事实还是政策假设？**

| 理论/人物 | 证据层级与机制 | Agent 执行规则 | 输入/数学验证 | 不适用或待验证情形 |
|---|---|---|---|---|
| Franco Modigliani：生命周期假说（Life-cycle hypothesis） | 消费和储蓄应跨生命阶段权衡（经济模型＋实证，模型假设非定律） | 按年龄、可预见转折、收入周期、社保、家庭责任设计10–30年消费与储蓄路径 | 多期现金流、未来负债、退休现金缺口、现值 | 信贷约束、收入不确定、遗产动机、健康/家庭冲击使平滑消费难以执行 |
| Harry Markowitz（1952）：投资组合选择 | 投资组合方差 = wᵀΣw（有前提的数学模型） | 看全球/国内股票、利率、信用、黄金、就业收入之间的相关暴露；先决定承受何种风险，再选产品 | 权重、协方差、波动和极端情景；长期模型不只依赖正态分布 | 未来相关性突变、尾部风险、未建模的流动性/政策风险 |
| William Sharpe（1991）：主动管理算术 | 总体主动投资的持仓构成与市场一致；费用让整体成本后表现变差（整体算术，不针对个人） | 总费用对比：管理、交易、税、价差、溢价、换汇 | 税费净收益差额，10/20年费用敏感性 | 不能断言某只主动基金必然跑输，也不能推导任何投资者都必须被动投资 |
| John Bogle / Vanguard：分散、低成本、纪律 | 长期投资实践原则 + 成本恒等式 + 大样本实证 | 主动给低维护成本候选，保护自动定投、年度复核 | 总拥有成本、换手率、跟踪误差、长期持有成本 | 不保证指数长期正收益，也不意味着单一国家集中投资等于全球分散 |
| Richard Thaler / Shlomo Benartzi（2004）：Save More Tomorrow | 预先承诺未来加薪储蓄的行为金融实证 | 用户授权时建议收入到账后的自动分账与加薪储蓄率调整 | 实际存款率、执行率、消费波动 | 不能把研究样本的储蓄率变化当成个体承诺收益 |
| William Bengen（1994）：初始退休提款率 | 特定美国股票债券历史区间和假设下的退休历史模拟 | 提款率作早期筛选，最后用通胀、税费、寿命、收益顺序、人民币支出做动态提款压力测试 | 目标资产=年净支出/初始提取率（只作粗筛）；提款路径模拟 | 4%不是永远安全的年利率，也不是中国人民币组合的已验证常数 |
| CFP Board 财务规划实践标准 | 职业流程规范（不是市场收益的科学证明） | 建立事实→明确目标→分析选择→建议→实施协同→复核 | 输入完整率、证据日志、月度可执行任务 | 不能代替所在司法管辖区的执业资质和适当性监管 |
| Robert Shiller / John Campbell：估值与长期收益 | 估值倍数对较长持有期回报的信息量高于短期，但仍有很大误差 | 把估值用于10年情景上下限和股票风险溢价检验，不用于月度择时 | CAPE/盈利收益率/股息率/增长率与市场一致币种，历史稳健性对照 | 估值高 ≠ 下个月跌；不得从单一CAPＥ给出精确10年收益或买卖指令 |
| Fisher 方程/实际购买力 | (1+名义收益)=(1+实际收益)(1+通胀)（价格指数口径匹配） | 同时输出未来名义资产和按规划通胀折算的今天购买力 | 精确复合公式而不是只用名义-通胀近似 | 美国TIPS不是无对冲人民币无风险利率；名义10年国债收益减当月CPI同比不是10年预期实际利率 |
| 资产负债匹配（ALM） | 金融学和精算学的现金流期限与风险匹配 | 0–3年支出优先流动性与本金风险控制；10年以上长期资金再考虑增长类投资 | 分桶、到期现金流与压力情景 | 极端资产组合优化不能弥补短期流动性缺口 |

## 证据用法（必须）

1. **数学恒等式**不等于**投资回报预测**；**研究总体结论**不等于**某个用户的最优解**。
2. 输出每项重大建议时，写明来源/年份、机制、用户的相关变量、可证伪指标、例外条件。
3. 来源真实性、方法细节或适用地区不明确时，降级为`[HEURISTIC]`或`[UNVERIFIED]`，不能声称“科学证明”。
4. 投资大师之间意见有冲突时，不要投票，按证据强度、期限、约束条件和用户偏好做决策；可给备选方案。
5. 若声称长期超额收益，要求样本外检验、费用和税后比较，防止选择性回测。

## 原始来源（用户需要时，应动态复核）

- Modigliani 生命周期假说，1985 Nobel Lecture: https://ideas.repec.org/p/ris/nobelp/1985_001.html
- Markowitz 经济学奖官方介绍: https://www.nobelprize.org/prizes/economic-sciences/1990/press-release/
- Sharpe《The Arithmetic of Active Management》: https://doi.org/10.2469/faj.v47.n1.7
- Thaler & Benartzi (2004): https://doi.org/10.1086/380085
- Campbell & Shiller (2001): https://www.nber.org/papers/w8221
- Vanguard Principles: https://corporate.vanguard.com/content/corporatesite/us/en/corp/about-our-funds/how-we-invest/principles-for-investing-success.html
- Vanguard long-term capital market assumptions (watch date, currency, fees): https://corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html
- CFP Board planning process: https://www.cfp.net/ethics/compliance-resources/2020/01/financial-planning-and-application-of-the-practice-standards-for-the-financial-planning-process
