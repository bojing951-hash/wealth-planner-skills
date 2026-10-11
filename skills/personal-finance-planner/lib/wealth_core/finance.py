"""Currency-isolated, provenance-aware household arithmetic.

Never silently converts currencies. Does not calculate tax, recommend securities,
or treat PF simulated account balances as wealth.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .profile import money

ZERO = Decimal('0')


def show(v: Decimal | None) -> str | None:
    if v is None:
        return None
    return format(v.quantize(Decimal('0.01')), 'f')


def financial_snapshot(profile: dict) -> dict[str, Any]:
    currencies = set()
    for list_name in ('income', 'expenses', 'assets', 'liabilities', 'goals'):
        currencies.update(obj['currency'] for obj in profile[list_name])
    data = {}
    warnings = []
    income_stability = profile.get('risk', {}).get('income_stability', 'unknown')
    reserve_months = profile.get('risk', {}).get('reserve_months', 6 if income_stability == 'stable' else 12)
    for cur in sorted(currencies):
        incomes = [i for i in profile['income'] if i['currency'] == cur]
        spending = [e for e in profile['expenses'] if e['currency'] == cur]
        assets = [a for a in profile['assets'] if a['currency'] == cur]
        liabilities = [a for a in profile['liabilities'] if a['currency'] == cur]
        bank_income = ZERO
        gross_only_ids = []
        income_provenance = {}
        excluded_unrealized = []
        uncertain_tax_ids = []
        for inc in incomes:
            income_provenance[inc['id']] = inc['source_status']
            if inc['kind'] == 'pf_simulated_profit' or not inc['bank_received'] or not inc['realized']:
                excluded_unrealized.append(inc['id'])
                continue
            if inc.get('net_received') is None:
                gross_only_ids.append(inc['id'])
            else:
                bank_income += money(inc['net_received'])
            if inc['tax_status'] not in ('settled', 'professional_verified', 'not_applicable'):
                uncertain_tax_ids.append(inc['id'])
        essentials = sum((money(e['monthly_amount']) for e in spending if e['category'] == 'essential'), ZERO)
        discretionary = sum((money(e['monthly_amount']) for e in spending if e['category'] == 'discretionary'), ZERO)
        business = sum((money(e['monthly_amount']) for e in spending if e['category'] == 'business'), ZERO)
        tax_reserve = sum((money(e['monthly_amount']) for e in spending if e['category'] == 'tax_reserve'), ZERO)
        debt_payment = sum((money(a.get('monthly_payment', '0')) for a in liabilities), ZERO)
        monthly_obligations = essentials + discretionary + business + tax_reserve + debt_payment
        # A partial income picture must never masquerade as actual aggregate surplus.
        surplus = bank_income - monthly_obligations if not gross_only_ids else None
        gross_count = sum((money(i['gross']) for i in incomes if i.get('gross') is not None and i['kind'] != 'pf_simulated_profit'), ZERO)
        liquid = ZERO
        restricted = ZERO
        owned_financial = ZERO
        excluded_simulated = ZERO
        for a in assets:
            value = money(a['amount'])
            if a['kind'] == 'pf_simulated_balance':
                excluded_simulated += value
                continue
            if a['ownership'] not in {'user', 'joint'}:
                warnings.append(f"{cur}: asset {a['id']} not confirmed owned by user; excluded")
                continue
            if a['kind'] == 'other':
                warnings.append(f"{cur}: unclassified asset {a['id']} excluded from financial assets")
                continue
            if a['ownership'] == 'joint':
                if a.get('beneficial_share') is None:
                    warnings.append(f"{cur}: joint asset {a['id']} has no beneficial_share; excluded until ownership clarified")
                    continue
                value *= money(a['beneficial_share'])
            owned_financial += value
            if a['liquidity'] == 'liquid':
                liquid += value
            else:
                restricted += value
        debt = sum((money(i['balance']) for i in liabilities), ZERO)
        reserve_target = essentials * reserve_months
        reserve_shortfall = max(reserve_target - liquid, ZERO)
        is_tax_clear = not uncertain_tax_ids
        cashflow_status = ('INCOMPLETE_GROSS_ONLY' if gross_only_ids else
                          'PROVISIONAL_TAX_UNVERIFIED' if not is_tax_clear else
                          'DECLARED_NET_NOT_LEGALLY_CERTIFIED')
        # A verified legal answer would additionally require an actual tax-law check.
        # v0.4 intentionally does NOT issue a final investable amount.
        data[cur] = {
            'currency': cur,
            'monthly_bank_received_user_reported': show(bank_income),
            'income_provenance_by_id': income_provenance,
            'gross_monthly_reference_not_usable': show(gross_count),
            'monthly_expenses': {
                'essential': show(essentials), 'discretionary': show(discretionary),
                'business': show(business), 'tax_reserve': show(tax_reserve),
                'debt_payment': show(debt_payment), 'total': show(monthly_obligations),
            },
            'monthly_surplus_conditional': show(surplus),
            'monthly_investable_final': None,
            'cashflow_status': cashflow_status,
            'gross_only_income_ids': gross_only_ids,
            'tax_uncertain_income_ids': uncertain_tax_ids,
            'excluded_unrealized_income_ids': excluded_unrealized,
            'financial_assets_owned_declared': show(owned_financial),
            'liquid_cash_and_liquid_investments_declared': show(liquid),
            'other_owned_assets_declared': show(restricted),
            'simulated_pf_assets_excluded': show(excluded_simulated),
            'liabilities_balance_declared': show(debt),
            'financial_net_worth_declared': show(owned_financial - debt),
            'reserve_months_heuristic': reserve_months,
            'reserve_target_conditional': show(reserve_target),
            'reserve_shortfall_declared': show(reserve_shortfall),
            'essential_cash_runway_months': show(liquid / essentials) if essentials > 0 else None,
        }
        if any(v == 'assumption' for v in income_provenance.values()):
            warnings.append(f'{cur}: some monthly incomes are synthetic/scenario assumptions, not real bank verification')
        if gross_only_ids:
            warnings.append(f'{cur}: {", ".join(gross_only_ids)} no verified net receipt; cannot calculate complete cash surplus')
        if uncertain_tax_ids:
            warnings.append(f'{cur}: {", ".join(uncertain_tax_ids)} outstanding tax treatment; surplus is provisional, not final investable')
        if excluded_unrealized:
            warnings.append(f'{cur}: excluded non-received and/or PF simulated income {", ".join(excluded_unrealized)}')
        if excluded_simulated:
            warnings.append(f'{cur}: excluded PF simulated nominal assets {show(excluded_simulated)}')
        if surplus is not None and surplus < 0:
            warnings.append(f'{cur}: monthly outflow exceeds confirmed bank receipts under stated assumptions')
    if len(data) > 1:
        warnings.append('MULTICURRENCY: amounts are NOT converted or summed; a dated authorized FX quote and purpose-specific accounting policy are required')
    return {
        'money_format': 'decimal_string_2dp',
        'tax_calculation': 'NOT_IMPLEMENTED',
        'investment_allocation': 'NOT_IMPLEMENTED',
        'currency_buckets': data,
        'warnings': sorted(set(warnings)),
        'reserve_method': 'Adjustable 6/12-month heuristic applied to declared essential spending only; not evidence of universal optimality.',
    }
