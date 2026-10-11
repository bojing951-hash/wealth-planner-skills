"""Strict profile validation and money parsing for the v0.4 contract.

Financial amounts are JSON decimal *strings* (not JSON floats) to avoid silent
binary rounding. All currencies are kept distinct; exchange rates are never
invented. This is a limited validator, not a legal/tax determination engine.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re

SCHEMA_VERSION = '0.4.0'
MONEY_PATTERN = re.compile(r'^(?:0|[1-9]\d*)(?:\.\d{1,4})?$')
CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')
INCOME_KINDS = {'employment', 'bonus', 'self_employment', 'business', 'pf_payout',
                'pf_simulated_profit', 'rental', 'pension', 'investment_distribution', 'other'}
TAX_STATUSES = {'unknown', 'withheld', 'reserved_estimate', 'professional_verified', 'settled', 'not_applicable'}
SOURCE_STATUSES = {'user_reported', 'document_present', 'independently_verified', 'assumption', 'unknown'}
EXPENSE_TYPES = {'essential', 'discretionary', 'business', 'tax_reserve'}
ASSET_KINDS = {'cash', 'investment', 'retirement', 'restricted', 'pf_simulated_balance', 'other'}


class ProfileError(ValueError):
    """Input is inconsistent with the v0.4 financial data contract."""


def money(value, field='amount') -> Decimal:
    if not isinstance(value, str) or not MONEY_PATTERN.fullmatch(value):
        raise ProfileError(f'{field} must be a nonnegative decimal string, e.g. "123.45" (not a JSON number)')
    try:
        v = Decimal(value)
        if not v.is_finite():
            raise ValueError
        return v
    except (InvalidOperation, ValueError):
        raise ProfileError(f'{field} is not a finite amount') from None


def currency(value, field='currency') -> str:
    if not isinstance(value, str) or not CURRENCY_PATTERN.fullmatch(value):
        raise ProfileError(f'{field} must be a three-letter uppercase currency code')
    return value


def _required(obj, field, typ, prefix):
    if field not in obj or not isinstance(obj[field], typ):
        raise ProfileError(f'{prefix}.{field} is required and must be {typ.__name__}')
    return obj[field]


def _valid_date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ProfileError(f'{field} must be ISO YYYY-MM-DD')
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ProfileError(f'{field} must be ISO YYYY-MM-DD') from None


def _validate_items(items, field, allowed_kinds=None):
    if not isinstance(items, list):
        raise ProfileError(f'{field} must be a list')
    ids = set()
    for i, entry in enumerate(items):
        path = f'{field}[{i}]'
        if not isinstance(entry, dict):
            raise ProfileError(f'{path} must be an object')
        identity = _required(entry, 'id', str, path)
        if not identity.strip() or identity in ids:
            raise ProfileError(f'{path}.id must be unique and nonempty')
        ids.add(identity)
        if 'currency' in entry:
            currency(entry['currency'], path + '.currency')
        if allowed_kinds:
            k = entry.get('kind') if field != 'expenses' else entry.get('category')
            if k not in allowed_kinds:
                raise ProfileError(f'{path}.kind/category invalid: {k}')
        if 'source_status' in entry and entry['source_status'] not in SOURCE_STATUSES:
            raise ProfileError(f'{path}.source_status is invalid')
    return items


def validate_profile(profile: dict) -> dict:
    if not isinstance(profile, dict):
        raise ProfileError('Root input must be a JSON object')
    if profile.get('schema_version') != SCHEMA_VERSION:
        raise ProfileError(f'schema_version must equal {SCHEMA_VERSION}')
    _valid_date(profile.get('as_of'), 'as_of')
    _required(profile, 'profile_id', str, 'profile')
    person = _required(profile, 'person', dict, 'profile')
    residence = _required(person, 'residence', dict, 'person')
    country = _required(residence, 'country', str, 'person.residence')
    if len(country) != 2 or not country.isalpha() or country != country.upper():
        raise ProfileError('person.residence.country must be ISO 2-letter uppercase jurisdiction')
    for field in ('region', 'city'):
        if field in residence and residence[field] is not None and not isinstance(residence[field], str):
            raise ProfileError(f'person.residence.{field} must be string or null')
    if 'citizenships' in person:
        if not isinstance(person['citizenships'], list) or not all(isinstance(x, str) and re.fullmatch(r'[A-Z]{2}',x) for x in person['citizenships']):
            raise ProfileError('person.citizenships must be a list of strings')
    if 'tax_residencies_claimed' in person:
        if not isinstance(person['tax_residencies_claimed'], list) or not all(isinstance(x,str) and re.fullmatch(r'[A-Z]{2}',x) for x in person['tax_residencies_claimed']):
            raise ProfileError('person.tax_residencies_claimed must be a list of jurisdiction codes')
    if 'age' in person and person['age'] is not None and (type(person['age']) is not int or not 0 <= person['age'] <= 120):
        raise ProfileError('person.age must be an integer 0–120 or null')
    consent = _required(profile, 'consents', dict, 'profile')
    for field in ('use_user_files', 'connect_accounts', 'persist'):
        if type(consent.get(field)) is not bool:
            raise ProfileError(f'consents.{field} must be explicit true/false')
    financial = _required(profile, 'income', list, 'profile')
    _validate_items(financial, 'income', INCOME_KINDS)
    for i, inc in enumerate(financial):
        prefix = f'income[{i}]'
        currency(inc.get('currency'), f'{prefix}.currency')
        if inc.get('period') != 'monthly':
            raise ProfileError(f'{prefix}.period must be monthly in v0.4')
        if type(inc.get('bank_received')) is not bool:
            raise ProfileError(f'{prefix}.bank_received must be boolean')
        if type(inc.get('realized')) is not bool:
            raise ProfileError(f'{prefix}.realized must be boolean')
        if inc.get('tax_status') not in TAX_STATUSES:
            raise ProfileError(f'{prefix}.tax_status invalid')
        if inc.get('source_status') not in SOURCE_STATUSES:
            raise ProfileError(f'{prefix}.source_status invalid')
        if 'gross' not in inc and 'net_received' not in inc:
            raise ProfileError(f'{prefix} must provide gross or net_received amount')
        for key in ('gross','net_received'):
            if key in inc and inc[key] is not None:
                money(inc[key], f'{prefix}.{key}')
        for field in ('payer_country','activity_country','bank_country'):
            if inc.get(field) is not None and (not isinstance(inc[field],str) or not re.fullmatch(r'[A-Z]{2}',inc[field])):
                raise ProfileError(f'{prefix}.{field} must be a 2-letter uppercase jurisdiction')
        if inc['kind'] == 'pf_simulated_profit' and inc['bank_received']:
            raise ProfileError(f'{prefix}: simulated PF profits cannot be bank_received')
        if inc['bank_received'] and not inc['realized']:
            raise ProfileError(f'{prefix}: bank_received cannot be true if realized is false')
    expenses = _validate_items(_required(profile, 'expenses', list, 'profile'), 'expenses', EXPENSE_TYPES)
    for i, entry in enumerate(expenses):
        currency(entry.get('currency'), f'expenses[{i}].currency')
        money(entry.get('monthly_amount'), f'expenses[{i}].monthly_amount')
    assets = _validate_items(_required(profile, 'assets', list, 'profile'), 'assets', ASSET_KINDS)
    for i, entry in enumerate(assets):
        currency(entry.get('currency'), f'assets[{i}].currency')
        money(entry.get('amount'), f'assets[{i}].amount')
        if entry.get('ownership') not in {'user', 'joint', 'other', 'unknown'}:
            raise ProfileError(f'assets[{i}].ownership invalid')
        if entry.get('liquidity') not in {'liquid', 'long_term', 'restricted', 'unavailable'}:
            raise ProfileError(f'assets[{i}].liquidity invalid')
        if entry.get('location_country') is not None and (not isinstance(entry['location_country'], str) or not re.fullmatch(r'[A-Z]{2}',entry['location_country'])):
            raise ProfileError(f'assets[{i}].location_country must be 2-letter uppercase')
        if entry.get('kind') in {'retirement','restricted'} and entry['liquidity']=='liquid':
            raise ProfileError(f'assets[{i}]: pension/restricted assets cannot be recorded as unrestricted liquid cash')
        if entry.get('kind')=='pf_simulated_balance' and entry['liquidity']!='unavailable':
            raise ProfileError(f'assets[{i}]: PF simulated capital must be marked unavailable')
        if 'beneficial_share' in entry:
            share=money(entry['beneficial_share'], f'assets[{i}].beneficial_share')
            if share > 1:
                raise ProfileError(f'assets[{i}].beneficial_share must be between 0 and 1')
    liabilities = _validate_items(_required(profile, 'liabilities', list, 'profile'), 'liabilities')
    for i, entry in enumerate(liabilities):
        currency(entry.get('currency'), f'liabilities[{i}].currency')
        money(entry.get('balance'), f'liabilities[{i}].balance')
        money(entry.get('monthly_payment', '0'), f'liabilities[{i}].monthly_payment')
    goals = _validate_items(_required(profile, 'goals', list, 'profile'), 'goals')
    for i, entry in enumerate(goals):
        currency(entry.get('currency'), f'goals[{i}].currency')
        money(entry.get('target_amount'), f'goals[{i}].target_amount')
        _valid_date(entry.get('target_date'), f'goals[{i}].target_date')
    risk = profile.get('risk', {})
    if not isinstance(risk, dict) or risk.get('income_stability', 'unknown') not in {'stable', 'volatile', 'unknown'}:
        raise ProfileError('risk.income_stability must be stable, volatile or unknown')
    if 'reserve_months' in risk and (type(risk['reserve_months']) is not int or not 1 <= risk['reserve_months'] <= 60):
        raise ProfileError('risk.reserve_months must be an integer 1–60')
    # Avoid accidentally inheriting hostile or untrusted executable content from user profile.
    # The host treats user-provided strings as data, not executable instructions.
    return profile
