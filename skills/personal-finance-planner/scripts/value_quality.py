#!/usr/bin/env python3
"""Optional v5.4 *structural* audit of behavior→mechanism→value→measurement cards.

Never certifies that planning improves wealth or that a tax/legal result is true.
For substantive plans only.  A correct no-change recommendation can also pass.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys


def money(raw:object,label:str,errs:list[str]) -> Decimal|None:
    if isinstance(raw,bool) or not isinstance(raw,(str,int)):
        errs.append(label+' must be a decimal string')
        return None
    try:
        d=Decimal(str(raw))
        if not d.is_finite():raise InvalidOperation
        return d
    except (InvalidOperation,ValueError):
        errs.append(label+' non-finite/invalid')
        return None


def text(value:object,label:str,errs:list[str],minimum:int=10)->None:
    if not isinstance(value,str) or len(value.strip())<minimum:
        errs.append(label+f' must be substantive ({minimum}+ chars)')


def audit(plan:dict)->dict:
    errors=[]; warnings=[]
    if not isinstance(plan,dict):
        return {'ok':False,'errors':['root must be object'],'warnings':[]}
    if plan.get('contract_version')!='5.4':errors.append('contract_version must be 5.4')
    if plan.get('kind') not in ('FULL_PLAN','FOLLOW_UP'):
        errors.append('kind must be FULL_PLAN or FOLLOW_UP')
    if plan.get('currency') is None or not isinstance(plan.get('currency'),str) or len(plan['currency'])!=3 or not plan['currency'].isupper():
        errors.append('single currency ISO-style code required; separate any other currencies')
    if plan.get('memory_written') not in (False,):
        errors.append('memory_written must be false for this audit artifact; actual authorized persistence is separate')
    cards=plan.get('value_cards')
    if not isinstance(cards,list):errors.append('value_cards must be list');cards=[]
    if not cards:
        text(plan.get('no_change_reason'),'no_change_reason',errors,minimum=35)
        text(plan.get('no_change_evidence'),'no_change_evidence',errors,minimum=20)
        if plan.get('next_review') is None:
            errors.append('next_review required even if no change is advised')
    seen=set()
    for idx,c in enumerate(cards):
        at=f'value_cards[{idx}]'
        if not isinstance(c,dict): errors.append(at+' must be object');continue
        if not isinstance(c.get('id'),str) or not c['id'].strip() or c['id'] in seen:
            errors.append(at+'.id missing or duplicate')
        else:seen.add(c['id'])
        for k in ('diagnosis_link','baseline_behavior','proposed_behavior','mechanism',
                  'assumption_and_evidence','metric','success_threshold','review_window',
                  'wellbeing_tradeoff','liquidity_and_risk_check','alternatives_considered','next_action'):
            text(c.get(k),at+'.'+k,errors,minimum=10)
        if c.get('implementation_status') not in ('PROPOSED','USER_CONFIRMED','USER_REPORTED_EXECUTED','DOCUMENTED_EXECUTED','BLOCKED','DEFERRED'):
            errors.append(at+'.implementation_status invalid')
        val=c.get('value_bridge')
        if not isinstance(val,dict):errors.append(at+'.value_bridge missing');continue
        if val.get('kind') != 'PROJECTED_COUNTERFACTUAL':
            errors.append(at+'.value_bridge.kind must be PROJECTED_COUNTERFACTUAL')
        if val.get('status')!='HYPOTHETICAL_NOT_OBSERVED':
            errors.append(at+'.value_bridge.status must be HYPOTHETICAL_NOT_OBSERVED')
        if val.get('currency')!=plan.get('currency'):
            errors.append(at+'.value_bridge.currency must match plan')
        a=money(val.get('delta_new_retained_cash'),'new cash flow',errors)
        b=money(val.get('delta_modeled_growth_and_allocation'),'modeled growth/reallocation',errors)
        t=money(val.get('delta_total'),'modeled total',errors)
        if all(x is not None for x in (a,b,t)) and abs((a+b)-t)>Decimal('.02'):
            errors.append(at+'.value_bridge arithmetic does not reconcile')
        text(val.get('same_assumptions'),'same_assumptions',errors,minimum=12)
        text(val.get('limitations'),'limitations',errors,minimum=18)
        text(val.get('model_ref'),'model_ref',errors,minimum=8)
        result=c.get('observed_outcome')
        if not isinstance(result,dict):errors.append(at+'.observed_outcome missing');continue
        if result.get('status') not in ('NOT_MEASURED','OBSERVED_DIFFERENCE_NOT_CAUSAL'):
            errors.append(at+'.observed_outcome cannot claim realized or causal gains by default')
        if result.get('status')=='OBSERVED_DIFFERENCE_NOT_CAUSAL':
            text(result.get('observation_dates'),'observation_dates',errors,minimum=12)
            text(result.get('data_sources'),'data_sources',errors,minimum=10)
        if c.get('implementation_status')=='DOCUMENTED_EXECUTED':
            text(c.get('execution_evidence_ref'),'execution_evidence_ref',errors,minimum=8)
        if c.get('implementation_status')=='PROPOSED' and result.get('status')!='NOT_MEASURED':
            errors.append(at+': PROPOSED action cannot be described as an observed effect')
        if c.get('implementation_status')=='BLOCKED' and result.get('status')!='NOT_MEASURED':
            errors.append(at+': BLOCKED action cannot claim observed effect')
    if plan.get('claim_of_realized_wealth_created') is not False:
        errors.append('claim_of_realized_wealth_created must be false in conditional plan audit')
    text(plan.get('attribution_disclaimer'),'attribution_disclaimer',errors,minimum=35)
    if plan.get('kind')=='FULL_PLAN' and not cards and not plan.get('no_change_reason'):
        errors.append('full plan without actions must explain why maintaining course is optimal')
    return {'ok':not errors,'errors':errors,'warnings':warnings,
            'scope':'STRUCTURE_AND_SIMPLE_IDENTITY_CHECK; NOT_CAUSAL_INFERENCE_OR_FINANCIAL_SUITABILITY'}


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True)
    args=p.parse_args()
    try:
        result=audit(json.loads(Path(args.input).read_text(encoding='utf-8')))
    except (OSError,json.JSONDecodeError) as e:
        print('VALIDATION_ERROR:',e,file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__=='__main__':
    raise SystemExit(main())
