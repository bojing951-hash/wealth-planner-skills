"""Conservative human-facing markdown summary for the v5 developer preview."""

def one_line(value):
    return str(value).replace('\r',' ').replace('\n',' ').replace('|',' / ')[:2000]


def render_md(r:dict) -> str:
    rows=[
        '# Wealth Planner Skill v5 — 条件性个人财富研究报告',
        '',
        f"- 用户ID: `{one_line(r['profile_id'])}` | 日期: {r['as_of']} | 报告ID: `{r['run_id']}`",
        '- 类型：**开发预览版；不构成具有法律效力的税务、法律或投资建议。**',
        '- 数据：用户声明/虚构案例；未独立审计。名义收入、银行到账、PF虚拟余额、养老金资产不得混算。',
        '', '## 1. 现金流与财务安全',
        '| 币种 | 月已到账净额（自述/假设） | 月支出 | 条件月结余 | 应急缺口 | 状态 |',
        '|---|---:|---:|---:|---:|---|',
    ]
    for cur,b in r['financial_snapshot']['currency_buckets'].items():
        rows.append(f"|{cur}|{b['monthly_bank_received_user_reported']}|{b['monthly_expenses']['total']}|{b['monthly_surplus_conditional'] or '不可计算'}|{b['reserve_shortfall_declared']}|{b['cashflow_status']}|")
    rows.extend(['','## 2. 法域与税务研究'])
    for issue in r['legal_tax_triage']['research_issues']:
        rows.append(f"- [{issue['severity']}] **{issue['code']}**：{one_line(issue['research_question'])}")
    rows.append('- 尚无经逐条实质验证的现行法域税额计算；不得把香港收款或跨境账户推定为免税。')
    rows.extend(['','## 3. 循证理论：仅有条件适用'])
    rows.append('本次主题：'+', '.join(r['evidence_assessment']['topics']))
    rows.append('关联理论：'+', '.join(x['id'] for x in r['evidence_assessment']['principles']))
    for i in r['evidence_assessment']['relationships'][:6]:
        rows.append(f"- {i['pair'][0]} vs {i['pair'][1]}：{one_line(i['conditional_resolution'])}")
    rows.extend(['','## 4. 宿主能力自主调度（须由宿主执行）'])
    rows.append(f"- 待宿主调用工具任务：{r['host_action_queue']['ready_count']}；已收到来源元数据：{r['host_action_queue']['completed_metadata_count']}。来源元数据≠内容及法律适用性核验。")
    rows.extend(['','## 5. 数学研究及长周期情景'])
    if 'portfolio_research' in r:
        pp=r['portfolio_research']
        rows.append(f"- 用户假设组合：加权费用比率 {pp['weighted_expense_ratio_only']:.4%}，假设加权净收益近似 {pp['assumed_net_of_expense_ratio_approximation']:.4%}；未校准期望收益或税费。")
    if 'hypothetical_tax_math' in r:
        tt=r['hypothetical_tax_math']
        rows.append(f"- **虚构税档算术**：{tt['currency']} {tt['illustrative_annual_net']} / 年；禁止将其写成当地税务结论。")
    ss=r['long_horizon_scenarios']
    if 'scenarios' in ss:
        rows.append(f"- 期限：{ss['horizon_years']}年；币种 {ss['currency']}；每情景路径 {ss['paths_per_scenario']} 条；随机种子 {ss['seed']}。全部宏观/收益参数均由用户设定。")
        rows.append('|情景|期末名义资产中位数|期末起始年份购买力中位数|样本5%分位|路径破产比例|')
        rows.append('|---|---:|---:|---:|---:|')
        for name,x in ss['scenarios'].items():
            rows.append(f"|{one_line(name)}|{x['final_nominal_median']:,.0f}|{x['final_real_today_median']:,.0f}|{x['final_nominal_p05']:,.0f}|{x['ever_insolvent_paths_fraction']:.1%}|")
        for name,x in ss['scenarios'].items():
            for g in x['goals']:
                v=g['success_probability_conditional']
                rows.append(f"- `{name}` / 目标 `{one_line(g['goal_id'])}`：" + ('无法计算净资产目标达成率（债务路径未建模）。' if v is None else f'模型内目标达成比例 {v:.1%}（**并非真实预测概率**）。'))
    else:
        rows.append('- 未执行长期预测：缺少明确的收益率、通胀、波动率等情景假设。')
    if 'goal_feasibility_math' in r:
        rows.extend(['','### 目标可行性（固定收益率数学恒等式，不是投资预测）'])
        rows.extend(['| 情景 | 目标 | 距离目标（月） | 理想条件需月投入 | 当前条件月结余 | 应急缺口未纳入 |','|---|---|---:|---:|---:|---:|'])
        for row in r['goal_feasibility_math']['rows'][:12]:
            rows.append(f"|{row['scenario']}|{row['goal']}|{row['months']}|{row['required_monthly_contribution_ideal']:,.0f}|{row['conditional_monthly_cash_surplus']:,.0f}|{row['initial_emergency_reserve_shortfall_not_included']:,.0f}|")
    if r.get('model_consistency_warnings'):
        rows.append('### 假设一致性提醒')
        for note in r['model_consistency_warnings'][:8]:
            rows.append(f"- {note['scenario']}：{note['type']}。检查组合与情景收益/波动的假设口径。")
    if 'fi_screen' in r:
        fi=r['fi_screen']
        rows.append(f"- FI资本筛查：按照假设初始提款率 {fi['assumed_initial_withdrawal_rate']:.2%}，参考资产 {fi['fi_reference_capital']:,.0f}（不是安全退休保证）。")
    rows.extend(['','## 6. 动态复核'])
    if 'change_detection' in r:
        d=r['change_detection']
        rows.append(f"- {d['status']} / 需要重新规划：{d['replan_required']}")
        for e in d['events']:
            rows.append(f"- {e['type']} [{e['importance']}]：{one_line(e.get('reason',e.get('currency','')))}")
    else:
        rows.append('- 未提供前次报告；不声称已自动监控或运行计划任务。')
    rows.extend(['','## 7. 决策阻断和下一步'])
    for a in r['conditional_policy_queue'][:12]:
        rows.append(f"- [{a['priority']}] {a['category']} / {a['status']}: {one_line(a['why'])}")
    rows.extend(['','## 8. 计算审计',
                 f"- 原始输入SHA256: `{r['audit']['original_input_sha256']}`",
                 f"- 版本：{r['skill_version']}；财经估计未包含税法实质审核、未知跨境义务、尾部风险等。",
                 '- 用户本人决定是否采纳和执行；高影响外部行动须另行明确授权。',''])
    return '\n'.join(rows)
