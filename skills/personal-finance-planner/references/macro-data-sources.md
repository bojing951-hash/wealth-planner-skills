# 可追溯的宏观数据与预测源登记

使用前检查官方定义、频率、最新日期及使用条款；**名单不是实时值，也不授予爬取权限**。

| 主题 | 机构与官方地址 | 建议系列/口径 | 限制 |
|---|---|---|---|
| 美国10年名义国债收益率 | FRED（美联储H.15来源） https://fred.stlouisfed.org/series/DGS10 | `DGS10`，年化百分比，日频 | 到期收益率，不是长期无波动投资回报 |
| 美国10年TIPS实际收益率 | FRED https://fred.stlouisfed.org/series/DFII10 | `DFII10`，年化百分比，日频 | 美元通胀保护工具；估值、期限、流动性与跨境币种限制 |
| 美国10年盈亏平衡通胀 | FRED https://fred.stlouisfed.org/series/T10YIE | `T10YIE`，年化百分比，日频 | 含通胀风险溢价等因素，非纯预期 |
| 长期均衡/自然实际利率 r-star | 纽约联储LW/HLW估计 https://www.newyorkfed.org/research/policy/rstar | 模型估计的均衡短期实际利率（不是投资品种收益率） | r-star并非TIPS10Y实际收益率，也不是市场可锁定的10年收益 |
| 美国CPI | BLS/FRED https://fred.stlouisfed.org/series/CPIAUCSL | CPI指数（不是百分数）；同比应由同口径12个月数据计算 | 历史同比≠未来10年通胀预期 |
| 中国人民币国债收益率 | 中央国债登记结算公司 https://yield.chinabond.com.cn/cbweb-cbrc-web | 10年中国国债曲线，年化百分比 | 人民币名义收益率；需记录估值日与曲线口径 |
| 中国CPI | 国家统计局 https://www.stats.gov.cn/ | 当期和同比CPI，按发布当日口径 | 注意指数换基、分类和发布修订；不是长期预期 |
| 长期通胀/增长预测 | IMF WEO https://www.imf.org/en/Publications/WEO | 中期预测，报告年/季度，统计口径 | 预测通常远短于20年；不得假定“IMF已预测20年” |
| 市场长期回报情景 | Vanguard VCMM https://corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html | 10/30年区间与分布、报告发布日期、美元名义投资收益 | 预测非承诺；常未扣税/费、人民币汇率与家庭支出通胀 |
| 估值长期解释 | Campbell & Shiller/NBER https://www.nber.org/papers/w8221 | 长期估值和收益的研究，不是实时交易价格接口 | 不把统计关系当精确择时公式 |

## 开放数据/自动检索边界

- 如果宿主支持 web、可靠 API 或 MCP，优先通过宿主检索并录入带来源的观测值；自动脚本是可选适配器。
- `scripts/fetch_fred.py` 可以在**用户允许联网**且运行环境可以访问 FRED CSV 时取得上面三个美国宏观序列的最新可用观测值，不需读取任何个人财务数据。它**不**自动抓取中国数据或改变投资假设。
- FRED CSV只是数据访问途径，不代表可随意再分发底层序列；尊重来源的数据政策、请求频率及版权。
- 下载失败/源不可访问→报`data_unavailable`；无真实数据时只能运行明确标注的示例假设，不能编造当前利率或默认填0。
- 自动检索不是自动**后台监控**；Skill仅在宿主执行任务时运行，要定期主动执行须额外授权调度服务。
