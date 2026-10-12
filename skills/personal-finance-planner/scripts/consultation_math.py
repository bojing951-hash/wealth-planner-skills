#!/usr/bin/env python3
"""Optional deterministic *illustrative* feasibility calculation for the v5.3 Skill.

No external retrieval, tax interpretation, financial transactions, persistence or agents.
The host decides which user facts and hypothetical return assumptions to pass.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

D = Decimal


def number(value, name: str, *, minimum: Decimal | None = D('0')) -> Decimal:
    try:
        n = D(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f'{name} is not a decimal number') from exc
    if not n.is_finite() or (minimum is not None and n < minimum):
        raise ValueError(f'{name} must be a finite number >= {minimum}')
    return n


def quant(n: Decimal) -> str:
    return str(n.quantize(D('0.01')))


def monthly_rate(annual_return: Decimal) -> Decimal:
    if annual_return <= -1 or annual_return > 1:
        raise ValueError('annual_return_assumed must be > -100% and <= 100% (scenario cap)')
    # Float used only for the fractional exponent; amounts are Decimal.
    return D(str((1 + float(annual_return)) ** (1 / 12) - 1))


def fixed_return_goal(
    initial_long_term: Decimal,
    monthly_contribution: Decimal,
    target: Decimal,
    months: int,
    annual_return: Decimal,
) -> dict:
    if not isinstance(months, int) or months <= 0 or months > 1200:
        raise ValueError('months must be an integer in 1..1200')
    values = (initial_long_term, monthly_contribution, target)
    if any(x < 0 or not x.is_finite() for x in values):
        raise ValueError('monetary values must be finite and nonnegative')
    i = monthly_rate(annual_return)
    growth = (D('1') + i) ** months
    annuity = D(months) if abs(i) < D('1e-12') else (growth - 1) / i
    future_value = initial_long_term * growth + monthly_contribution * annuity
    required = max(D('0'), (target - initial_long_term * growth) / annuity)
    return {
        'future_value': quant(future_value),
        'monthly_contribution_required': quant(required),
        'monthly_gap': quant(max(D('0'), required - monthly_contribution)),
        'goal_shortfall_at_horizon': quant(max(D('0'), target - future_value)),
        'mathematical_status': 'FIXED_HYPOTHETICAL_RETURN_NOT_A_FORECAST',
    }


def future_value_with_protected_cash(
    initial_long_term: Decimal,
    monthly_surplus: Decimal,
    protected_shortfall: Decimal,
    months: int,
    annual_return: Decimal,
) -> tuple[Decimal,Decimal,int]:
    """Allocate positive net cash to short-goal and emergency cash before investing.

    Protected cash is assumed to earn 0% in this simplified illustrative example.
    End-of-month top-ups; future investments also happen at end of month.
    """
    i=monthly_rate(annual_return)
    balance=initial_long_term
    need=protected_shortfall
    months_to_fill=0
    for m in range(months):
        balance *= (D('1')+i)
        new_cash = max(D('0'),monthly_surplus)
        held = min(new_cash,need)
        need -= held
        invested = new_cash-held
        balance += invested
        if held>0:
            months_to_fill=m+1
    return balance,need,months_to_fill


def required_surplus_after_reserves(
    initial_long_term: Decimal,
    protected_shortfall: Decimal,
    target: Decimal,
    months: int,
    annual_return: Decimal,
) -> Decimal:
    """Numerically solve minimum TOTAL monthly savings, allowing for reserve refill."""
    if target<=0:
        return D('0')
    def result(x):
        return future_value_with_protected_cash(initial_long_term,x,protected_shortfall,months,annual_return)[0]
    if result(D('0'))>=target:
        return D('0')
    hi=max(D('1'),required_monthly_identity(initial_long_term,target,months,annual_return) + protected_shortfall / months)
    for _ in range(100):
        if result(hi)>=target:
            break
        hi*=2
    else:
        raise ValueError('cannot bracket required monthly surplus')
    lo=D('0')
    for _ in range(105):
        mid=(hi+lo)/2
        if result(mid)>=target:hi=mid
        else:lo=mid
    return hi


def required_monthly_identity(start:Decimal,target:Decimal,months:int,annual_return:Decimal)->Decimal:
    i=monthly_rate(annual_return)
    growth=(D('1')+i)**months
    annuity=D(months) if abs(i)<D('1e-12') else (growth-1)/i
    return max(D('0'),(target-start*growth)/annuity)


def calculate(payload: dict) -> dict:
    expected = (
        'currency', 'monthly_net_received', 'monthly_essential',
        'monthly_discretionary', 'monthly_other_obligations',
        'owned_unrestricted_cash', 'reserve_months',
        'near_term_goals_cash', 'goal_target', 'goal_months',
        'annual_net_return_assumed',
    )
    for key in expected:
        if key not in payload:
            raise ValueError(f'missing field: {key}')
    if not isinstance(payload['currency'], str) or len(payload['currency']) != 3 or not payload['currency'].isalpha() or not payload['currency'].isupper():
        raise ValueError('currency must be a 3-letter uppercase ISO code')
    if payload.get('is_real_user_data') is True and payload.get('tax_status') not in ('settled', 'not_applicable', 'professional_verified'):
        raise ValueError('actual net cash flow needs tax_status settled or explicit conditional scenario instead')
    numeric_fields = {
        k: number(payload[k], k) for k in (
            'monthly_net_received', 'monthly_essential',
            'monthly_discretionary', 'monthly_other_obligations',
            'owned_unrestricted_cash', 'near_term_goals_cash',
            'goal_target',
        )
    }
    if type(payload['reserve_months']) is not int or not 0 <= payload['reserve_months'] <= 60:
        raise ValueError('reserve_months must be int 0..60; heuristic, not universal')
    if type(payload['goal_months']) is not int or not 1 <= payload['goal_months'] <= 1200:
        raise ValueError('goal_months must be int 1..1200')
    ret = number(payload['annual_net_return_assumed'], 'annual_net_return_assumed', minimum=None)
    monthly_outflows = sum((numeric_fields[k] for k in ('monthly_essential', 'monthly_discretionary', 'monthly_other_obligations')), D('0'))
    surplus = numeric_fields['monthly_net_received'] - monthly_outflows
    reserve_target = numeric_fields['monthly_essential'] * payload['reserve_months']
    cash = numeric_fields['owned_unrestricted_cash']
    protected = reserve_target + numeric_fields['near_term_goals_cash']
    cash_after_reserves = max(D('0'), cash-protected)
    protected_shortfall=max(D('0'), protected-cash)
    reserve_shortfall=max(D('0'),reserve_target-max(D('0'),cash-numeric_fields['near_term_goals_cash']))
    near_term_shortfall=max(D('0'),numeric_fields['near_term_goals_cash']-cash)
    calculations = fixed_return_goal(cash_after_reserves, max(D('0'),surplus),numeric_fields['goal_target'],payload['goal_months'],ret)
    # Correct simple-annuity overstatement if the protection buffer is initially not funded.
    actual_future,unfilled,fill_month=future_value_with_protected_cash(
        cash_after_reserves,surplus,protected_shortfall,payload['goal_months'],ret)
    required=required_surplus_after_reserves(cash_after_reserves,protected_shortfall,numeric_fields['goal_target'],payload['goal_months'],ret)
    calculations.update({
        'future_value':quant(actual_future),
        'monthly_contribution_required':quant(required),
        'monthly_gap':quant(max(D('0'), required-max(D('0'),surplus))),
        'goal_shortfall_at_horizon':quant(max(D('0'),numeric_fields['goal_target']-actual_future)),
        'unfunded_protected_cash_at_horizon':quant(unfilled),
        'months_with_protected_cash_top_up':fill_month,
        'required_monthly_amount_basis':'TOTAL_POSITIVE_MONTHLY_SURPLUS_INCLUDING_BUFFER_REFILL',
    })
    return {
        'currency': payload['currency'],
        'monthly_conditional_surplus': quant(surplus),
        'reserve_target_heuristic': quant(reserve_target),
        'reserve_shortfall': quant(reserve_shortfall),
        'near_term_shortfall':quant(near_term_shortfall),
        'protected_cash_shortfall_at_start':quant(protected_shortfall),
        'near_term_goals_cash': quant(numeric_fields['near_term_goals_cash']),
        'long_term_start_after_reserved_cash': quant(cash_after_reserves),
        'target_months':payload['goal_months'],
        'goal_target':quant(numeric_fields['goal_target']),
        'annual_return_assumed':str(ret),
        'goal_math':calculations,
        'cashflow_basis':'USER_SUPPLIED_NET_RECEIVED_OR_HYPOTHETICAL; VERIFY_OR_WITHHOLD_DECISION',
        'limitations':[
            'Pure annuity identity assuming fixed net nominal return; no probabilistic forecast.',
            'Cash reserve and near-term obligations held out of initial long-term capital; positive monthly savings replenish any protected-cash deficit first.',
            'This calculation does not account for taxes not already reflected, business costs, loss events or multi-currency exchange.',
            'A positive surplus may not all be investable; verify additional future liabilities, unresolved tax and household needs.',
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True, help='private JSON path; never use real data in a public repo')
    args = ap.parse_args()
    inp = json.loads(Path(args.input).read_text(encoding='utf-8'))
    print(json.dumps(calculate(inp),indent=2,ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f'INPUT_ERROR: {exc}') from exc
