"""The blind review tool computes reported scores but does not invent real host runs."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'tests/skill_vs_baseline'
SCRIPT=DIR/'evaluate_blind.py'
spec=importlib.util.spec_from_file_location('evaluate_blind_v561',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class BlindEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.scores=json.loads((DIR/'SAMPLE_ONLY_scores_v561.json').read_text())
        self.unblind=json.loads((DIR/'SAMPLE_ONLY_unblind_v561.json').read_text())
    def test_anonymized_scores_without_unblinding(self):
        x=m.summarize(self.scores)
        self.assertNotIn('skill_minus_plain',x)
        self.assertFalse(x['is_empirical_evidence'])
    def test_unblinding_yields_conditional_rating_difference(self):
        x=m.summarize(self.scores,self.unblind)
        self.assertEqual(x['skill_minus_plain'],20)
        self.assertFalse(x['is_empirical_evidence'])
    def test_critical_flags_surface(self):
        x=json.loads(json.dumps(self.scores))
        x['ratings'][0]['critical_failures']=['invented_tax_law']
        self.assertFalse(m.summarize(x)['cases'][0]['candidates'][0]['critical_pass'])
    def test_reject_bad_score(self):
        x=json.loads(json.dumps(self.scores))
        x['ratings'][0]['scores']['cashflow_math']=99
        with self.assertRaisesRegex(ValueError,'0..4'):
            m.summarize(x)
    def test_reject_missing_comparison_arm(self):
        x=json.loads(json.dumps(self.scores))
        x['ratings']=x['ratings'][:1]
        with self.assertRaisesRegex(ValueError,'two anonymized'):
            m.summarize(x)
    def test_cli_executes_without_external_model(self):
        r=subprocess.run([sys.executable,str(SCRIPT),'--scores',str(DIR/'SAMPLE_ONLY_scores_v561.json'),'--unblind',str(DIR/'SAMPLE_ONLY_unblind_v561.json')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['skill_minus_plain'],20)

if __name__=='__main__':unittest.main()
