#!/usr/bin/env python3
"""Offline cross-border research preflight + optional conservative CNY scenario.

Deliberately separates binding-law verification from deterministic financial math.
No taxes, remittances, investment trades, or filings can be performed.
"""
import argparse
import json
from pathlib import Path

from jurisdiction_router import read_json, route_case
from theory_adjudicator import reconcile_case
from planner import build_report as build_cashflow_report
from long_horizon import build_long_horizon_report


def build_report(case, financial_profile=None, macro_snapshot=None, allow_hypothetical=False):
    legal = route_case(case)
    report = {
        'workflow_version':'0.3.0',
        'legal_tax_preflight':legal,
        'evidence_reconciliation':reconcile_case(case),
        'next_steps':[
            '核对税收居民/所得来源/扣缴税务及适用双边协定；查该税年官方最新条文和执业意见',
            '把真实税后已到账现金、净负债、应急储备和长期投资资金分开记录',
            '分短期1–3年资金、长期10–20年资金；建立币种匹配、费用、通胀与风险情景',
            '在法律约束和现金流事实落实后，以可复算模型比较至少两项长期配置备选',
            '年度及重大生活、税法事件复核；不得因为单月宏观波动自动交易',
        ],
    }
    if financial_profile is not None:
        tax_unknown = any('不能给出确定税后可投资金额' in x for x in legal['blocking_facts'])
        if tax_unknown and not allow_hypothetical:
            report['cashflow_calculation'] = {
                'status':'BLOCKED_UNRESOLVED_TAX',
                'explanation':'Tax is not known; no final after-tax investible-cash amount. Use --allow-hypothetical only if illustrative modeling is deliberately requested.'}
        else:
            cf = build_cashflow_report(financial_profile)
            report['cashflow_calculation'] = {
                'status':'ILLUSTRATIVE_NOT_TAX_VERIFIED' if tax_unknown else 'ILLUSTRATIVE_USER_ASSERTED_NET',
                'explanation':'Deterministic CNY scenario only. This program does not independently verify user tax records.',
                'report':cf,
            }
            if macro_snapshot is not None:
                report['long_horizon_calculation'] = {
                    'status':'ILLUSTRATIVE_NOT_PROBABILITY',
                    'report':build_long_horizon_report(financial_profile, macro_snapshot, (10,20)),
                }
    return report


def as_markdown(report):
    legal = report['legal_tax_preflight']
    theory = report['evidence_reconciliation']
    out = [
        '# Personal Finance Planner v0.3 — 跨司法管辖区循证预检',
        f"- 规划日：{legal['as_of_date']}；税年：{legal['tax_year']}",
        f"- 合规预检状态：**{legal['status']}**；不是税务裁决/个性化证券建议。",
        '\n## 地区规则研究路线',
    ]
    for p in legal['jurisdictions']:
        out.append(f"\n### {p['jurisdiction']} — {p.get('name','待补国家包')}")
        out.append('- 适用联系点：'+', '.join(p['roles']))
        for flag in p['flags']:
            out.append(f"- [{flag['severity']}] {flag['message']}")
        out.append('- 应查来源：'+(', '.join(p['source_ids']) if p['source_ids'] else '待官方检索'))
    out.append('\n## 不确定项 / 不能直接执行')
    for msg in legal['blocking_facts'] or ['当前无强制阻断项；仍须核查法规适用税年与实际身份。']:
        out.append('- '+msg)
    for msg in legal['missing_facts']:
        out.append('- [待补] '+msg)
    out.append('\n## 理论关系（可兼容与条件性冲突）')
    for r in theory['comparison']:
        out.append(f"- **{r['pair'][0]} × {r['pair'][1]}** [{r['relation']}/{r['decision_state']}]：{r['resolution']}")
    out.append('\n## 官方核验来源（来源线索，不代替适用条文审查）')
    for src in legal['primary_sources']:
        out.append(f"- {src['id']} — {src.get('title','缺失')}；复核状态 {src['state']}；{src.get('url','')}")
    if 'cashflow_calculation' in report:
        obj = report['cashflow_calculation']
        out.extend(['\n## 财务计算接入（仅条件情景）',f"- 执行状态：{obj['status']}；{obj['explanation']}"])
        if 'report' in obj:
            d = obj['report']['diagnosis']
            out.append(f"- 用户自报口径每月结余：¥{d['monthly_current_cash_surplus']:,.0f}；应急储备缺口：¥{d['emergency_reserve_shortfall']:,.0f}")
    if 'long_horizon_calculation' in report:
        out.append('\n## 10/20年条件模拟（非概率）')
        for name, cases in report['long_horizon_calculation']['report']['results'].items():
            labels = [f"{y}年 ¥{v['ending_purchasing_power_today_cny']:,.0f}（当前购买力）" for y,v in cases.items()]
            out.append('- '+name+': '+', '.join(labels))
    out.append('\n## 后续工作')
    for step in report['next_steps']:
        out.append('- '+step)
    out.append('\n> 本报告不计算应纳税额、自动选择证券、安排跨境汇款或声称长期回报概率。')
    return '\n'.join(out)+'\n'


def main():
    ap=argparse.ArgumentParser(description='Offline, auditable legal-tax research preflight and illustrative finance math')
    ap.add_argument('--case',required=True)
    ap.add_argument('--format',choices=['md','json'],default='md')
    ap.add_argument('--out')
    ap.add_argument('--financial-profile',help='Optional CNY finance model JSON; illustrative only')
    ap.add_argument('--macro',help='Optional dated macro scenario; requires --financial-profile')
    ap.add_argument('--allow-hypothetical',action='store_true',help='Permit expressly illustrative CNY math despite unverified tax status')
    args=ap.parse_args()
    if args.macro and not args.financial_profile:
        ap.error('--macro requires --financial-profile')
    report=build_report(
        read_json(args.case),
        read_json(args.financial_profile) if args.financial_profile else None,
        read_json(args.macro) if args.macro else None,
        allow_hypothetical=args.allow_hypothetical,
    )
    output=as_markdown(report) if args.format=='md' else json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        out=Path(args.out)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(output,encoding='utf8')
    else:
        print(output,end='')

if __name__=='__main__':
    main()
