"""Release governance tests: ORIGINAL architecture invariants, not financial accreditation."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('original_arch_guard', ROOT/'tools/check_architecture.py')
guard = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(guard)


class TestReleaseArchitecture(unittest.TestCase):
    def test_release_passes_original_baseline_guard(self):
        result = guard.check()
        self.assertTrue(result['ok'], msg=str(result['errors']))
        self.assertEqual(result['domains_present'], 10)
        self.assertEqual(result['states_present'], 12)
        self.assertEqual(result['warnings'], [])
        self.assertIn('DOES_NOT_PROVE_AGENT_BEHAVIOR', result['contract_scope'])

    def _isolated(self):
        temp = tempfile.TemporaryDirectory()
        dest = Path(temp.name)/'release'
        shutil.copytree(ROOT/'docs', dest/'docs')
        shutil.copytree(ROOT/'skills', dest/'skills', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (dest/'tests'/'host_e2e').mkdir(parents=True, exist_ok=True)
        (dest/'.github'/'workflows').mkdir(parents=True,exist_ok=True)
        (dest/'.github'/'workflows'/'tests.yml').write_text('name: test',encoding='utf-8')
        return temp,dest

    def test_original_baseline_tamper_blocks_release(self):
        context, root = self._isolated()
        with context:
            baseline = root/'docs'/'BASELINE_ORIGINAL_v0.4.md'
            baseline.write_text(baseline.read_text(encoding='utf-8')+'\nchanged',encoding='utf-8')
            result=guard.check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('baseline' in e.lower() for e in result['errors']))

    def test_missing_domain_resource_blocks_release(self):
        context, root = self._isolated()
        with context:
            target=root/'skills'/'personal-finance-planner'/'references'/'architecture-10-domains.md'
            target.unlink()
            result=guard.check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('D01' in e or 'mandatory' in e for e in result['errors']))

    def test_missing_twelve_state_blocks_release(self):
        context, root = self._isolated()
        with context:
            states = root/'skills'/'personal-finance-planner'/'workflows'/'skill-first-execution.md'
            original = states.read_text(encoding='utf-8')
            states.write_text(original.replace('`EVIDENCE_RESEARCH`','`OMITTED_STEP`'),encoding='utf-8')
            result=guard.check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('EVIDENCE_RESEARCH' in e for e in result['errors']))

    def test_no_report_means_not_released(self):
        context, root = self._isolated()
        with context:
            ver=json.loads((root/'docs'/'architecture_contract.json').read_text())['release']
            (root/'docs'/f'ARCHITECTURE_ALIGNMENT_v{ver}.md').unlink()
            result=guard.check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('requires a completed architecture comparison' in e for e in result['errors']))

    def test_v52_missing_memory_guide_blocks_release(self):
        context, root = self._isolated()
        with context:
            target=root/'skills'/'personal-finance-planner'/'workflows'/'local-memory.md'
            target.unlink()
            result=guard.check(root)
            self.assertFalse(result['ok'])
            self.assertTrue(any('memory' in e.lower() for e in result['errors']))

    def test_original_domains_and_roles_in_contract(self):
        contract=json.loads((ROOT/'docs'/'architecture_contract.json').read_text(encoding='utf-8'))
        self.assertEqual([d['key'] for d in contract['ten_domains']],guard.EXPECTED_DOMAINS)
        self.assertEqual(contract['twelve_states'],guard.EXPECTED_STATES)
        self.assertIn('host',contract['roles'])
        self.assertIn('skill',contract['roles'])
        self.assertIn('optional_math',contract['roles'])
        self.assertTrue(all(d['status']=='PARTIAL' for d in contract['ten_domains']))


if __name__=='__main__':
    unittest.main()
