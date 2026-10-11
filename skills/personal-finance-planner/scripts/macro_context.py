#!/usr/bin/env python3
"""Evidence-checked long-horizon macro context. NO market timing and NO live fetch.

Loads a dated macro snapshot supplied via official-source tools or local files.
Computes only comparable, correctly dated real-rate proxies and scenario ranges.
Stdlib only; never reads a personal financial profile or sends data anywhere.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


KNOWN_INDICATORS = {
    'US_NOMINAL10Y': {'region': 'US', 'currency': 'USD', 'definition': '10y_nominal_government_yield', 'max_age_days': 45},
    'US_TIPS_REAL10Y': {'region': 'US', 'currency': 'USD', 'definition': '10y_tips_real_yield', 'max_age_days': 45},
    'US_BREAKEVEN10Y': {'region': 'US', 'currency': 'USD', 'definition': '10y_breakeven_inflation', 'max_age_days': 45},
    'CN_NOMINAL10Y': {'region': 'CN', 'currency': 'CNY', 'definition': '10y_nominal_government_yield', 'max_age_days': 45},
    'CN_CPI_YOY': {'region': 'CN', 'currency': 'CNY', 'definition': 'observed_historical_yoy_inflation', 'max_age_days': 120},
}


class MacroInputError(ValueError):
    pass


def parse_iso(raw: str, label: str) -> date:
    try:
        return date.fromisoformat(raw)
    except (ValueError, TypeError) as exc:
        raise MacroInputError(f'{label} 必须为 YYYY-MM-DD') from exc


def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MacroInputError(f'{label} 须为有限数字')
    return float(value)


def validate_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get('schema') != 'macro-snapshot-v1':
        raise MacroInputError('预期 schema=macro-snapshot-v1 的JSON对象')
    as_of = parse_iso(raw.get('as_of'), 'as_of')
    if raw.get('planning_currency') != 'CNY':
        raise MacroInputError('当前示例只支持人民币CNY的长期消费情景')
    obs = raw.get('observations', [])
    if not isinstance(obs, list):
        raise MacroInputError('observations 应为数组')
    ids = set()
    for item in obs:
        if not isinstance(item, dict):
            raise MacroInputError('每条观测应为对象')
        key = item.get('id')
        if key not in KNOWN_INDICATORS or key in ids:
            raise MacroInputError(f'不支持或重复的宏观指标：{key}')
        ids.add(key)
        definition = KNOWN_INDICATORS[key]
        if item.get('region') != definition['region'] or item.get('currency') != definition['currency']:
            raise MacroInputError(f'{key} 地区/币种与指标定义不匹配')
        if item.get('unit') != 'pct_per_year':
            raise MacroInputError(f'{key} 单位须为 pct_per_year，例如2.5表示2.5%')
        value = finite(item.get('value_pct'), f'{key}.value_pct')
        if not -50 <= value <= 100:
            raise MacroInputError(f'{key} 年百分比数值异常，拒绝自动使用')
        observed = parse_iso(item.get('observed_on'), f'{key}.observed_on')
        if observed > as_of:
            raise MacroInputError(f'{key} 观测日期在分析日期之后')
        quality = item.get('quality')
        if quality not in {'sourced', 'illustrative'}:
            raise MacroInputError(f'{key} quality只能为sourced/illustrative')
        if quality == 'sourced' and not (item.get('publisher') and str(item.get('source_url','')).startswith('https://')):
            raise MacroInputError(f'{key} 正式数据必须有发布机构和HTTPS来源')
    assumptions = raw.get('planning_assumptions', {})
    if not isinstance(assumptions, dict):
        raise MacroInputError('planning_assumptions应为对象')
    scenarios = assumptions.get('scenarios')
    if not isinstance(scenarios, dict) or not all(k in scenarios for k in ('adverse','base','favorable')):
        raise MacroInputError('应提供adverse/base/favorable三个明确标注的规划情景')
    for name, cfg in scenarios.items():
        if not isinstance(cfg, dict):
            raise MacroInputError(f'{name} 须为对象')
        for key in ('annual_net_return', 'annual_inflation', 'annual_nominal_income_growth'):
            number = finite(cfg.get(key), f'{name}.{key}')
            if key == 'annual_net_return' and not (-0.99 < number <= 1):
                raise MacroInputError('净收益率必须在(-99%,+100%]范围内')
            if key == 'annual_inflation' and not (-0.3 < number <= 0.3):
                raise MacroInputError('通胀情景必须在(-30%,+30%]范围内')
            if key == 'annual_nominal_income_growth' and not (-0.5 < number <= 0.5):
                raise MacroInputError('名义收入增长率情景应在(-50%,+50%]')
    return raw


def build_context(raw: dict[str, Any]) -> dict[str, Any]:
    raw = validate_snapshot(raw)
    as_of = parse_iso(raw['as_of'], 'as_of')
    obs = {item['id']: item for item in raw.get('observations', [])}
    warnings: list[str] = []
    observed = []
    for key, item in obs.items():
        d = parse_iso(item['observed_on'], 'observed_on')
        age = (as_of - d).days
        stale = age > KNOWN_INDICATORS[key]['max_age_days']
        observed.append({
            'id': key, 'value_pct': item['value_pct'], 'observation_date': d.isoformat(),
            'age_days': age, 'stale': stale, 'quality': item['quality'],
            'publisher': item.get('publisher'), 'source_url': item.get('source_url'),
            'definition': KNOWN_INDICATORS[key]['definition'], 'currency': item['currency'],
        })
        if stale:
            warnings.append(f'{key} 距观测日{age}天，超过原型提醒阈值；如需当前情况应重新查询官方来源。')
        if item['quality'] == 'illustrative':
            warnings.append(f'{key} 是虚构/示例输入，不属于已经核实的经济事实。')
    calculated = {}
    a, b = obs.get('US_NOMINAL10Y'), obs.get('US_TIPS_REAL10Y')
    if a is not None and b is not None:
        days = abs((parse_iso(a['observed_on'], 'date') - parse_iso(b['observed_on'], 'date')).days)
        if days <= 7:
            difference = float(a['value_pct']) - float(b['value_pct'])
            calculated['us_breakeven_inflation_10y_pct_approx'] = {
                'value_pct': round(difference, 4), 'unit':'pct_per_year',
                'observations_days_apart': days,
                'interpretation': '美元名义国债10Y收益率减美国TIPS10Y实际收益率；含通胀风险溢价及流动性因素，并非纯预期通胀。',
                'quality': 'sourced' if a['quality']=='sourced' and b['quality']=='sourced' else 'illustrative',
            }
            if 'US_BREAKEVEN10Y' in obs:
                actual = float(obs['US_BREAKEVEN10Y']['value_pct'])
                if abs(difference - actual) > 0.35:
                    warnings.append('T10YIE与名义减TIPS利差的差异超过0.35个百分点，检查日期和口径。')
        else:
            warnings.append('US_NOMINAL10Y与US_TIPS_REAL10Y日期相差超过7天，拒绝拼接计算10年盈亏平衡通胀。')
    if 'CN_NOMINAL10Y' in obs:
        cn_yield = float(obs['CN_NOMINAL10Y']['value_pct']) / 100
        scenario_results = {}
        for name, cfg in raw['planning_assumptions']['scenarios'].items():
            inflation = float(cfg['annual_inflation'])
            scenario_results[name] = round(100 * ((1 + cn_yield)/(1 + inflation) - 1), 4)
        calculated['cn_nominal_10y_bond_yield_vs_inflation_assumptions'] = {
            'scenario_real_yield_pct_approx': scenario_results,
            'unit': 'pct_per_year',
            'interpretation': '仅为同一币种中债10年名义收益率与假设未来年通胀的Fisher购买力敏感性；不是中国真实可交易的10年实际国债收益率，也不是预期20年收益。',
            'quality': 'scenario_sensitivity_not_observed_real_rate',
        }
    if 'CN_NOMINAL10Y' in obs and 'CN_CPI_YOY' in obs:
        warnings.append('中国10年名义国债收益率与过去12个月CPI同比不能直接相减作为未来10年预期实际利率。')
    if any(key.startswith('US_') for key in obs) and raw['planning_currency'] == 'CNY':
        warnings.append('美国TIPS为美元市场实际收益率，不能不经汇率/税费/对冲调整就作为人民币安全资产回报。')
    return {
        'schema': 'macro-context-v1', 'as_of': raw['as_of'],
        'planning_currency': raw['planning_currency'],
        'horizon_years': [10, 20], 'observed_evidence': observed,
        'calculations': calculated, 'planning_assumptions': raw['planning_assumptions'],
        'warnings': warnings,
        'decision_rule': '宏观观测只辅助10/20年规划情景及风险审查；不从最新利率/估值直接推导买卖、目标仓位或成功概率。',
        'source_verification_limit': '程序只验证来源字段形式、币种、日期和单位；不会联网独立验证发布页面是否真的含有这些值。',
        'status': ('macro_unverified' if not observed or not any(o['quality'] == 'sourced' for o in observed) else ('needs_source_refresh' if any(o['stale'] for o in observed) else 'dated_snapshot_reviewed')),
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        '# 宏观经济长期规划证据快照',
        f"分析日期：{report['as_of']}；消费及目标计价币种：{report['planning_currency']}。",
        '', '**经济数据并非未来收益保证；此程序没有联网，输入来源由调用方提供，出处由调用Agent或用户负责独立核对。**',
        '', '|指标|值（%/年）|观测日|证据质量|过期警告|', '|---|---:|---|---|---|',
    ]
    for item in report['observed_evidence']:
        lines.append(f"|{item['id']}|{item['value_pct']:.3f}|{item['observation_date']}|{item['quality']}|{'是' if item['stale'] else '否'}|")
    lines += ['', '## 可核对的计算（非未来预测）']
    for key, entry in report['calculations'].items():
        if 'value_pct' in entry:
            lines.append(f"- {key}: {entry['value_pct']:.3f}%/年；{entry['interpretation']}")
        else:
            values = ', '.join(f"{name}: {value:.3f}%" for name, value in entry['scenario_real_yield_pct_approx'].items())
            lines.append(f"- {key}: {values}；{entry['interpretation']}")
    if not report['calculations']:
        lines.append('- 无日期和口径可比的指标，不推断实际利率。')
    lines += ['', '## 已显式声明的长期情景假设（不是观测数据）',
              '|情景|年化净投资回报|年通胀|名义收入年增长|', '|---|---:|---:|---:|']
    for name, scenario in report['planning_assumptions']['scenarios'].items():
        lines.append(f"|{name}|{scenario['annual_net_return']:.1%}|{scenario['annual_inflation']:.1%}|{scenario['annual_nominal_income_growth']:.1%}|")
    lines += ['', '## 复核事项']
    lines += [f'- {item}' for item in report['warnings']] or ['- 无其他自动告警；仍需确认来源适用性。']
    return '\n'.join(lines) + '\n'


def main() -> int:
    p = argparse.ArgumentParser(description='长期宏观经济观察值口径/时效验证器（离线）')
    p.add_argument('--input', required=True, help='有来源、日期的宏观快照JSON文件')
    p.add_argument('--format', choices=('json', 'md'), default='md')
    p.add_argument('--out')
    args = p.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
        report = build_context(data)
        result = json.dumps(report, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else to_markdown(report)
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result, encoding='utf-8')
            print('已写入：' + str(output))
        else:
            print(result, end='')
        return 0
    except (MacroInputError, OSError, json.JSONDecodeError) as exc:
        p.exit(2, '宏观快照输入错误：' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
