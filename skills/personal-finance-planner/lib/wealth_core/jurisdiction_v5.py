"""Issue spotting for cross-border tax/legal systems; never a legal opinion.

Residence, tax residency, citizenship, payroll nexus, asset location, bank,
and payer are distinct connectors. Law must be reviewed for the as-of tax year.
"""
from __future__ import annotations

COVERED_RESEARCH = {'CN','US','HK','TH','FR','EU'}


def issue_spotting(profile:dict,scopes:list[dict]) -> dict:
    codes = {x['scope'].split(':')[0] for x in scopes}
    p=profile['person']
    residence=p['residence']['country']
    issues=[]
    def add(code,severity,what):
        issues.append({'code':code,'severity':severity,'research_question':what,'status':'REQUIRES_REAL_PRIMARY_SOURCE_AND_FACT_REVIEW'})
    if not p.get('tax_residencies_claimed'):
        add('RESIDENCE_UNVERIFIED','high','Confirm applicable personal tax-residency tests and any conflicts; residence alone is not dispositive.')
    if 'EU' in codes:
        add('EU_NOT_A_COUNTRY_TAX_RULE','high','Identify actual EU member state; EU is not one resident-person income tax code.')
    if len(codes) > 1:
        add('MULTI_NEXUS','high','Evaluate separate income source, residency, treaty qualification, permanent establishment and reporting obligations.')
    if any(i['bank_country'] != residence for i in profile['income'] if i.get('bank_country')):
        add('CROSS_BORDER_BANK','high','Receiving money offshore is not tax exemption; verify local reporting, AML/FX rules and income character.')
    if any(i['kind'] in ('pf_payout','pf_simulated_profit') for i in profile['income']):
        add('PROP_FIRM_CLASSIFICATION','high','Determine contractual PF payout, beneficial ownership, actual receipts, taxes and platform rules.')
    if residence=='US':
        add('US_SUBNATIONAL','high','Evaluate federal + applicable state and city resident taxes, filing status, payroll tax and local retirement accounts.')
    if residence=='CN':
        add('CN_SOCIAL_AND_IIT','high','Evaluate residence, annual IIT income class, contribution bases, benefits and foreign-income settlement with correct city-year.')
    if residence=='TH':
        add('TH_FOREIGN_INCOME','high','Evaluate year-specific treatment of foreign-sourced income and remittance, applicable residence status.')
    if any(a.get('location_country')=='US' for a in profile['assets']):
        add('US_ASSET_SITUS','high','Review US estate / inheritance and fund domicile exposures for non-US holders where relevant.')
    if len(p.get('citizenships',[]))>1:
        add('CITIZENSHIP_NEXUS','medium','Review citizenship-based filing rules where applicable and dual-status conflicts.')
    if set(codes)-COVERED_RESEARCH:
        add('UNCATALOGUED_JURISDICTION','high','Do not extrapolate from nearby country; seek local professional and official law.')
    return {
        'status':'LEGAL_TAX_RESEARCH_TRIAGE_ONLY',
        'scopes': [x['scope'] for x in scopes],
        'research_issues': issues,
        'law_verification_complete': False,
        'automatic_tax_liability': None,
        'declaration': 'No tax avoidance assurance, residency determination or permission to execute cross-border transactions.',
    }
