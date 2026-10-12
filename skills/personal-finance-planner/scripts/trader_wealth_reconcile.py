#!/usr/bin/env python3
"""Optional, pure accounting checker for complex trading-income consultations.

SKILL FIRST: the host researches, reasons and decides.  This utility performs
ONLY reproducible, single-currency arithmetic on supplied JSON; it neither
fetches financial records nor determines law, ownership, taxes or suitability.

Usage: python scripts/trader_wealth_reconcile.py --input - < private.json
       python scripts/trader_wealth_reconcile.py --input synthetic-example.json

No persistence, no network, no default tax rate, no automated transactions.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import re
import sys
from pathlib import Path

CENT = Decimal('0.01')
MAX_MONEY = Decimal('1000000000000')
RECEIPT_KINDS = {'PF_BANK_PAYOUT', 'OTHER_EXTERNAL_RECEIPT',
                 'BROKER_PROFIT_RANGE', 'BROKER_WITHDRAWAL_TRANSFER', 'PF_SIMULATED_PNL'}
EXPENSE_KINDS = {'ESSENTIAL', 'DISCRETIONARY', 'DEBT_PAYMENT', 'OPERATING_COST'}
STATUS_CURRENT = 'CURRENT_USER_REPORTED'
STATUS_PRIOR = 'PRIOR_NOT_RECONFIRMED'
STATUS_VERIFIED = 'DOCUMENTED'


class InputError(ValueError):
    """Supplied fields cannot support a safe accounting computation."""


def money(value, field, required=True, signed=False):
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise InputError(f'{field}: monetary value must be a numeric string or integer')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise InputError(f'{field}: invalid monetary amount') from exc
    if not number.is_finite() or not ((-MAX_MONEY if signed else Decimal("0")) <= number <= MAX_MONEY):
        raise InputError(f'{field}: amount is outside permitted signed/nonnegative range')
    if number.as_tuple().exponent < -2:
        raise InputError(f'{field}: limit monetary inputs to currency minor units (2 decimals)')
    return number.quantize(CENT, rounding=ROUND_HALF_UP)


def amount_str(number):
    return format(number.quantize(CENT, rounding=ROUND_HALF_UP), '.2f') if number is not None else None


def ensure_currency(item, currency, path):
    if item.get('currency') != currency:
        raise InputError(f'{path}: currency differs from plan currency; split currencies or provide sourced FX')


def ensure_unique_ids(rows, path):
    ids = [x.get('id') for x in rows]
    if any(not isinstance(x, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', x) for x in ids):
        raise InputError(f'{path}: each row needs an alphanumeric id')
    if len(ids) != len(set(ids)):
        raise InputError(f'{path}: duplicate identifiers can double count amounts')


def _flag_once(flags, key):
    if key not in flags:
        flags.append(key)


def analyze(data):
    if not isinstance(data, dict):
        raise InputError('input must be a JSON object')
    if data.get('schema_version') != '5.5':
        raise InputError('schema_version must be 5.5')
    if not isinstance(data.get('as_of'), str) or not re.fullmatch(r'20\d\d-\d\d-\d\d', data['as_of']):
        raise InputError('as_of: YYYY-MM-DD date required')
    from datetime import date
    try:
        date.fromisoformat(data['as_of'])
    except ValueError as exc:
        raise InputError('as_of: invalid date') from exc
    currency = data.get('currency')
    if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
        raise InputError('currency must be a 3-letter ISO code')
    rows = data.get('income_items')
    expenses = data.get('outflows')
    if not isinstance(rows, list) or not isinstance(expenses, list):
        raise InputError('income_items and outflows must be arrays')
    ensure_unique_ids(rows, 'income_items')
    ensure_unique_ids(expenses, 'outflows')

    flags, recognition = [], []
    gross_reported_cash = Decimal('0')
    verified_received_cash = Decimal('0')
    reported_broker_to_bank_transfers = Decimal('0')
    for item in rows:
        path = 'income_items.' + item['id']
        ensure_currency(item, currency, path)
        kind = item.get('kind')
        if item.get('period') != 'MONTHLY':
            raise InputError(path + ': period must be MONTHLY; host must normalize first')
        if kind not in RECEIPT_KINDS:
            raise InputError(path + ': unknown income kind')
        status = item.get('evidence')
        if status not in {'USER_REPORTED', 'DOCUMENTED', 'HYPOTHETICAL'}:
            raise InputError(path + ': evidence must be USER_REPORTED, DOCUMENTED or HYPOTHETICAL')
        if kind == 'BROKER_PROFIT_RANGE':
            rng = item.get('range')
            if not isinstance(rng, dict):
                raise InputError(path + ': range low/high required')
            low = money(rng.get('low'), path+'.range.low', signed=True)
            high = money(rng.get('high'), path+'.range.high', signed=True)
            if high < low:
                raise InputError(path + ': reversed range')
            if item.get('realization') not in {'UNKNOWN', 'REALIZED_IN_BROKER', 'UNREALIZED'}:
                raise InputError(path + ': realization must be explicit')
            _flag_once(flags, 'BROKER_PNL_NOT_BANK_CASH')
            recognition.append({'id': item['id'], 'kind':kind, 'reported_range':{'low':amount_str(low),'high':amount_str(high)},
                                'realization':item['realization'], 'bank_cash_inflow_included':False, 'new_external_household_cash_income_included':False,
                                'net_worth_rule':'Broker NAV (net of financing), not this P&L added to NAV; cannot estimate NAV from monthly P&L.'})
            continue
        val = money(item.get('amount'), path+'.amount')
        if kind in {'PF_BANK_PAYOUT', 'OTHER_EXTERNAL_RECEIPT'}:
            status_pay = item.get('settlement_status')
            if status_pay not in {'CLAIMED_BANK_RECEIVED', 'DOCUMENTED_BANK_RECEIVED', 'PENDING'}:
                raise InputError(path + ': settlement_status is required')
            if status_pay == 'DOCUMENTED_BANK_RECEIVED' and status != 'DOCUMENTED':
                raise InputError(path + ': DOCUMENTED_BANK_RECEIVED requires DOCUMENTED source evidence')
            if status == 'HYPOTHETICAL' and status_pay != 'PENDING':
                raise InputError(path + ': hypothetical receipt cannot be labeled actual bank cash')
            eligible = status_pay != 'PENDING'
            if eligible:
                gross_reported_cash += val
                if status_pay == 'DOCUMENTED_BANK_RECEIVED':
                    verified_received_cash += val
                else:
                    _flag_once(flags, 'CASH_RECEIPTS_USER_REPORTED_NOT_DOCUMENT_VERIFIED')
            recognition.append({'id':item['id'], 'kind':kind, 'reported_amount':amount_str(val),
                                'settlement_status':status_pay, 'bank_cash_inflow_included':eligible,
                                'new_external_household_cash_income_included':eligible,
                                'net_worth_rule':'Cash receipt is an inflow, not proof that income tax and operating expenses are settled.'})
        elif kind == 'BROKER_WITHDRAWAL_TRANSFER':
            reported_broker_to_bank_transfers += val
            _flag_once(flags, 'BROKER_TRANSFER_IS_NOT_NEW_HOUSEHOLD_EARNINGS')
            recognition.append({'id': item['id'], 'kind':kind,'reported_amount':amount_str(val),
                                'bank_cash_inflow_included':True, 'new_external_household_cash_income_included':False,
                                'net_worth_rule':'Internal transfer broker→bank: decreases broker assets and increases bank cash; no newly created net worth.'})
        else:
            _flag_once(flags, 'PF_SIMULATED_IS_NOT_OWNED_PERSONAL_WEALTH')
            recognition.append({'id':item['id'], 'kind':kind,'reported_amount':amount_str(val),
                                'bank_cash_inflow_included':False, 'new_external_household_cash_income_included':False,
                                'net_worth_rule':'Non-owned simulated account capital/P&L excluded from personal assets and available cash.'})

    current_essential = Decimal('0')
    current_debt = Decimal('0')
    current_discretionary = Decimal('0')
    prior_discretionary = Decimal('0')
    current_ops = Decimal('0')
    active_discretionary_groups = {row.get('reference_group', row.get('id')) for row in expenses
                                   if row.get('category') == 'DISCRETIONARY'
                                   and row.get('evidence') in {STATUS_CURRENT, STATUS_VERIFIED}}
    loan_details_missing = False
    for item in expenses:
        path = 'outflows.' + item['id']
        ensure_currency(item, currency, path)
        kind = item.get('category')
        if kind not in EXPENSE_KINDS:
            raise InputError(path + ': unrecognized expense category')
        if item.get('period') != 'MONTHLY':
            raise InputError(path + ': period must be MONTHLY; host must normalize first')
        amt = money(item.get('amount'), path+'.amount')
        status = item.get('evidence')
        if status not in {STATUS_CURRENT, STATUS_PRIOR, STATUS_VERIFIED}:
            raise InputError(path + ': expense evidence invalid')
        if kind in {'ESSENTIAL', 'DEBT_PAYMENT', 'OPERATING_COST'} and status == STATUS_PRIOR:
            raise InputError(path + ': prior expense cannot be silently treated as current fixed obligation')
        if kind == 'ESSENTIAL':
            current_essential += amt
        elif kind == 'DEBT_PAYMENT':
            current_debt += amt
            loan_details_missing = loan_details_missing or item.get('apr') is None or item.get('principal_balance') is None
        elif kind == 'OPERATING_COST':
            current_ops += amt
        elif status == STATUS_PRIOR:
            if item.get('reference_group', item['id']) in active_discretionary_groups:
                _flag_once(flags, 'PRIOR_EXPENSE_SUPERSEDED_BY_CURRENT_SAME_CATEGORY')
            else:
                prior_discretionary += amt
                _flag_once(flags, 'HISTORICAL_DISCRETIONARY_SPENDING_NEEDS_RECONFIRMATION')
        else:
            current_discretionary += amt
    if loan_details_missing:
        _flag_once(flags, 'DEBT_INTEREST_PRINCIPAL_SPLIT_UNKNOWN')

    missing_ops = data.get('operating_costs_complete') is not True
    missing_outflows = data.get('outflows_complete') is not True
    if missing_outflows:
        _flag_once(flags, 'HOUSEHOLD_OUTFLOWS_NOT_COMPLETE')
    if missing_ops:
        _flag_once(flags, 'OPERATING_COSTS_INCOMPLETE')
    tax = data.get('tax', {'status':'UNKNOWN'})
    if not isinstance(tax, dict) or tax.get('status') not in {'UNKNOWN', 'DOCUMENTED_LIABILITY'}:
        raise InputError('tax.status: use UNKNOWN or DOCUMENTED_LIABILITY')
    if tax['status'] == 'DOCUMENTED_LIABILITY':
        tax_paid_or_reserved = money(tax.get('monthly_cash_requirement'), 'tax.monthly_cash_requirement')
        if not tax.get('source_date') or not tax.get('verified_rule'):
            raise InputError('documented tax liability requires dated source and verified_rule note')
    else:
        tax_paid_or_reserved = None
        _flag_once(flags, 'TAX_RESIDENCE_INCOME_CLASSIFICATION_AND_LIABILITY_UNVERIFIED')

    core = current_essential + current_debt
    current_total = core + current_discretionary + current_ops
    if prior_discretionary:
        high_total = current_total + prior_discretionary
    else:
        high_total = current_total
    months = data.get('reserve_months', 12)
    if type(months) is not int or not 1 <= months <= 36:
        raise InputError('reserve_months must be integer 1..36; a heuristic, not universal rule')
    balances = data.get('balances', {})
    if not isinstance(balances, dict):
        raise InputError('balances must be an object')
    spendable_cash = money(balances.get('unrestricted_cash_after_earmarks'), 'balances.unrestricted_cash_after_earmarks', required=False)
    broker_nav = money(balances.get('broker_net_equity'), 'balances.broker_net_equity', required=False)
    car_loan_balance = money(balances.get('car_loan_balance'), 'balances.car_loan_balance', required=False)
    if spendable_cash is None:
        _flag_once(flags, 'UNRESTRICTED_LIQUID_CASH_BALANCE_NOT_PROVIDED')
    if broker_nav is None:
        _flag_once(flags, 'BROKER_NET_EQUITY_NOT_PROVIDED')
        if any(x.get('kind') == 'BROKER_PROFIT_RANGE' for x in rows):
            _flag_once(flags, 'BROKER_NAV_AND_MARGIN_STATUS_UNKNOWN_UNLESS_SUPPLIED')
    if car_loan_balance is None:
        _flag_once(flags, 'CAR_LOAN_OUTSTANDING_PRINCIPAL_NOT_PROVIDED')
    if broker_nav is not None and balances.get('broker_nav_is_net_of_margin_debt') is not True:
        raise InputError('broker_net_equity requires broker_nav_is_net_of_margin_debt=true or omit')

    # 'core' includes contractual debt service: never call this all consumption;
    # repayment of principal changes liabilities, interest is expense.
    reserve_core = core * months
    reserve_full = high_total * months
    reserve_gap = None if spendable_cash is None else max(Decimal('0'), reserve_core-spendable_cash)
    cash_reported = gross_reported_cash
    low_before_unresolved = cash_reported-current_total
    high_before_unresolved = cash_reported-high_total
    after_required = None
    if tax_paid_or_reserved is not None and not missing_ops and not missing_outflows:
        after_required = low_before_unresolved - tax_paid_or_reserved
    else:
        _flag_once(flags, 'NET_INVESTABLE_FUNDS_NOT_ESTABLISHED')
    if spendable_cash is None or reserve_gap is None or reserve_gap > 0:
        after_required = None
        _flag_once(flags, 'RESERVE_FUNDING_NOT_VERIFIED')
    if after_required is not None:
        after_required = max(Decimal('0'), after_required)

    # This component subtotal is NOT a complete household net-worth figure:
    # excluded cash earmarks, other investments, other liabilities and taxes
    # can all be material. Brokerage NAV is already net of *broker margin debt*.
    known_component_subtotal = None
    if spendable_cash is not None and broker_nav is not None and car_loan_balance is not None:
        known_component_subtotal = spendable_cash + broker_nav - car_loan_balance
        _flag_once(flags, 'NET_FINANCIAL_WORTH_REQUIRES_ALL_ASSETS_LIABILITIES_AND_TAXES')

    hypothetical_rates = data.get('hypothetical_provision_rates', [])
    if not isinstance(hypothetical_rates, list) or len(hypothetical_rates)>5:
        raise InputError('hypothetical_provision_rates must contain 0..5 scenario inputs')
    sensitivity=[]
    for val in hypothetical_rates:
        try:
            pct = Decimal(str(val))
        except InvalidOperation as exc:
            raise InputError('invalid hypothetical rate') from exc
        if not pct.is_finite() or pct<0 or pct>Decimal('0.95'):
            raise InputError('hypothetical rates must be between 0 and 0.95')
        sensitivity.append({'hypothetical_rate_NOT_TAX_LAW': str(pct),
                            'illustrative_earmark': amount_str(cash_reported*pct),
                            'remainder_after_earmark_and_current_outflows_BEFORE_UNKNOWN_COSTS':amount_str(low_before_unresolved-cash_reported*pct),
                            'NOT_INVESTABLE_CASH':True})
    if sensitivity:
        _flag_once(flags, 'TAX_SENSITIVITY_IS_NOT_LEGAL_TAX_RATE_OR_RECOMMENDATION')

    return {
      'schema_version':'5.5','as_of':data['as_of'],'currency':currency,
      'evidence':'SYNTHETIC_CALCULATION_OVER_INPUT_NOT_BANK_VERIFICATION',
      'recognition':recognition,
      'cashflow':{
        'reported_external_received_per_month_PROVISIONAL': amount_str(cash_reported),
        'documented_external_received_per_month': amount_str(verified_received_cash),
        'reported_broker_to_bank_transfers_per_month_NOT_NEW_WEALTH':amount_str(reported_broker_to_bank_transfers),
        'total_reported_bank_credits_external_plus_internal_transfers':amount_str(cash_reported+reported_broker_to_bank_transfers),
        'current_essential_excluding_debt':amount_str(current_essential),
        'current_contractual_debt_service':amount_str(current_debt),
        'current_discretionary':amount_str(current_discretionary),
        'unreconfirmed_prior_discretionary':amount_str(prior_discretionary),
        'known_operating_costs':amount_str(current_ops),
        'current_cash_outflows':amount_str(current_total),
        'higher_lifestyle_cash_outflows_if_prior_spend_continues':amount_str(high_total),
        'monthly_surplus_BEFORE_unknown_tax_and_costs_current': amount_str(low_before_unresolved),
        'monthly_surplus_BEFORE_unknown_tax_and_costs_higher_lifestyle':amount_str(high_before_unresolved),
        'conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals':amount_str(after_required),
        'tax_status':tax['status'], 'operating_costs_complete':not missing_ops,
        'household_outflows_complete':not missing_outflows,
        'debt_payment_partly_principal_not_pure_consumption':current_debt>0,
      },
      'reserves':{
        'months_assumed_HEURISTIC':months,
        'core_including_debt_service':amount_str(reserve_core),
        'higher_lifestyle_if_prior_spend_continues':amount_str(reserve_full),
        'unrestricted_cash_after_earmarks': amount_str(spendable_cash),
        'core_reserve_gap':amount_str(reserve_gap),
        'runway_months_core':amount_str(spendable_cash/core) if spendable_cash is not None and core else None,
      },
      'balance_sheet':{
        'broker_net_equity_if_supplied':amount_str(broker_nav),
        'car_loan_balance_if_supplied':amount_str(car_loan_balance),
        'personal_net_financial_assets':'UNKNOWN',
        'known_components_subtotal_NOT_TOTAL_NET_WORTH':amount_str(known_component_subtotal),
        'subtotal_inclusions':'Unrestricted bank cash after earmarks + own broker net equity - car loan balance; excludes other assets, restricted cash, other debts and tax liabilities',
        'do_not_add_monthly_broker_PNL_to_broker_NAV':True,
      },
      'tax_sensitivity_HYPOTHETICAL_NOT_LAW':sensitivity,
      'review_flags':flags,
      'policy_limits':[
        'This utility does not determine tax residency, tax brackets, tax legality, or broker account terms.',
        'Gross monthly receipts alone do not establish safe investable surplus or present net worth.',
        '12 reserve months are an illustrative user-changeable heuristic, not an evidence-based optimum.',
        'All investment allocation, legal research, behavioral decisions and final recommendations belong to host Agent.',
        'No automatic trades, transfers, filings, savings, or personal-data persistence.'
      ]
    }


def main(argv=None):
    p=argparse.ArgumentParser(description='Optional private single-currency trader-finance accounting check')
    p.add_argument('--input',required=True,help='Path to JSON or - for stdin (preferred for private records)')
    p.add_argument('--indent',type=int,default=2)
    args=p.parse_args(argv)
    try:
        if args.input=='-':
            raw=sys.stdin.read()
        else:
            raw=Path(args.input).read_text(encoding='utf-8')
        result=analyze(json.loads(raw))
    except (InputError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({'error_type':type(exc).__name__,'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=args.indent))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
