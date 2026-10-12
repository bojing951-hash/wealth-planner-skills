#!/usr/bin/env python3
"""Offline structural/identity check for an illustrative high-income wealth plan.

Not legal review, suitability review, causal inference or proof of host quality.
The host runs it *optionally*, then applies substantive professional judgment.
"""
import argparse
from decimal import Decimal, InvalidOperation
import json
import sys
from pathlib import Path


def audit(plan, ledger):
    errors=[]
    def req(cond, reason):
        if not cond:errors.append(reason)

    req(plan.get('skill_version_loaded') == '5.5.0', 'Must report the actually installed v5.5.0; mismatch is not a passed v5.5 case')
    req(plan.get('plan_status') == 'CONDITIONAL_PARTIAL' or plan.get('plan_status') == 'CONDITIONALLY_COMPLETE', 'Plan must state provisional status')
    cash=ledger.get('cashflow',{})
    facts=plan.get('financial_facts',{})
    for key in ['reported_external_received_per_month_PROVISIONAL','current_cash_outflows',
                'higher_lifestyle_cash_outflows_if_prior_spend_continues']:
        req(facts.get(key)==cash.get(key),f'Reconciliation mismatch or missing {key}')
    tax_unknown=cash.get('tax_status')=='UNKNOWN'
    if tax_unknown:
        req(plan.get('exact_current_tax') in (None, 'NOT_VERIFIED', 'BLOCKED'), 'Cannot state precise tax when unknown')
        req(plan.get('safe_investable_cash') in (None,'UNKNOWN','NOT_VERIFIED'), 'Cannot invent net investable amount before tax is verified')
    if ledger.get('balance_sheet',{}).get('personal_net_financial_assets')=='UNKNOWN':
        req(plan.get('known_personal_net_worth') in ('UNKNOWN',None),'Cannot claim known net worth without net owned assets')
    req(plan.get('stocks_monthly_profit_counted_as_bank_cash') is False,'Broker trading P&L was treated as collected bank cash')
    req(plan.get('broker_withdrawal_counted_as_new_household_wealth') is False,'Broker→bank is internal transfer')
    req(plan.get('liquid_runway_claimed_without_balance') is False,'Cannot assert cash runway without restricted/earmarked cash balance')
    req(plan.get('tax_rate_claimed_as_statute_without_source') is False,'No legal tax rates without official source')
    req(isinstance(plan.get('user_value'),list) and len(plan['user_value'])>=2,'Provide at least two concrete user-specific financial-planning decisions')
    for dec in (plan.get('user_value') if isinstance(plan.get('user_value'),list) else []):
        req(all(dec.get(k) for k in ('decision','trigger','expected_mechanism','next_observation')),
            'Decision value must link facts → action → mechanism → metric')
    opt=plan.get('strategy_options',[])
    req(isinstance(opt,list) and len(opt)>=2,'Missing meaningful alternative financial strategies')
    if isinstance(opt,list):
        for row in opt:
            req(all(row.get(k) for k in ('name','eligibility_gate','downside','decision_tradeoff')),
                'Each strategy needs conditions, downside and tradeoff')
    waterfall=plan.get('funds_waterfall',[])
    req(isinstance(waterfall,list) and len(waterfall)>=4,'Missing ownership-aware funding waterfall')
    stress=plan.get('joint_stress',{})
    req(stress.get('pf_receipt_interruption') is True and stress.get('broker_drawdown_same_period') is True,
        'Must test PF payout loss and brokerage decline together')
    req(stress.get('liquid_runway_status') in ('UNKNOWN','CALCULATED_FROM_DOCUMENTED_LIQUIDITY'),
        'Stress liquidity must remain UNKNOWN unless source-supported')
    tasks=plan.get('actions',[])
    tasks=tasks if isinstance(tasks,list) else []
    req({a.get('horizon') for a in tasks if isinstance(a,dict)} >= {'D30','D90','D365'},
        'Missing 30/90/365 action coverage')
    for action in tasks:
        req(all(action.get(k) for k in ('action','owner','metric','status')),
            'Every user action requires an owner, observable metric and status')
        req(action.get('status') in {'PROPOSED','USER_CONFIRMED','USER_REPORTED_EXECUTED','DOCUMENTED_EXECUTED'},'Use a precise action execution status')
        if action.get('status')=='DOCUMENTED_EXECUTED':
            req(bool(action.get('execution_evidence_ref')),'Documented execution needs a matched source reference')
    req(plan.get('memory_write_authorized') is False or
        (plan.get('memory_write_authorized') is True and
         plan.get('memory_write_approval_record')=='USER_APPROVED_PER_CHANGE'),
        'Private memory writes require a specific host-side user approval record (not cryptographic proof)')
    return {'ok':not errors,'errors':errors,'scope':'OFFLINE_SYNTHETIC_STRUCTURE_AND_ACCOUNTING_ONLY',
            'does_not_validate':['tax law','investment suitability','financial-account ownership',
                                 'actual host tool calls','user approval','causal effect','real-world outcomes']}


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',required=True)
    parser.add_argument('--ledger',required=True)
    a=parser.parse_args(argv)
    try:
        plan=json.loads(Path(a.plan).read_text(encoding='utf-8'))
        led=json.loads(Path(a.ledger).read_text(encoding='utf-8'))
        output=audit(plan,led)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
        print(json.dumps({'ok':False,'errors':[type(e).__name__+': '+str(e)]}))
        return 2
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if output['ok'] else 1

if __name__=='__main__':
    raise SystemExit(main())
