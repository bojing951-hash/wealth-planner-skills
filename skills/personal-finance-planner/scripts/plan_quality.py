#!/usr/bin/env python3
"""Optional v5.3 structural + deterministic audit for a professional-plan JSON.

Not a substitute for qualified financial judgment, current law or blind A/B evaluation.
Does not autonomously call any tool or write client data.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

D = Decimal


def dec(v: Any, name: str, issues: list[str]) -> Decimal | None:
    if isinstance(v, bool):
        issues.append(f'{name}: bool is not a money amount')
        return None
    try:
        x = D(str(v))
        if not x.is_finite():
            raise InvalidOperation()
        return x
    except (InvalidOperation, ValueError, TypeError):
        issues.append(f'{name}: invalid decimal')
        return None


def value(obj: dict, name: str, issues: list[str]) -> Any:
    if name not in obj:
        issues.append(f'missing: {name}')
    return obj.get(name)


def substantive(s: Any, field: str, issues: list[str], min_chars: int = 18) -> None:
    generic = {'saving is important', 'invest regularly', 'diversify', '待补充', 'tbd', 'later', 'n/a', 'none', 'unknown', '理性投资', '建议长期投资'}
    if not isinstance(s,str) or len(s.strip()) < min_chars or s.strip().lower() in generic:
        issues.append(f'{field}: missing client-specific explanation')


def audit(plan: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan,dict):
        return {'ok':False,'errors':['report must be a JSON object'],'warnings':[], 'scope':'structure/math only'}
    if plan.get('schema_version') != '5.3.0':
        errors.append('schema_version: expected 5.3.0')
    if plan.get('report_kind') != 'COMPREHENSIVE':
        errors.append('report_kind: expected COMPREHENSIVE for full consultation')
    try:
        date.fromisoformat(str(value(plan,'as_of',errors)))
    except ValueError:
        errors.append('as_of: invalid ISO date')
    if plan.get('mode') not in {'HYPOTHETICAL','USER_REPORTED','PARTIALLY_VERIFIED'}:
        errors.append('mode: must label hypothetical or real un/partially verified')
    substantive(value(plan,'client_objective',errors),'client_objective',errors)

    dq=value(plan,'data_quality',errors)
    if not isinstance(dq,dict):
        errors.append('data_quality must be an object')
    else:
        for field in ('verified','user_reported','assumed','unknown','material_gaps'):
            if not isinstance(dq.get(field),list):
                errors.append(f'data_quality.{field} must be list')
        if plan.get('mode')=='HYPOTHETICAL' and not dq.get('assumed'):
            errors.append('hypothetical inputs must be labeled assumed')

    fs=value(plan,'financial_snapshot',errors)
    money = {}
    if not isinstance(fs,dict):
        errors.append('financial_snapshot must be object')
    else:
        if not isinstance(fs.get('currency'),str) or len(fs['currency'])!=3 or not fs['currency'].isalpha() or not fs['currency'].isupper():
            errors.append('financial_snapshot.currency must be uppercase 3-letter code')
        for field in ('monthly_net_received','monthly_essential','monthly_discretionary',
                      'monthly_other_obligations','monthly_surplus','owned_unrestricted_cash',
                      'emergency_reserve_target','near_term_goal_cash','eligible_long_term_initial'):
            money[field]=dec(value(fs,field,errors),field,errors)
        if all(money.get(v) is not None for v in ('monthly_net_received','monthly_essential','monthly_discretionary','monthly_other_obligations','monthly_surplus')):
            expected = money['monthly_net_received'] - money['monthly_essential'] - money['monthly_discretionary'] - money['monthly_other_obligations']
            if abs(expected-money['monthly_surplus'])>D('0.01'):
                errors.append('monthly_surplus does not reconcile to net cash minus outflows')
        for field in ('monthly_net_received','monthly_essential','monthly_discretionary','monthly_other_obligations','owned_unrestricted_cash','emergency_reserve_target','near_term_goal_cash','eligible_long_term_initial'):
            if money.get(field) is not None and money[field]<0:
                errors.append(f'{field} cannot be negative')
        if all(money.get(v) is not None for v in ('owned_unrestricted_cash','emergency_reserve_target','near_term_goal_cash','eligible_long_term_initial')):
            cap = max(D('0'),money['owned_unrestricted_cash']-money['emergency_reserve_target']-money['near_term_goal_cash'])
            if money['eligible_long_term_initial'] > cap+D('0.01'):
                errors.append('eligible_long_term_initial exceeds unreserved owned cash')
        reserve_months=fs.get('reserve_months')
        if type(reserve_months) is not int or reserve_months<0 or reserve_months>60:
            errors.append('reserve_months must be int 0..60; heuristic')
        elif money.get('monthly_essential') is not None and money.get('emergency_reserve_target') is not None:
            if abs(money['monthly_essential']*reserve_months-money['emergency_reserve_target'])>D('0.01'):
                errors.append('emergency reserve target does not reconcile with essential × months')
        if money.get('monthly_surplus') is not None and money['monthly_surplus']<0:
            warnings.append('negative surplus: substantive plan must prioritize solvency')

    issues=value(plan,'diagnoses',errors)
    issue_ids=set()
    if not isinstance(issues,list):
        errors.append('diagnoses must be array')
        issues=[]
    if not issues:
        substantive(plan.get('no_material_issue_reason'),'no_material_issue_reason',errors)
    for idx,it in enumerate(issues):
        if not isinstance(it,dict):
            errors.append(f'diagnoses[{idx}] must be object')
            continue
        iid=it.get('id')
        if not isinstance(iid,str) or not iid.strip() or iid in issue_ids:
            errors.append(f'diagnoses[{idx}].id missing or duplicate')
        else:issue_ids.add(iid)
        if it.get('priority') not in ('CRITICAL','HIGH','MEDIUM','LOW'):
            errors.append(f'{iid}: invalid priority')
        for field in ('observed_condition','root_cause_or_hypothesis','goal_effect','priority_reason'):
            substantive(it.get(field),f'{iid}.{field}',errors)
        if not isinstance(it.get('evidence_refs'),list) or not it['evidence_refs']:
            errors.append(f'{iid}: requires evidence references to facts/assumptions')

    goals=value(plan,'goal_feasibility',errors)
    if not isinstance(goals,list) or not goals:
        errors.append('goal_feasibility requires at least one quantified/conditional goal')
        goals=[]
    for idx,g in enumerate(goals):
        if not isinstance(g,dict):
            errors.append(f'goal_feasibility[{idx}] invalid');continue
        for field in ('goal_id','basis','limitations'):
            if not g.get(field):errors.append(f'goal_feasibility[{idx}].{field} missing')
        for field in ('target','monthly_required','monthly_available','monthly_gap'):
            dec(value(g,field,errors),f'goal[{idx}].{field}',errors)
        need=dec(g.get('monthly_required'),'monthly_required',[])
        available=dec(g.get('monthly_available'),'monthly_available',[])
        gap=dec(g.get('monthly_gap'),'monthly_gap',[])
        if None not in (need,available,gap) and abs(max(D('0'),need-available)-gap)>D('0.02'):
            errors.append(f'goal[{idx}]: contribution gap calculation does not reconcile')
        if g.get('assumption_status')!='HYPOTHETICAL_NOT_FORECAST':
            errors.append(f'goal[{idx}]: not explicitly marked conditional assumption')
        if type(g.get('months')) is not int or g.get('months',0)<=0:
            errors.append(f'goal[{idx}]: months must be positive integer')

    options=value(plan,'options',errors)
    optids=set()
    if not isinstance(options,list) or len(options)<2:
        errors.append('options: comprehensive plans require >=2 defensible alternatives')
        options=[]
    for idx,opt in enumerate(options):
        if not isinstance(opt,dict):errors.append(f'options[{idx}] invalid');continue
        oid=opt.get('id')
        if not isinstance(oid,str) or not oid.strip() or oid in optids:
            errors.append(f'options[{idx}].id missing or duplicated')
        else:optids.add(oid)
        if opt.get('feasibility') not in ('FEASIBLE','CONDITIONAL','INFEASIBLE'):
            errors.append(f'{oid}: invalid feasibility')
        for fld in ('mechanism','quantified_or_bounded_effect','tradeoffs'):
            substantive(opt.get(fld),f'option[{oid}].{fld}',errors)
        if not isinstance(opt.get('issue_ids'),list) or any(z not in issue_ids for z in opt.get('issue_ids',[])):
            errors.append(f'option[{oid}]: issue_ids invalid')
        if not opt.get('issue_ids') and issues:
            errors.append(f'option[{oid}]: must link to a diagnosis')
        contribution=dec(value(opt,'monthly_commitment',errors),f'option[{oid}].monthly_commitment',errors)
        if contribution is not None and contribution<0:
            errors.append(f'option[{oid}]: monthly commitment cannot be negative')
        if contribution is not None and money.get('monthly_surplus') is not None and contribution > money['monthly_surplus']+D('0.01'):
            if opt.get('feasibility')!='CONDITIONAL' or not opt.get('funding_change_source'):
                errors.append(f'option[{oid}]: exceeds surplus without conditional funding source')
            extra=dec(opt.get('extra_monthly_cash_needed'),'extra_monthly_cash_needed',errors)
            if extra is None or extra+D('0.01') < contribution-money['monthly_surplus']:
                errors.append(f'option[{oid}]: monthly funding gap insufficient')
        if not isinstance(opt.get('preconditions'),list) or not isinstance(opt.get('risks'),list):
            errors.append(f'option[{oid}]: preconditions/risks must be arrays')

    rec=value(plan,'recommendation',errors)
    if not isinstance(rec,dict):errors.append('recommendation invalid')
    else:
        if rec.get('chosen_option_id') not in optids:errors.append('recommendation must choose a stated alternative')
        substantive(rec.get('reason_for_ranking'),'recommendation.reason_for_ranking',errors)
        if not isinstance(rec.get('blockers'),list):errors.append('recommendation.blockers missing')
        if rec.get('is_authorized_to_execute') is not False:
            errors.append('recommendation cannot confer permission for external money/tax actions')

    tasks=value(plan,'actions',errors)
    linked=set()
    if not isinstance(tasks,list) or not tasks:
        errors.append('actions: must have concrete accountable work')
        tasks=[]
    for idx,act in enumerate(tasks):
        if not isinstance(act,dict): errors.append(f'actions[{idx}] invalid'); continue
        if act.get('horizon') not in ('D30','D90','D365'):
            errors.append(f'actions[{idx}]: invalid horizon')
        if act.get('status') not in ('PROPOSED','USER_CONFIRMED','DONE','BLOCKED','DEFERRED'):
            errors.append(f'actions[{idx}]: invalid status')
        iid=act.get('issue_id')
        if iid not in issue_ids and issues:
            errors.append(f'actions[{idx}]: missing link to diagnosed issue')
        else:linked.add(iid)
        if act.get('owner') not in ('USER','LICENSED_PROFESSIONAL','HOST_RESEARCH_ONLY'):
            errors.append(f'actions[{idx}]: invalid owner')
        for fld in ('action','success_measure','prerequisites'):
            substantive(act.get(fld),f'actions[{idx}].{fld}',errors, min_chars=13)
    for iid in issue_ids:
        item=next((x for x in issues if isinstance(x,dict) and x.get('id')==iid),{})
        if item.get('priority') in ('CRITICAL','HIGH') and iid not in linked:
            errors.append(f'critical/high issue {iid} has no linked next action')

    review=value(plan,'review',errors)
    if not isinstance(review,dict):errors.append('review must be object')
    else:
        if not isinstance(review.get('triggers'),list) or not review['triggers']:
            errors.append('review: trigger list missing')
        if review.get('memory_status') not in ('OFF','OPT_IN_NOT_WRITTEN','APPROVED_PERSISTED'):
            errors.append('review: actual memory status missing')
        if review.get('has_background_monitoring') is not False:
            errors.append('review: no implicit ongoing background monitoring')

    audit_data=value(plan,'audit',errors)
    if not isinstance(audit_data,dict):errors.append('audit: must be object')
    else:
        for field in ('tax_legal_status','model_limitations','tools_actually_used','material_unknowns'):
            if field not in audit_data: errors.append(f'audit.{field} missing')
        if audit_data.get('tax_legal_status') not in ('VERIFIED_FOR_SCOPE','NOT_VERIFIED','NOT_APPLICABLE'):
            errors.append('audit.tax_legal_status invalid')
    return {
        'ok':not errors,
        'errors':errors,
        'warnings':warnings,
        'scope':'STRUCTURE_AND_LIMITED_ARITHMETIC_ONLY; NOT_LEGAL_TAX_EXPERT_CERTIFICATION_OR_REAL_HOST_A_B_TEST',
        'checks':'Goal monthly gap, cashflow and reserve reconciliation, alternatives, traceability, implementation actions, evidence status',
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True)
    p.add_argument('--json',action='store_true')
    a=p.parse_args()
    report=audit(json.loads(Path(a.input).read_text(encoding='utf-8')))
    if a.json:print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        print('Professional plan structural gate:', 'PASS' if report['ok'] else 'FAIL')
        for s in report['errors']:print('ERROR:',s)
        for s in report['warnings']:print('WARNING:',s)
        print('LIMIT:',report['scope'])
    return 0 if report['ok'] else 1


if __name__=='__main__':
    raise SystemExit(main())
