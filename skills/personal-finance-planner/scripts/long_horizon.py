#!/usr/bin/env python3
"""Deterministic 10/20-year CNY scenarios from a dated macro planning snapshot.

Scenarios are explicitly assumed, NOT estimated success probabilities.
Expenses inflate while nominal income follows a separate assumption.
Net returns are explicitly after ongoing investment costs under the user's
assumptions; actual tax liabilities require separate verification.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


planner = load_module('portable_planner_v02', 'planner.py')
macro = load_module('portable_macro_v02', 'macro_context.py')


def simulation(profile: dict[str, Any], years: int, cfg: dict[str, float]) -> dict[str, Any]:
    if years not in (10, 20):
        raise ValueError('首个10/20年版本仅接受10或20年')
    annual_return = cfg['annual_net_return']
    annual_inflation = cfg['annual_inflation']
    annual_income_growth = cfg['annual_nominal_income_growth']
    m_return = (1 + annual_return) ** (1/12) - 1
    m_inflation = (1 + annual_inflation) ** (1/12) - 1
    m_income_growth = (1 + annual_income_growth) ** (1/12) - 1

    cash = float(profile['liquid_cash'])
    invest = float(profile['financial_assets']) - cash
    debt = float(profile['outstanding_debt'])
    monthly_debt_payment = float(profile['monthly_debt_payment'])
    annual_debt_rate = float(profile['debt_annual_rate'])
    essential = float(profile['monthly_essential_spending'])
    discretionary = float(profile['monthly_discretionary_spending'])
    business_cost = float(profile['monthly_required_business_cost'])
    tax_reserve = float(profile['monthly_tax_reserve'])
    monthly_receipts = float(profile['monthly_cash_receipts'])
    emergency_months = profile['emergency_months']
    if not math.isfinite(monthly_receipts):
        raise ValueError('财务收入非有限数字')

    initial_buffer = emergency_months * (essential + business_cost + (monthly_debt_payment if debt > 0 else 0))
    if cash > initial_buffer and debt <= 0:
        invest += cash - initial_buffer
        cash = initial_buffer
    shortfall_month = None
    reserve_gap_max = 0.0
    for month in range(1, years * 12 + 1):
        price_index = (1 + m_inflation) ** (month - 1)
        income_factor = (1 + m_income_growth) ** (month - 1)
        income = monthly_receipts * income_factor
        expenses = (essential + discretionary + business_cost) * price_index + tax_reserve
        # Monthly tax reserve is held constant by assumption; for changing
        # tax obligations, user must amend scenarios outside this simplified model.
        current_debt_payment = 0.0
        if debt > 0:
            debt *= 1 + annual_debt_rate / 12
            current_debt_payment = min(monthly_debt_payment, debt)
            debt -= current_debt_payment
        expenses += current_debt_payment
        invest *= 1 + m_return
        available_flow = income - expenses
        cash += available_flow
        if cash < 0 and invest > 0:
            liquidation = min(-cash, invest)
            invest -= liquidation
            cash += liquidation
        if cash < -0.005 and shortfall_month is None:
            shortfall_month = month
        buffer = emergency_months * ((essential + business_cost) * price_index + (monthly_debt_payment if debt > 0 else 0))
        if cash > buffer and debt <= 0:
            invest += cash - buffer
            cash = buffer
        if buffer > 0:
            reserve_gap_max = max(reserve_gap_max, max(0.0, buffer-cash))

    nominal_net_worth = cash + invest - debt
    inflation_factor = (1 + annual_inflation) ** years
    return {
        'years':years,
        'ending_nominal_net_financial_worth_cny':round(nominal_net_worth, 2),
        'ending_purchasing_power_today_cny':round(nominal_net_worth/inflation_factor, 2),
        'ending_liquid_cash_cny':round(cash, 2),
        'ending_invested_cny':round(invest, 2),
        'ending_debt_cny':round(debt, 2),
        'first_unfunded_shortfall_month':shortfall_month,
        'max_emergency_reserve_shortfall_cny':round(reserve_gap_max, 2),
        'assumed_annual_net_return':annual_return,
        'assumed_annual_inflation':annual_inflation,
        'assumed_nominal_income_growth':annual_income_growth,
    }


def build_long_horizon_report(profile_raw: dict[str, Any], macro_raw: dict[str, Any], years: tuple[int, ...] = (10, 20)) -> dict[str, Any]:
    profile = planner.validate(profile_raw)
    macro_report = macro.build_context(macro_raw)
    output: dict[str, Any] = {}
    for name, cfg in macro_report['planning_assumptions']['scenarios'].items():
        output[name] = {str(y): simulation(profile, y, cfg) for y in years}
    warnings = [
        '三条路径是固定年化收益率/通胀/名义收入增长的确定性假设，不是成功概率、预测或风险分布。',
        '长期模型将必要/可选消费按通胀增长，名义收入按独立情景增长；经营成本随通胀，预留税金保持名义不变需人工修正。',
        '未建模真实市场收益顺序、突发失业、养老金/保险/子女/购房支出及多币种税法；真实规划需增加这些模块。',
        '如果出现资金未覆盖缺口，不能将最终负资产当成仍可正常生活的可执行方案。',
    ] + macro_report['warnings']
    if profile['outstanding_debt'] > 0:
        warnings.append('长期演算只采用单笔合计债务和固定月供，不包括提前还款策略及贷款利率变动。')
    return {
        'model_type':'deterministic_long_horizon_scenario_not_probability',
        'profile_label':profile['label'], 'currency': 'CNY', 'macro_as_of':macro_report['as_of'],
        'macro_snapshot_status':macro_report['status'],
        'profile_inputs_used':{'monthly_cash_receipts':profile['monthly_cash_receipts'],
                               'financial_assets':profile['financial_assets'],
                               'liquid_cash':profile['liquid_cash'],
                               'emergency_months':profile['emergency_months']},
        'results':output,
        'warning':warnings,
        'source_trace':macro_report['observed_evidence'],
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        '# 10–20年长期财富规划（纯情景演算）',
        f"用户案例：{report['profile_label']}。币种：{report['currency']}。宏观数据取数截止参考日：{report['macro_as_of']}。",
        '', '|情景|期限|期末名义金融净资产|折算今天的购买力|首次资金缺口月份|', '|---|---:|---:|---:|---:|',
    ]
    for name, results in report['results'].items():
        for y, values in results.items():
            fail = values['first_unfunded_shortfall_month']
            lines.append(f"|{name}|{y}年|¥{values['ending_nominal_net_financial_worth_cny']:,.0f}|¥{values['ending_purchasing_power_today_cny']:,.0f}|{fail if fail else '未触发'}|")
    lines += ['', '## 数据与方法约束'] + [f'- {w}' for w in report['warning']]
    return '\n'.join(lines)+'\n'


def main() -> int:
    p = argparse.ArgumentParser(description='带宏观假设口径的10/20年财务确定性情景（不预测收益概率）')
    p.add_argument('--profile', required=True, help='个人财务JSON（参考examples）')
    p.add_argument('--macro', required=True, help='含观测数据/明确长期假设的宏观快照JSON')
    p.add_argument('--years', type=int, nargs='+', choices=[10,20], default=[10,20])
    p.add_argument('--format', choices=['md','json'], default='md')
    p.add_argument('--out')
    args = p.parse_args()
    try:
        profile = json.loads(Path(args.profile).read_text(encoding='utf-8'))
        macro_input = json.loads(Path(args.macro).read_text(encoding='utf-8'))
        r = build_long_horizon_report(profile, macro_input, tuple(sorted(set(args.years))))
        result = json.dumps(r, ensure_ascii=False, indent=2)+'\n' if args.format=='json' else to_markdown(r)
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result, encoding='utf-8')
            print('报告已写入：'+str(output))
        else:
            print(result, end='')
        return 0
    except (planner.ProfileError, macro.MacroInputError, OSError, ValueError, json.JSONDecodeError) as exc:
        p.exit(2, '长期情景输入错误：'+str(exc)+'\n')


if __name__=='__main__':
    raise SystemExit(main())
