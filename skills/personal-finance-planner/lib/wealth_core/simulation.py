"""Reproducible retirement / saving Monte Carlo SCENARIOS, not forecasts.

Inputs supply all capital-market assumptions; no fake calibration and no tax law.
Monthly nominal stochastic returns are normal approximations, so fat tails and
nonstationarity are NOT captured. Inflation and income dynamics are assumptions.
"""
from __future__ import annotations
from datetime import date
import math
import random
from statistics import fmean


def _number(v, label, low=None, high=None):
    if isinstance(v, bool):
        raise ValueError(f'{label} cannot be boolean')
    try: x=float(v)
    except (TypeError, ValueError): raise ValueError(f'{label} invalid number') from None
    if not math.isfinite(x) or (low is not None and x<low) or (high is not None and x>high):
        raise ValueError(f'{label} outside allowed range')
    return x


def _percentile(values:list[float], p:float):
    if not values: return None
    values=sorted(values)
    loc=(len(values)-1)*p
    low=int(math.floor(loc)); high=int(math.ceil(loc))
    return values[low]*(1-(loc-low))+values[high]*(loc-low)


def _months_until(start: str, end: str):
    delta=(date.fromisoformat(end)-date.fromisoformat(start)).days
    return max(0, round(delta / (365.2425/12)))


def _eligible_balances(profile:dict, currency:str, reserve_months:int):
    cash=0.0; invested=0.0; excluded=0.0
    for a in profile['assets']:
        if a['currency']!=currency or a['kind']=='pf_simulated_balance':
            continue
        if a['ownership'] not in ('user','joint'):
            continue
        share=float(a.get('beneficial_share',0)) if a['ownership']=='joint' else 1.0
        if share == 0: continue
        val=float(a['amount'])*share
        if a['kind']=='cash' and a['liquidity']=='liquid':
            cash+=val
        elif a['kind']=='investment' and a['liquidity'] in ('liquid','long_term'):
            invested+=val
        else:
            excluded+=val
    ess=sum(float(e['monthly_amount']) for e in profile['expenses'] if e['currency']==currency and e['category']=='essential')
    reserve_target=ess*reserve_months
    return {
        'initial_cash_like':cash, 'initial_unrestricted_risk_investment': invested,
        'restricted_and_unmodeled_assets':excluded,'essential_monthly':ess,
        'reserve_target_at_start':reserve_target,
        'initial_reserve':min(cash, reserve_target),
        'initial_long_term_portfolio': invested+max(0.0,cash-reserve_target),
    }


def _income_and_spending(profile:dict,currency:str):
    income=0.0; unverifiable=[]
    for i in profile['income']:
        if i['currency']!=currency:continue
        if i['kind']=='pf_simulated_profit' or not i['bank_received'] or not i['realized']:
            continue
        if i.get('net_received') is None:
            unverifiable.append(i['id']);continue
        income+=float(i['net_received'])
        if i['tax_status'] not in ('settled','professional_verified','not_applicable'):
            unverifiable.append(i['id'] + ':tax_provisional')
    out=sum(float(e['monthly_amount']) for e in profile['expenses'] if e['currency']==currency)
    out+=sum(float(d.get('monthly_payment','0')) for d in profile['liabilities'] if d['currency']==currency)
    return income,out,unverifiable


def _validate_assumptions(cfg:dict):
    if not isinstance(cfg,dict) or cfg.get('model_kind')!='UNCALIBRATED_USER_SCENARIOS':
        raise ValueError('Explicit model_kind=UNCALIBRATED_USER_SCENARIOS required')
    cur=cfg.get('currency')
    if not isinstance(cur,str) or len(cur)!=3 or not cur.isalpha() or not cur.isupper():
        raise ValueError('model currency must be uppercase ISO three-letter')
    years=cfg.get('horizon_years')
    paths=cfg.get('paths')
    seed=cfg.get('seed')
    if type(years)!=int or not 1<=years<=50: raise ValueError('horizon_years 1..50 integer')
    if type(paths)!=int or not 100<=paths<=10000: raise ValueError('paths 100..10000 integer')
    if type(seed)!=int or not 0<=seed<=2**32-1: raise ValueError('seed integer 0..2**32-1')
    if not isinstance(cfg.get('scenarios'),dict) or not 1<=len(cfg['scenarios'])<=5:
        raise ValueError('scenarios must contain 1..5 scenarios')
    for key, s in cfg['scenarios'].items():
        if not isinstance(key,str) or not isinstance(s,dict): raise ValueError('invalid scenario')
        _number(s.get('annual_nominal_return_net'), 'annual_nominal_return_net', -0.95, 2)
        _number(s.get('annual_volatility'), 'annual_volatility', 0, 2)
        _number(s.get('annual_inflation'), 'annual_inflation', -0.2, 1)
        _number(s.get('annual_income_growth'), 'annual_income_growth', -0.9, 2)
        _number(s.get('annual_spending_growth'), 'annual_spending_growth', -0.9, 2)
        if 'retire_after_years' in s:
            ra=s['retire_after_years']
            if type(ra)!=int or not 0<=ra<=years:raise ValueError('retire_after_years invalid')
        interruption=s.get('income_interruption',{})
        if interruption:
            if type(interruption.get('start_month'))!=int or type(interruption.get('duration_months'))!=int:
                raise ValueError('income interruption month/duration must be integers')
            if not 1<=interruption['start_month']<=years*12 or not 0<=interruption['duration_months']<=years*12:
                raise ValueError('income interruption out of bounds')
            _number(interruption.get('income_loss_fraction'), 'income_loss_fraction',0,1)
    if cfg.get('goal_basis') not in {'nominal_future', 'real_today'}:
        raise ValueError('goal_basis required: nominal_future or real_today')


def simulate(profile:dict,cfg:dict) -> dict:
    _validate_assumptions(cfg)
    currency=cfg['currency']; years=cfg['horizon_years']; months=years*12; paths=cfg['paths']; seed=cfg['seed']
    st=profile.get('risk',{}).get('income_stability','unknown')
    reserve_m=profile.get('risk',{}).get('reserve_months', 6 if st=='stable' else 12)
    balances=_eligible_balances(profile,currency,reserve_m)
    received,expense,quality=_income_and_spending(profile,currency)
    if not any(i['currency']==currency for i in profile['income']):
        raise ValueError('model currency has no income in profile')
    if any(i['currency']==currency and i['bank_received'] and i['realized'] and i.get('net_received') is None
           for i in profile['income']):
        raise ValueError('Cannot simulate complete cash flow with gross-only received income')
    goals=[]
    for g in profile['goals']:
        if g['currency']!=currency:continue
        n=_months_until(profile['as_of'],g['target_date'])
        if 0<n<=months:
            goals.append({'id':g['id'],'amount':float(g['target_amount']),'due_month':n})
    debts=[i for i in profile['liabilities'] if i['currency']==currency and float(i['balance'])>0]
    output={}
    for scenario_name,s in cfg['scenarios'].items():
        rng=random.Random(seed+int.from_bytes(scenario_name.encode('utf-8'),'little') % 100000)
        avg=_number(s['annual_nominal_return_net'],'return',-0.95,2)
        vol=_number(s['annual_volatility'],'vol',0,2)
        inf=_number(s['annual_inflation'],'infl',-0.2,1)
        income_g=_number(s['annual_income_growth'],'income_growth',-0.9,2)
        spending_g=_number(s['annual_spending_growth'],'spending_growth',-0.9,2)
        monthly_return=(1+avg)**(1/12)-1
        monthly_vol=vol / math.sqrt(12)
        monthly_income_g=(1+income_g)**(1/12)
        monthly_spending_g=(1+spending_g)**(1/12)
        deflator=(1+inf)**years
        retirement_month=s.get('retire_after_years',years+1)*12
        interruption=s.get('income_interruption') or {}
        point_names=[g['id'] for g in goals]
        goal_wins={k:0 for k in point_names}
        end_nominal=[];end_real=[]; ruins=0; total_contrib=[]
        for k in range(paths):
            reserve=balances['initial_reserve']; investment=balances['initial_long_term_portfolio']
            ever_ruined=False; contribution=0.0
            for month in range(1,months+1):
                t=month-1
                current_income=received*(monthly_income_g**t)
                if month>retirement_month:
                    current_income=0
                if interruption:
                    start=interruption['start_month']; dur=interruption['duration_months']
                    if start<=month<start+dur:
                        current_income*=(1-interruption['income_loss_fraction'])
                current_expense=expense*(monthly_spending_g**t)
                required_reserve=balances['reserve_target_at_start']*(monthly_spending_g**t)
                net=current_income-current_expense
                market_draw=0 if monthly_vol==0 else rng.gauss(0,monthly_vol)
                investment=max(0.0,investment*(1+max(-0.999,monthly_return+market_draw)))
                if net>=0:
                    save=min(net,max(0.0,required_reserve-reserve));reserve+=save
                    contribution+=net-save;investment+=net-save
                else:
                    hit=min(reserve,-net);reserve-=hit
                    shortfall=-net-hit
                    if shortfall>0:
                        investment-=shortfall
                        if investment<0:ever_ruined=True;investment=0.0
                if month in [g['due_month'] for g in goals]:
                    for g in goals:
                        if g['due_month'] != month: continue
                        ref=g['amount'] if cfg['goal_basis']=='nominal_future' else g['amount']*(1+inf)**(month/12)
                        if reserve+investment>=ref:
                            goal_wins[g['id']]+=1
            if ever_ruined:ruins+=1
            value=reserve+investment
            end_nominal.append(value);end_real.append(value/deflator);total_contrib.append(contribution)
        goal_report=[]
        for g in goals:
            goal_report.append({
                'goal_id': g['id'], 'goal_month': g['due_month'],
                'target_basis':cfg['goal_basis'],
                'success_probability_conditional': None if debts else round(goal_wins[g['id']]/paths,4),
                'status': 'BLOCKED_NET_WORTH_DEBT_AMORTIZATION' if debts else 'MODEL_CONDITIONAL_NOT_PREDICTIVE',
            })
        output[scenario_name]={
            'assumed_annual_nominal_return_net':avg,'assumed_annual_volatility':vol,
            'assumed_annual_inflation':inf,
            'final_nominal_p05':round(_percentile(end_nominal,.05),2),
            'final_nominal_median':round(_percentile(end_nominal,.5),2),
            'final_nominal_p95':round(_percentile(end_nominal,.95),2),
            'final_real_today_p05':round(_percentile(end_real,.05),2),
            'final_real_today_median':round(_percentile(end_real,.5),2),
            'final_real_today_p95':round(_percentile(end_real,.95),2),
            'ever_insolvent_paths_fraction':round(ruins/paths,4),
            'median_new_long_term_contributions_nominal':round(_percentile(total_contrib,.5),2),
            'goals': goal_report,
        }
    return {
        'status':'UNCALIBRATED_PROBABILITY_WITHIN_ASSUMED_MODEL_ONLY',
        'currency':currency,'horizon_years':years,'paths_per_scenario':paths,'seed':seed,
        'cash_model':{'initial_received_income_monthly':received,'initial_expenses_and_debt_payment_monthly':expense,**balances},
        'scenarios':output,
        'assumption_origin':'ALL RETURNS, INFLATION, VOLATILITY, SHOCKS AND INCOME PATHS USER-SUPPLIED, NOT LIVE DATA',
        'input_provisional_reasons':quality,
        'net_wealth_goal_blocked_by_unmodeled_debt': bool(debts),
        'risk_limits':[
            'Normal monthly return approximation misses crashes, fat tails, structural breaks and changing correlations.',
            'Constant annual inflation/income trend within each scenario; no validated capital-market distribution.',
            'Restricted pension, property, tax regime, employer matching and debt amortization are NOT in stochastic asset paths.',
            'No automatic tax payments or security-specific decisions. Probability means only under supplied assumptions.',
        ],
    }
