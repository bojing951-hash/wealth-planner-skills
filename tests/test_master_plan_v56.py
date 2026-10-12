"""Regression tests for v5.6 skill-first Personal Wealth Master Plan.

Synthetic test artifacts only. Passing does not certify legal, investment or host E2E suitability.
"""
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
SCRIPT=SKILL/'scripts/master_plan_quality.py'
EX=SKILL/'examples'

spec=importlib.util.spec_from_file_location('master_plan_quality',SCRIPT)
module=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def case(name):
    return json.loads((EX/name).read_text(encoding='utf-8'))


class MasterPlanTests(unittest.TestCase):
    def setUp(self):
        self.salary=case('v5.6-salary-shenzhen-SYNTHETIC.json')
        self.trader=case('v5.6-high-income-trader-SYNTHETIC.json')

    def reject(self,data,part):
        errors=module.validate(data)
        self.assertTrue(errors, 'expected rejection')
        self.assertTrue(any(part in e for e in errors), f"expected {part!r}; got {errors}")

    def test_salary_valid(self):
        self.assertEqual(module.validate(self.salary), [])

    def test_salary_nominal_target_can_be_met_without_assumed_investment_return(self):
        # Professional planning may legitimately recommend maintain + monitor.
        # The cashflow assumption is HYPOTHETICAL and future market/earnings unknown.
        self.assertEqual(100000 + 9000 * 120, 1180000)
        self.assertGreaterEqual(100000 + 9000 * 120, int(self.salary['goals'][0]['target_amount']))

    def test_crossborder_conditional_valid(self):
        self.assertEqual(module.validate(self.trader), [])
        self.assertIsNone(self.trader['cash_policy']['investable_amount'])

    def test_invalid_double_count_fixture_rejected(self):
        p=case('v5.6-invalid-double-count-SYNTHETIC.json')
        e=module.validate(p)
        self.assertTrue(any('earmarks' in i for i in e))
        self.assertTrue(any('unverified tax' in i for i in e))
        self.assertTrue(any('status-quo' in i for i in e))
        self.assertTrue(any('documented execution' in i for i in e))

    def test_nonowned_pf_cannot_enter_pool(self):
        x=copy.deepcopy(self.trader)
        x['pools'][0]['allocations']=[{'asset_id':'pf_simulated','currency':'USD','amount':'100'}]
        self.reject(x, 'cannot assign nonowned asset')

    def test_simulated_pf_cannot_be_owned(self):
        x=copy.deepcopy(self.trader)
        x['balance_sheet']['assets'][2]['ownership']='OWNED'
        self.reject(x, 'PF simulated funds cannot be owned')

    def test_broker_pnl_cannot_be_asset_line_item(self):
        x=copy.deepcopy(self.trader)
        x['balance_sheet']['assets'][1]['kind']='UNREALIZED_PNL'
        self.reject(x, 'net asset, not separately recorded P&L')

    def test_restricted_retirement_does_not_fund_liquidity(self):
        x=copy.deepcopy(self.salary)
        x['balance_sheet']['assets'][0]['ownership']='RESTRICTED_BENEFICIAL'
        self.reject(x, 'cannot fund immediately accessible')

    def test_pool_wrong_currency(self):
        x=copy.deepcopy(self.salary)
        x['pools'][0]['allocations'][0]['currency']='USD'
        self.reject(x, 'currency mismatch')

    def test_pool_cannot_exceed_owned_amount(self):
        x=copy.deepcopy(self.salary)
        x['pools'][1]['allocations'][0]['amount']='52000.01'
        self.reject(x, 'earmarks')

    def test_unknown_tax_blocks_exact_available_to_invest(self):
        x=copy.deepcopy(self.salary)
        x['cash_policy']['investable_amount']='9000'
        self.reject(x, 'unverified tax')

    def test_assumed_tax_not_verified_liability(self):
        x=copy.deepcopy(self.salary)
        x['cash_policy']['tax_reserve_status']='VERIFIED_OBLIGATION'
        self.reject(x, 'tax obligation cannot be verified')

    def test_missing_status_quo_rejected(self):
        x=copy.deepcopy(self.salary)
        x['options'][0]['type']='ALTERNATIVE'
        self.reject(x, 'status-quo')

    def test_action_needs_policy_link(self):
        x=copy.deepcopy(self.salary)
        x['actions'][0]['policy_id']='GHOST'
        self.reject(x, 'unlinked policy_id')

    def test_unproved_execution_rejected(self):
        x=copy.deepcopy(self.salary)
        x['actions'][0]['status']='DOCUMENTED_EXECUTED'
        self.reject(x, 'documented execution requires evidence')

    def test_missing_30_90_365_rejected(self):
        x=copy.deepcopy(self.salary)
        x['actions'][0]['within_days']=90
        self.reject(x,'30/90/365')

    def test_no_autonomous_financial_actions(self):
        x=copy.deepcopy(self.salary)
        x['permissions']['autonomous_financial_actions']=True
        self.reject(x,'L3 autonomous')

    def test_nonfinite_negative_money_rejected(self):
        for value in ('NaN','-1','Infinity'):
            with self.subTest(value=value):
                x=copy.deepcopy(self.salary)
                x['balance_sheet']['assets'][0]['amount']=value
                self.reject(x,'amount must be finite and nonnegative' if value in ('NaN','Infinity') else 'finite and nonnegative')

    def test_duplicate_asset_id(self):
        x=copy.deepcopy(self.salary)
        x['balance_sheet']['assets'].append(copy.deepcopy(x['balance_sheet']['assets'][0]))
        self.reject(x,'duplicate id')

    def test_incomplete_assets_cannot_be_reconciled_networth(self):
        x=copy.deepcopy(self.salary)
        x['balance_sheet']['net_worth_status']='RECONCILED'
        self.reject(x,'cannot claim reconciled net worth')

    def test_required_sections_not_optional_in_complete_plan(self):
        x=copy.deepcopy(self.salary)
        del x['policies']
        self.reject(x,'missing required section: policies')

    def test_cli_positive_and_negative_exit(self):
        pos=subprocess.run([sys.executable,str(SCRIPT),'--input',str(EX/'v5.6-salary-shenzhen-SYNTHETIC.json')],capture_output=True,text=True)
        neg=subprocess.run([sys.executable,str(SCRIPT),'--input',str(EX/'v5.6-invalid-double-count-SYNTHETIC.json')],capture_output=True,text=True)
        self.assertEqual(pos.returncode,0,pos.stdout+pos.stderr)
        self.assertEqual(neg.returncode,1,neg.stdout+neg.stderr)

    def test_private_input_not_written_to_disk_by_validator(self):
        with tempfile.TemporaryDirectory(prefix='pwmp_v56_test_') as d:
            source=Path(d)/'private.json'
            source.write_text(json.dumps(self.salary))
            before=set(p.name for p in Path(d).iterdir())
            done=subprocess.run([sys.executable,str(SCRIPT),'--input',str(source)],capture_output=True,text=True)
            after=set(p.name for p in Path(d).iterdir())
            self.assertEqual(done.returncode,0)
            self.assertEqual(before,after)

    def test_skill_first_architecture_and_links(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('HOST Agent performs',text)
        self.assertIn('personal-wealth-master-plan.md',text)
        self.assertIn('5.6.0',text)
        self.assertTrue((SKILL/'assets/personal-wealth-master-plan-template.md').exists())
        contract=json.loads((ROOT/'docs/architecture_contract.json').read_text(encoding='utf-8'))
        self.assertEqual(len(contract['ten_domains']),10)
        self.assertEqual(len(contract['twelve_states']),12)
        self.assertEqual(contract['baseline_sha256'],'552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb')

    @unittest.skipUnless(importlib.util.find_spec('jsonschema') is not None,'jsonschema not installed; optional draft2020 schema test skipped')
    def test_optional_json_schema(self):
        import jsonschema
        schema=json.loads((SKILL/'schemas/master-plan-v5.6.schema.json').read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator.check_schema(schema)
        for x in (self.salary,self.trader):
            jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(x)
        with self.assertRaises(jsonschema.ValidationError):
            x=copy.deepcopy(self.salary)
            x['permissions']['autonomous_financial_actions']=True
            jsonschema.Draft202012Validator(schema).validate(x)

if __name__ == '__main__':
    unittest.main()
