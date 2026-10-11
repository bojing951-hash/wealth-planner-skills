"""Lifecycle/debt/insurance planning issue detection (no regulated recommendations)."""
from __future__ import annotations


def household_check(profile:dict) -> dict:
    needs=[]
    age=profile['person'].get('age')
    if age is None:
        needs.append({'code':'AGE_UNKNOWN','priority':'data','why':'Retirement horizon and withdrawal period cannot be individualized.'})
    if age is not None and age >= 45:
        needs.append({'code':'RETIREMENT_TIMING','priority':'planning','why':'Request retirement age, pension and anticipated health/long-term care cash flow.'})
    if not profile['liabilities']:
        pass
    for d in profile['liabilities']:
        if 'apr' not in d:
            needs.append({'code':'DEBT_APR_MISSING','priority':'data','why':f"APR and repayment schedule needed for {d['id']} before debt payoff comparison."})
        else:
            apr=float(d['apr'])
            if not 0<=apr<3:raise ValueError('loan APR outside permitted range')
            if apr>=0.15:
                needs.append({'code':'HIGH_APR_DEBT','priority':'high','why':f"Debt {d['id']} high user-reported APR; review contractual minimums, payoff and liquidity."})
    for g in profile['goals']:
        needs.append({'code':'GOAL_LIABILITY_MATCHING','priority':'planning',
                      'why':f"Goal {g['id']} in {g['currency']} on {g['target_date']}: separate near-term liquidity from long-term risk exposure."})
    needs.append({'code':'INSURANCE_DEPENDANTS','priority':'data','why':'Confirm dependants, disability/health protection, exclusions and coverage gaps before long-term commitments.'})
    needs.append({'code':'ESTATE_SUCCESSION','priority':'planning','why':'Confirm estate domicile, ownership, beneficiaries, cross-border inheritance and powers of attorney.'})
    return {'status':'SCREENING_ISSUES_NOT_INSURANCE_OR_LEGAL_ADVICE','checklist':needs}
