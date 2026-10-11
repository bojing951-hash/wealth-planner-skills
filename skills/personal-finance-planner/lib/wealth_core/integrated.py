"""End-to-end bounded decision support assembled around the v0.4 contracts."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from . import VERSION_V5 as VERSION

# 5.1 changes the *Skill instructions*, not the v5.0 financial schema/math.
SKILL_RELEASE = '5.1.0'
from .orchestration import build_plan, digest
from .profile import validate_profile
from .host_bridge import make_host_queue
from .evidence import evaluate
from .jurisdiction_v5 import issue_spotting
from .tax_scenarios import calculate_hypothetical_tax
from .portfolio import portfolio_diagnostics
from .simulation import simulate
from .dynamic import compare
from .law_registry import inspect_law_packets
from .macro_review import check_macro_evidence
from .household import household_check
from .goal_math import goal_math, fi_screen


def normalize_profile_v5(raw:dict) -> tuple[dict,str]:
    if not isinstance(raw,dict):raise ValueError('profile must be an object')
    version=raw.get('schema_version')
    if version not in ('0.4.0','5.0.0'):
        raise ValueError('Profile schema_version must be 0.4.0 or 5.0.0')
    # Stable old contract; user input is not modified. All v5 model assumptions are separate.
    temp=deepcopy(raw)
    temp['schema_version']='0.4.0'
    validate_profile(temp)
    return temp,version


def build_integrated(profile:dict, capabilities:dict|None=None, receipts:list|None=None,
                     assumptions:dict|None=None, hypothetical_tax:dict|None=None,
                     portfolio:dict|None=None, previous:dict|None=None,
                     law_packets:list|None=None, macro_bundle:dict|None=None) -> dict:
    normalized,source_version=normalize_profile_v5(profile)
    report=build_plan(normalized,capabilities,receipts)
    report['skill_version']=SKILL_RELEASE
    report['schema_version']=source_version
    # Revision ID covers EVERY decision-changing input, not merely cash-flow inputs.
    graph_path = Path(__file__).resolve().parents[2] / 'policies' / 'theory_graph.json'
    graph_hash=sha256(graph_path.read_bytes()).hexdigest()
    fingerprints={'profile': profile, 'capabilities': capabilities, 'receipts': receipts,
                  'assumptions': assumptions, 'hypothetical_tax': hypothetical_tax,
                  'portfolio': portfolio, 'law_packets': law_packets, 'macro_bundle': macro_bundle,
                  'graph_sha256': graph_hash, 'code_version': VERSION, 'skill_release': SKILL_RELEASE}
    report['run_id']='v5-'+digest(fingerprints)[:20]
    report['audit']['theory_graph_sha256']=graph_hash
    report['audit']['model_inputs_sha256']=digest({'assumptions':assumptions,'portfolio':portfolio,'hypothetical_tax':hypothetical_tax})
    report['audit']['code_version']=VERSION
    report['audit']['skill_release']=SKILL_RELEASE
    report['audit']['architecture_baseline']='original-v0.4'
    report['audit']['calculator']='wealth_core integrated v5 (cashflow / theory / scenario)'
    report['audit']['original_input_sha256']=digest(profile)
    report['host_action_queue']=make_host_queue(report)
    report['evidence_assessment']=evaluate(normalized)
    report['legal_tax_triage']=issue_spotting(normalized,report['jurisdiction_map'])
    report['household_lifecycle_triage']=household_check(normalized)
    if law_packets is not None:
        report['law_packet_triage']=inspect_law_packets(law_packets,normalized['as_of'],
                                                    [x['scope'] for x in report['jurisdiction_map']])
    if macro_bundle is not None:
        macro_currency=macro_bundle.get('currency')
        if macro_currency not in report['financial_snapshot']['currency_buckets']:
            raise ValueError('macro currency not present in user finance cash-flow buckets')
        report['macro_observations_review']=check_macro_evidence(macro_bundle,normalized['as_of'],macro_currency)
    report['assumption_checks']={
        'tax_from_2026_law_verified':False,
        'host_research_completed': report['host_action_receipts']['receipt_count']>0,
        'research_substantively_legally_verified':False,
        'user_income_independently_audited':False,
        'macroeconomic_forecasts_calibrated':False,
    }
    if hypothetical_tax is not None:
        if hypothetical_tax.get('currency') not in report['financial_snapshot']['currency_buckets']:
            raise ValueError('hypothetical tax currency absent from financial snapshot')
        report['hypothetical_tax_math']=calculate_hypothetical_tax(hypothetical_tax)
    if portfolio is not None:
        report['portfolio_research']=portfolio_diagnostics(portfolio)
    if assumptions is not None:
        report['long_horizon_scenarios']=simulate(normalized,assumptions)
        report['goal_feasibility_math']=goal_math(normalized,assumptions)
        if assumptions.get('assumed_initial_withdrawal_rate') is not None:
            sp=report['financial_snapshot']['currency_buckets'][assumptions['currency']]['monthly_expenses']['total']
            report['fi_screen']=fi_screen(float(sp),float(assumptions['assumed_initial_withdrawal_rate']))
        report['audit']['scenario_assumptions_sha256']=digest(assumptions)
        report['assumption_checks']['user_supplied_scenario_inputs']=True
    else:
        report['long_horizon_scenarios']={'status':'NOT_RUN_NO_EXPLICIT_ASSUMPTIONS'}
    consistency=[]
    if assumptions is not None and portfolio is not None:
        returns=report['portfolio_research']['assumed_net_of_expense_ratio_approximation']
        vol=report['portfolio_research']['portfolio_volatility_from_provided_covariance']
        for label,item in assumptions['scenarios'].items():
            if abs(returns-float(item['annual_nominal_return_net']))>0.01:
                consistency.append({'scenario':label,'type':'RETURN_ASSUMPTION_MISMATCH',
                                    'portfolio_approx_net_return':returns,
                                    'scenario_return':float(item['annual_nominal_return_net']),
                                    'guidance':'Compare modeling universes, costs, fees, tax assumptions and horizons before using scenario.'})
            if vol is not None and abs(vol-float(item['annual_volatility']))>0.03:
                consistency.append({'scenario':label,'type':'VOLATILITY_ASSUMPTION_MISMATCH',
                                    'portfolio_volatility':vol,
                                    'scenario_volatility':float(item['annual_volatility']),
                                    'guidance':'A covariance estimate should not be silently replaced by an unrelated stochastic-vol assumption.'})
    report['model_consistency_warnings']=consistency
    # Decisions are CONDITIONAL questions, not a securities trade order or jurisdictional conclusion.
    actions=[]
    for cur,b in report['financial_snapshot']['currency_buckets'].items():
        if b['cashflow_status'] == 'INCOMPLETE_GROSS_ONLY':
            actions.append({'category':'CASHFLOW','currency':cur,'priority':1,
                            'status':'BLOCKED','why':'Gross-only income, no confirmed net receipt; need post-tax record.'})
        elif b['monthly_surplus_conditional'] is not None and float(b['monthly_surplus_conditional']) < 0:
            actions.append({'category':'CASHFLOW','currency':cur,'priority':1,
                            'status':'REVIEW','why':'Monthly budget negative; avoid adding investment risk before restoring cash flow.'})
        if float(b['reserve_shortfall_declared']) > 0:
            actions.append({'category':'LIQUIDITY','currency':cur,'priority':2,
                            'status':'REVIEW','why':'Emergency reserve below explicitly selected heuristic; check actual cash and obligations.'})
        if b['tax_uncertain_income_ids']:
            actions.append({'category':'TAX','currency':cur,'priority':1,
                            'status':'BLOCKED_FOR_DEFINITIVE_TAX_ADVICE',
                            'why':'Withholding or user estimate alone does not settle annual/cross-border tax liability.'})
    actions.append({'category':'LAW','priority':1,'status':'RESEARCH_REQUIRED',
                    'why':'Verify effective-year and multi-scope law before claiming tax advantage or product access.'})
    actions.append({'category':'INVESTMENT','priority':3,'status':'RESEARCH_ONLY',
                    'why':'Compare low-cost diversified candidates; match time horizon and liabilities; no personalized trade order.'})
    report['conditional_policy_queue']=sorted(actions,key=lambda x:x['priority'])
    report['workflow_v5']={
        'intake':'COMPLETE_SCHEMA_VALIDATED',
        'host_tools':'DELEGATED_HOST_QUEUE_NOT_SELF_EXECUTING',
        'theory':'INTEGRATED_CONDITIONAL_ANALYSIS',
        'jurisdiction':'ISSUE_SPOTTING_NOT_CURRENT_TAX_CALCULATION',
        'portfolio':'RUN_USER_ASSUMPTIONS' if portfolio is not None else 'NEEDS_EXPLICIT_INPUTS',
        'tax':'HYPOTHETICAL_ONLY' if hypothetical_tax is not None else 'NEEDS_VERIFIED_RULES',
        'long_horizon':'UNCALIBRATED_MONTE_CARLO' if assumptions is not None else 'NEEDS_ASSUMPTIONS',
        'monitoring':'ON_DEMAND_REVIEW_NO_BACKGROUND_JOB',
        'law_packets':'DATE_SCOPE_TRIAGE_ONLY' if law_packets is not None else 'NO_PACKET',
        'macro_observations':'UNVERIFIED_DATA_OBSERVATIONS' if macro_bundle is not None else 'NO_DATA',
    }
    report['product_maturity']={
        'designation':'VERSION_5_1_SKILL_FIRST_DEVELOPER_PREVIEW',
        'available':['deterministic finance snapshot','host task queue','theory conflict selection',
                     'jurisdiction issue spotting','optional hypothetical marginal-tax math',
                     'optional risk and fee analytics','optional reproducible Monte Carlo',
                     'law packet date/domain scope triage', 'macro snapshot sanity checks',
                     'lifecycle/debt/insurance issues', 'on-demand change comparison'],
        'not_available':['verified complete global tax engines','host plugin installation proof',
                         'automated bank account reading','credential management',
                         'live macro calibration and guaranteed forecast','automatic trades, filing or background monitoring'],
    }
    report.pop('out_of_scope_until_later_version',None)
    if previous is not None:
        report['change_detection']=compare(previous,report)
    return report
