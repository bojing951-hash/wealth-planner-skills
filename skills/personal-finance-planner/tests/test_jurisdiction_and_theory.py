import json
from datetime import date
from pathlib import Path
import sys
import unittest

SK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SK / 'scripts'))
from jurisdiction_router import route_case, read_json, scan_sources
from theory_adjudicator import reconcile_case
from finance_workflow import build_report, as_markdown


def example(name):
    return read_json(SK / 'examples' / name)


class TestJurisdictionRouting(unittest.TestCase):
    def test_cn_hk_pf_multi_links_without_tax_free_claim(self):
        result = route_case(example('cn-hk-pf-crossborder.json'))
        countries = {j['jurisdiction'] for j in result['jurisdictions']}
        self.assertTrue({'CN', 'HK', 'US'}.issubset(countries))
        self.assertEqual(result['status'], 'NEEDS_LEGAL_TAX_REVIEW')
        self.assertTrue(any('不能给出确定税后可投资金额' in x for x in result['blocking_facts']))
        self.assertTrue(any(f['id'] == 'BANK_NOT_SOURCE' for f in result['issues']))
        self.assertEqual(result['income_events'][0]['bank_received'], True)
        self.assertNotIn('income_tax_rate', result)

    def test_missing_eu_member_blocks_eu_one_tax(self):
        result = route_case(example('europe-unknown-country.json'))
        self.assertEqual(result['status'], 'NEEDS_LEGAL_TAX_REVIEW')
        self.assertTrue(any('欧盟' in x for x in result['blocking_facts']))
        self.assertIn('EU', {x['jurisdiction'] for x in result['jurisdictions']})

    def test_fr_specific_can_be_routed_and_eu_coordination_retained(self):
        result = route_case(example('france-domestic.json'))
        self.assertTrue({'FR','EU'}.issubset({x['jurisdiction'] for x in result['jurisdictions']}))
        self.assertNotIn('欧盟不是', ''.join(result['blocking_facts']))

    def test_us_citizen_abroad_keeps_us_jurisdiction(self):
        result=route_case(example('us-citizen-thailand.json'))
        codes={x['jurisdiction']:x for x in result['jurisdictions']}
        self.assertIn('US',codes)
        self.assertIn('TH',codes)
        self.assertIn('self_declared_us_person_global_reporting_check',codes['US']['roles'])

    def test_tax_unknown_blocks_definitive_aftertax(self):
        obj=example('us-citizen-thailand.json')
        obj['income_streams'][0]['tax_status']='unknown'
        self.assertTrue(any('税务' in x for x in route_case(obj)['blocking_facts']))

    def test_pf_simulated_profits_not_accounted_as_personal_cash(self):
        obj=example('cn-hk-pf-crossborder.json')
        obj['income_streams'][0]['kind']='prop_firm_simulated_profit'
        obj['income_streams'][0]['bank_received']=False
        result=route_case(obj)
        self.assertTrue(any('模拟账户' in x for x in result['blocking_facts']))
        self.assertTrue(any('尚未银行实际到账' in x for x in result['blocking_facts']))

    def test_absent_country_pack_fail_closed(self):
        obj=example('france-domestic.json')
        obj['person']['living_country']='JP'
        result=route_case(obj)
        self.assertIn('JP',{x['jurisdiction'] for x in result['jurisdictions']})
        self.assertTrue(any('JP:知识库无已核查' in x for x in result['blocking_facts']))

    def test_planned_move_does_not_change_current_status(self):
        obj=example('cn-hk-pf-crossborder.json')
        obj['planned_moves']=[{'country':'TH','year':2027}]
        result=route_case(obj)
        self.assertEqual(result['planned_moves'][0]['year'],2027)
        self.assertIn('future_move_not_current_tax_residency',
                      next(x['roles'] for x in result['jurisdictions'] if x['jurisdiction']=='TH'))

    def test_source_registry_has_authority_dates_and_staleness(self):
        src=scan_sources(['CN-IIT-2018'], '2026-10-11')[0]
        self.assertEqual(src['state'],'REFERENCE_ONLY_RECHECK_ON_USE')
        src=scan_sources(['CN-IIT-2018'], '2027-10-11')[0]
        self.assertEqual(src['state'],'STALE_RECHECK_REQUIRED')
        with self.assertRaises(ValueError):
            scan_sources(['CN-IIT-2018'], 'bogus-date')

    def test_dated_tax_year_mismatch_and_earlier_earned_year(self):
        obj=example('france-domestic.json')
        obj['tax_year']=2025
        result=route_case(obj)
        self.assertTrue(any(x['id']=='YEAR_MISMATCH' for x in result['issues']))
        self.assertTrue(any('晚于当前申报年度' in x for x in result['missing_facts']))


class TestEvidenceAdjudication(unittest.TestCase):
    def test_theory_cards_use_classification_and_no_truth_vote(self):
        x=reconcile_case(example('cn-hk-pf-crossborder.json'))
        self.assertIn('No popularity voting',x['research_policy'])
        self.assertGreaterEqual(len(x['principles']),10)
        self.assertTrue(all(x['evidence_kind'] for x in x['principles']))
        self.assertGreaterEqual(len(x['comparison']),7)

    def test_no_active_edge_bogle_as_research_baseline(self):
        x=reconcile_case(example('france-domestic.json'))
        r=next(c for c in x['comparison'] if set(c['pair'])=={'GRAHAM','BOGLE'})
        self.assertEqual(r['decision_state'],'INDEX_AS_BASELINE_ACTIVE_EDGE_UNVERIFIED')

    def test_verified_edge_still_not_guaranteed(self):
        obj=example('france-domestic.json')
        obj['targets']['active_edge_evidence']='independently_verified_after_costs'
        x=reconcile_case(obj)
        r=next(c for c in x['comparison'] if set(c['pair'])=={'GRAHAM','BOGLE'})
        self.assertEqual(r['decision_state'],'COMPARE_INDEX_VERSUS_RESEARCH_PROCESS')
        self.assertIn('不能推导未来必胜',r['resolution'])

    def test_short_goal_alternatives_put_liquidity_first(self):
        obj=example('france-domestic.json')
        obj['targets']['time_horizon_years']=2
        x=reconcile_case(obj)
        r=next(c for c in x['comparison'] if set(c['pair'])=={'ALM','BOGLE'})
        self.assertEqual(r['decision_state'],'LIQUIDITY_FIRST_FOR_THIS_GOAL')

    def test_integration_md_contains_controls_and_provenance(self):
        report=build_report(example('cn-hk-pf-crossborder.json'))
        txt=as_markdown(report)
        self.assertIn('NEEDS_LEGAL_TAX_REVIEW',txt)
        self.assertIn('GRAHAM × BOGLE',txt)
        self.assertIn('https://www.ird.gov.hk',txt)
        self.assertIn('2026-10-11',txt)


class TestIntegratedCashflowGating(unittest.TestCase):
    def test_tax_unknown_blocks_finance_engine_by_default(self):
        case = example('cn-hk-pf-crossborder.json')
        monetary = example('salary-20000.json')
        report = build_report(case, monetary)
        self.assertEqual(report['cashflow_calculation']['status'], 'BLOCKED_UNRESOLVED_TAX')
        self.assertNotIn('report', report['cashflow_calculation'])

    def test_explicit_hypothetical_only_runs_labeled_math(self):
        case = example('cn-hk-pf-crossborder.json')
        monetary = example('salary-20000.json')
        report = build_report(case, monetary, allow_hypothetical=True)
        self.assertEqual(report['cashflow_calculation']['status'], 'ILLUSTRATIVE_NOT_TAX_VERIFIED')
        self.assertEqual(report['cashflow_calculation']['report']['diagnosis']['monthly_current_cash_surplus'], 8000.0)

    def test_long_horizon_not_represented_as_probability(self):
        case=example('cn-hk-pf-crossborder.json')
        monetary=example('salary-20000.json')
        macro=example('macro-snapshot-sourced-dated-example.json')
        report=build_report(case,monetary,macro,allow_hypothetical=True)
        self.assertEqual(report['long_horizon_calculation']['status'],'ILLUSTRATIVE_NOT_PROBABILITY')
        self.assertIn('10',report['long_horizon_calculation']['report']['results']['base'])


if __name__=='__main__':
    unittest.main()
