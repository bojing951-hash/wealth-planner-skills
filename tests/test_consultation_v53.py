"""v5.3 professional-plan offline contract checks; NOT a real blinded host-model evaluation."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/personal-finance-planner'


def script_import(name, file):
    spec=importlib.util.spec_from_file_location(name,SKILL/'scripts'/file)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


quality=script_import('professional_quality','plan_quality.py')
math=script_import('professional_math','consultation_math.py')


class ProfessionalConsultationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((SKILL/'examples/v5.3-consultation-shenzhen-SYNTHETIC.json').read_text())
        cls.weak=json.loads((SKILL/'examples/v5.3-generic-failure-SYNTHETIC.json').read_text())

    def good(self):
        return copy.deepcopy(self.data)

    def bad(self, modified, phrase):
        result=quality.audit(modified)
        self.assertFalse(result['ok'],result)
        self.assertTrue(any(phrase in e.lower() for e in result['errors']),result['errors'])

    def test_valid_professional_plan_example_passes_structural_audit(self):
        r=quality.audit(self.good())
        self.assertTrue(r['ok'],r['errors'])
        self.assertIn('LIMITED_ARITHMETIC',r['scope'])
        self.assertIn('NOT_LEGAL_TAX_EXPERT_CERTIFICATION',r['scope'])

    def test_generic_non_skill_response_is_rejected(self):
        r=quality.audit(self.weak)
        self.assertFalse(r['ok'])
        self.assertGreater(len(r['errors']),5)

    def test_bad_cash_surplus_detected(self):
        d=self.good();d['financial_snapshot']['monthly_surplus']='19000.00'
        self.bad(d,'does not reconcile')

    def test_bad_emergency_reserve_detected(self):
        d=self.good();d['financial_snapshot']['emergency_reserve_target']='20000.00'
        self.bad(d,'reserve target')

    def test_spending_emergency_reserve_as_investable_detected(self):
        d=self.good();d['financial_snapshot']['eligible_long_term_initial']='100000.00'
        self.bad(d,'exceeds unreserved')

    def test_goal_contribution_gap_detected(self):
        d=self.good();d['goal_feasibility'][0]['monthly_gap']='1.00'
        self.bad(d,'gap calculation')

    def test_unlabeled_assumptions_rejected(self):
        d=self.good();d['data_quality']['assumed']=[]
        self.bad(d,'hypothetical inputs')

    def test_model_returns_not_guaranteed(self):
        d=self.good();d['goal_feasibility'][0]['assumption_status']='PROVEN_SUCCESS_PROBABILITY'
        self.bad(d,'conditional assumption')

    def test_single_option_rejected(self):
        d=self.good();d['options']=d['options'][:1]
        self.bad(d,'defensible alternatives')

    def test_ungrounded_overbudget_plan_rejected(self):
        d=self.good();d['options'][1]['feasibility']='FEASIBLE'
        d['options'][1].pop('funding_change_source')
        self.bad(d,'exceeds surplus')

    def test_unsupported_funding_gap_rejected(self):
        d=self.good();d['options'][1]['extra_monthly_cash_needed']='10'
        self.bad(d,'funding gap insufficient')

    def test_missing_root_cause_rejected(self):
        d=self.good();d['diagnoses'][0]['root_cause_or_hypothesis']=''
        self.bad(d,'root_cause_or_hypothesis')

    def test_unlinked_critical_issue_rejected(self):
        d=self.good();d['actions']=[a for a in d['actions'] if a['issue_id']!='I-01']
        self.bad(d,'critical/high issue')

    def test_missing_human_action_check_rejected(self):
        d=self.good();d['actions'][0]['success_measure']=''
        self.bad(d,'success_measure')

    def test_cannot_authorize_trades_through_consultation(self):
        d=self.good();d['recommendation']['is_authorized_to_execute']=True
        self.bad(d,'cannot confer permission')

    def test_no_implicit_background_monitor(self):
        d=self.good();d['review']['has_background_monitoring']=True
        self.bad(d,'no implicit')

    def test_client_who_has_no_major_issue_must_explain_that(self):
        d=self.good();d['diagnoses']=[]
        self.bad(d,'no_material_issue_reason')

    def test_numerical_example_agrees_with_reserve_first_math(self):
        inp={
            'currency':'CNY','monthly_net_received':'20000','monthly_essential':'8000',
            'monthly_discretionary':'3000','monthly_other_obligations':'0',
            'owned_unrestricted_cash':'100000','reserve_months':6,'near_term_goals_cash':'0',
            'goal_target':'1000000','goal_months':60,'annual_net_return_assumed':'0.05',
            'is_real_user_data':False,
        }
        r=math.calculate(inp)
        self.assertEqual(r['monthly_conditional_surplus'],'9000.00')
        self.assertEqual(r['long_term_start_after_reserved_cash'],'52000.00')
        self.assertEqual(r['goal_math']['monthly_contribution_required'],'13767.61')
        self.assertEqual(r['goal_math']['monthly_gap'],'4767.61')
        self.assertEqual(r['goal_math']['future_value'],'676690.28')
        self.assertEqual(r['goal_math']['mathematical_status'],'FIXED_HYPOTHETICAL_RETURN_NOT_A_FORECAST')

    def test_zero_return_and_reserved_near_term_cash(self):
        inp={
            'currency':'USD','monthly_net_received':'10000','monthly_essential':'4000',
            'monthly_discretionary':'2000','monthly_other_obligations':'1000',
            'owned_unrestricted_cash':'30000','reserve_months':6,'near_term_goals_cash':'9000',
            'goal_target':'50000','goal_months':12,'annual_net_return_assumed':'0',
            'is_real_user_data':False,
        }
        r=math.calculate(inp)
        self.assertEqual(r['long_term_start_after_reserved_cash'],'0.00')
        self.assertEqual(r['monthly_conditional_surplus'],'3000.00')
        self.assertEqual(r['goal_math']['future_value'],'33000.00')
        self.assertEqual(r['goal_math']['monthly_contribution_required'],'4416.67')

    def test_real_data_with_unknown_taxes_is_blocked(self):
        inp={
            'currency':'USD','monthly_net_received':'10000','monthly_essential':'4000',
            'monthly_discretionary':'2000','monthly_other_obligations':'1000',
            'owned_unrestricted_cash':'30000','reserve_months':6,'near_term_goals_cash':'0',
            'goal_target':'50000','goal_months':12,'annual_net_return_assumed':'0',
            'is_real_user_data':True, 'tax_status':'unknown',
        }
        with self.assertRaisesRegex(ValueError,'tax_status'):
            math.calculate(inp)

    def test_nonfinite_input_rejected(self):
        with self.assertRaises(ValueError):
            math.number('NaN','money')

    def test_currency_must_be_explicit(self):
        d={
            'currency':'CNY/USD','monthly_net_received':'20000','monthly_essential':'8000',
            'monthly_discretionary':'3000','monthly_other_obligations':'0',
            'owned_unrestricted_cash':'100000','reserve_months':6,'near_term_goals_cash':'0',
            'goal_target':'1000000','goal_months':60,'annual_net_return_assumed':'0.05',
        }
        with self.assertRaisesRegex(ValueError,'currency'):
            math.calculate(d)

    def test_optional_math_cli_from_synthetic_input(self):
        inp=SKILL/'examples/v5.3-shenzhen-math-input-SYNTHETIC.json'
        p=subprocess.run([sys.executable,str(SKILL/'scripts/consultation_math.py'),'--input',str(inp)],cwd='/tmp',capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout)
        self.assertEqual(r['goal_math']['monthly_gap'],'4767.61')
        self.assertEqual(r['long_term_start_after_reserved_cash'],'52000.00')

    def test_cli_runs_outside_project_root_without_private_data_write(self):
        s=SKILL/'examples/v5.3-consultation-shenzhen-SYNTHETIC.json'
        p=subprocess.run([sys.executable,str(SKILL/'scripts/plan_quality.py'),'--input',str(s),'--json'],cwd='/tmp',capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertTrue(json.loads(p.stdout)['ok'])

    def test_production_skill_routes_full_plan_into_consultation(self):
        t=(SKILL/'SKILL.md').read_text()
        for k in ('Professional consultation mode','workflows/professional-consultation.md','workflows/diagnosis-prioritization.md','30/90/365-day'):
            self.assertIn(k,t)
        self.assertIn('The HOST Agent performs research',t)
        self.assertIn('Memory is OFF by default',t)

    def test_benchmark_is_marked_not_executed(self):
        t=(ROOT/'tests/skill_vs_baseline/README.md').read_text()
        self.assertIn('NOT_RUN',t)
        self.assertIn('same',t.lower())
        self.assertIn('not a substitute',t.lower())


if __name__=='__main__':unittest.main()
