"""Effective-date validation for externally supplied law/source packages.

NEVER self-certifies substantive legal interpretation or tax-residency status.
This module requires the host to retrieve official publication text and verify
facts, dates and legal conditions separately. It cannot validate a legal claim.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import json
import re
from urllib.parse import urlsplit
from .orchestration import official_domain

TYPES={'tax','retirement','inheritance','securities_access','cross_border','social_security','insurance','consumer_protection'}


def _date(raw):
    if not isinstance(raw,str):raise ValueError('date string YYYY-MM-DD required')
    return date.fromisoformat(raw)


def inspect_law_packets(packets:list[dict],as_of:str,applicable_scopes:list[str]) -> dict:
    if not isinstance(packets,list):raise ValueError('law packets must be array')
    now=_date(as_of);results=[]
    for j,p in enumerate(packets):
        if not isinstance(p,dict):raise ValueError(f'law packet {j} must be object')
        scope=p.get('scope'); category=p.get('category')
        if not isinstance(scope,str) or not scope or category not in TYPES:
            raise ValueError(f'law packet {j} invalid scope/category')
        ef=_date(p['effective_from'])
        until=_date(p['effective_until']) if p.get('effective_until') else None
        if until and until<ef: raise ValueError('effective_until before effective_from')
        fetched=_date(p['retrieved_on'])
        if fetched>now: raise ValueError('source retrieval after planning as_of')
        url=p.get('source_url')
        if not isinstance(url,str) or not url.startswith('https://'):
            raise ValueError('HTTPS source_url required')
        sh=p.get('content_sha256')
        if not isinstance(sh,str) or not re.fullmatch('[0-9a-fA-F]{64}',sh):
            raise ValueError('content_sha256 required; host-generated fingerprint of fetched material')
        digest=sh.lower()
        target_country=scope.split(':')[0]
        found_source_scope=scope if official_domain(scope,url) else target_country
        is_official=official_domain(found_source_scope,url)
        is_effective=ef<=now and (until is None or now<=until)
        is_in_relevant_scope=scope in applicable_scopes or target_country in applicable_scopes
        results.append({
            'id':p.get('rule_id',f'no-id-{j}'),'category':category,'scope':scope,
            'country':target_country,'retrieved_on':fetched.isoformat(),'effective_from':ef.isoformat(),
            'effective_until':None if until is None else until.isoformat(),
            'source_on_curated_primary_domain':is_official,
            'effective_on_planning_date_by_claimed_metadata':is_effective,
            'scope_matches_research_targets':is_in_relevant_scope,
            'tax_year_claimed':p.get('tax_year'), 'source_sha256':digest,
            'triage_status':('CANDIDATE_AWAIT_SUBSTANTIVE_REVIEW'
                             if is_official and is_effective and is_in_relevant_scope else
                             'NOT_APPLICABLE_OR_NOT_PRIMARY_SOURCE_BY_METADATA'),
            'not_verified':'Host URL and hash may be untrustworthy; no validation of fetched body, legal scope, personal eligibility or rates.'
        })
    return {'status':'DATE_DOMAIN_SCOPE_PRECHECK_ONLY_NOT_LAW_CERTIFICATION','items':results,
            'binding_legal_opinion':False,
            'no_auto_tax_forecast':True}
