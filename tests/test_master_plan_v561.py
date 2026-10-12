"""v5.6.1 regression: enforce the entire shipped plan schema and truthfulness.

These are synthetic mutations, not evidence of professional investment suitability.
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
EX=SKILL/'examples'
SCRIPT=SKILL/'scripts/master_plan_quality.py'
spec=importlib.util.spec_from_file_location('pwmp_quality_patch',SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    return json.loads((EX/'v5.6-high-income-trader-SYNTHETIC.json').read_text())


class TruthfulReconciliationTests(unittest.TestCase):
    def reject(self, value, contains):
        errors=module.validate(value)
        self.assertTrue(errors, 'malformed plan incorrectly accepted')
        self.assertTrue(any(contains in e for e in errors), f'expected {contains!r}, got {errors}')

    def test_original_positive_still_valid(self):
        self.assertEqual(module.validate(sample()),[])

    def test_invalid_net_worth_status_enum(self):
        x=sample();x['balance_sheet']['net_worth_status']='APPROVED_BY_MODEL'
        self.reject(x,'net_worth_status')

    def test_invalid_asset_completeness_enum(self):
        x=sample();x['fact_basis']['asset_completeness']='SURE'
        self.reject(x,'asset_completeness')

    def test_incorrect_reconciled_networth_with_incomplete_assets(self):
        x=sample();x['balance_sheet']['net_worth_status']='RECONCILED'
        self.reject(x,'cannot claim reconciled net worth')

    def test_incorrect_complete_assets_with_unknown_balances(self):
        x=sample();x['fact_basis']['asset_completeness']='RECONCILED'
        x['fact_basis']['reconciliation_reference']='User said all accounts present'
        self.reject(x,'cannot claim reconciled/complete balance sheet')

    def test_claim_complete_requires_reference_even_with_numeric_balances(self):
        x=sample();x['balance_sheet']['assets'][0]['amount']='10000'
        x['balance_sheet']['assets'][0]['provenance']='USER_REPORTED'
        x['balance_sheet']['assets'][1]['amount']='20000'
        x['balance_sheet']['assets'][1]['provenance']='USER_REPORTED'
        x['fact_basis']['asset_completeness']='RECONCILED'
        x['balance_sheet']['net_worth_status']='RECONCILED'
        self.reject(x,'reconciliation_reference is required')
        x['fact_basis']['reconciliation_reference']='User affirmed all known account balances on 2026-10-12 (self-reported)'
        for debt in x['balance_sheet']['liabilities']:
            debt['amount']='10000'
            debt['provenance']='USER_REPORTED'
        self.assertEqual(module.validate(x),[])

    def test_reconciled_with_unknown_debt_rejected(self):
        x=sample();x['balance_sheet']['assets'][0]['amount']='10000'
        x['balance_sheet']['assets'][0]['provenance']='USER_REPORTED'
        x['balance_sheet']['assets'][1]['amount']='20000'
        x['balance_sheet']['assets'][1]['provenance']='USER_REPORTED'
        x['fact_basis']['asset_completeness']='RECONCILED'
        x['fact_basis']['reconciliation_reference']='User says accounts are all listed'
        x['balance_sheet']['liabilities'].append({'id':'car_loan','amount':None,'currency':'USD','kind':'VEHICLE_LOAN','as_of':'2026-10-12','provenance':'UNKNOWN'})
        self.reject(x,'liability car_loan')

    def test_invalid_subfield_enum(self):
        x=sample();x['goals'][0]['priority']='ALWAYS_WIN'
        self.reject(x,'goals[0].priority')

    def test_unknown_extra_field(self):
        x=sample();x['balance_sheet']['made_up_networth']='9000000'
        self.reject(x,'extra property made_up_networth')

    def test_deep_required_missing(self):
        x=sample();del x['goals'][0]['purpose']
        self.reject(x,'missing required field purpose')

    def test_illegal_approval_without_reference(self):
        x=sample();x['status']='USER_APPROVED'
        self.reject(x,'plan_approval_reference')
        x['permissions']['plan_approval_reference']='Separate user confirmation logged 2026-10-12 (not cryptographic proof)'
        self.assertEqual(module.validate(x),[])

    def test_bad_date(self):
        x=sample();x['balance_sheet']['assets'][0]['as_of']='2026-02-30'
        self.reject(x,'invalid ISO date')

    def test_nested_type_corruption_is_rejected_without_crash(self):
        x=sample();x['pools'][0]['allocations']={'asset_id':'bank_usd'}
        self.reject(x,'expected type array')

    def test_negative_or_nan_amount_rejected(self):
        for value in ('-5','NaN','Infinity'):
            with self.subTest(value=value):
                x=sample();x['balance_sheet']['assets'][0]['amount']=value
                self.reject(x,'amount must be finite and nonnegative')

    def test_boolean_is_not_integer(self):
        x=sample();x['actions'][0]['within_days']=True
        self.reject(x,'invalid enum')

    def test_schema_and_builtin_same_on_fixtures_when_jsonschema_installed(self):
        if importlib.util.find_spec('jsonschema') is None:
            self.skipTest('Optional jsonschema absent')
        import jsonschema
        s=json.loads((SKILL/'schemas/master-plan-v5.6.schema.json').read_text())
        check=jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker())
        variants=[sample()]
        for field,value in [('status','SHIPPED'),('status',False)]:
            x=sample();x[field]=value;variants.append(x)
        x=sample();x['permissions']['autonomous_financial_actions']=0;variants.append(x)
        x=sample();x['balance_sheet']['assets'][0]['amount']='-99';variants.append(x)
        for x in variants:
            with self.subTest(case=str(x.get('status'))):
                self.assertEqual(bool(module._schema_errors(x)),bool(list(check.iter_errors(x))))

    def test_bad_nested_ids_or_horizons_never_crash(self):
        for path, value in ((('balance_sheet','assets',0,'id'), ['bad']),
                            (('actions',0,'within_days'), ['bad']),
                            (('actions',0,'policy_id'), ['bad'])):
            with self.subTest(path=path):
                x=sample(); target=x
                for component in path[:-1]: target=target[component]
                target[path[-1]]=value
                self.assertTrue(module.validate(x), 'invalid shape must return diagnostics')

    def test_new_unsupported_schema_keyword_fails_closed(self):
        import tempfile
        from unittest.mock import patch
        original=json.loads((SKILL/'schemas/master-plan-v5.6.schema.json').read_text())
        original['properties']['permissions']['properties']['plan_approval_reference']['contains']={'const':'must_not_be_ignored'}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tampered_schema.json';p.write_text(json.dumps(original))
            with patch.object(module,'_SCHEMA_PATH',p):
                self.reject(sample(),'unsupported schema keywords')

    def test_cli_rejects_bad_enum(self):
        x=sample();x['fact_basis']['asset_completeness']='SURE'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fiction.json';p.write_text(json.dumps(x))
            r=subprocess.run([sys.executable,str(SCRIPT),'--input',str(p)],capture_output=True,text=True)
        self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertIn('asset_completeness',r.stdout)


if __name__=='__main__':unittest.main()
