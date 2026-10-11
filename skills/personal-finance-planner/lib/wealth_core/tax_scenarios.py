"""User-provided HYPOTHETICAL tax and contribution calculations.

No built-in jurisdiction tax rates or legally operative conclusions. Real tax
engines require independently maintained effective-dated law AND residency tests.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP


def D(v) -> Decimal:
    if isinstance(v, bool) or not isinstance(v, (str, int, float, Decimal)):
        raise ValueError('tax inputs must be numeric')
    x = Decimal(str(v))
    if not x.is_finite():
        raise ValueError('NaN/Infinity prohibited')
    return x


def amount(x: Decimal) -> str:
    return format(x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f')


def calculate_hypothetical_tax(config: dict) -> dict:
    """Annual progressive schedule, thresholds apply to taxable income (not marginal intervals)."""
    if config.get('classification') != 'HYPOTHETICAL_USER_SUPPLIED':
        raise ValueError('no tax treatment unless explicitly HYPOTHETICAL_USER_SUPPLIED')
    currency = config.get('currency')
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        raise ValueError('currency must be three letters')
    gross = D(config['annual_gross'])
    deduction = D(config.get('deductions', '0'))
    credits = D(config.get('credits', '0'))
    if min(gross, deduction, credits) < 0:
        raise ValueError('gross/deductions/credits cannot be negative')
    taxable = max(D(0), gross - deduction)
    b = config.get('tax_brackets', [])
    if not b or not isinstance(b, list):
        raise ValueError('tax_brackets required')
    previous = D(0)
    due = D(0)
    details = []
    for idx, row in enumerate(b):
        upper = row.get('upper')
        top = D(upper) if upper is not None else None
        rate = D(row['rate'])
        if not D(0) <= rate <= D(1):
            raise ValueError('tax rates must be between 0 and 1')
        if top is not None and top <= previous:
            raise ValueError('thresholds must be strictly increasing')
        if top is None and idx != len(b) - 1:
            raise ValueError('open-ended bracket must be last')
        portion = max(D(0), min(taxable, top) - previous) if top is not None else max(D(0), taxable - previous)
        due += portion * rate
        details.append({'taxable_slice': amount(portion), 'marginal_rate': str(rate)})
        if top is None:
            break
        previous = top
    else:
        if taxable > previous:
            raise ValueError('top tax_bracket must cover taxable income; use upper:null')
    due = max(D(0), due - credits)
    social = D(config.get('social_contributions', '0'))
    if social < 0:
        raise ValueError('social contributions cannot be negative')
    net = gross - due - social
    return {
        'currency': currency.upper(),
        'status': 'HYPOTHETICAL_NONBINDING_NEVER_REAL_TAX_ADVICE',
        'annual_gross': amount(gross), 'annual_taxable': amount(taxable),
        'estimated_tax': amount(due), 'social_contributions': amount(social),
        'illustrative_annual_net': amount(net), 'illustrative_monthly_net': amount(net / D(12)),
        'bracket_slices': details,
        'not_checked': 'No actual local filing status, tax residence, credits, limits, treaties, social-insurance law or tax-year rules were verified.',
    }
