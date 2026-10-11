"""Dated macro observations and hypothetical future assumptions remain separate."""
from __future__ import annotations
from datetime import date
import math
from urllib.parse import urlsplit


def check_macro_evidence(bundle:dict, as_of:str,currency:str) -> dict:
    if bundle.get('currency')!=currency:
        raise ValueError('macro bundle must match planning currency')
    now=date.fromisoformat(as_of)
    observations=bundle.get('observations',[])
    checked=[]
    for o in observations:
        d=date.fromisoformat(o['observation_date']);retrieved=date.fromisoformat(o['retrieved_on'])
        if d>now or retrieved>now:raise ValueError('future-dated observation/retrieval')
        v=float(o['value'])
        if not math.isfinite(v):raise ValueError('macro observation cannot be nonfinite')
        if o['currency']!=currency:raise ValueError('macro series in different currency')
        if not o.get('unit') or not o.get('series_id') or not o.get('source_url', '').startswith('https://'):
            raise ValueError('source, unit and series id required')
        age=(now-d).days
        checked.append({'series_id':o['series_id'],'value':v,'unit':o['unit'],
                        'observation_date':d.isoformat(),'observation_age_days':age,
                        'retrieved_on':retrieved.isoformat(),
                        'status':'STALE_FOR_ECONOMIC_REVIEW' if age>365 else 'REPORTED_NOT_INDEPENDENTLY_FETCHED'})
    return {
        'status':'USER_OR_HOST_REPORTED_MACRO_NOT_FORECAST',
        'currency':currency,'observations':checked,
        'policy':'Do not mechanically allocate based on a monthly CPI or a single interest-rate observation.',
        'model_calibration_completed':False,
        'no_automatic_20_year_expected_return':True,
    }
