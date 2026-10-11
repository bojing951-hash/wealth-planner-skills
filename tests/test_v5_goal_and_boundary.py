"""Additional mathematical and trust-boundary tests."""
import copy
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]/'skills'/'personal-finance-planner'
sys.path.insert(0,str(ROOT/'lib'))
from wealth_core.goal_math import required_monthly_contribution, fi_screen, goal_math
from wealth_core.simulation import simulate
from wealth_core.portfolio import portfolio_diagnostics
from wealth_core.integrated import build_integrated
from wealth_core.dynamic import compare


def load(name):return json.loads((ROOT/'examples'/name).read_text())

class GoalMathTests(unittest.TestCase):
    def test_zero_return_goal_gap(self):
        self.assertEqual(required_monthly_contribution(100000,1000000,12,0),75000.0)

    def test_initial_asset_sufficient_return_means_zero_contribution(self):
        self.assertEqual(required_monthly_contribution(1000000,1000000,120,.05),0)

    def test_one_year_positive_return_requires_less_than_zero_return(self):
        self.assertLess(required_monthly_contribution(100000,1000000,12,.05),75000)

    def test_withdrawal_screen(self):
        x=fi_screen(20000,.04)
        self.assertAlmostEqual(x['fi_reference_capital'],6000000)

    def test_ideal_cashflow_gaps_included(self):
        p=load('v5-shenzhen.json');c=load('v5-scenarios-cny.json')
        x=goal_math(p,c)
        self.assertEqual(len(x['rows']),3)
        self.assertTrue(all(q['status'].startswith('IDEAL_') for q in x['rows']))

    def test_goal_math_does_not_claim_investable_net(self):
        p=load('v5-shenzhen.json');c=load('v5-scenarios-cny.json')
        r=build_integrated(p,assumptions=c)
        self.assertIsNone(r['financial_snapshot']['currency_buckets']['CNY']['monthly_investable_final'])

class MoreBoundaries(unittest.TestCase):
    def test_invalid_psd_3_assets(self):
        p={'assets':[{'name':'a','weight':.3,'assumed_nominal_return':.05},
                     {'name':'b','weight':.3,'assumed_nominal_return':.05},
                     {'name':'c','weight':.4,'assumed_nominal_return':.05}],
           'annual_covariance':[[1,0,0],[0,1,2],[0,2,1]]}
        with self.assertRaises(ValueError):portfolio_diagnostics(p)

    def test_negative_inflation_allowed_but_nominal_real_direction_reverses(self):
        p=load('v5-shenzhen.json');cfg=load('v5-scenarios-cny.json');cfg['scenarios']={'deflation':copy.deepcopy(cfg['scenarios']['base'])}
        cfg['scenarios']['deflation']['annual_inflation']=-.02
        r=simulate(p,cfg)['scenarios']['deflation']
        self.assertGreater(r['final_real_today_median'],r['final_nominal_median'])

    def test_fake_retrieval_receipt_never_legally_certified(self):
        p=load('v5-new-york.json')
        manifest=load('v04-capabilities-codex-EXAMPLE.json')
        r=build_integrated(p,manifest)
        ready=[a for a in r['requested_host_actions'] if a['id']=='law:US:2026' and a['state']=='READY_FOR_HOST_EXECUTION']
        self.assertEqual(len(ready),1)
        bogus_test_receipt=[{'action_id':'law:US:2026','status':'completed',
                            'source_url':'https://www.irs.gov/','retrieved_on':'2026-10-10',
                            'content_sha256':'a'*64,'tax_year':2026}]
        done=build_integrated(p,manifest,bogus_test_receipt)
        states={x['state'] for x in done['host_action_receipts']['items']}
        self.assertIn('RETRIEVED_PRIMARY_DOMAIN_PENDING_LEGAL_INTERPRETATION',states)
        self.assertFalse(done['legal_tax_triage']['law_verification_complete'])
        self.assertFalse(done['assumption_checks']['research_substantively_legally_verified'])

    def test_absent_permissions_deny_receipts(self):
        p=load('v5-new-york.json')
        invalid_receipt=[{'action_id':'law:US:2026','status':'completed','source_url':'https://www.irs.gov/',
                          'retrieved_on':'2026-10-10','content_sha256':'a'*64,'tax_year':2026}]
        with self.assertRaises(ValueError):build_integrated(p,receipts=invalid_receipt)

    def test_host_declared_ready_not_true_execution(self):
        p=load('v5-new-york.json');m=load('v04-capabilities-codex-EXAMPLE.json')
        r=build_integrated(p,m)
        self.assertEqual(r['host_action_receipts']['receipt_count'],0)
        self.assertGreater(r['host_action_queue']['ready_count'],0)

    def test_expense_change_triggers_review(self):
        p=load('v5-shenzhen.json');old=build_integrated(p)
        p['expenses'][0]['monthly_amount']='6500'
        cur=build_integrated(p)
        self.assertIn('MATERIAL_SURPLUS_CHANGE',[x['type'] for x in compare(old,cur)['events']])

if __name__=='__main__':unittest.main()
