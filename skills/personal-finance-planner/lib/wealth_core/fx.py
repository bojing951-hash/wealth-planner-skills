"""Explicit, dated foreign-exchange translation only. Never silently nets currencies."""
from __future__ import annotations
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def convert(money: str, base: str, quote: str,rate: str,rate_date: str,as_of: str,source_url: str) -> dict:
    if not isinstance(base,str) or not isinstance(quote,str) or len(base)!=3 or len(quote)!=3:
        raise ValueError('currency codes invalid')
    if not isinstance(source_url,str) or not source_url.startswith('https://'):
        raise ValueError('source_url required to document rate')
    d=date.fromisoformat(rate_date);now=date.fromisoformat(as_of)
    if d>now:raise ValueError('FX quote in the future')
    x=Decimal(money);r=Decimal(rate)
    if not x.is_finite() or not r.is_finite() or x<0 or r<=0:raise ValueError('amount/rate invalid')
    return {'source_currency':base,'target_currency':quote,'source_amount':format(x,'f'),
            'target_amount':format((x*r).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP),'f'),
            'quote':'1 '+base+' = '+str(r)+' '+quote,
            'rate_date':d.isoformat(),'rate_age_days':(now-d).days,
            'source_url':source_url,'caveat':'User-supplied exchange quote; not verified or guaranteed executable rate; fees and tax omitted.'}
