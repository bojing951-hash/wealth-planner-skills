# 数学模型约定（v0.1）

## 1. 数据的所有权与口径

- `monthly_cash_receipts`: 当月用户实际拥有、已经到账的现金流；对于需自行缴税的人，可以是缴税前到帐，但必须另提供税务备付以防多算可投资金额。用户自己声明，并非本软件联网验证。
- `financial_assets`: 所有个人**金融**资产市值（现金+其他可估值金融资产；不包括PF名义账户额度、模拟利润或自住房）。
- `liquid_cash`: 金融资产中的流动现金子集，必须 <= `financial_assets`。
- `outstanding_debt`: 期初金融负债本金；期初净金融资产 = `financial_assets - outstanding_debt`。

## 2. 月度现金流

`monthly_surplus = cash_receipts - essential - discretionary - required_business_cost - tax_reserve - required_debt_payment`

月度收入中断月份将 cash_receipts 视为0， discretionary 按指定系数缩减（默认0）。模拟中的“额外经常性净现金流”不受该中断假设影响，仅用于比较目标差额，不能当成可获得的现金。

## 3. 现金储备

`emergency_target = (essential + required_business_cost + due_debt_payment) × emergency_months`

默认稳定工资6个月、不稳定收入12个月，均属于启发式，可修改。高息债情景的先行储备默认2个月，付清高息债后再补齐全额储备。部分期初富余现金会被“假定重新配置”；真实操作需要用户另行授权。

## 4. 投资复利与负债演变

`monthly_return = (1 + annual_net_return) ** (1/12) - 1`

每月先对上月的投资资金应用收益，再入账月末的现金流、最低债务支付、分配到现金储备和长期投资。**平滑月收益仅是数学假设**。

`interest_m = debt_(m-1) × annual_debt_rate / 12`

`debt_m = max(0, debt_(m-1) + interest_m - scheduled_payment_m - optional_extra_repayment_m)`

`net_worth_m = cash_m + invested_m - debt_m`

如果现金与投入资金均耗尽，记录第一个“无法覆盖的现金缺口月份”；负现金表示尚未融资的缺口。不会自动创造借款。

## 5. 三情景与购买力

当用户基准收益假设为5%时，三情景参数为-2%、5%、8%年化净投资收益；若用户调整基准收益假设，悲观情景=基准-7个百分点（下限-95%）、乐观情景=基准+3个百分点。它们**不是预测、历史分位数或概率**。

`today_money = nominal_future_net_worth / (1 + annual_inflation_assumption) ** years`

## 6. 目标差额计算

以二分搜索寻找最小非负 `extra_monthly_cashflow`，使得用户当前支出和收入情景不变时，月度模型在目标期末满足 `ending_net_worth >= target_net_worth`。

输出的是**额外可用净现金流需求**，没有计算为了获得这些净现金流可能需要的税前金额、社保、PF平台成本等。

## 7. 在开发下个版本前不得声称具备的能力

- 收益顺序风险／随机抽样模拟／目标成功概率。
- 多币种FX历史模拟、合规税务识别、具体证券推荐。
- 退休领取养老金和年金现金流。
- 存贷款全面定价或实际债务合同分析。


## v0.2 跨10/20年名义财富、实际购买力和宏观假设

- 月投资回报：`r_m=(1+r_annual_net)^(1/12)-1`；期间每月固定，是纯情景而非真实行情路径。
- 每月必要与可选消费：`spending_m=(spending_0)*(1+inflation_annual)^((m-1)/12)`；名义工资：`income_m=income_0*(1+nominal_income_growth_annual)^((m-1)/12)`。
- 期末实际购买力：`real_end_wealth=nominal_end_wealth/(1+inflation_annual)^years`。必须区分家庭支出通胀与统计局CPI。
- 宏观Fisher关系：`(1+nominal)=(1+real)*(1+expected_inflation)`只在同币种同期限同计量时适用。`US_DGS10 - US_DFII10`近似美国美元10年Breakeven，不等于纯预期通胀；不能用中国CPI过去同比替代未来10年预期通胀。
- 期限重配：10年中国国债到期收益率最多用于同期限名义债券收益的参考，直接将其固定滚动至20年不成立；目前只做10年收益率相对长期通胀*情景*的购买力敏感性。
- 收入和市场共振、市场回报序列、现金流日期、保险/税费及多币种FX尚未全部建模。三条情景**没有概率意义**。
