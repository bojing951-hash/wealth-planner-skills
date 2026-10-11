"""Goal feasibility by exact monthly annuity algebra, given hypothetical return inputs."""
from __future__ import annotations
import math
from datetime import date
from .simulation import _months_until,_eligible_balances,_income_and_spending,_number


def required_monthly_contribution(start_balance:float,target:float,months:int,annual_return:float)->float:
    if months<=0 or start_balance<0 or target<0:raise ValueError('invalid months/balances')
    if annual_return <= -1:raise ValueError('return must exceed -100%')
    i=(1+annual_return)**(1/12)-1
    factor=(1+i)**months
    annuity=months if abs(i)<1e-12 else (factor-1)/i
    return max(0.0, (target-start_balance*factor)/annuity)


def goal_math(profile:dict,scenario_config:dict) -> dict:
    """Pure constant return identity; reserve replenishment and debts are separate constraints."""
    cur=scenario_config['currency']
    st=profile.get('risk',{}).get('income_stability','unknown')
    reserve_m=profile.get('risk',{}).get('reserve_months',6 if st=='stable' else 12)
    assets=_eligible_balances(profile,cur,reserve_m)
    cash,expenses,quality=_income_and_spending(profile,cur)
    income_surplus=cash-expenses
    rows=[]
    for label,s in scenario_config['scenarios'].items():
        growth=float(s['annual_nominal_return_net']);inflation=float(s['annual_inflation'])
        for g in profile['goals']:
            if g['currency']!=cur:continue
            months=_months_until(profile['as_of'],g['target_date'])
            if months<=0:continue
            amount=float(g['target_amount'])
            nominal_target=amount if scenario_config['goal_basis']=='nominal_future' else amount*(1+inflation)**(months/12)
            req=required_monthly_contribution(assets['initial_long_term_portfolio'],nominal_target,months,growth)
            rows.append({
                'scenario':label,'goal':g['id'],'months':months,
                'target_nominal_at_date':round(nominal_target,2),
                'required_monthly_contribution_ideal':round(req,2),
                'conditional_monthly_cash_surplus':round(income_surplus,2),
                'ideal_surplus_minus_requirement':round(income_surplus-req,2),
                'initial_emergency_reserve_shortfall_not_included':round(max(0,assets['reserve_target_at_start']-assets['initial_reserve']),2),
                'status':'IDEAL_ANNUITY_FORMULA_ONLY_NOT_PREDICTIVE_OR_INVESTABLE',
            })
    return {'status':'HYPOTHETICAL_CONSTANT_RETURN_GOAL_FEASIBILITY',
            'currency':cur,'rows':rows,'unverified_income_or_tax':quality,
            'not_modeled':'Income interruptions, stochastic investment returns, tax changes, reserve refilling and loans.'}


def fi_screen(monthly_spending:float,assumed_initial_withdrawal_rate:float):
    spend=_number(monthly_spending,'monthly_spending',0)
    rate=_number(assumed_initial_withdrawal_rate,'assumed_initial_withdrawal_rate',.001,.15)
    return {'annual_expense':round(12*spend,2), 'fi_reference_capital':round(12*spend/rate,2),
            'assumed_initial_withdrawal_rate':rate,
            'note':'Screening ratio only. Retirement duration, inflation, taxes, health care, pension and sequence risk can invalidate withdrawal sustainability.'}
