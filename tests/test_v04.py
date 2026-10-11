"""v0.4 nontrivial unit and integration guards, using fictional data only."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / 'skills' / 'personal-finance-planner'
sys.path.insert(0, str(SKILL / 'lib'))
from wealth_core.capabilities import normalize_manifest, CapabilityError, capability_state
from wealth_core.finance import financial_snapshot
from wealth_core.orchestration import build_plan, official_domain, receipts_result
from wealth_core.profile import money, validate_profile, ProfileError


def fixture(name):
    return json.loads((REPO / 'tests' / 'golden_cases' / f'{name}.json').read_text(encoding='utf8'))


class TestContract(unittest.TestCase):
    def test_five_profiles_valid(self):
        for name in ('shenzhen', 'shanghai', 'new-york', 'chicago', 'cn-hk-pf'):
            with self.subTest(name=name):
                self.assertEqual(validate_profile(fixture(name))['schema_version'], '0.4.0')

    def test_money_requires_string(self):
        for bad in (20, 20.25, '-1.00', '1e8', 'NaN', 'Infinity', ' 5', '', '5.12345'):
            with self.subTest(value=bad), self.assertRaises(ProfileError):
                money(bad)
        self.assertEqual(str(money('20123.45')), '20123.45')

    def test_invalid_tax_and_consent(self):
        v = fixture('shenzhen')
        v['income'][0]['tax_status'] = 'certified_by_AI'
        with self.assertRaises(ProfileError): validate_profile(v)
        v = fixture('shenzhen')
        v['consents']['connect_accounts'] = 'yes'
        with self.assertRaises(ProfileError): validate_profile(v)

    def test_simulated_bank_fraud_block(self):
        v = fixture('cn-hk-pf')
        v['income'][1]['bank_received'] = True
        v['income'][1]['realized'] = True
        with self.assertRaisesRegex(ProfileError, 'simulated PF'):
            validate_profile(v)

    def test_duplicate_ids_and_wrong_period(self):
        v = fixture('shenzhen')
        v['income'].append(copy.deepcopy(v['income'][0]))
        with self.assertRaises(ProfileError): validate_profile(v)
        v = fixture('shenzhen')
        v['income'][0]['period'] = 'weekly'
        with self.assertRaises(ProfileError): validate_profile(v)

    def test_schema_json_matches_fixtures_if_available(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema optional; Python stdlib validator is primary')
        schema = json.loads((SKILL / 'schemas' / 'profile-v0.4.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        for name in ('shenzhen','shanghai','new-york','chicago','cn-hk-pf'):
            jsonschema.validate(fixture(name), schema, format_checker=jsonschema.FormatChecker())


class TestFourCityGoldenCases(unittest.TestCase):
    EXPECTED = {
        'shenzhen': ('CNY', '9750.00', '6050.00','49500.00'),
        'shanghai': ('CNY','11950.00','3750.00','62700.00'),
        'new-york': ('USD','7150.00','5650.00','35700.00'),
        'chicago': ('USD','5500.00','8200.00','26400.00'),
    }

    def test_four_city_exact_conservation(self):
        for name, (cur, spend, surplus, reserve) in self.EXPECTED.items():
            with self.subTest(name=name):
                b = financial_snapshot(fixture(name))['currency_buckets'][cur]
                self.assertEqual((b['monthly_expenses']['total'], b['monthly_surplus_conditional'],
                                  b['reserve_target_conditional']), (spend,surplus,reserve))
                self.assertEqual(b['monthly_investable_final'], None)
                self.assertEqual(b['cashflow_status'], 'PROVISIONAL_TAX_UNVERIFIED')

    def test_different_us_states_and_city_scopes(self):
        n = {x['scope'] for x in build_plan(fixture('new-york'))['jurisdiction_map']}
        c = {x['scope'] for x in build_plan(fixture('chicago'))['jurisdiction_map']}
        self.assertIn('US:NY:New York', n)
        self.assertIn('US:IL:Chicago', c)
        self.assertNotIn('US:NY:New York', c)
        self.assertNotIn('US:IL:Chicago', n)

    def test_china_province_city_not_identical(self):
        s = {x['scope'] for x in build_plan(fixture('shenzhen'))['jurisdiction_map']}
        h = {x['scope'] for x in build_plan(fixture('shanghai'))['jurisdiction_map']}
        self.assertIn('CN:Guangdong:Shenzhen',s)
        self.assertIn('CN:Shanghai:Shanghai',h)

    def test_pf_simulated_not_owned_multicurrency_no_conversions(self):
        out=build_plan(fixture('cn-hk-pf'))
        cny=out['financial_snapshot']['currency_buckets']['CNY']
        usd=out['financial_snapshot']['currency_buckets']['USD']
        self.assertEqual(cny['monthly_surplus_conditional'],'-28000.00')
        self.assertEqual(usd['monthly_surplus_conditional'],'10000.00')
        self.assertEqual(usd['simulated_pf_assets_excluded'],'50000.00')
        self.assertEqual(usd['financial_assets_owned_declared'],'0.00')
        self.assertIn('paper-profit',usd['excluded_unrealized_income_ids'])
        self.assertEqual(usd['monthly_investable_final'],None)
        self.assertTrue(any('MULTICURRENCY' in x for x in out['financial_snapshot']['warnings']))
        self.assertIn('HK',{o['scope'] for o in out['jurisdiction_map']})
        self.assertIn('US',{o['scope'] for o in out['jurisdiction_map']})
        self.assertIn('CN',{o['scope'] for o in out['jurisdiction_map']})

    def test_gross_only_produces_no_surplus(self):
        p = fixture('chicago')
        del p['income'][0]['net_received']
        b=financial_snapshot(validate_profile(p))['currency_buckets']['USD']
        self.assertEqual(b['monthly_surplus_conditional'],None)
        self.assertEqual(b['cashflow_status'],'INCOMPLETE_GROSS_ONLY')
        self.assertTrue(any('gross income' in m for m in build_plan(p)['blocked_decisions']))

    def test_tax_reserve_subtracted_only_from_net_deposits(self):
        p = fixture('shenzhen')
        p['expenses'].append({'id':'tax-reserve','category':'tax_reserve','currency':'CNY','monthly_amount':'900'})
        b=financial_snapshot(validate_profile(p))['currency_buckets']['CNY']
        self.assertEqual(b['monthly_surplus_conditional'],'5150.00')

    def test_joint_asset_requires_beneficial_share_policy(self):
        # Current v0.4 requires clarification, never assumes a joint asset is solely owned.
        p=fixture('shenzhen')
        p['assets'][0]['ownership']='joint'
        b=financial_snapshot(validate_profile(p))['currency_buckets']['CNY']
        self.assertEqual(b['financial_assets_owned_declared'],'0.00')
        self.assertTrue(any('joint asset' in w for w in financial_snapshot(p)['warnings']))
        p['assets'][0]['beneficial_share']='0.50'
        c=financial_snapshot(validate_profile(p))['currency_buckets']['CNY']
        self.assertEqual(c['financial_assets_owned_declared'],'50000.00')


class TestHostToolRouting(unittest.TestCase):
    def setUp(self):
        self.profile=fixture('new-york')
        self.manifest=fixture('capabilities-codex-EXAMPLE')

    def test_default_offline_not_claim_online(self):
        o=build_plan(self.profile)
        self.assertEqual(o['host']['status'], 'DECLARED_NOT_EXECUTED')
        self.assertTrue(all(a['state']=='UNAVAILABLE' for a in o['requested_host_actions']))
        self.assertEqual(o['host_action_receipts']['receipt_count'],0)

    def test_manifest_requests_tools_but_does_not_execute(self):
        o=build_plan(self.profile,self.manifest)
        self.assertTrue(all(a['state']=='READY_FOR_HOST_EXECUTION' for a in o['requested_host_actions']))
        self.assertEqual(o['host_action_receipts']['receipt_count'],0)
        self.assertFalse(any(x.get('status')=='COMPLETED' for x in o['requested_host_actions']))

    def test_other_host_requires_fetch_approval(self):
        m=fixture('capabilities-claude-code-EXAMPLE')
        o=build_plan(self.profile,m)
        self.assertEqual(o['requested_host_actions'][0]['state'],'NEEDS_USER_OR_HOST_APPROVAL')

    def test_source_domain_spoof_rejected(self):
        self.assertFalse(official_domain('US', 'https://irs.gov.attacker.site/rule'))
        self.assertFalse(official_domain('US', 'http://www.irs.gov/rule'))
        self.assertFalse(official_domain('US', 'https://other.com@irs.gov:443/fake'))
        self.assertTrue(official_domain('US', 'https://www.irs.gov/newsroom'))

    def test_receipt_requires_prior_tool_declaration(self):
        receipt={'action_id':'law:US:2026','status':'completed','source_url':'https://www.irs.gov/',
                 'retrieved_on':'2026-10-11','content_sha256':'a'*64,'tax_year':2026}
        offline=build_plan(self.profile)
        with self.assertRaises(ProfileError):
            receipts_result([receipt],offline['requested_host_actions'], self.profile['as_of'])

    def test_valid_host_receipt_does_not_validate_law(self):
        receipt={'action_id':'law:US:2026','status':'completed','source_url':'https://www.irs.gov/',
                 'retrieved_on':'2026-10-10','content_sha256':'a'*64,'tax_year':2026}
        o=build_plan(self.profile,self.manifest,[receipt])
        self.assertEqual(o['host_action_receipts']['receipt_count'],1)
        self.assertEqual(o['host_action_receipts']['items'][0]['state'],
                         'RETRIEVED_PRIMARY_DOMAIN_PENDING_LEGAL_INTERPRETATION')
        self.assertTrue(any('No tax-year-specific' in x for x in o['blocked_decisions']))

    def test_wrong_year_not_authoritative(self):
        receipt={'action_id':'law:US:2026','status':'completed','source_url':'https://www.irs.gov/',
                 'retrieved_on':'2026-10-10','content_sha256':'b'*64,'tax_year':2025}
        o=build_plan(self.profile,self.manifest,[receipt])
        self.assertEqual(o['host_action_receipts']['items'][0]['state'],'UNVERIFIED_WRONG_YEAR_OR_NONOFFICIAL_DOMAIN')

    def test_receipt_replay_and_future_rejected(self):
        receipt={'action_id':'law:US:2026','status':'completed','source_url':'https://www.irs.gov/',
                 'retrieved_on':'2026-10-12','content_sha256':'b'*64,'tax_year':2026}
        actions=build_plan(self.profile,self.manifest)['requested_host_actions']
        with self.assertRaises(ProfileError): receipts_result([receipt],actions,'2026-10-11')
        receipt['retrieved_on']='2026-10-11'
        with self.assertRaises(ProfileError): receipts_result([receipt, receipt],actions,'2026-10-11')

    def test_declared_consent_denial_and_request(self):
        p=fixture('shenzhen')
        p['documents']=[{'ref':'confidential.pdf'}]
        p['account_connection_requested']=True
        p['schedule_requested']=True
        out=build_plan(p,self.manifest)
        states={a['id']:a['state'] for a in out['requested_host_actions']}
        for name in ('files:parse:user-provided','accounts:read_only','schedule:periodic-review'):
            self.assertEqual(states[name],'DISABLED_NO_USER_CONSENT')
        p['consents']['use_user_files']=True
        out=build_plan(p,self.manifest)
        states={a['id']:a['state'] for a in out['requested_host_actions']}
        self.assertEqual(states['files:parse:user-provided'],'NEEDS_USER_OR_HOST_APPROVAL')

    def test_bad_capability_manifest_rejected(self):
        with self.assertRaises(CapabilityError):normalize_manifest({'host':'codex','capabilities':{'magic_trade':{}}})
        with self.assertRaises(CapabilityError):normalize_manifest({'host':'codex','capabilities':{'source_fetch':{'available':'yes'}}})

    def test_no_financial_trade_actions(self):
        o=build_plan(fixture('cn-hk-pf'),self.manifest)
        self.assertFalse(any('trade' in a['kind'] or 'transfer' in a['kind'] for a in o['requested_host_actions']))

    def test_reproducibility_and_as_of(self):
        a=build_plan(self.profile,self.manifest)
        b=build_plan(self.profile,self.manifest)
        self.assertEqual(a,b)
        self.assertEqual(a['audit']['input_sha256'],b['audit']['input_sha256'])
        altered=fixture('new-york'); altered['expenses'][0]['monthly_amount']='4200'
        c=build_plan(altered,self.manifest)
        self.assertNotEqual(a['run_id'],c['run_id'])

    def test_portable_skill_only_no_external_package(self):
        # Copy just the portable skill into a clean directory; no repository root.
        with tempfile.TemporaryDirectory() as tmp:
            copied=Path(tmp)/'personal-finance-planner'
            shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            pr=subprocess.run([sys.executable,str(copied/'scripts'/'wealth_cli.py'), 'plan',
                 '--input',str(copied/'examples'/'v04-shenzhen.json'),'--format','json'],
                capture_output=True,text=True,check=False)
            self.assertEqual(pr.returncode,0,pr.stderr)
            self.assertEqual(json.loads(pr.stdout)['skill_version'],'0.4.0')

    def test_cli_invalid_input_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'p.json'; inp.write_text('{}')
            p=subprocess.run([sys.executable,str(SKILL/'scripts'/'wealth_cli.py'),'validate',
                '--input',str(inp)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertIn('ERROR:',p.stderr)

if __name__=='__main__': unittest.main()
