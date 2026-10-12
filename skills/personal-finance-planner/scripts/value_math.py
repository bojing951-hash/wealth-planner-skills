#!/usr/bin/env python3
"""Wealth Planner v5.4 optional *deterministic* behavior-to-value calculator.

Not an agent or product recommendation.  Competing policies share the SAME
initial assets, period, currency and *hypothetical* returns.  Total modeled
liquid wealth (investments + uncommitted cash) is compared to avoid counting
cash-to-investment transfers as newly created wealth.  Emergency reserves are
held outside both scenarios and NEVER silently invested.

The `review` command reports *observed differences only*, not causal effects.
No storage, bank access, FX, tax law, model calibration or L3 operations.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import re
import sys

D = Decimal
CENT = D('0.01')


def dec(value: object, key: str, *, allow_negative: bool = False) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f'{key}: a finite decimal string is required')
    if not isinstance(value, (str, int, Decimal)):
        raise ValueError(f'{key}: use decimal strings, not binary floats')
    try:
        result = D(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f'{key}: invalid decimal') from exc
    if not result.is_finite() or (not allow_negative and result < 0):
        raise ValueError(f'{key}: value must be finite and nonnegative')
    if abs(result) > D('1e15'):
        raise ValueError(f'{key}: exceeds numerical safety limit')
    return result


def amount(x: Decimal) -> str:
    q=x.quantize(CENT, rounding=ROUND_HALF_UP)
    return format(D('0.00') if q == 0 else q, 'f')


def check_currency(code: object) -> str:
    if not isinstance(code, str) or re.fullmatch(r'[A-Z]{3}',code) is None:
        raise ValueError('currency must be a 3-letter uppercase ISO 4217 code')
    # Sufficient for a transparent single-currency comparison, not an ISO registry lookup.
    return code


def annual_rate(x: object, name: str) -> Decimal:
    v=dec(x,name,allow_negative=True)
    if not D('-1') < v <= D('1'):
        raise ValueError(f'{name} must be > -1 and <= 1; no prediction implied')
    return v


def monthly_rate(a: Decimal) -> Decimal:
    # Effective monthly return matches the given effective annual return.
    with localcontext() as ctx:
        ctx.prec=42
        if a==0:
            return D('0')
        return (D('1')+a) ** (D('1')/D('12')) - D('1')


def positive_int(x: object,name:str,min_val:int=1,max_val:int=600) -> int:
    if type(x) is not int or not min_val<=x<=max_val:
        raise ValueError(f'{name}: integer {min_val}..{max_val} required')
    return x


def cashflow(row:object,which:str)->dict:
    if not isinstance(row,dict):
        raise ValueError(f'{which}: object required')
    fields=('net_income','essential_spend','discretionary_spend','other_outflows','investment_contribution')
    out={k:dec(row.get(k),f'{which}.{k}') for k in fields}
    # These monthly outflows reduce modeled liquid assets; payments reducing loan
    # principal are NOT appropriately counted as wealth losses.  The host must
    # analyze liabilities separately when calculating NET WORTH.
    out['surplus']=out['net_income']-out['essential_spend']-out['discretionary_spend']-out['other_outflows']
    if out['surplus'] < 0:
        raise ValueError(f'{which}: negative surplus; plan must address solvency first')
    if out['investment_contribution'] > out['surplus']:
        raise ValueError(f'{which}: planned long-term contribution exceeds own net cash surplus')
    out['remaining_cash']=out['surplus']-out['investment_contribution']
    return out


def next_step(row:dict, investments:Decimal, cash:Decimal, rate_invest:Decimal, rate_cash:Decimal)->tuple[Decimal,Decimal]:
    return (investments*(1+rate_invest)+row['investment_contribution'],
            cash*(1+rate_cash)+row['remaining_cash'])


def portfolio_path(row:dict,start_invest:Decimal,start_cash:Decimal,r_invest:Decimal,r_cash:Decimal,
                   months:int,one_time_cost:Decimal=D('0')) -> dict[int,dict]:
    if one_time_cost>start_cash:
        raise ValueError('one_time_cost_proposed exceeds initial_uncommitted_cash; do not invade protected reserve')
    invested=start_invest
    cash=start_cash-one_time_cost
    result={}
    for m in range(1,months+1):
        invested,cash=next_step(row,invested,cash,r_invest,r_cash)
        if m in {12,60,120,240,360,480,600,months}:
            result[m]={'invested':invested,'uncommitted_cash':cash,'total':invested+cash}
    return result


def project(p:dict)->dict:
    """Compare two *conditional* policies against an identical counterfactual.

    Assumption discipline is enforced by having exactly ONE capital-market
    assumption set; alternative arms cannot smuggle in different returns.
    """
    if not isinstance(p,dict) or p.get('mode')!='project':
        raise ValueError('mode must be project')
    if p.get('schema_version')!='5.4':
        raise ValueError('schema_version 5.4 required')
    currency=check_currency(p.get('currency'))
    if p.get('input_status') not in ('HYPOTHETICAL','USER_REPORTED'):
        raise ValueError('input_status must be HYPOTHETICAL or USER_REPORTED; no automatic verified status')
    allowed_income=('HYPOTHETICAL_NET','OWNED_BANK_RECEIVED_NET_TAX_UNVERIFIED','OWNED_BANK_RECEIVED_NET_TAX_SETTLED')
    if p.get('income_basis') not in allowed_income:
        raise ValueError('income_basis must distinguish hypothetical from owned bank-received income; PF simulated profits are not income')
    if p['input_status']=='USER_REPORTED' and p['income_basis']=='HYPOTHETICAL_NET':
        raise ValueError('user-reported real cash cannot use hypothetical-only income basis')
    months=positive_int(p.get('months'),'months')
    init_invest=dec(p.get('initial_invested_assets'),'initial_invested_assets')
    init_cash=dec(p.get('initial_uncommitted_cash'),'initial_uncommitted_cash')
    reserve_current=dec(p.get('protected_reserve_current'),'protected_reserve_current')
    reserve_target=dec(p.get('protected_reserve_target'),'protected_reserve_target')
    cost=dec(p.get('one_time_cost_proposed','0'),'one_time_cost_proposed')
    before=cashflow(p.get('status_quo'),'status_quo')
    after=cashflow(p.get('proposal'),'proposal')
    assumptions=p.get('assumptions')
    if not isinstance(assumptions,dict) or assumptions.get('status')!='HYPOTHETICAL_NOT_FORECAST':
        raise ValueError('assumptions.status must declare hypothetical/not forecast')
    i=monthly_rate(annual_rate(assumptions.get('annual_investment_return'),'annual_investment_return'))
    c=monthly_rate(annual_rate(assumptions.get('annual_cash_return'),'annual_cash_return'))
    inflation=annual_rate(assumptions.get('annual_inflation'),'annual_inflation')
    with localcontext() as ctx:
        ctx.prec=42
        b=portfolio_path(before,init_invest,init_cash,i,c,months)
        a=portfolio_path(after,init_invest,init_cash,i,c,months,cost)
        output=[]
        extra_cash_flow=(after['surplus']-before['surplus'])
        for m in sorted(b):
            baseline=b[m]['total']; planned=a[m]['total']
            principal_delta=extra_cash_flow*m-cost
            value_delta=planned-baseline
            modeled_growth_and_reallocation=value_delta-principal_delta
            denom=(D('1')+inflation)**(D(m)/D(12))
            output.append({
              'months':m,'status_quo_liquid_assets':amount(baseline),
              'proposal_liquid_assets':amount(planned),
              'delta_total_nominal':amount(value_delta),
              'delta_new_unconsumed_cashflow_nominal':amount(principal_delta),
              'delta_modeled_growth_and_allocation_nominal':amount(modeled_growth_and_reallocation),
              'delta_total_in_today_purchasing_power':amount(value_delta/denom),
              'nominal_decomposition_check':amount(principal_delta+modeled_growth_and_reallocation),
            })
        warnings=[]
        if p['income_basis']=='OWNED_BANK_RECEIVED_NET_TAX_UNVERIFIED':
            warnings.append('TAX_UNVERIFIED: bank receipt may still carry unpaid tax; resulting investable cash remains conditional')
        if reserve_current < reserve_target:
            warnings.append('RESERVE_UNDERFUNDED: protect short-term survival; do not implement risk investing until funding plan is confirmed')
        if after['investment_contribution'] > before['investment_contribution'] and extra_cash_flow==0:
            warnings.append('REALLOCATION_NOT_NEW_SAVINGS: higher investment contributions come from existing cash surplus; do not label transferred principal as newly created wealth')
        if after['net_income']>before['net_income']:
            warnings.append('FUTURE_INCOME_UPLIFT_UNVERIFIED: additional net income is a scenario until received and taxes/costs checked')
        if after['discretionary_spend']<before['discretionary_spend']:
            warnings.append('WELLBEING_CHECK_REQUIRED: confirm that lower spending does not undermine essential needs or valued quality of life')
        if after['investment_contribution']>before['investment_contribution']:
            warnings.append('ADDITIONAL_MARKET_EXPOSURE: model does not calibrate return risk, liquidity stress or taxes; compare downside and loss capacity')
        if cost>0:
            warnings.append('ONE_TIME_COST_MODELED: the proposed upfront outlay is deducted once from investable non-reserved cash')
        return {
          'model':'VALUE_BRIDGE_FIXED_RETURN_TWO_POLICY_COUNTERFACTUAL_V5.4',
          'status':'HYPOTHETICAL_SCENARIO_NOT_OBSERVED_SAVINGS_OR_CAUSAL_EFFECT',
          'currency':currency,'months':months,'income_basis':p['income_basis'],
          'comparison_basis':'same initial owned assets, same return/inflation assumptions, monthly end-of-period flows; protected reserve held outside BOTH paths',
          'income_and_expense_basis':'after-tax user input or hypothetical net cash. Does NOT calculate local taxes or loan principal changes.',
          'status_quo_monthly':{k:amount(v) for k,v in before.items()},
          'proposal_monthly':{k:amount(v) for k,v in after.items()},
          'monthly_additional_retained_cash':amount(extra_cash_flow),
          'monthly_investment_contribution_change':amount(after['investment_contribution']-before['investment_contribution']),
          'protected_reserve_current':amount(reserve_current),
          'protected_reserve_target':amount(reserve_target),
          'long_term_policy_gate':'CONDITIONAL_RESERVE_GAP' if reserve_current<reserve_target else 'RESERVE_THRESHOLD_MET_IN_INPUT',
          'one_time_cost_proposed':amount(cost),
          'assumptions':{'annual_investment_return':str(assumptions['annual_investment_return']),
                         'annual_cash_return':str(assumptions['annual_cash_return']),
                         'annual_inflation':str(assumptions['annual_inflation'])},
          'checkpoints':output,
          'warnings':warnings,
          'scope_limitations':['No realized outcome, tax liability, pension, loan amortization, insurance pricing, risk calibration or demonstrated causal effect.','Do not count emergency reserves as investable; compare purchasing power and user wellbeing.']
        }


def validate_date(s:object,name:str)->str:
    from datetime import date
    if not isinstance(s,str):raise ValueError(f'{name}: ISO date required')
    try: iso=date.fromisoformat(s)
    except ValueError as e:raise ValueError(f'{name}: invalid ISO date') from e
    if iso.isoformat()!=s:raise ValueError(f'{name}: YYYY-MM-DD required')
    return s


def observation(o:object, label:str)->dict:
    if not isinstance(o,dict):raise ValueError(f'{label}: object required')
    out={}
    out['as_of']=validate_date(o.get('as_of'),label+'.as_of')
    out['source_status']=o.get('source_status')
    if out['source_status'] not in ('USER_REPORTED','HOST_REVIEWED_DOCUMENT'):
        raise ValueError(f'{label}.source_status must be USER_REPORTED/HOST_REVIEWED_DOCUMENT')
    if out['source_status']=='HOST_REVIEWED_DOCUMENT' and not (isinstance(o.get('source_ref'),str) and o['source_ref'].strip()):
        raise ValueError(f'{label}: host-reviewed figures require a source reference')
    out['source_ref']=o.get('source_ref')
    out['flow']=cashflow(o.get('monthly'),label+'.monthly')
    out['owned_liquid_assets']=dec(o.get('owned_liquid_assets'),label+'.owned_liquid_assets')
    return out


def review(p:dict)->dict:
    if not isinstance(p,dict) or p.get('mode')!='review' or p.get('schema_version')!='5.4':
        raise ValueError('mode review and schema_version 5.4 required')
    currency=check_currency(p.get('currency'))
    previous=observation(p.get('previous'),'previous')
    current=observation(p.get('current'),'current')
    if current['as_of'] <= previous['as_of']:
        raise ValueError('current.as_of must follow previous.as_of')
    action=p.get('action')
    if not isinstance(action,dict) or not isinstance(action.get('id'),str) or not action['id']:
        raise ValueError('action.id required')
    if action.get('status') not in ('PROPOSED','USER_CONFIRMED','USER_REPORTED_EXECUTED','DOCUMENTED_EXECUTED','BLOCKED','DEFERRED'):
        raise ValueError('action.status invalid; plans are not automatically DONE')
    if action['status']=='DOCUMENTED_EXECUTED' and not (isinstance(action.get('evidence_ref'),str) and action['evidence_ref'].strip()):
        raise ValueError('documented action needs reviewed evidence_ref')
    delta={k:current['flow'][k]-previous['flow'][k] for k in ('net_income','essential_spend','discretionary_spend','other_outflows','investment_contribution','surplus')}
    return {
        'model':'OBSERVED_FINANCIAL_STATE_CHANGE_V5.4',
        'status':'OBSERVED_INPUT_DIFFERENCE_NOT_CAUSAL_ATTRIBUTION',
        'currency':currency,
        'previous_as_of':previous['as_of'],'current_as_of':current['as_of'],
        'previous_source_status':previous['source_status'],'current_source_status':current['source_status'],
        'action_id':action['id'],'action_status':action['status'],
        'monthly_deltas':{k:amount(v) for k,v in delta.items()},
        'owned_liquid_assets_change':amount(current['owned_liquid_assets']-previous['owned_liquid_assets']),
        'claim_of_causal_effect':'NOT_ESTABLISHED',
        'interpretation':'Differences in monthly income/spending/investment and liquid asset snapshots do NOT prove the action caused the change. Market return, taxes, other inflows, timing and omitted debts may explain results.',
        'needed_for_realized_value_attribution':['period-aligned account flows and investment returns','scope-aligned after-tax amounts','material changes in income and household needs','verified implementation dates','credible counterfactual'],
    }


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('project','review'))
    parser.add_argument('--input',required=True,help='JSON file path; keep real user data out of any public repository')
    args=parser.parse_args(argv)
    try:
        payload=json.loads(Path(args.input).read_text(encoding='utf-8'))
        result=project(payload) if args.command=='project' else review(payload)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError, ArithmeticError) as e:
        print(f'VALIDATION_ERROR: {e}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
