"""Evidence-based, contextual, deterministic selection of existing theory graph.

This is not an LLM, an academic citation verifier, or a popularity vote.
Primary research is a separate host-agent task. Every claim is conditional.
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

GRAPH_PATH = Path(__file__).resolve().parents[2] / 'policies' / 'theory_graph.json'

# Maps a financial problem to relevant METHODS. These are NOT guarantees of performance.
TOPIC_THEORIES = {
    'cash_flow': {'LIFECYCLE', 'THALER', 'CFP', 'ALM'},
    'portfolio': {'MARKOWITZ', 'BOGLE', 'GRAHAM', 'SHARPE', 'ALM', 'TAIL_RISK', 'SHILLER'},
    'long_horizon': {'LIFECYCLE', 'FISHER', 'SHILLER', 'BENGEN', 'ALM'},
    'retirement': {'BENGEN', 'LIFECYCLE', 'FISHER', 'ALM', 'TAIL_RISK'},
    'macro': {'FISHER', 'SHILLER', 'LIFECYCLE', 'TAIL_RISK'},
    'behavior': {'THALER', 'CFP'},
    'risk': {'ALM', 'TAIL_RISK', 'MARKOWITZ'},
    'active_trading': {'SHARPE', 'GRAHAM', 'BOGLE', 'TAIL_RISK'},
}

TIER = {
    'math_identity': 'MATHEMATICAL_RELATION_WITH_CONDITIONS',
    'accounting_identity_with_assumptions': 'ACCOUNTING_IDENTITY_WITH_ASSUMPTIONS',
    'conditional_math_model': 'MODEL_NOT_EMPIRICAL_CERTAINTY',
    'economic_model': 'ECONOMIC_MODEL_ASSUMPTION_DEPENDENT',
    'historical_backtest': 'HISTORICAL_SAMPLE_NO_FUTURE_GUARANTEE',
    'behavioral_empirical': 'EMPIRICAL_CONTEXT_DEPENDENT',
    'empirical_predictive_model': 'EMPIRICAL_FORECAST_UNCERTAIN',
    'normative_policy_with_empirical_costs': 'PRACTITIONER_POLICY_WITH_EMPIRICAL_SUPPORT',
    'investment_philosophy': 'NORMATIVE_PHILOSOPHY',
    'risk_management_model': 'CONDITIONAL_RISK_FRAMEWORK',
    'risk_philosophy': 'RISK_PHILOSOPHY',
    'professional_process': 'PROFESSIONAL_PROCESS_NOT_LOCAL_LAW',
}


def _years(profile: dict) -> float | None:
    asof = date.fromisoformat(profile['as_of'])
    values = []
    for g in profile['goals']:
        d = date.fromisoformat(g['target_date'])
        if d >= asof:
            values.append((d - asof).days / 365.2425)
    return max(values) if values else None


def identify_topics(profile: dict, explicit: list[str] | None = None) -> list[str]:
    if explicit is not None:
        if not isinstance(explicit, list) or any(x not in TOPIC_THEORIES for x in explicit):
            raise ValueError('unknown evidence research topics')
        return sorted(set(explicit))
    topics = {'cash_flow', 'risk', 'portfolio'}
    h = _years(profile)
    if h is not None and h >= 8:
        topics.update({'long_horizon', 'macro'})
    if h is not None and h >= 15:
        topics.add('retirement')
    if profile['risk'].get('income_stability') == 'volatile':
        topics.add('active_trading')
    if any(i['kind'] in {'pf_payout', 'pf_simulated_profit', 'business', 'self_employment'} for i in profile['income']):
        topics.add('active_trading')
    return sorted(topics)


def evaluate(profile: dict, explicit_topics: list[str] | None = None) -> dict:
    graph = json.loads(GRAPH_PATH.read_text(encoding='utf-8'))
    topics = identify_topics(profile, explicit_topics)
    selected = set().union(*(TOPIC_THEORIES[x] for x in topics)) if topics else set()
    principles = []
    for item in graph['principles']:
        if item['id'] not in selected:
            continue
        principles.append({
            'id': item['id'], 'label': item['label'],
            'role': item['decision'], 'required_assumptions': item['assumptions'],
            'limits': item['limits'], 'evidence_class': TIER.get(item['kind'], 'UNCATEGORIZED'),
            'reference_ids': item['refs'],
            'source_status': 'CURATED_REFERENCE_NOT_THIS_RUN_INDEPENDENTLY_VERIFIED',
        })
    relations = []
    horizon = _years(profile)
    for r in graph['relations']:
        if r['a'] not in selected or r['b'] not in selected:
            continue
        decision = r['resolution']
        conditional_state = 'CONDITIONAL_RECONCILIATION'
        pair = {r['a'], r['b']}
        if pair == {'BOGLE', 'GRAHAM'}:
            conditional_state = 'ACTIVE_ALPHA_UNVERIFIED_DEFAULT_TO_COST_BASELINE'
            decision = '未提供独立、长期、税费后主动优势证据：低成本广泛分散组合仅作为比较基准；不得推导必须买入特定证券。'
        elif pair == {'BOGLE', 'ALM'}:
            conditional_state = 'GOAL_BUCKETING_FIRST'
            decision = '应急和短期支出优先流动性与币种匹配，其余长期资金再比较指数/其他配置。'
        elif pair == {'BENGEN', 'LIFECYCLE'}:
            conditional_state = 'LOCAL_RETIREMENT_MODEL_REQUIRED'
            decision = '历史美国提款率不是全球可复制的安全收益率；退休期限、税制、币种、养老金应单独模拟。'
        relations.append({
            'pair': [r['a'], r['b']], 'relation': r['relation'],
            'problem': r['question'], 'decision_state': conditional_state,
            'conditional_resolution': decision, 'limitations': r['disclosure'],
        })
    return {
        'status': 'DECISION_SUPPORT_NOT_AUTOMATIC_SCIENTIFIC_CONSENSUS',
        'topics': topics,
        'time_horizon_years': None if horizon is None else round(horizon, 2),
        'principles': principles,
        'relationships': relations,
        'hard_constraint_order': [
            'CURRENT_APPLICABLE_LAW_AND_AUTHORIZATION',
            'SOLVENCY_AND_LIQUIDITY', 'ACTUAL_GOALS_AND_TIME_HORIZON',
            'VERIFIED_DATA_AND_MATHEMATICS', 'RISK_AND_MODEL_UNCERTAINTY',
            'TAX_AFTER_FEE_COMPARISON', 'BEHAVIORAL_IMPLEMENTABILITY',
        ],
        'cannot_conclude': [
            '文献是否最新且可转用于本用户：须通过宿主真实检索与实质审阅。',
            '不能用理论调和替代当地现行法律、职业资质或税务核定。',
            '文献与投资理念不等于未来收益预测或长期超额收益保证。',
        ],
    }
