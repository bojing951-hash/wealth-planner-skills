"""Release-level offline alignment tests. Not a live Codex/Claude Agent E2E test."""
from __future__ import annotations
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/personal-finance-planner'
sys.path.insert(0,str(ROOT))
from tools.check_architecture import check, EXPECTED_DOMAINS, EXPECTED_STATES


class OriginalArchitectureAlignmentTests(unittest.TestCase):
    def test_original_baseline_sha256_locked_and_exact(self):
        contract=json.loads((ROOT/'docs/architecture_contract.json').read_text(encoding='utf8'))
        observed=hashlib.sha256((ROOT/contract['baseline_file']).read_bytes()).hexdigest()
        self.assertEqual(contract['baseline_sha256'],observed)

    def test_full_structural_gate_passes(self):
        result=check(ROOT)
        self.assertTrue(result['ok'],result['errors'])
        self.assertEqual(result['domains_present'],10)
        self.assertEqual(result['states_present'],12)
        self.assertIn('DOES_NOT_PROVE_AGENT_BEHAVIOR',result['contract_scope'])

    def test_baseline_mutation_is_fatal_even_if_other_files_exist(self):
        # Fast targeted tamper test: checker must *not* silently accept changed original plan.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'docs').mkdir()
            (root/'docs/architecture_contract.json').write_bytes((ROOT/'docs/architecture_contract.json').read_bytes())
            (root/'docs/BASELINE_ORIGINAL_v0.4.md').write_text('modified baseline',encoding='utf8')
            result=check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('baseline missing or modified' in e for e in result['errors']))

    def test_ten_domains_preserved_in_original_order(self):
        c=json.loads((ROOT/'docs/architecture_contract.json').read_text())
        self.assertEqual([x['key'] for x in c['ten_domains']],EXPECTED_DOMAINS)
        for x in c['ten_domains']:
            self.assertIn(x['status'],('PARTIAL','BLOCKED','WORKFLOW_ONLY','COMPLETE'))
            self.assertTrue(x['unresolved'])

    def test_twelve_states_preserved_in_original_order(self):
        c=json.loads((ROOT/'docs/architecture_contract.json').read_text())
        self.assertEqual(c['twelve_states'],EXPECTED_STATES)
        text=(SKILL/'workflows/skill-first-execution.md').read_text()
        for state in EXPECTED_STATES:
            self.assertIn(f'`{state}`',text)

    def test_skill_manifest_and_progressive_reference_links(self):
        text=(SKILL/'SKILL.md').read_text()
        self.assertLess(len(text.splitlines()),500)
        self.assertIn('name: personal-finance-planner',text)
        self.assertIn('version: "5.3.0"',text)
        self.assertIn('Skill supplies the financial methodology',text)

    def test_host_is_exec_owner_and_cli_queue_not_mandatory(self):
        text=(SKILL/'SKILL.md').read_text()
        self.assertIn('The HOST Agent performs research',text)
        self.assertIn('host-queue',text)
        self.assertIn('OPTIONAL',text)
        self.assertIn('it is neither required nor an actual tool call',text)
        self.assertIn('directly',text)

    def test_cannot_automate_sensitive_external_actions(self):
        skill=(SKILL/'SKILL.md').read_text().lower()
        policy=(SKILL/'policies/core-decision.md').read_text().lower()
        self.assertIn('no automated trades',skill)
        self.assertIn('explicit consent',skill)
        self.assertIn('l3',policy)
        self.assertIn('not_verified',skill)

    def test_not_fake_theory_consensus(self):
        text=(SKILL/'workflows/theory-evidence-and-conflicts.md').read_text()
        self.assertIn('primary',text.lower())
        self.assertIn('Graham vs Bogle',text)
        self.assertIn('Markowitz vs Taleb',text)
        self.assertIn('not a vote',text.lower())

    def test_dynamic_review_requires_an_event_or_real_scheduler(self):
        text=(SKILL/'workflows/dynamic-review-protocol.md').read_text().lower()
        self.assertIn('not a daemon',text)
        self.assertIn('separately supported',text)
        self.assertIn('no_prior_state',text)
        self.assertIn('one-day',text)

    def test_report_contract_preserves_unknowns(self):
        text=(SKILL/'workflows/report-contract.md').read_text()
        self.assertIn('NOT_VERIFIED',text)
        self.assertIn('blocked_decisions',text)
        self.assertIn('reproducibility',text)
        self.assertIn('capital_market_assumptions',text)

    def test_host_e2e_not_claimed(self):
        manual=(ROOT/'tests/host_e2e/ACCEPTANCE_v5.1.md').read_text()
        self.assertIn('NOT_TESTED',manual)
        self.assertIn('actual tool calls',manual)


class LegacyOptionalMathSmokeTests(unittest.TestCase):
    def run_case(self,location):
        path=SKILL/'examples'/f'v5-{location}.json'
        proc=subprocess.run([sys.executable,str(SKILL/'scripts/wealth_v5.py'),'run','--input',str(path),'--format','json'],
                            text=True,capture_output=True,timeout=20)
        self.assertEqual(proc.returncode,0,proc.stderr)
        return json.loads(proc.stdout)

    def test_five_city_and_pf_cases_do_not_implicitly_verify_law(self):
        for case in ('shenzhen','shanghai','new-york','chicago','cn-hk-pf'):
            with self.subTest(case=case):
                data=self.run_case(case)
                self.assertEqual(data['skill_version'],'5.1.0')
                self.assertEqual(data['audit']['code_version'],'5.0.0')
                self.assertEqual(data['audit']['architecture_baseline'],'original-v0.4')
                self.assertFalse(data['assumption_checks']['tax_from_2026_law_verified'])
                self.assertFalse(data['assumption_checks']['host_research_completed'])
                self.assertEqual(data['host_action_receipts']['receipt_count'],0)
                self.assertEqual(data['long_horizon_scenarios']['status'],'NOT_RUN_NO_EXPLICIT_ASSUMPTIONS')

    def test_real_private_money_separate_from_pf_demo(self):
        data=self.run_case('cn-hk-pf')
        buckets=data['financial_snapshot']['currency_buckets']
        self.assertGreater(sum(float(x['simulated_pf_assets_excluded']) for x in buckets.values()),0)
        self.assertGreaterEqual(len(buckets),2)

    def test_us_localities_not_assumed_identical(self):
        ny=self.run_case('new-york')
        chi=self.run_case('chicago')
        ny_scopes=[j['scope'] for j in ny['jurisdiction_map']]
        chi_scopes=[j['scope'] for j in chi['jurisdiction_map']]
        self.assertTrue(any('New York' in s for s in ny_scopes))
        self.assertTrue(any(':IL' in s or 'Illinois' in s for s in chi_scopes))
        self.assertNotEqual(ny_scopes,chi_scopes)

    def test_release_report_is_not_presented_as_certified_tax(self):
        self.assertIn('Developer Preview',(ROOT/'README.md').read_text())
        doc=(ROOT/'docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md').read_text()
        for i in range(1,11):self.assertIn(f'D{i:02d}',doc)
        self.assertIn('NOT_TESTED',doc)


if __name__=='__main__': unittest.main()
