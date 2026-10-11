"""Auditable planning-state change detection; not a background scheduler."""
from __future__ import annotations


def _fraction_or_none(old, new):
    try: a=float(old);b=float(new)
    except (TypeError,ValueError):return None
    if abs(a)<1e-10:return None if abs(b)<1e-10 else 1.0
    return (b-a)/abs(a)


def compare(previous:dict,current:dict,threshold:float=.20) -> dict:
    if not 0 < threshold <= 1:raise ValueError('threshold 0..1 required')
    events=[]
    if previous.get('profile_id')!=current.get('profile_id'):
        raise ValueError('cannot compare different profile IDs')
    if previous.get('run_id')==current.get('run_id'):
        return {'status':'UNCHANGED_IDENTICAL_PLAN_ID','events':[],'replan_required':False,
                'automatic_external_action':False}
    pmap={(x['scope'],tuple(x['roles'])) for x in previous.get('jurisdiction_map',[])}
    cmap={(x['scope'],tuple(x['roles'])) for x in current.get('jurisdiction_map',[])}
    if pmap!=cmap:
        events.append({'type':'JURISDICTION_REVIEW','importance':'critical','reason':'Country/state/city/source-of-income or status claims changed'})
    if previous.get('as_of','')[:4]!=current.get('as_of','')[:4]:
        events.append({'type':'TAX_YEAR_ROLLOVER','importance':'critical','reason':'Tax-year-specific law requires renewed verification'})
    pcur=previous.get('financial_snapshot',{}).get('currency_buckets',{})
    ccur=current.get('financial_snapshot',{}).get('currency_buckets',{})
    if set(pcur)!=set(ccur):
        events.append({'type':'CURRENCY_EXPOSURE_CHANGED','importance':'critical','reason':'Currency buckets were added or removed; no silent FX conversion'})
    for cur in sorted(set(pcur)&set(ccur)):
        p=pcur[cur]; c=ccur[cur]
        for key,label in [
            ('monthly_bank_received_user_reported','INCOME'),
            ('monthly_surplus_conditional','SURPLUS'),
            ('reserve_shortfall_declared','RESERVE_SHORTFALL'),
            ('financial_net_worth_declared','NET_WORTH'),
        ]:
            delta=_fraction_or_none(p.get(key),c.get(key))
            if delta is not None and abs(delta)>=threshold:
                events.append({'type':'MATERIAL_'+label+'_CHANGE','currency':cur,
                               'importance':'high','relative_change':round(delta,5)})
        if c.get('cashflow_status') != p.get('cashflow_status'):
            events.append({'type':'DATA_OR_TAX_STATUS_CHANGED','currency':cur,
                           'importance':'high','before':p.get('cashflow_status'),'after':c.get('cashflow_status')})
        if c.get('monthly_surplus_conditional') is not None and float(c['monthly_surplus_conditional'])<0:
            events.append({'type':'NEGATIVE_MONTHLY_CASHFLOW','currency':cur,'importance':'critical'})
    gprev=previous.get('goals_registered_not_forecast',[])
    gcur=current.get('goals_registered_not_forecast',[])
    if gprev!=gcur:events.append({'type':'GOAL_DATE_OR_SIZE_CHANGED','importance':'high'})
    if previous.get('audit',{}).get('model_inputs_sha256')!=current.get('audit',{}).get('model_inputs_sha256'):
        events.append({'type':'MODEL_ASSUMPTIONS_CHANGED','importance':'high',
                       'reason':'Re-run outcome sensitivity; assumptions change does not justify automatic investment trades'})
    if previous.get('host_action_receipts',{}).get('items')!=current.get('host_action_receipts',{}).get('items'):
        events.append({'type':'PRIMARY_SOURCE_METADATA_CHANGED','importance':'high',
                       'reason':'Substantive source review needed before changing legal conclusion'})
    if previous.get('audit',{}).get('input_sha256') != current.get('audit',{}).get('input_sha256') and not events:
        events.append({'type':'NONMATERIAL_INPUT_CHANGE','importance':'low'})
    return {
        'status':'REVIEW_REQUIRED' if any(x['importance'] in ('high','critical') for x in events) else 'MINOR_OR_MODEL_ONLY_CHANGE',
        'events':events,
        'replan_required':any(x['importance'] in ('high','critical') for x in events),
        'review_order': ['Confirm facts and authorization','Recheck tax/law if changed','Re-run math and evidence','Explain differences to user'],
        'automatic_external_action':False,
        'note':'No background monitoring or change subscriptions: compare is invoked on supplied reports only.',
    }
