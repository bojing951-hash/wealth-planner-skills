"""v5.4 offline value-of-planning tests — illustrative, NOT real host or causality tests."""
from __future__ import annotations
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/personal-finance-planner'
SCRIPTS=SKILL/'scripts'
sys.path.insert(0,str(SCRIPTS))
import value_math  # noqa: E402
import value_quality  # noqa: E402


def fixture(name:str)->dict:
    return json.loads((SKILL/'examples'/name).read_text(encoding='utf8'))


class ValueProjectionTests(unittest.TestCase):
    def setUp(self):
        self.p=fixture('v5.4-spending-behavior-SYNTHETIC.json')

    def test_project_discloses_not_observed(self):
        r=value_math.project(self.p)
        self.assertEqual(r['status'],'HYPOTHETICAL_SCENARIO_NOT_OBSERVED_SAVINGS_OR_CAUSAL_EFFECT')
        self.assertEqual(r['currency'],'CNY')

    def test_twenty_year_principal_vs_return(self):
        z=value_math.project(self.p)['checkpoints'][-1]
        self.assertEqual(z['delta_new_unconsumed_cashflow_nominal'],'720000.00')
        self.assertTrue(Decimal('497000')<Decimal(z['delta_modeled_growth_and_allocation_nominal'])<Decimal('498000'))
        self.assertTrue(Decimal('1217000')<Decimal(z['delta_total_nominal'])<Decimal('1218000'))

    def test_zero_return_pure_principal(self):
        self.p['assumptions']['annual_investment_return']='0'
        z=value_math.project(self.p)['checkpoints'][-1]
        self.assertEqual(z['delta_total_nominal'],'720000.00')
        self.assertEqual(z['delta_modeled_growth_and_allocation_nominal'],'0.00')

    def test_6_month_horizon(self):
        self.p['months']=6
        z=value_math.project(self.p)['checkpoints'][-1]
        self.assertEqual(z['months'],6)
        self.assertEqual(z['delta_new_unconsumed_cashflow_nominal'],'18000.00')

    def test_price_level_real_less_than_nominal(self):
        z=value_math.project(self.p)['checkpoints'][-1]
        self.assertLess(Decimal(z['delta_total_in_today_purchasing_power']),Decimal(z['delta_total_nominal']))

    def test_internal_reallocation_is_not_new_savings(self):
        p=fixture('v5.4-reallocate-not-new-savings-SYNTHETIC.json')
        r=value_math.project(p)
        self.assertEqual(r['monthly_additional_retained_cash'],'0.00')
        self.assertEqual(r['checkpoints'][-1]['delta_new_unconsumed_cashflow_nominal'],'0.00')
        self.assertTrue(any('REALLOCATION_NOT_NEW_SAVINGS' in w for w in r['warnings']))

    def test_reallocation_at_equal_invest_and_cash_returns_is_neutral(self):
        p=fixture('v5.4-reallocate-not-new-savings-SYNTHETIC.json')
        p['assumptions']['annual_cash_return']='0.05'
        self.assertEqual(value_math.project(p)['checkpoints'][-1]['delta_total_nominal'],'0.00')

    def test_identical_behaviors_no_extra_wealth(self):
        self.p['proposal']=copy.deepcopy(self.p['status_quo'])
        r=value_math.project(self.p)
        self.assertEqual(r['checkpoints'][-1]['delta_total_nominal'],'0.00')

    def test_cost_deducted_once(self):
        self.p['initial_uncommitted_cash']='1000'
        self.p['one_time_cost_proposed']='1000'
        self.p['months']=12
        r=value_math.project(self.p)
        self.assertEqual(r['checkpoints'][-1]['delta_new_unconsumed_cashflow_nominal'],'35000.00')

    def test_insufficient_nonreserved_cash_reject_cost(self):
        self.p['one_time_cost_proposed']='500'
        with self.assertRaisesRegex(ValueError,'uncommitted_cash'):
            value_math.project(self.p)

    def test_reserve_shortfall_conditions_recommendation(self):
        self.p['protected_reserve_current']='10000'
        r=value_math.project(self.p)
        self.assertEqual(r['long_term_policy_gate'],'CONDITIONAL_RESERVE_GAP')
        self.assertTrue(any('RESERVE_UNDERFUNDED' in w for w in r['warnings']))

    def test_costs_are_not_money_creation(self):
        self.p['initial_uncommitted_cash']='1000';self.p['one_time_cost_proposed']='1000'
        self.p['proposal']=copy.deepcopy(self.p['status_quo'])
        z=value_math.project(self.p)['checkpoints'][-1]
        self.assertEqual(z['delta_new_unconsumed_cashflow_nominal'],'-1000.00')
        self.assertEqual(z['delta_total_nominal'],'-1000.00')

    def test_pf_simulated_income_basis_rejected(self):
        self.p['income_basis']='PF_SIMULATED_PNL'
        with self.assertRaisesRegex(ValueError,'income_basis'):
            value_math.project(self.p)

    def test_unverified_tax_income_warned(self):
        self.p['income_basis']='OWNED_BANK_RECEIVED_NET_TAX_UNVERIFIED'
        self.p['input_status']='USER_REPORTED'
        result=value_math.project(self.p)
        self.assertTrue(any('TAX_UNVERIFIED' in w for w in result['warnings']))

    def test_real_user_not_relabelled_hypothetical_income(self):
        self.p['input_status']='USER_REPORTED'
        with self.assertRaisesRegex(ValueError,'cannot use hypothetical'):
            value_math.project(self.p)

    def test_negative_surplus_rejected(self):
        self.p['proposal']['essential_spend']='20001'
        with self.assertRaisesRegex(ValueError,'negative surplus'):
            value_math.project(self.p)

    def test_investing_more_than_free_cash_rejected(self):
        self.p['proposal']['investment_contribution']='8001'
        with self.assertRaisesRegex(ValueError,'exceeds own net'):
            value_math.project(self.p)

    def test_no_conflation_income_gain_with_investment(self):
        self.p['proposal']['net_income']='23000'
        self.p['proposal']['discretionary_spend']='7000'
        r=value_math.project(self.p)
        self.assertEqual(r['monthly_additional_retained_cash'],'3000.00')
        self.assertTrue(any('INCOME_UPLIFT_UNVERIFIED' in w for w in r['warnings']))

    def test_reject_non_decimal_or_nan(self):
        for v in ('NaN','Infinity','-1',1.2,True):
            p=copy.deepcopy(self.p)
            p['proposal']['net_income']=v
            with self.assertRaises(ValueError,msg=f'accepted {v}'):
                value_math.project(p)

    def test_reject_rate_upper_and_lower(self):
        for v in ('-1','1.1','nan'):
            p=copy.deepcopy(self.p)
            p['assumptions']['annual_cash_return']=v
            with self.assertRaises(ValueError):value_math.project(p)

    def test_reject_currency_and_horizon(self):
        self.p['currency']='CNY/USD'
        with self.assertRaises(ValueError):value_math.project(self.p)
        self.p['currency']='CNY';self.p['months']=601
        with self.assertRaises(ValueError):value_math.project(self.p)

    def test_return_path_same_assumptions_not_profile_data(self):
        self.p['assumptions']['status']='OBSERVED'
        with self.assertRaises(ValueError):value_math.project(self.p)

    def test_scale_forecast_not_reward_inducement(self):
        self.p['proposal']['discretionary_spend']='7000'
        self.p['proposal']['investment_contribution']='5000'
        r=value_math.project(self.p)
        self.assertEqual(r['checkpoints'][-1]['delta_total_nominal'],'0.00')


class ValueReviewTests(unittest.TestCase):
    def setUp(self):self.p=fixture('v5.4-followup-SYNTHETIC.json')

    def test_changed_monthly_surplus_not_caused(self):
        x=value_math.review(self.p)
        self.assertEqual(x['monthly_deltas']['surplus'],'3000.00')
        self.assertEqual(x['owned_liquid_assets_change'],'12000.00')
        self.assertEqual(x['claim_of_causal_effect'],'NOT_ESTABLISHED')

    def test_review_rejects_equal_or_reversed_dates(self):
        self.p['current']['as_of']=self.p['previous']['as_of']
        with self.assertRaises(ValueError):value_math.review(self.p)

    def test_review_rejects_fake_verified(self):
        self.p['current']['source_status']='VERIFIED'
        with self.assertRaises(ValueError):value_math.review(self.p)

    def test_document_requires_reference(self):
        self.p['current']['source_status']='HOST_REVIEWED_DOCUMENT'
        with self.assertRaises(ValueError):value_math.review(self.p)
        self.p['current']['source_ref']='PRIVATE_SOURCE_REF'
        self.assertEqual(value_math.review(self.p)['current_source_status'],'HOST_REVIEWED_DOCUMENT')

    def test_documented_execution_requires_evidence(self):
        self.p['action']['status']='DOCUMENTED_EXECUTED'
        with self.assertRaises(ValueError):value_math.review(self.p)
        self.p['action']['evidence_ref']='private-monthly-transfer'
        self.assertEqual(value_math.review(self.p)['action_status'],'DOCUMENTED_EXECUTED')

    def test_review_action_status_stays_proposed(self):
        self.p['action']['status']='PROPOSED'
        r=value_math.review(self.p)
        self.assertEqual(r['action_status'],'PROPOSED')
        self.assertIn('NOT_CAUSAL',r['status'])


class ValueQualityTests(unittest.TestCase):
    def setUp(self): self.p=fixture('v5.4-value-card-SYNTHETIC.json')

    def test_good_value_card_passes(self):self.assertTrue(value_quality.audit(self.p)['ok'])

    def test_bad_double_causal_and_math_fails(self):
        p=fixture('v5.4-value-card-INVALID-SYNTHETIC.json')
        a=value_quality.audit(p)
        self.assertFalse(a['ok'])
        self.assertGreaterEqual(len(a['errors']),2)

    def test_no_change_is_legitimate(self):
        self.p['value_cards']=[]
        self.p['no_change_reason']='在这些可用数据和限制下，当前计划已满足目标，不存在可以正当推荐的新开支削减或投资配置动作。'
        self.p['no_change_evidence']='家庭净现金流已经稳定且应急储备足够，目标要求与期限暂时匹配。'
        self.assertTrue(value_quality.audit(self.p)['ok'])

    def test_no_change_without_evidence_fails(self):
        self.p['value_cards']=[]
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_non_specific_generic_fails(self):
        self.p['value_cards'][0]['mechanism']='save more'
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_plan_cannot_claim_completed(self):
        self.p['claim_of_realized_wealth_created']=True
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_memory_write_cannot_be_claimed(self):
        self.p['memory_written']=True
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_double_counted_principal_fails(self):
        self.p['value_cards'][0]['value_bridge']['delta_new_retained_cash']='1440000.00'
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_fake_measured_status_rejected(self):
        self.p['value_cards'][0]['observed_outcome']={'status':'REALIZED_GAIN'}
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_actions_without_wellbeing_fails(self):
        self.p['value_cards'][0]['wellbeing_tradeoff']=''
        self.assertFalse(value_quality.audit(self.p)['ok'])

    def test_skill_hard_routes_value_protocol(self):
        skill=(SKILL/'SKILL.md').read_text()
        for t in ('Value and behavior protocol','workflows/value-and-behavior.md','new retained principal','Memory remains'):
            self.assertIn(t,skill)
        self.assertIn('The HOST Agent performs research',skill)

    def test_baseline_10_and_12_unchanged(self):
        contract=json.loads((ROOT/'docs/architecture_contract.json').read_text())
        self.assertEqual(len(contract['ten_domains']),10)
        self.assertEqual(len(contract['twelve_states']),12)
        self.assertEqual(contract['baseline_sha256'],'552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb')

    def test_cli_from_external_working_dir(self):
        run=subprocess.run([sys.executable,str(SCRIPTS/'value_math.py'),'project','--input',str(SKILL/'examples/v5.4-spending-behavior-SYNTHETIC.json')],cwd='/tmp',capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn('HYPOTHETICAL_SCENARIO',run.stdout)

    def test_model_schema_optional(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('jsonschema is optional in host; math semantic validation still applies')
        for example,schema in [('v5.4-spending-behavior-SYNTHETIC.json','value-project-v5.4.schema.json'),
                                ('v5.4-reallocate-not-new-savings-SYNTHETIC.json','value-project-v5.4.schema.json'),
                                ('v5.4-followup-SYNTHETIC.json','value-review-v5.4.schema.json'),
                                ('v5.4-value-card-SYNTHETIC.json','value-card-v5.4.schema.json')]:
            payload=fixture(example); schema_json=json.loads((SKILL/'schemas'/schema).read_text())
            Draft202012Validator.check_schema(schema_json)
            Draft202012Validator(schema_json).validate(payload)

    def test_no_real_e2e_claim(self):
        m=(ROOT/'tests/skill_vs_baseline/MEASURE_VALUE_v5.4.md').read_text()
        self.assertIn('NOT_RUN',m)
        self.assertIn('Skill OFF',m)
        self.assertIn('Skill ON',m)


if __name__=='__main__':unittest.main()
