#!/usr/bin/env python3
"""Optional deterministic four-bucket cashflow calculator for the v5.7 Skill.

Layer model (anti double-counting):
  L1 fact ledger inputs (received money, balances, obligations) ->
  L2 four-bucket period budget:  allocatable == sum(buckets) + unallocated ->
  L3 references (never sums) into v5.6 long-term purpose pools.

No network, no persistence, no agent, no financial transaction, no tax law.
All amounts are Decimal strings with an explicit currency; cross-currency
values are summed ONLY through dated user-supplied FX (fail closed).
Heuristic parameters are labeled HEURISTIC_EDITABLE and may be overridden;
nothing here is a scientifically proven universal optimum.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

D = Decimal
ZERO = D('0')

DEFAULTS = {
    'high_cost_apr_threshold': D('0.08'),   # above this, extra repayment precedes risk investment
    'safety_gap_fill_share': D('0.5'),      # share of post-floor surplus into reserve gap (balanced mode)
    'financial_invest_share': D('0.5'),     # share of remaining surplus into long-term investment
    'defensive_safety_share': D('1.0'),     # defensive mode: fill reserve gap first
}
PCT = D('0.05')  # NO_CHANGE tolerance band (share of allocatable)


def _die_exit(msg: str) -> int:
    print(f'ERROR: {msg}', file=sys.stderr)
    return 3  # invalid-input exit code; distinguishable from DEFICIT (2) and OK (0)


def die(msg: str) -> 'None':
    raise SystemExit(_die_exit(msg))


def money(value, name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        die(f'{name} must be a decimal string, not {type(value).__name__}/null')
    try:
        n = D(str(value))
    except (InvalidOperation, ValueError, TypeError):
        die(f'{name} is not a valid decimal amount: {value!r}')
    if not n.is_finite():
        die(f'{name} must be finite (NaN/Infinity rejected)')
    if n < 0:
        die(f'{name} must be >= 0 (got {value!r})')
    return n


def q(n: Decimal) -> str:
    return str(n.quantize(D('0.01')))


def parse_iso_day(value, name: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        die(f'{name} is not a valid ISO date: {value!r}')


def parse_month(value, name: str) -> tuple[int, int]:
    s = str(value)
    if len(s) != 7 or s[4] != '-':
        die(f'{name} must be YYYY-MM: {value!r}')
    y, m = s[:4], s[5:]
    if not (y.isdigit() and m.isdigit() and 1 <= int(m) <= 12):
        die(f'{name} must be YYYY-MM with month 01-12: {value!r}')
    return int(y), int(m)


def load_input(raw) -> dict:
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            die(f'input is not valid JSON: {exc}')
    elif isinstance(raw, dict):
        data = raw
    else:
        die('input must be a JSON object')
    if not isinstance(data, dict):
        die('input must be a JSON object')
    if data.get('schema_version') != '5.7.0':
        die("schema_version must be '5.7.0'")
    for key in ('as_of', 'currency', 'current_period_income', 'necessary_living'):
        if key not in data:
            die(f'missing required field: {key}')
    parse_iso_day(data['as_of'], 'as_of')
    base = data['currency']
    if not (isinstance(base, str) and len(base) == 3):
        die('currency must be a 3-letter code')
    return data


class FX:
    """Dated, user-supplied conversions only. No bundled rates, no network."""

    def __init__(self, spec: dict | None, base: str, as_of: str):
        self.base = base
        self.rates: dict[tuple[str, str], tuple[str, Decimal]] = {}
        self.log: list[dict] = []
        for r in ((spec or {}).get('rates') or []):
            frm, to = r.get('from'), r.get('to')
            rate = money(r.get('rate'), 'fx.rate')
            if rate <= 0:
                die('fx.rate must be > 0')
            parse_iso_day(r.get('date'), 'fx.date')
            self.rates[(frm, to)] = (r.get('date'), rate)

    def to_base(self, amount: Decimal, ccy: str, label: str) -> Decimal:
        if ccy == self.base:
            return amount
        key = (ccy, self.base)
        if key not in self.rates:
            die(f'{label}: {ccy} amount cannot be summed into {self.base} without a dated FX rate '
                f'(cross-currency mixing without conversion is rejected)')
        day, rate = self.rates[key]
        converted = (amount * rate).quantize(D('0.01'))
        self.log.append({'from': ccy, 'to': self.base, 'date': day, 'rate': str(rate),
                         'amount': q(amount), 'converted': q(converted), 'label': label})
        return converted


def income_entries(data: dict) -> list[dict]:
    entries = []
    hist = data.get('income_history') or []
    if not isinstance(hist, list):
        die('income_history must be an array')
    for i, m in enumerate(hist):
        if not isinstance(m, dict):
            die(f'income_history[{i}] must be an object')
        for key in ('month', 'amount', 'received'):
            if key not in m:
                die(f'income_history[{i}] missing {key}')
        parse_month(m['month'], f'income_history[{i}].month')
        entries.append({
            'month': m['month'],
            'amount': money(m['amount'], f'income_history[{i}].amount'),
            'currency': m.get('currency') or data['currency'],
            'received': m['received'] is True,
            'recurring': m.get('recurring'),
            'one_off': m.get('one_off') is True,
        })
    return entries


def build_allocatable(data: dict, fx: FX) -> dict:
    """Layer-1 to Layer-2: only received money funds the household budget.

    Statutory/contractual obligations are NOT pre-deducted here (they live in
    the Living bucket); known tax due and required business operating money are
    deducted because they are not household-disposable.
    """
    inc = data['current_period_income']
    if not isinstance(inc, dict) or 'amount' not in inc:
        die('current_period_income must be an object with amount')
    streams = [inc] + list(data.get('current_period_income_extra') or [])
    gross = ZERO
    received_all = True
    for idx, s in enumerate(streams):
        label = 'current_period_income' if idx == 0 else f'current_period_income_extra[{idx-1}]'
        amt = money(s.get('amount'), f'{label}.amount')
        ccy = s.get('currency') or data['currency']
        conv = fx.to_base(amt, ccy, label)
        if s.get('received', True) is not True:
            received_all = False
            continue
        gross += conv
    received = received_all
    converted = gross
    after_tax = inc.get('after_tax', None)

    facts = data.get('facts') or {}
    tax_due = money(facts.get('known_tax_due_this_period'), 'facts.known_tax_due_this_period') \
        if facts.get('known_tax_due_this_period') is not None else None
    biz = money(facts.get('business_operating_reserve_required'), 'facts.business_operating_reserve_required') \
        if facts.get('business_operating_reserve_required') is not None else None

    unknowns: list[str] = []
    if not received:
        unknowns.append('some or all period income not yet received; unreceived streams are excluded from allocatable')
    gross = converted if received else ZERO
    deductions = (tax_due or ZERO) + (biz or ZERO)
    allocatable = gross - deductions
    if allocatable < 0:
        die('known tax due + business reserve exceed received income; verify facts (negative allocatable rejected)')
    tax_status = 'KNOWN_NET' if (tax_due is not None or after_tax is True) else 'UNKNOWN_TAX_CONDITIONAL'
    if tax_status == 'UNKNOWN_TAX_CONDITIONAL':
        unknowns.append('income tax status unknown; allocatable is pre-tax and investable amounts stay conditional')
    return {
        'amount': allocatable, 'gross': gross, 'tax_due': tax_due, 'business': biz,
        'tax_status': tax_status, 'received': received,
        'one_off': inc.get('one_off') is True,
        'fx_log': fx.log, 'unknowns': unknowns,
    }


def classify_income(data: dict, alloc: dict) -> dict:
    hist = income_entries(data)
    received_hist = [e for e in hist if e['received']]
    warnings: list[str] = []
    stability = (data.get('profile') or {}).get('income_stability', 'unknown')
    months = len(received_hist)

    def stats(vals: list[Decimal]) -> dict | None:
        if len(vals) < 6:
            return None
        s = sorted(vals)
        median = s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2
        return {'low': s[max(0, len(s) // 4)], 'typical': median, 'high': s[min(len(s) - 1, (3 * len(s)) // 4)],
                'min': s[0], 'max': s[-1], 'method': 'quartiles of received recurring months (descriptive, not a forecast)'}

    recurring_vals = [e['amount'] for e in received_hist if e.get('recurring') is not False and not e['one_off']]
    if months == 0:
        classification = 'SINGLE_PERIOD'
    elif len(recurring_vals) >= 6:
        classification = 'VARIABLE_HISTORY' if stability == 'variable' or (max(recurring_vals) - min(recurring_vals)) > D('0.3') * min(recurring_vals) else 'STABLE_SALARY'
    elif stability == 'stable' and months >= 6:
        classification = 'STABLE_SALARY'
    else:
        classification = 'INSUFFICIENT_HISTORY'
        warnings.append(f'only {months} month(s) of received history; cannot claim a long-run normal income')
    if stability == 'stable' and months and months < 6:
        warnings.append('income_stability=stable declared with <6 months evidence; treated as claimed, not verified')
    band = stats(recurring_vals)
    if band is None and len(recurring_vals) >= 2:
        warnings.append('scenario band needs >=6 months; single-period figures only')
    if alloc['one_off']:
        warnings.append('current period contains one-off income; not a recurring budget base')
    return {'classification': classification, 'months_analyzed': months,
            'scenario_band': ({'low': q(band['low']), 'typical': q(band['typical']),
                               'high': q(band['high']), 'method': band['method']} if band else None),
            'warnings': warnings}


def living_floor(data: dict) -> dict:
    nl = data.get('necessary_living') or {}
    fixed = [(item['name'], money(item['amount'], f'necessary_living.fixed[{i}].amount'))
             for i, item in enumerate(nl.get('fixed') or [])]
    variable = [(item['name'], money(item['amount'], f'necessary_living.variable[{i}].amount'))
                for i, item in enumerate(nl.get('variable') or [])]
    obligations = data.get('obligations') or []
    debt_cash = ZERO
    for i, ob in enumerate(obligations):
        if not isinstance(ob, dict) or 'monthly_payment' not in ob:
            die(f'obligations[{i}] missing monthly_payment')
        pay = money(ob['monthly_payment'], f'obligations[{i}].monthly_payment')
        if ob.get('apr') is not None:
            apr = money(ob['apr'], f'obligations[{i}].apr')
            if apr > 1:
                die(f'obligations[{i}].apr must be a decimal fraction (0.039 = 3.9%)')
        debt_cash += pay
    fixed_total = sum((a for _, a in fixed), ZERO)
    variable_total = sum((a for _, a in variable), ZERO)
    return {'fixed_items': fixed, 'variable_items': variable, 'fixed': fixed_total,
            'variable': variable_total, 'debt_service_cash': debt_cash,
            'total': fixed_total + variable_total + debt_cash}


def reserve_target(data: dict, floor_total: Decimal) -> tuple[int | None, Decimal | None, str]:
    pref = data.get('preferences') or {}
    months = pref.get('reserve_months_target')
    facts = data.get('facts') or {}
    deps = (data.get('profile') or {}).get('dependents', 0)
    stability = (data.get('profile') or {}).get('income_stability', 'unknown')
    if months is not None:
        if not isinstance(months, int) or not 1 <= months <= 36:
            die('reserve_months_target must be an integer 1..36')
        return months, (D(months) * floor_total), 'USER_INPUT'
    # Editable heuristic baseline; explicitly NOT claimed as a universal optimum.
    if stability == 'variable':
        months = 9 if deps > 0 else 6
    else:
        months = 6 if deps > 0 else 3
    return months, (D(months) * floor_total), 'HEURISTIC_EDITABLE'


def overrides(data: dict) -> tuple[dict, dict]:
    o = dict(DEFAULTS)
    source = {k: 'HEURISTIC_EDITABLE' for k in DEFAULTS}
    for k, v in (data.get('assumption_overrides') or {}).items():
        if k in o:
            o[k] = money(v, f'assumption_overrides.{k}')
            source[k] = 'USER_INPUT'
    return o, source


def allocate(mode: str, allocatable: Decimal, floor: dict, data: dict, ov: dict, src: dict,
             safety_cash: Decimal | None, reserve_gap: Decimal, facts_high_cost: Decimal) -> dict:
    """Priority-ordered allocation. Every bucket records its rationale.

    Order (default, user-editable via preferences.surplus_priority for the HOST
    to re-run): necessary living floor -> reserve gap -> high-cost debt ->
    capability plans -> social floor -> conditional long-term investment ->
    unallocated remainder. Investment budget is a ceiling, never a must-spend.
    """
    living_total = floor['total']
    assumptions: list[dict] = []
    prefs = data.get('preferences') or {}

    if allocatable < living_total:
        gap = living_total - allocatable
        draw = min(gap, safety_cash) if safety_cash is not None else None
        return {
            'status': 'DEFICIT',
            'buckets': {
                'safety_savings': {'add_this_period': q(ZERO), 'extra_high_cost_debt_repayment': q(ZERO),
                                   'use_of_reserve': q(draw) if draw is not None else None,
                                   'existing_eligible': q(safety_cash) if safety_cash is not None else None,
                                   'target_months': None, 'target_amount': None, 'gap_after': None,
                                   'rationale': 'deficit period: no savings added; optional reserve draw listed, never negative savings'},
                'living': {'fixed': q(floor['fixed']), 'variable': q(floor['variable']),
                           'debt_service_cash': q(floor['debt_service_cash']), 'funded': q(allocatable),
                           'total': q(living_total),
                           'rationale': f'necessary obligations {q(living_total)} exceed allocatable {q(allocatable)}; funded part only'},
                'necessary_investment': {'capability': q(ZERO), 'financial': q(ZERO), 'business_capital': q(ZERO),
                                         'total': q(ZERO), 'rationale': 'no investable surplus in deficit'},
                'social_discretionary': {'committed': q(ZERO), 'free': q(ZERO), 'total': q(ZERO),
                                         'rationale': 'frozen in deficit before any discretionary spend'},
            },
            'unallocated': q(ZERO),
            'deficit': {'gap': q(gap), 'reserve_draw_available': q(draw) if draw is not None else None,
                        'note': 'fund the gap from eligible reserves or verified extra income; do not fabricate income or negative savings'},
            'assumptions': assumptions,
        }

    surplus = allocatable - living_total
    # 1) reserve gap (safety bucket)
    share = ov['defensive_safety_share'] if mode == 'defensive' else ov['safety_gap_fill_share']
    share_src = src['defensive_safety_share'] if mode == 'defensive' else src['safety_gap_fill_share']
    assumptions.append({'id': f'{mode}.safety_gap_fill_share', 'value': str(share), 'source': share_src})
    safety_add = min(reserve_gap, surplus * share).quantize(D('0.01'))
    remaining = surplus - safety_add
    # 2) committed social/relationship obligations (culturally rigid) keep standing
    committed = money(prefs.get('social_committed_floor') or '0', 'preferences.social_committed_floor')
    free_pref = money(prefs.get('social_free_preference') or '0', 'preferences.social_free_preference')
    social = min(committed, remaining).quantize(D('0.01'))
    remaining -= social
    # 3) high-cost debt extra repayment (balance-repair saving; precedes risk investment)
    hc_extra = ZERO
    if facts_high_cost > 0:
        hc_extra = min(facts_high_cost, remaining).quantize(D('0.01'))
        remaining -= hc_extra
    # 4) capability plans (user-declared, capped by remaining)
    cap_total = ZERO
    for i, plan in enumerate(prefs.get('capability_plans') or []):
        cap_total += money(plan.get('amount'), f'preferences.capability_plans[{i}].amount')
    capability = min(cap_total, remaining).quantize(D('0.01'))
    remaining -= capability
    # 5) free discretionary (user lifestyle choice; zero in defensive mode)
    if mode == 'defensive':
        free = ZERO
    else:
        free = min(free_pref, remaining).quantize(D('0.01'))
    remaining -= free
    social_total = social + free
    # 5) conditional long-term financial investment (ceiling, never must-spend)
    invest = ZERO
    eligible = prefs.get('investment_eligible') is True
    if eligible and mode != 'defensive':
        share_i = ov['financial_invest_share']
        invest = (remaining * share_i).quantize(D('0.01'))
        invest = min(invest, remaining)
        remaining -= invest
    biz = money(prefs.get('business_capital_plan') or '0', 'preferences.business_capital_plan')
    biz = min(biz, remaining).quantize(D('0.01'))
    remaining -= biz
    return {
        'status': 'OK',
        'buckets': {
            'safety_savings': {'add_this_period': q(safety_add), 'extra_high_cost_debt_repayment': q(hc_extra),
                               'use_of_reserve': q(ZERO),
                               'existing_eligible': q(safety_cash) if safety_cash is not None else None,
                               'target_months': None, 'target_amount': None,
                               'gap_after': q(max(ZERO, reserve_gap - safety_add)),
                               'rationale': f'gap-driven fill (share {share}, editable); extra repayment only for APR >= {ov["high_cost_apr_threshold"]}'},
            'living': {'fixed': q(floor['fixed']), 'variable': q(floor['variable']),
                       'debt_service_cash': q(floor['debt_service_cash']), 'funded': q(living_total),
                       'total': q(living_total),
                       'rationale': 'necessary floor: fixed+variable necessities + contractual debt service (principal-vs-interest split is a net-worth layer question)'},
            'necessary_investment': {'capability': q(capability), 'financial': q(invest),
                                     'business_capital': q(biz), 'total': q(capability + invest + biz),
                                     'rationale': 'capability = declared human-capital plans (real spending); financial = conditional ceiling '
                                                  + ('(eligible)' if eligible else '(NOT eligible: high-cost debt / liquidity first)') + '; not a must-spend quota'},
            'social_discretionary': {'committed': q(social), 'free': q(free), 'total': q(social_total),
                                     'rationale': 'committed relationship/obligation floor preserved; free spending is a user-kept lifestyle choice, capped by remaining surplus'},
        },
        'unallocated': q(remaining),
        'deficit': None,
        'assumptions': assumptions,
    }


def high_cost_balance(data: dict, ov: dict) -> Decimal:
    total = ZERO
    for i, d in enumerate(data.get('high_cost_debt') or []):
        apr = money(d.get('apr'), f'high_cost_debt[{i}].apr')
        if apr >= ov['high_cost_apr_threshold']:
            total += money(d.get('balance'), f'high_cost_debt[{i}].balance')
    return total


def build_plan(data: dict) -> dict:
    fx = FX(data.get('fx'), data['currency'], data['as_of'])
    alloc = build_allocatable(data, fx)
    basis = classify_income(data, alloc)
    floor = living_floor(data)
    ov, ov_src = overrides(data)
    prefs = data.get('preferences') or {}
    facts = data.get('facts') or {}

    cash_raw = facts.get('safety_eligible_cash')
    safety_cash = money(cash_raw, 'facts.safety_eligible_cash') if cash_raw is not None else None
    for restricted in ('pf_simulated_funds', 'restricted_investment_assets'):
        if facts.get(restricted) is not None:
            money(facts[restricted], f'facts.{restricted}')  # validated, never merged into safety cash
    r_months, r_target, r_source = reserve_target(data, floor['total'])
    reserve_gap = max(ZERO, r_target - (safety_cash or ZERO)) if r_target is not None else ZERO
    hc_total = high_cost_balance(data, ov)
    if hc_total > 0 and prefs.get('investment_eligible') is True:
        # not an error: user claim recorded, but engine reports the priority inversion
        alloc['unknowns'].append('investment_eligible=true while high-cost debt exists; financial bucket stays 0 until extra repayment plan agreed (priority rule)')

    allocatable = alloc['amount'].quantize(D('0.01'))
    alloc['amount'] = allocatable
    balanced = allocate('balanced', allocatable, floor, data, ov, ov_src, safety_cash, reserve_gap, hc_total)
    defensive = allocate('defensive', allocatable, floor, data, ov, ov_src, safety_cash, reserve_gap, hc_total)

    # status-quo comparison from user-reported current pattern
    cp = data.get('current_pattern') or None
    sq = None
    if cp:
        sq_total = sum((money(cp.get(k) or '0', f'current_pattern.{k}') for k in
                        ('living', 'savings_add', 'capability', 'financial_investment', 'social', 'unallocated')), ZERO)
        viable = sq_total <= allocatable
        sq = {'name': 'status_quo', 'viable': viable,
              'buckets': {'living': q(money(cp.get('living') or '0', 'current_pattern.living')),
                          'safety_savings': q(money(cp.get('savings_add') or '0', 'current_pattern.savings_add')),
                          'necessary_investment': q(money(cp.get('capability') or '0', 'current_pattern.capability')
                                                    + money(cp.get('financial_investment') or '0', 'current_pattern.financial_investment')),
                          'social_discretionary': q(money(cp.get('social') or '0', 'current_pattern.social')),
                          'unallocated': q(money(cp.get('unallocated') or '0', 'current_pattern.unallocated'))},
              'summary': ('reported pattern fits allocatable' if viable else
                          f'reported pattern {q(sq_total)} exceeds allocatable {q(allocatable)}: UNSUSTAINABLE without reserve draw')}

    b = balanced['buckets']
    # DEFICIT periods conserve on actually funded amounts; the full requirement
    # stays visible in living.total and the explicit deficit gap.
    living_in_conservation = D(b['living'].get('funded') if balanced['status'] == 'DEFICIT' else b['living']['total'])
    sum_b = (D(b['safety_savings']['add_this_period']) + D(b['safety_savings']['extra_high_cost_debt_repayment'])
             + living_in_conservation + D(b['necessary_investment']['total'])
             + D(b['social_discretionary']['total']) + D(balanced['unallocated']))
    conservation_holds = sum_b == allocatable
    if not conservation_holds:
        die(f'internal conservation violation: {q(sum_b)} != {q(allocatable)}')

    no_change = None
    if sq and sq['viable']:
        diffs = [abs(D(sq['buckets']['safety_savings']) - D(b['safety_savings']['add_this_period'])),
                 abs(D(sq['buckets']['living']) - D(b['living']['total'])),
                 abs(D(sq['buckets']['necessary_investment']) - D(b['necessary_investment']['total'])),
                 abs(D(sq['buckets']['social_discretionary']) - D(b['social_discretionary']['total']))]
        no_change = all(d <= PCT * allocatable for d in diffs) and reserve_gap == 0

    status = balanced['status']
    if status != 'DEFICIT' and (alloc['tax_status'] == 'UNKNOWN_TAX_CONDITIONAL' or safety_cash is None
                                or basis['classification'] == 'INSUFFICIENT_HISTORY' or not alloc['received']):
        status = 'CONDITIONAL'

    unknowns = list(alloc['unknowns']) + list(basis['warnings'])
    if cash_raw is None:
        unknowns.append('safety_eligible_cash UNKNOWN: reserve gap not computable; savings advice stays conditional')
    if facts.get('opening_balance_before_period') is None:
        unknowns.append('opening balance before period UNKNOWN: retention-rate claims from two-month data are rejected')

    goals = data.get('goals') or []
    mp_links = [{'goal': g.get('name'), 'purpose_pool': g.get('purpose_pool'),
                 'funded_from': 'four_bucket.safety_savings' if (g.get('purpose_pool') in (None, 'liquidity')) else 'existing_assets_earmark'}
                for g in goals]

    return {
        'schema_version': '5.7.0',
        'generated_for': data['as_of'],
        'currency': data['currency'],
        'status': status,
        'allocatable': {'amount': q(allocatable),
                        'basis': 'received income of the budgeted period minus known tax due and business operating reserve; '
                                 'contractual obligations are inside the Living bucket (not pre-deducted)',
                        'tax_status': alloc['tax_status'],
                        'fx_conversions': alloc['fx_log'],
                        'excluded_not_received': q(alloc['gross']) if not alloc['received'] else None},
        'income_basis': basis,
        'buckets': b,
        'unallocated': balanced['unallocated'],
        'conservation': {'allocatable': q(allocatable), 'sum_buckets_plus_unallocated': q(sum_b), 'holds': True},
        'deficit': balanced['deficit'],
        'zero_income_stress': {
            'floor_monthly': q(floor['total']),
            'eligible_cash': q(safety_cash) if safety_cash is not None else None,
            'coverage_months': (q(safety_cash / floor['total']) if (safety_cash is not None and floor['total'] > 0) else None),
        },
        'comparisons': [defensive_comparison(defensive),
                        {'name': 'balanced', 'viable': True,
                         'buckets': {'safety_savings': q(D(b['safety_savings']['add_this_period']) + D(b['safety_savings']['extra_high_cost_debt_repayment'])),
                                     'living': b['living']['total'], 'necessary_investment': b['necessary_investment']['total'],
                                     'social_discretionary': b['social_discretionary']['total'], 'unallocated': balanced['unallocated']},
                         'summary': 'gap-driven priority allocation with explicit assumptions'},
                        (sq or {'name': 'status_quo', 'viable': None, 'buckets': {}, 'summary': 'NO_BASELINE: user did not report a current pattern'})],
        'no_change_recommended': no_change,
        'master_plan_links': mp_links,
        'assumptions': (balanced['assumptions'] + [
            {'id': 'reserve_months_target', 'value': str(r_months), 'source': r_source},
            {'id': 'reserve_target_amount', 'value': q(r_target) if r_target is not None else 'N/A', 'source': 'CALCULATED'},
            {'id': 'high_cost_apr_threshold', 'value': str(ov['high_cost_apr_threshold']), 'source': 'HEURISTIC_EDITABLE'},
        ]),
        'unknowns': unknowns,
        'review_reminders': [
            'next month: compare planned vs actual per bucket; report net NEW savings (income - consumption), not transfers',
            'internal transfers (bank->brokerage) and market gains are never new savings',
            're-run when income stability, family structure, debts or goals materially change',
        ],
    }


def defensive_comparison(defensive: dict) -> dict:
    b = defensive['buckets']
    return {'name': 'defensive', 'viable': True,
            'buckets': {'safety_savings': q(D(b['safety_savings']['add_this_period']) + D(b['safety_savings']['extra_high_cost_debt_repayment'])),
                        'living': b['living']['total'], 'necessary_investment': b['necessary_investment']['total'],
                        'social_discretionary': b['social_discretionary']['total'], 'unallocated': defensive['unallocated']},
            'summary': 'reserve-gap-first; free social spend and risk investment closed'}


def cmd_plan(args) -> int:
    raw = sys.stdin.read() if args.input in ('-', 'stdin') else Path(args.input).read_text(encoding='utf-8')
    data = load_input(raw)
    result = build_plan(data)
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    # exit-code contract: 0 = OK/CONDITIONAL plan produced, 2 = DEFICIT (gap
    # reported, never negative savings), 3 = invalid input (die()).
    return 2 if result['status'] == 'DEFICIT' else 0


def render_markdown(r: dict) -> str:
    b = r['buckets']
    lines = [
        f"# Four-Bucket Budget ({r['currency']}, status {r['status']})",
        '',
        f"- Allocatable this period: **{r['allocatable']['amount']}** ({r['allocatable']['tax_status']})",
        f"- Income basis: {r['income_basis']['classification']} ({r['income_basis']['months_analyzed']} months)",
        '',
        '| Bucket | Amount | Share | Rationale |', '|---|---|---|---|',
    ]
    alloc = D(r['allocatable']['amount']) or D('1')
    rows = [
        ('Safety & savings', D(b['safety_savings']['add_this_period']) + D(b['safety_savings']['extra_high_cost_debt_repayment']), b['safety_savings']['rationale']),
        ('Living (necessary)', D(b['living']['total']), b['living']['rationale']),
        ('Necessary investment', D(b['necessary_investment']['total']), b['necessary_investment']['rationale']),
        ('Social & discretionary', D(b['social_discretionary']['total']), b['social_discretionary']['rationale']),
        ('Unallocated', D(r['unallocated']), 'kept unassigned rather than forced into a bucket'),
    ]
    for name, amount, why in rows:
        share = (amount / alloc * 100).quantize(D('0.1'))
        lines.append(f'| {name} | {q(amount)} | {share}% | {why[:90]} |')
    lines += ['', f"Conservation holds: {r['conservation']['holds']} ({r['conservation']['allocatable']})",
              f"Zero-income stress coverage: {r['zero_income_stress']['coverage_months']} months"]
    if r['deficit']:
        lines.append(f"DEFICIT gap {r['deficit']['gap']}; optional reserve draw {r['deficit']['reserve_draw_available']}")
    if r['unknowns']:
        lines += ['', '## Unknowns / conditions', *[f'- {u}' for u in r['unknowns']]]
    if r['assumptions']:
        lines += ['', '## Assumptions', *[f"- {a['id']} = {a['value']} [{a['source']}]" for a in r['assumptions']]]
    return '\n'.join(lines)


def cmd_review(args) -> int:
    raw = sys.stdin.read() if args.input in ('-', 'stdin') else Path(args.input).read_text(encoding='utf-8')
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f'review input is not valid JSON: {exc}')
    plan = data.get('plan') or {}
    act = data.get('actuals') or {}
    if plan.get('schema_version') != '5.7.0':
        die("review requires the prior plan with schema_version '5.7.0'")
    for key in ('income_received', 'living_spent', 'social_spent'):
        if key not in act:
            die(f'actuals missing {key}')

    income = money(act['income_received'], 'actuals.income_received')
    living = money(act['living_spent'], 'actuals.living_spent')
    social = money(act['social_spent'], 'actuals.social_spent')
    capability = money(act.get('capability_spent') or '0', 'actuals.capability_spent')
    invested = money(act.get('financial_invested') or '0', 'actuals.financial_invested')
    extra_debt = money(act.get('extra_debt_repayment') or '0', 'actuals.extra_debt_repayment')
    reserve_add = money(act.get('reserve_addition_actual') or '0', 'actuals.reserve_addition_actual')
    transfers = money(act.get('internal_transfers') or '0', 'actuals.internal_transfers')

    net_new_savings = income - living - social - capability
    deployed = living + social + capability + invested + extra_debt + reserve_add + transfers
    unexplained = income - deployed
    floor = D(plan['zero_income_stress']['floor_monthly']) if plan.get('zero_income_stress') else ZERO
    reserve_end = money(act['reserve_end_balance'], 'actuals.reserve_end_balance') if act.get('reserve_end_balance') is not None else None

    buckets = plan.get('buckets') or {}
    def variance(key_path: str, actual: Decimal) -> dict | None:
        planned = None
        if key_path == 'living':
            planned = D(buckets['living']['total']) if buckets.get('living') else None
        elif key_path == 'social':
            planned = D(buckets['social_discretionary']['total']) if buckets.get('social_discretionary') else None
        elif key_path == 'safety':
            planned = D(buckets['safety_savings']['add_this_period']) if buckets.get('safety_savings') else None
        if planned is None:
            return None
        return {'planned': q(planned), 'actual': q(actual), 'variance': q(actual - planned),
                'variance_pct': (q((actual - planned) / planned * 100) if planned > 0 else 'n/a')}

    flags: list[str] = []
    if invested > 0 and net_new_savings <= 0:
        flags.append('REALLOCATION_NOT_NEW_SAVINGS: investment increased while net new savings <= 0; '
                     'money came from existing balances (internal reallocation), not from new retained income')
    if transfers > 0:
        flags.append('internal transfers are neither consumption nor new savings; excluded from all deltas')
    if abs(unexplained) > D('0.01') * max(D('1'), income):
        flags.append(f'large unexplained cash difference: {q(unexplained)}; reconcile before trusting the review')
    result = {
        'schema_version': '5.7.0',
        'status': 'OK',
        'net_new_savings': q(net_new_savings),
        'savings_definition': 'income_received - living - social - capability (investment purchases, debt prepayment and internal transfers are uses of savings, not consumption)',
        'variances': {k: v for k, v in (('living', variance('living', living)),
                                        ('social', variance('social', social)),
                                        ('safety', variance('safety', reserve_add))) if v},
        'unexplained_cash_difference': q(unexplained),
        'internal_transfers_excluded': q(transfers),
        'investment_vs_savings_flags': flags,
        'reserve_coverage_months': (q(reserve_end / floor) if (reserve_end is not None and floor > 0) else None),
        'review_rules_reminder': [
            'income clearly below plan -> cut free social first, never necessary floor',
            'reserve was drawn -> restore before increasing discretionary or investment',
            'income clearly above plan -> surplus goes to reserve/goals first to avoid lifestyle inflation',
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan', help='build a four-bucket budget from a layer-1 fact input')
    p.add_argument('--input', required=True, help="JSON file path, or '-' for stdin (private data stays off disk)")
    p.add_argument('--format', choices=['json', 'md'], default='json')
    p.set_defaults(func=cmd_plan)
    r = sub.add_parser('review', help='compare a prior plan JSON with actual monthly figures')
    r.add_argument('--input', required=True, help="JSON file path or '-' for stdin")
    r.set_defaults(func=cmd_review)
    args = ap.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
