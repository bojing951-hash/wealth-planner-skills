# 五个虚构案例：相同 Skill 的跨法域和风险分桶验收

**提醒**：以下2026净收入是人为输入的情景，不是当地法定税费试算。20年投资结果为未经市场数据校准、由模拟参数生成的虚构数值；概率是模型内比例，不是现实达标可能性。

|城市|币种|假设月净到账|月支出|月条件结余|20年后基准情景购买力中位数|模型内目标达标比例|税务情况|
|---|---|---:|---:|---:|---:|---:|---|
|shenzhen|CNY|15,800|9,750|6,050|1,786,239|93.2%|PROVISIONAL_TAX_UNVERIFIED|
|shanghai|CNY|15,700|11,950|3,750|1,128,824|61.7%|PROVISIONAL_TAX_UNVERIFIED|
|new-york|USD|12,800|7,150|5,650|1,577,256|88.8%|PROVISIONAL_TAX_UNVERIFIED|
|chicago|USD|13,700|5,500|8,200|2,294,437|98.7%|PROVISIONAL_TAX_UNVERIFIED|

**注意比较限制**：不同币种不直接比较绝对金额、净资产、福利及生活购买力。人民币工资2万元与美元工资2万元不具有收入水平可比性。净到账预扣税不等于最终法定义务。

**CN/HK/PF 核心测试**：另见 v5-cn-hk-pf.json 和 v5 跨境报告，必须隔离模拟账户余额、用户真正拥有的资金与不同币种金额；跨境所得性质/实际税务没有核定。

**代码指令**：`wealth_v5.py run --input examples/v5-<city>.json --assumptions examples/v5-scenarios-<currency>.json --format md`。
