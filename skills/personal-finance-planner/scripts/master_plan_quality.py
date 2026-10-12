#!/usr/bin/env python3
"""Optional static, deterministic consistency gate for a Wealth Planner Master Plan.

This does NOT research or certify tax law, financial suitability, market estimates,
user identity, approval, or actual execution. Host Agent does those jobs (with consent).
Only synthetic fixtures belong in GitHub; run private documents in a private directory.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys


def _num(value: object, label: str, errors: list[str]) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{label}: monetary amount must be a decimal string (or null)")
        return None
    try:
        x = Decimal(value)
    except (InvalidOperation, ValueError):
        errors.append(f"{label}: invalid amount")
        return None
    if not x.is_finite() or x < 0:
        errors.append(f"{label}: amount must be finite and nonnegative")
        return None
    return x


def _date(value: object, label: str, errors: list[str]) -> None:
    try:
        date.fromisoformat(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        errors.append(f"{label}: invalid ISO date")


def _check_ids(rows: object, label: str, errors: list[str]) -> set[str]:
    if not isinstance(rows, list):
        errors.append(f"{label}: expected array")
        return set()
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
            errors.append(f"{label}[{index}]: missing id")
        elif row['id'] in seen:
            errors.append(f"{label}: duplicate id {row['id']}")
        else:
            seen.add(row['id'])
    return seen


def validate(data: object) -> list[str]:
    """Check report completeness and a few accounting/permission invariants.

    Structural check is intentionally strict for *full-plan* JSON, not for narrow
    questions. It is not proof that the human advice is sound or the input verified.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return ['root: expected JSON object']
    required = ('schema_version', 'as_of', 'status', 'client_scope', 'fact_basis',
                'balance_sheet', 'cash_policy', 'goals', 'pools', 'policies',
                'options', 'stress_tests', 'actions', 'reviews', 'blockers', 'evidence', 'permissions')
    for key in required:
        if key not in data:
            errors.append(f'missing required section: {key}')
    if errors:
        return errors
    if data['schema_version'] != '5.6.0':
        errors.append('schema_version must be 5.6.0')
    _date(data['as_of'], 'as_of', errors)
    if data['status'] not in ('DRAFT', 'CONDITIONAL', 'USER_APPROVED'):
        errors.append('status must be DRAFT/CONDITIONAL/USER_APPROVED')
    if not isinstance(data['client_scope'], dict) or not data['client_scope'].get('jurisdiction'):
        errors.append('client_scope.jurisdiction is required')

    facts, bs, cash = data['fact_basis'], data['balance_sheet'], data['cash_policy']
    if not all(isinstance(x, dict) for x in (facts, bs, cash)):
        return errors+['fact_basis, balance_sheet and cash_policy must be objects']
    assets, debts = bs.get('assets'), bs.get('liabilities')
    asset_ids = _check_ids(assets, 'balance_sheet.assets', errors)
    _check_ids(debts, 'balance_sheet.liabilities', errors)
    eligible: dict[str, tuple[str, Decimal, str, str]] = {}
    if isinstance(assets, list):
        for a in assets:
            if not isinstance(a, dict) or 'id' not in a:
                continue
            aid = a['id']; own = a.get('ownership'); kind = a.get('kind')
            currency = a.get('currency')
            if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
                errors.append(f'asset {aid}: invalid ISO currency')
            v = _num(a.get('amount'), f'asset {aid}', errors)
            _date(a.get('as_of'), f'asset {aid}', errors)
            if own == 'NON_OWNED_PF' and kind != 'PF_SIMULATED':
                errors.append(f'asset {aid}: non-owned PF kind must be PF_SIMULATED')
            if kind == 'PF_SIMULATED' and own != 'NON_OWNED_PF':
                errors.append(f'asset {aid}: PF simulated funds cannot be owned')
            if own not in ('OWNED', 'RESTRICTED_BENEFICIAL', 'NON_OWNED_PF', 'THIRD_PARTY'):
                errors.append(f'asset {aid}: unknown ownership')
            if kind not in ('CASH','BROKER_NET_EQUITY','PROPERTY','BUSINESS_CAPITAL','RETIREMENT','PF_SIMULATED','OTHER'):
                errors.append(f'asset {aid}: kind must be net asset, not separately recorded P&L')
            if a.get('provenance') == 'DOCUMENTED' and not a.get('description'):
                errors.append(f'asset {aid}: undocumented provenance detail')
            if v is not None and isinstance(currency,str):
                eligible[aid] = (currency, v, str(own), str(kind))
    if isinstance(debts, list):
        for debt in debts:
            if isinstance(debt, dict):
                _num(debt.get('amount'), f'liability {debt.get("id")}', errors)
                _date(debt.get('as_of'), f'liability {debt.get("id")}', errors)
    if cash.get('tax_reserve_status') not in ('UNKNOWN','HYPOTHETICAL_HOLD','VERIFIED_OBLIGATION'):
        errors.append('cash_policy.tax_reserve_status is not valid')
    _num(cash.get('monthly_bank_received'), 'cash_policy.monthly_bank_received', errors)
    _num(cash.get('investable_amount'), 'cash_policy.investable_amount', errors)
    if facts.get('tax_status') != 'VERIFIED' and cash.get('investable_amount') is not None:
        errors.append('unverified tax status: cannot claim a numeric final investable amount')
    if cash.get('tax_reserve_status') == 'VERIFIED_OBLIGATION' and facts.get('tax_status') != 'VERIFIED':
        errors.append('tax obligation cannot be verified while tax_status is not VERIFIED')
    if facts.get('asset_completeness') == 'INCOMPLETE' and bs.get('net_worth_status') == 'RECONCILED':
        errors.append('cannot claim reconciled net worth when balance sheet is incomplete')

    pools, policies, goals, actions, options = (data.get(k) for k in ('pools','policies','goals','actions','options'))
    pool_ids = _check_ids(pools, 'pools', errors)
    policy_ids = _check_ids(policies, 'policies', errors)
    _check_ids(goals, 'goals', errors)
    _check_ids(actions, 'actions', errors)
    _check_ids(options, 'options', errors)
    for label,rows,minitems in [('pools',pools,2),('policies',policies,2),('goals',goals,1),('actions',actions,3),('options',options,2),('stress_tests',data.get('stress_tests'),1),('reviews',data.get('reviews'),2)]:
        if not isinstance(rows,list) or len(rows)<minitems:
            errors.append(f'{label}: requires at least {minitems} entries')

    amounts = defaultdict(Decimal)
    if isinstance(pools, list):
        for pool in pools:
            if not isinstance(pool,dict):continue
            pid=pool.get('id'); purpose=pool.get('purpose')
            for aa in pool.get('allocations',[]):
                if not isinstance(aa,dict):
                    errors.append(f'pool {pid}: allocation must be object');continue
                aid=aa.get('asset_id'); cur=aa.get('currency')
                v=_num(aa.get('amount'),f'pool {pid} asset {aid}',errors)
                if aid not in asset_ids or aid not in eligible:
                    errors.append(f'pool {pid}: asset {aid} not in numeric asset ledger');continue
                acur,total,own,kind=eligible[aid]
                if acur != cur:
                    errors.append(f'pool {pid}: currency mismatch for {aid} ({cur} vs {acur})')
                if own not in ('OWNED','RESTRICTED_BENEFICIAL'):
                    errors.append(f'pool {pid}: cannot assign nonowned asset {aid}')
                if own == 'RESTRICTED_BENEFICIAL' and purpose not in ('LONGEVITY','LEGACY'):
                    errors.append(f'pool {pid}: restricted {aid} cannot fund immediately accessible {purpose}')
                if v is not None: amounts[aid] += v
    for aid,alloc in amounts.items():
        if alloc > eligible[aid][1]:
            errors.append(f'asset {aid}: earmarks exceed eligible asset value (amounts redacted)')

    if isinstance(goals,list):
        for g in goals:
            if isinstance(g,dict):
                _num(g.get('target_amount'),f'goal {g.get("id")}',errors)
                if g.get('target_date') is not None:_date(g['target_date'],f'goal {g.get("id")}',errors)
    if isinstance(policies,list):
        for p in policies:
            if not isinstance(p,dict):continue
            for key in ('when','then','block_if','decision_owner','review_trigger','metric'):
                if not isinstance(p.get(key),str) or not p[key].strip():
                    errors.append(f'policy {p.get("id")}: missing {key}')
    if isinstance(options,list) and not any(isinstance(x,dict) and x.get('type')=='STATUS_QUO' for x in options):
        errors.append('options must include a status-quo counterfactual')
    if isinstance(actions,list):
        horizons=set()
        for action in actions:
            if not isinstance(action,dict):continue
            aid=action.get('id'); horizon=action.get('within_days')
            horizons.add(horizon)
            if action.get('policy_id') not in policy_ids:
                errors.append(f'action {aid}: unlinked policy_id')
            if action.get('status')=='DOCUMENTED_EXECUTED' and not action.get('proof_reference'):
                errors.append(f'action {aid}: documented execution requires evidence reference')
            for key in ('description','prerequisite','proof_metric'):
                if not isinstance(action.get(key),str) or not action[key].strip():
                    errors.append(f'action {aid}: missing {key}')
        if not set((30,90,365)).issubset(horizons):
            errors.append('full plan needs 30/90/365 day action windows')
    permission=data.get('permissions')
    if not isinstance(permission,dict) or permission.get('autonomous_financial_actions') is not False:
        errors.append('L3 autonomous financial action authorization is prohibited')
    if not isinstance(data.get('evidence'),list):
        errors.append('evidence must be a list (may be empty)')
    return errors


def main() -> int:
    parser=argparse.ArgumentParser(description='Validate PWMP structure and accounting; does NOT certify professional financial advice.')
    parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args()
    try:
        data=json.loads(args.input.read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc:
        print('FAIL: cannot read valid JSON input',str(exc));return 2
    errors=validate(data)
    if errors:
        print('FAIL — PWMP structural/accounting checks (not suitability):')
        for i,e in enumerate(errors,1):print(f'{i}. {e}')
        return 1
    print('PASS — PWMP fields and static accounting/permission checks only; NOT professional suitability or legal/tax certification.')
    return 0


if __name__=='__main__':
    sys.exit(main())
