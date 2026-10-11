"""v5 integrated algorithmic and safety regression tests. No real account or web access."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE=pathlib.Path(__file__).resolve().parents[1]
SKILL=HERE/'skills'/'personal-finance-planner'
sys.path.insert(0,str(SKILL/'lib'))
from wealth_core.integrated import normalize_profile_v5,build_integrated
from wealth_core.evidence import evaluate,identify_topics
from wealth_core.host_bridge import make_host_queue
from wealth_core.tax_scenarios import calculate_hypothetical_tax
from wealth_core.portfolio import portfolio_diagnostics
from wealth_core.simulation import simulate
from wealth_core.dynamic import compare
from wealth_core.law_registry import inspect_law_packets
from wealth_core.macro_review import check_macro_evidence
from wealth_core.household import household_check
from wealth_core.fx import convert


def fixture(name):
    return json.loads((SKILL/'examples'/name).read_text(encoding='utf8'))

class V5IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sz=fixture('v5-shenzhen.json')
        cls.ny=fixture('v5-new-york.json')
        cls.cnmodel=fixture('v5-scenarios-cny.json')

    def test_schema_migration_v5_to_v04_is_backward_compatible(self):
        p,v=normalize_profile_v5(self.sz)
        self.assertEqual(p['schema_version'],'0.4.0')
        self.assertEqual(v,'5.0.0')

    def test_schema_migration_not_mutating_original(self):
        before=copy.deepcopy(self.sz)
        normalize_profile_v5(self.sz)
        self.assertEqual(before,self.sz)

    def test_v04_input_accepted(self):
        p=fixture('v04-shenzhen.json')
        self.assertEqual(build_integrated(p)['schema_version'],'0.4.0')

    def test_no_fake_actual_tax_or_law_proof(self):
        r=build_integrated(self.ny)
        self.assertFalse(r['assumption_checks']['tax_from_2026_law_verified'])
        self.assertIsNone(r['legal_tax_triage']['automatic_tax_liability'])
        self.assertFalse(r['legal_tax_triage']['law_verification_complete'])

    def test_cny_usd_separate(self):
        p=fixture('v5-cn-hk-pf.json')
        r=build_integrated(p)
        self.assertIn('CNY',r['financial_snapshot']['currency_buckets'])
        self.assertNotIn('fx_conversion',r)
        self.assertIn('PROP_FIRM_CLASSIFICATION',[i['code'] for i in r['legal_tax_triage']['research_issues']])

    def test_pf_virtual_balances_not_net_wealth(self):
        r=build_integrated(fixture('v5-cn-hk-pf.json'))
        cs=r['financial_snapshot']['currency_buckets']
        has_exclusion=any(float(x['simulated_pf_assets_excluded'])>0 for x in cs.values())
        self.assertTrue(has_exclusion)

    def test_routing_no_capability_no_imaginary_tools(self):
        r=build_integrated(self.ny)
        self.assertEqual(r['host_action_queue']['ready_count'],0)
        self.assertTrue(any(x['status']=='UNAVAILABLE' for x in r['host_action_queue']['queue']))
        self.assertFalse(r['assumption_checks']['host_research_completed'])

    def test_declared_tools_do_not_mean_invoked(self):
        r=build_integrated(self.ny,fixture('v04-capabilities-codex-EXAMPLE.json'))
        self.assertTrue(any(x['status']=='QUEUED_FOR_HOST' for x in r['host_action_queue']['queue']))
        self.assertEqual(r['host_action_queue']['completed_metadata_count'],0)
        self.assertTrue(r['host_action_queue']['ready_count']>0)

    def test_evidence_auto_integrated(self):
        r=build_integrated(self.sz)
        ids={i['id'] for i in r['evidence_assessment']['principles']}
        self.assertTrue({'LIFECYCLE','MARKOWITZ','BOGLE','ALM','BENGEN'}<=ids)
        self.assertGreaterEqual(len(r['evidence_assessment']['relationships']),4)

    def test_evidence_not_claim_scientific_consensus(self):
        r=evaluate(self.sz)
        self.assertIn('NOT_AUTOMATIC_SCIENTIFIC_CONSENSUS',r['status'])
        self.assertTrue(all(x['source_status']=='CURATED_REFERENCE_NOT_THIS_RUN_INDEPENDENTLY_VERIFIED' for x in r['principles']))

    def test_version_and_run_fingerprints_distinguish_assumptions(self):
        a=build_integrated(self.sz,assumptions=self.cnmodel)
        cfg=copy.deepcopy(self.cnmodel);cfg['scenarios']['base']['annual_nominal_return_net']=.051
        b=build_integrated(self.sz,assumptions=cfg)
        self.assertNotEqual(a['run_id'],b['run_id'])
        self.assertEqual(compare(a,b)['events'][0]['type'],'MODEL_ASSUMPTIONS_CHANGED')

    def test_run_determinism_same_inputs(self):
        a=build_integrated(self.sz,assumptions=self.cnmodel)
        b=build_integrated(self.sz,assumptions=self.cnmodel)
        self.assertEqual(a,b)

    def test_no_persistence_or_external_transfers(self):
        r=build_integrated(self.sz)
        self.assertFalse(r['audit']['stores_personal_financial_data'])
        self.assertNotIn('account_transfer',r['host_action_queue'])
        self.assertEqual(r['workflow_v5']['monitoring'],'ON_DEMAND_REVIEW_NO_BACKGROUND_JOB')

    def test_lifecycle_check(self):
        r=build_integrated(self.sz)
        self.assertIn('ESTATE_SUCCESSION',[x['code'] for x in r['household_lifecycle_triage']['checklist']])

    def test_missing_tax_residency_flags(self):
        p=copy.deepcopy(self.sz);p['person'].pop('tax_residencies_claimed')
        self.assertIn('RESIDENCE_UNVERIFIED',[x['code'] for x in build_integrated(p)['legal_tax_triage']['research_issues']])

    def test_cli_runs_portable_skill_copied_without_repository(self):
        with tempfile.TemporaryDirectory() as t:
            import shutil
            dst=pathlib.Path(t)/'skill'
            shutil.copytree(SKILL,dst,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            p=subprocess.run([sys.executable,str(dst/'scripts'/'wealth_v5.py'),'validate',
                              '--input',str(dst/'examples'/'v5-shenzhen.json')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)['status'],'VALID')

class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=fixture('v5-shenzhen.json')
        cls.cfg=fixture('v5-scenarios-cny.json')

    def test_probabilities_bounded(self):
        r=simulate(self.p,self.cfg)
        for v in r['scenarios'].values():
            for goal in v['goals']:
                self.assertGreaterEqual(goal['success_probability_conditional'],0)
                self.assertLessEqual(goal['success_probability_conditional'],1)
            self.assertLessEqual(v['final_nominal_p05'],v['final_nominal_median'])
            self.assertLessEqual(v['final_nominal_median'],v['final_nominal_p95'])
            self.assertGreaterEqual(v['final_real_today_median'],0)

    def test_seed_replay_identical(self):
        a=simulate(self.p,self.cfg);b=simulate(self.p,self.cfg)
        self.assertEqual(a,b)

    def test_no_returns_guessed_without_scenarios(self):
        r=build_integrated(self.p)
        self.assertEqual(r['long_horizon_scenarios']['status'],'NOT_RUN_NO_EXPLICIT_ASSUMPTIONS')

    def test_real_median_below_nominal_when_positive_inflation(self):
        r=simulate(self.p,self.cfg)
        self.assertLess(r['scenarios']['base']['final_real_today_median'],r['scenarios']['base']['final_nominal_median'])

    def test_different_currency_reject(self):
        cfg=copy.deepcopy(self.cfg);cfg['currency']='USD'
        with self.assertRaises(ValueError):simulate(self.p,cfg)

    def test_no_model_kind_reject(self):
        cfg=copy.deepcopy(self.cfg);cfg.pop('model_kind')
        with self.assertRaises(ValueError):simulate(self.p,cfg)

    def test_no_goal_basis_reject(self):
        cfg=copy.deepcopy(self.cfg);cfg.pop('goal_basis')
        with self.assertRaises(ValueError):simulate(self.p,cfg)

    def test_paths_bounds(self):
        cfg=copy.deepcopy(self.cfg);cfg['paths']=100000
        with self.assertRaises(ValueError):simulate(self.p,cfg)

    def test_if_zero_vol_each_path_identical_for_same_scenario(self):
        cfg=copy.deepcopy(self.cfg);cfg['scenarios']={'deterministic':copy.deepcopy(cfg['scenarios']['base'])}
        cfg['scenarios']['deterministic']['annual_volatility']=0
        x=simulate(self.p,cfg)['scenarios']['deterministic']
        self.assertEqual(x['final_nominal_p05'],x['final_nominal_p95'])

    def test_income_interruption_damages_low_reserve(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['scenarios']={'stress':cfg['scenarios']['stress']}
        p=copy.deepcopy(self.p);p['assets'][0]['amount']='0'
        x=simulate(p,cfg)
        self.assertLess(x['scenarios']['stress']['final_real_today_median'],1000000)

    def test_pf_owning_not_assumed(self):
        p=fixture('v5-cn-hk-pf.json')
        # CNY and USD remain separate. Individual risk in unconfirmed capital excluded.
        r=build_integrated(p)
        self.assertTrue(any('excluded PF simulated' in s for s in r['financial_snapshot']['warnings']))

    def test_unmodeled_debt_blocks_net_wealth_probability(self):
        p=copy.deepcopy(self.p)
        p['liabilities']=[{'id':'loan','currency':'CNY','balance':'100000','monthly_payment':'1000'}]
        r=simulate(p,self.cfg)
        self.assertTrue(r['net_wealth_goal_blocked_by_unmodeled_debt'])
        self.assertIsNone(r['scenarios']['base']['goals'][0]['success_probability_conditional'])

class TaxMathTests(unittest.TestCase):
    def test_simple_progressive_bracket(self):
        cfg={'classification':'HYPOTHETICAL_USER_SUPPLIED','currency':'USD','annual_gross':'150',
             'tax_brackets':[{'upper':'100','rate':'.1'},{'upper':None,'rate':'.2'}]}
        o=calculate_hypothetical_tax(cfg)
        self.assertEqual(o['estimated_tax'],'20.00')
        self.assertEqual(o['illustrative_annual_net'],'130.00')

    def test_deduction_and_credit(self):
        cfg={'classification':'HYPOTHETICAL_USER_SUPPLIED','currency':'CNY','annual_gross':'200',
             'deductions':'50','credits':'10','social_contributions':'20',
             'tax_brackets':[{'upper':None,'rate':'.1'}]}
        o=calculate_hypothetical_tax(cfg)
        self.assertEqual(o['estimated_tax'],'5.00')
        self.assertEqual(o['illustrative_annual_net'],'175.00')

    def test_classification_hard_gate(self):
        cfg=fixture('v5-FAKE-tax-math.json');cfg['classification']='OFFICIAL_VERIFIED'
        with self.assertRaises(ValueError):calculate_hypothetical_tax(cfg)

    def test_brackets_must_cover_taxable_income(self):
        cfg={'classification':'HYPOTHETICAL_USER_SUPPLIED','currency':'USD','annual_gross':200,
             'tax_brackets':[{'upper':100,'rate':.1}]}
        with self.assertRaises(ValueError):calculate_hypothetical_tax(cfg)

    def test_no_negative_deductions(self):
        cfg=fixture('v5-FAKE-tax-math.json');cfg['deductions']=-1
        with self.assertRaises(ValueError):calculate_hypothetical_tax(cfg)

class PortfolioTests(unittest.TestCase):
    def test_hypothetical_portfolio_weights(self):
        o=portfolio_diagnostics(fixture('v5-portfolio-HYPOTHETICAL.json'))
        self.assertTrue(o['weighted_expense_ratio_only']>0)
        self.assertEqual(o['portfolio_volatility_from_provided_covariance'],None)

    def test_correlation_more_than_one_reject(self):
        o={'assets':[{'name':'a','weight':.5,'assumed_nominal_return':.05},
                     {'name':'b','weight':.5,'assumed_nominal_return':.03}],
           'annual_covariance':[[.01,.03],[.03,.01]]}
        with self.assertRaises(ValueError):portfolio_diagnostics(o)

    def test_drift_is_separate_from_suggesting_trades(self):
        o={'assets':[{'name':'a','weight':.6,'assumed_nominal_return':.05},
                     {'name':'b','weight':.4,'assumed_nominal_return':.03}]}
        r=portfolio_diagnostics(o,{'a':.4,'b':.6})
        self.assertEqual(r['drift'][0]['drift_pp'],-20.0)
        self.assertNotIn('trade_orders',r)

    def test_negative_weight_reject(self):
        o={'assets':[{'name':'a','weight':-1,'assumed_nominal_return':.05}]}
        with self.assertRaises(ValueError):portfolio_diagnostics(o)

class DynamicTests(unittest.TestCase):
    def test_material_income_change(self):
        p=fixture('v5-shenzhen.json')
        before=build_integrated(p)
        p['income'][0]['net_received']='25000'
        after=build_integrated(p)
        d=compare(before,after)
        self.assertTrue(d['replan_required'])
        self.assertIn('MATERIAL_INCOME_CHANGE',[x['type'] for x in d['events']])

    def test_tax_year_rollover(self):
        p=fixture('v5-shenzhen.json')
        before=build_integrated(p)
        p['as_of']='2027-01-11'
        after=build_integrated(p)
        d=compare(before,after)
        self.assertIn('TAX_YEAR_ROLLOVER',[x['type'] for x in d['events']])

    def test_jurisdiction_change(self):
        p=fixture('v5-shenzhen.json')
        before=build_integrated(p)
        p['person']['residence']['city']='Shanghai';p['person']['residence']['region']='Shanghai'
        after=build_integrated(p)
        d=compare(before,after)
        self.assertIn('JURISDICTION_REVIEW',[x['type'] for x in d['events']])

    def test_same_plan_id_not_replan(self):
        a=build_integrated(fixture('v5-shenzhen.json'))
        self.assertEqual(compare(a,a)['status'],'UNCHANGED_IDENTICAL_PLAN_ID')

class LawAndMacroTests(unittest.TestCase):
    def test_law_metadata_only_no_conclusion(self):
        p={'rule_id':'FAKE-TEST','category':'tax','scope':'US',
           'effective_from':'2026-01-01','retrieved_on':'2026-10-01',
           'source_url':'https://www.irs.gov/','content_sha256':'a'*64,'tax_year':2026}
        x=inspect_law_packets([p],'2026-10-11',['US'])
        self.assertEqual(x['items'][0]['triage_status'],'CANDIDATE_AWAIT_SUBSTANTIVE_REVIEW')
        self.assertFalse(x['binding_legal_opinion'])

    def test_law_future_effective_not_claim_current(self):
        p={'category':'tax','scope':'US','effective_from':'2028-01-01','retrieved_on':'2026-01-01',
           'source_url':'https://www.irs.gov/','content_sha256':'b'*64}
        x=inspect_law_packets([p],'2026-10-11',['US'])
        self.assertFalse(x['items'][0]['effective_on_planning_date_by_claimed_metadata'])

    def test_law_unverified_domain_reject_as_primary(self):
        p={'category':'tax','scope':'US','effective_from':'2026-01-01','retrieved_on':'2026-01-01',
           'source_url':'https://irs.gov.evil.example/','content_sha256':'b'*64}
        x=inspect_law_packets([p],'2026-10-11',['US'])
        self.assertFalse(x['items'][0]['source_on_curated_primary_domain'])

    def test_macro_currency_mismatch_reject(self):
        o={'currency':'USD','observations':[]}
        with self.assertRaises(ValueError):check_macro_evidence(o,'2026-10-11','CNY')

    def test_macro_stale_detect(self):
        o={'currency':'USD','observations':[{'series_id':'REAL_10Y','currency':'USD','value':1.7,
            'unit':'pct','observation_date':'2022-01-01','retrieved_on':'2026-10-10',
            'source_url':'https://fred.stlouisfed.org'}]}
        x=check_macro_evidence(o,'2026-10-11','USD')
        self.assertEqual(x['observations'][0]['status'],'STALE_FOR_ECONOMIC_REVIEW')
        self.assertFalse(x['model_calibration_completed'])

    def test_fx_explicit_dated(self):
        x=convert('100','USD','CNY','7','2026-10-10','2026-10-11','https://www.safe.gov.cn')
        self.assertEqual(x['target_amount'],'700.00')

if __name__=='__main__':unittest.main()
