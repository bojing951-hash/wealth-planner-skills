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
import re
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



# The shipped JSON Schema is the format contract.  Keep this stdlib-only subset
# here so a portable Skill validates it even when jsonschema is not installed.
# Fail closed if the schema starts using keywords not understood here.
_SCHEMA_PATH = Path(__file__).resolve().parents[1] / 'schemas/master-plan-v5.6.schema.json'
_SUPPORTED_SCHEMA_KEYS = {
    '$schema', '$id', 'title', 'description', 'type', 'const', 'enum',
    'required', 'properties', 'additionalProperties', 'items', 'minItems',
    'minLength', 'pattern', 'format', 'minimum', 'anyOf',
}


def _matches_type(value: object, typ: str) -> bool:
    return {
        'object': lambda: isinstance(value, dict),
        'array': lambda: isinstance(value, list),
        'string': lambda: isinstance(value, str),
        'integer': lambda: isinstance(value, int) and not isinstance(value, bool),
        'number': lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
        'boolean': lambda: isinstance(value, bool),
        'null': lambda: value is None,
    }[typ]()


def _same_json_scalar(a: object, b: object) -> bool:
    # Python's False == 0 and True == 1 are not JSON-Schema equality.
    return type(a) is type(b) and a == b


def _schema_validate(value: object, schema: dict, path: str = '$') -> list[str]:
    errors: list[str] = []
    unknown = set(schema) - _SUPPORTED_SCHEMA_KEYS
    if unknown:
        return [f'{path}: unsupported schema keyword(s): {sorted(unknown)}; fail closed']
    if 'anyOf' in schema:
        candidates = schema['anyOf']
        if not isinstance(candidates, list) or not candidates:
            return [f'{path}: malformed schema anyOf']
        if not any(not _schema_validate(value, option, path) for option in candidates):
            return [f'{path}: does not match any allowed schema alternative']
    if 'type' in schema:
        typ = schema['type']
        types = typ if isinstance(typ, list) else [typ]
        if not any(_matches_type(value, t) for t in types):
            return [f'{path}: expected type {typ}']
    if 'const' in schema and not _same_json_scalar(value, schema['const']):
        errors.append(f'{path}: must equal constant {schema["const"]!r}')
    if 'enum' in schema and not any(_same_json_scalar(value, candidate) for candidate in schema['enum']):
        errors.append(f'{path}: invalid enum value {value!r}; allowed {schema["enum"]}')
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{path}: missing required field {key}')
        if schema.get('additionalProperties') is False:
            for key in value.keys() - properties.keys():
                errors.append(f'{path}: extra property {key}')
        for key, sub in properties.items():
            if key in value:
                errors.extend(_schema_validate(value[key], sub, f'{path}.{key}'))
    if isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            errors.append(f'{path}: requires at least {schema["minItems"]} entries')
        if 'items' in schema:
            for index, item in enumerate(value):
                errors.extend(_schema_validate(item, schema['items'], f'{path}[{index}]'))
    if isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            errors.append(f'{path}: string shorter than {schema["minLength"]}')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            if 'amount' in path or 'investable' in path or 'received' in path:
                errors.append(f'{path}: amount must be finite and nonnegative decimal string')
            else:
                errors.append(f'{path}: invalid pattern')
        if schema.get('format') == 'date':
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                errors.append(f'{path}: invalid ISO date')
            else:
                _date(value, path, errors)
    if 'minimum' in schema and isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema['minimum']:
            errors.append(f'{path}: smaller than minimum {schema["minimum"]}')
    return errors



def permission_reference(data: dict) -> bool:
    permission = data.get('permissions')
    return isinstance(permission, dict) and isinstance(permission.get('plan_approval_reference'), str) and bool(permission['plan_approval_reference'].strip())

def _schema_errors(data: object) -> list[str]:
    try:
        schema = json.loads(_SCHEMA_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [f'cannot load bundled master-plan schema; fail closed: {exc}']

    # Reject unsupported contract keywords even in optional fields not supplied
    # by this client. Otherwise installing an updated schema could weaken a gate.
    def inspect(s: dict, path: str) -> list[str]:
        unsupported = set(s) - _SUPPORTED_SCHEMA_KEYS
        findings = [f'{path}: unsupported schema keywords {sorted(unsupported)}; fail closed'] if unsupported else []
        for k, child in s.get('properties', {}).items():
            findings.extend(inspect(child, f'{path}.properties.{k}'))
        if isinstance(s.get('items'), dict):
            findings.extend(inspect(s['items'], f'{path}.items'))
        for i, child in enumerate(s.get('anyOf', [])):
            findings.extend(inspect(child, f'{path}.anyOf[{i}]'))
        return findings
    unsupported = inspect(schema, '$schema')
    return unsupported or _schema_validate(data, schema)

def _safe_for_accounting_checks(data: dict) -> bool:
    """Avoid exceptions when malformed JSON is already rejected by schema checks."""
    if not all(isinstance(data.get(k), dict) for k in ('fact_basis', 'balance_sheet', 'cash_policy', 'permissions')):
        return False
    bs = data['balance_sheet']
    for rows in (bs.get('assets'), bs.get('liabilities'), *(data.get(k) for k in
                 ('pools', 'policies', 'goals', 'actions', 'options', 'reviews', 'stress_tests'))):
        if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
            return False
    if not all(isinstance(pool.get('allocations'), list) and
               all(isinstance(a, dict) for a in pool['allocations']) for pool in data['pools']):
        return False
    # Malformed nested identifiers must not trigger unhashable exceptions in
    # the secondary accounting checker. The schema error is sufficient.
    for row in bs['assets'] + bs['liabilities']:
        if not isinstance(row.get('id'), str):
            return False
    for pool in data['pools']:
        for row in pool['allocations']:
            if not isinstance(row.get('asset_id'), str):
                return False
    return all(isinstance(a.get('policy_id'), str) and
               type(a.get('within_days')) in (int, str)
               for a in data['actions'])


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
    # Standalone validation must enforce ALL enums/required/types, not just
    # a few manually selected fields. No optional dependency is necessary.
    schema_errors = _schema_errors(data)
    errors.extend(schema_errors)
    if schema_errors and not _safe_for_accounting_checks(data):
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
    # A flag is not itself evidence. Even with a syntactically valid schema,
    # a reconciled claim is unsupportable with unknown owned balances or debts.
    if facts.get('asset_completeness') == 'RECONCILED' or bs.get('net_worth_status') == 'RECONCILED':
        unresolved = []
        for a in assets:
            if a['ownership'] in ('OWNED', 'RESTRICTED_BENEFICIAL') and (
                a['amount'] is None or a['provenance'] == 'UNKNOWN'
            ):
                unresolved.append(f'asset {a["id"]}')
        for debt in debts:
            if debt['amount'] is None or debt['provenance'] == 'UNKNOWN':
                unresolved.append(f'liability {debt["id"]}')
        if unresolved:
            errors.append('cannot claim reconciled/complete balance sheet with unresolved owned amounts or liabilities: ' + ', '.join(unresolved))
        if not facts.get('reconciliation_reference'):
            errors.append('reconciliation_reference is required for a claim of reconciled/complete assets; flags alone cannot certify missing accounts')
    if data.get('status') == 'USER_APPROVED' and not permission_reference(data):
        errors.append('plan USER_APPROVED requires explicit plan_approval_reference; an AI or report status alone is not consent')

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
