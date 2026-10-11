"""Human-readable summary of the v0.4 auditable plan contract."""


def _clean(v) -> str:
    return str(v).replace('\r', ' ').replace('\n', ' ').replace('|', ' / ')


def render_markdown(report: dict) -> str:
    lines = [
        '# Evidence-Based Wealth Planner — v0.4',
        '',
        f"- 日期：{_clean(report['as_of'])}；用户画像：`{_clean(report['profile_id'])}`",
        f"- 运行 ID：`{report['run_id']}`；宿主：`{_clean(report['host']['name'])}`",
        '- 注意：本报告对收入与生活费做条件计算；不是纳税核定、法律意见、证券指令或未来收益预测。',
        '', '## A. 财务快照（原币种独立，不自动换汇）',
        '| 币种 | 已到账月收入（声明/假设） | 月支出含债务 | 条件月结余 | 应急储备缺口 | 流动资产 | 状态 |',
        '|---|---:|---:|---:|---:|---:|---|',
    ]
    for cur, b in report['financial_snapshot']['currency_buckets'].items():
        lines.append('| ' + ' | '.join((cur,
                    b['monthly_bank_received_user_reported'],
                    b['monthly_expenses']['total'],
                    b['monthly_surplus_conditional'] or '不可计算',
                    b['reserve_shortfall_declared'],
                    b['liquid_cash_and_liquid_investments_declared'],
                    b['cashflow_status'])) + ' |')
    for warning in report['financial_snapshot']['warnings']:
        lines.append('- ⚠ ' + _clean(warning))
    lines.extend(['', '## B. 司法辖区研究（含城市层级）'])
    for obj in report['jurisdiction_map']:
        lines.append(f"- `{obj['scope']}` — {', '.join(obj['roles'])}")
    lines.extend(['', '## C. 宿主工具执行清单（只生成计划，未假装联网）',
                  '| 任务 | 能力要求 | 状态 |', '|---|---|---|'])
    for a in report['requested_host_actions']:
        lines.append('| ' + ' | '.join((_clean(a['id']), ', '.join(a['requires']), a['state'])) + ' |')
    lines.extend(['', '## D. 已收到的来源元数据（不是法律适用性确认）'])
    if report['host_action_receipts']['items']:
        for receipt in report['host_action_receipts']['items']:
            lines.append(f"- `{receipt['action_id']}`: `{receipt['state']}`; {receipt.get('url', '无有效来源')}")
    else:
        lines.append('- 无。尚未执行真实宿主资料检索；不可声称已查验现行税法、实质利率或市场数据。')
    lines.extend(['', '## E. 12 阶段执行状态'])
    for s in report['workflow']:
        lines.append(f"- {s['name']}: **{s['status']}**")
    lines.extend(['', '## F. 决策阻断与待核实事项'])
    for s in report['blocked_decisions']:
        lines.append('- [阻断] ' + _clean(s))
    for s in report['missing_facts']:
        lines.append('- [待核实] ' + _clean(s))
    lines.extend(['', '## G. 后续复核触发条件'])
    for s in report['monitoring_triggers']:
        lines.append('- ' + _clean(s))
    lines.extend(['', '## H. 审计信息',
                  f"- 数据摘要 SHA256：`{report['audit']['input_sha256']}`",
                  f"- 工具声明 SHA256：`{report['audit']['capabilities_sha256']}`",
                  '- v0.4 仅提供工作流协调协议、地区路由与确定性的条件现金流计算。',
                  '- 税额、地区法律适用、概率模拟、实际下单/转账均未实现。', ''])
    return '\n'.join(lines)
