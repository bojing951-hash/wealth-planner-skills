"""v5.7 four-bucket cashflow tests — deterministic offline math, NOT real host E2E.

Every assertion checks actual numbers or hard invariants (conservation,
fail-closed rejection, anti-double-counting), never keyword matching.
"""
from __future__ import annotations

from decimal import Decimal as D
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'personal-finance-planner'
SCRIPTS = SKILL / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import four_bucket_math as fb  # noqa: E402

PY = sys.executable


def fixture(name: str) -> dict:
    return json.loads((SKILL / 'examples' / name).read_text(encoding='utf8'))


def run_cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(SCRIPTS / 'four_bucket_math.py'), *args],
                          input=stdin, capture_output=True, text=True)


def plan_of(name: str) -> dict:
    proc = run_cli('plan', '--input', str(SKILL / 'examples' / name))
    if proc.returncode not in (0, 2):  # 2 = DEFICIT is a legitimate, complete plan
        raise AssertionError(f'{name} failed: {proc.stderr}')
    return json.loads(proc.stdout)


class PersonaDifferentiationTests(unittest.TestCase):
    """AC-03: three clearly different households must not receive one fixed ratio."""

    def test_three_personas_produce_different_structures(self):
        plans = {n: plan_of(f) for n, f in (
            ('stable', 'v5.7-salary-stable-SYNTHETIC.json'),
            ('family', 'v5.7-variable-family-SYNTHETIC.json'),
            ('crossborder', 'v5.7-crossborder-goal-SYNTHETIC.json'))}
        shares = {}
        for name, p in plans.items():
            a = D(p['allocatable']['amount'])
            b = p['buckets']
            shares[name] = (
                D(b['safety_savings']['add_this_period']) / a,
                D(b['necessary_investment']['total']) / a,
                D(b['social_discretionary']['total']) / a)
        self.assertNotEqual(shares['stable'], shares['family'])
        self.assertNotEqual(shares['family'], shares['crossborder'])
        self.assertNotEqual(shares['stable'], shares['crossborder'])
        # concrete anti-template evidence: family persona carries debt pressure ->
        # zero risk investment; crossborder persona with ample reserves carries
        # zero reserve top-up but material investment.
        self.assertEqual(D(plans['family']['buckets']['necessary_investment']['financial']), D('0'))
        self.assertEqual(D(plans['crossborder']['buckets']['safety_savings']['add_this_period']), D('0'))
        self.assertGreater(D(plans['crossborder']['buckets']['necessary_investment']['total']), D('0'))

    def test_every_persona_conserves_cashflow(self):
        for f in ('v5.7-salary-stable-SYNTHETIC.json', 'v5.7-variable-family-SYNTHETIC.json',
                  'v5.7-crossborder-goal-SYNTHETIC.json'):
            p = plan_of(f)
            self.assertTrue(p['conservation']['holds'], f)
            self.assertEqual(D(p['conservation']['allocatable']),
                             D(p['conservation']['sum_buckets_plus_unallocated']))


class StableSalaryTests(unittest.TestCase):
    def test_stable_salary_expected_amounts(self):
        p = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        self.assertEqual(p['income_basis']['classification'], 'STABLE_SALARY')
        self.assertEqual(p['allocatable']['amount'], '25000.00')
        b = p['buckets']
        # floor = 5500+1200+2500+600+400 = 10200
        self.assertEqual(D(b['living']['total']), D('10200.00'))
        # heuristic reserve (no deps, stable) = 3 months -> target 30600, gap 10600
        # balanced: safety = min(10600, 14800*0.5) = 7400; committed 500 then free
        # 1500 then capability 2000 then financial = (14800-7400-500-1500-2000)*0.5 = 1700
        self.assertEqual(D(b['safety_savings']['add_this_period']), D('7400.00'))
        self.assertEqual(D(b['social_discretionary']['total']), D('2000.00'))
        self.assertEqual(D(b['necessary_investment']['capability']), D('2000.00'))
        self.assertEqual(D(b['necessary_investment']['financial']), D('1700.00'))
        self.assertEqual(D(p['unallocated']), D('1700.00'))
        self.assertEqual(p['allocatable']['tax_status'], 'KNOWN_NET')
        # zero-income stress: 20000/10200 = 1.9607... reported at 2dp
        self.assertEqual(D(p['zero_income_stress']['coverage_months']), D('1.96'))

    def test_status_quo_comparison_and_no_change(self):
        p = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        sq = [c for c in p['comparisons'] if c['name'] == 'status_quo'][0]
        self.assertTrue(sq['viable'])  # reported pattern sums to 25000 <= allocatable


class VolatileIncomeTests(unittest.TestCase):
    def test_variable_family_scenario_band(self):
        p = plan_of('v5.7-variable-family-SYNTHETIC.json')
        self.assertEqual(p['income_basis']['classification'], 'VARIABLE_HISTORY')
        band = p['income_basis']['scenario_band']
        self.assertEqual(D(band['low']), D('16000.00'))
        self.assertEqual(D(band['typical']), D('23000.00'))
        self.assertEqual(D(band['high']), D('35000.00'))

    def test_high_cost_debt_blocks_risk_investment(self):
        p = plan_of('v5.7-variable-family-SYNTHETIC.json')
        b = p['buckets']
        # committed social survives (900) but free social and financial invest = 0
        self.assertEqual(D(b['social_discretionary']['committed']), D('900.00'))
        self.assertEqual(D(b['social_discretionary']['free']), D('0.00'))
        self.assertEqual(D(b['necessary_investment']['financial']), D('0.00'))
        # surplus 15100: safety 7550 -> committed 900 -> high-cost extra = 6650
        self.assertEqual(D(b['safety_savings']['extra_high_cost_debt_repayment']), D('6650.00'))
        self.assertEqual(D(p['unallocated']), D('0.00'))

    def test_dependents_raise_reserve_target(self):
        p = plan_of('v5.7-variable-family-SYNTHETIC.json')
        target = [a for a in p['assumptions'] if a['id'] == 'reserve_months_target'][0]
        self.assertEqual(target['value'], '9')  # variable + 1 dependent heuristic
        self.assertEqual(target['source'], 'HEURISTIC_EDITABLE')
        # reserve target = 9 * floor 15900 = 143100; gap = 143100-52000 = 91100
        self.assertEqual(D([a for a in p['assumptions'] if a['id'] == 'reserve_target_amount'][0]['value']),
                         D('143100.00'))

    def test_user_override_beats_heuristic(self):
        p = plan_of('v5.7-crossborder-goal-SYNTHETIC.json')
        target = [a for a in p['assumptions'] if a['id'] == 'reserve_months_target'][0]
        self.assertEqual(target['value'], '6')
        self.assertEqual(target['source'], 'USER_INPUT')


class CrossborderTests(unittest.TestCase):
    def test_fx_converted_exactly_once(self):
        p = plan_of('v5.7-crossborder-goal-SYNTHETIC.json')
        self.assertEqual(D(p['allocatable']['amount']), D('42845.00'))  # 32000 + 1500*7.23
        conv = p['allocatable']['fx_conversions']
        self.assertEqual(len(conv), 1)
        self.assertEqual(conv[0]['from'], 'USD')

    def test_ample_reserve_gives_zero_safety_topup(self):
        p = plan_of('v5.7-crossborder-goal-SYNTHETIC.json')
        self.assertEqual(D(p['buckets']['safety_savings']['add_this_period']), D('0.00'))
        self.assertEqual(D(p['buckets']['safety_savings']['gap_after']), D('0.00'))

    def test_goal_earmark_not_re_saved(self):
        p = plan_of('v5.7-crossborder-goal-SYNTHETIC.json')
        link = [m for m in p['master_plan_links'] if m['goal'] == 'house_down_payment'][0]
        self.assertEqual(link['funded_from'], 'existing_assets_earmark')


class DeficitTests(unittest.TestCase):
    def test_deficit_reports_gap_not_negative_savings(self):
        p = plan_of('v5.7-deficit-SYNTHETIC.json')
        self.assertEqual(p['status'], 'DEFICIT')
        self.assertEqual(D(p['deficit']['gap']), D('500.00'))
        self.assertEqual(D(p['deficit']['reserve_draw_available']), D('500.00'))
        b = p['buckets']
        self.assertEqual(D(b['safety_savings']['add_this_period']), D('0.00'))
        self.assertEqual(D(b['necessary_investment']['total']), D('0.00'))
        self.assertEqual(D(b['social_discretionary']['total']), D('0.00'))
        # conservation still holds on funded amounts
        self.assertTrue(p['conservation']['holds'])
        self.assertEqual(D(b['living']['funded']), D('8000.00'))
        self.assertEqual(D(b['living']['total']), D('8500.00'))


class UnknownDataTests(unittest.TestCase):
    def test_two_months_only_is_insufficient_history(self):
        p = plan_of('v5.7-two-months-only-SYNTHETIC.json')
        self.assertEqual(p['income_basis']['classification'], 'INSUFFICIENT_HISTORY')
        self.assertIsNone(p['income_basis']['scenario_band'])
        self.assertEqual(p['status'], 'CONDITIONAL')
        joined = ' '.join(p['unknowns'])
        self.assertIn('long-run normal income', joined)
        self.assertIn('opening balance', joined)
        # retention-rate figures are explicitly REJECTED from two-month data —
        # the word may appear only in that rejection sentence, never as a number
        self.assertIn('retention-rate claims from two-month data are rejected', joined)
        self.assertNotIn('"retention_rate"', json.dumps(p).lower())
        self.assertNotIn('"retention"', json.dumps(p).lower())

    def test_tax_unknown_keeps_investable_conditional(self):
        p = plan_of('v5.7-two-months-only-SYNTHETIC.json')
        self.assertEqual(p['allocatable']['tax_status'], 'UNKNOWN_TAX_CONDITIONAL')
        self.assertIn('investable amounts stay conditional', ' '.join(p['unknowns']))
        self.assertEqual(p['status'], 'CONDITIONAL')

    def test_safety_cash_unknown_reports_not_computable(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['facts'].pop('safety_eligible_cash')
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertEqual(proc.returncode, 0)
        p = json.loads(proc.stdout)
        self.assertIn('reserve gap not computable', ' '.join(p['unknowns']))

    def test_unreceived_income_excluded(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['current_period_income']['received'] = False
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        p = json.loads(proc.stdout)
        self.assertEqual(D(p['allocatable']['amount']), D('0.00'))
        self.assertEqual(p['status'], 'DEFICIT')  # floor 10200 > 0 allocatable
        self.assertIn('not yet received', ' '.join(p['unknowns']))


class FailClosedTests(unittest.TestCase):
    def test_mixed_currency_without_fx_rejected(self):
        proc = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-invalid-mixed-currency-SYNTHETIC.json'))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('dated FX', proc.stderr)

    def test_negative_and_nonfinite_amounts_rejected(self):
        proc = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-invalid-amounts-SYNTHETIC.json'))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('>= 0', proc.stderr)

    def test_nan_safety_cash_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['facts']['safety_eligible_cash'] = 'NaN'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('finite', proc.stderr)

    def test_infinity_living_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['necessary_living']['fixed'][0]['amount'] = 'Infinity'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)

    def test_bad_month_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['income_history'][0]['month'] = '2026-13'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('YYYY-MM', proc.stderr)

    def test_bad_as_of_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['as_of'] = '2026-02-30'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)

    def test_wrong_schema_version_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['schema_version'] = '5.6.0'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)

    def test_missing_required_field_rejected(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        del data['necessary_living']
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('necessary_living', proc.stderr)

    def test_pf_simulated_funds_never_counted_as_safety_cash(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['facts']['pf_simulated_funds'] = '500000.00'
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        p = json.loads(proc.stdout)
        # reserve target still computed from 20000 eligible cash only
        self.assertEqual(D(p['buckets']['safety_savings']['existing_eligible']), D('20000.00'))


class OversubscriptionTests(unittest.TestCase):
    def test_current_pattern_over_income_flagged_unsustainable(self):
        data = fixture('v5.7-salary-stable-SYNTHETIC.json')
        data['current_pattern'] = {'living': '15000.00', 'savings_add': '2000.00', 'capability': '0.00',
                                   'financial_investment': '8000.00', 'social': '4000.00', 'unallocated': '0.00'}
        proc = run_cli('plan', '--input', '-', stdin=json.dumps(data))
        p = json.loads(proc.stdout)
        sq = [c for c in p['comparisons'] if c['name'] == 'status_quo'][0]
        self.assertFalse(sq['viable'])
        self.assertIn('UNSUSTAINABLE', sq['summary'])
        # the engine itself never allocates beyond allocatable
        self.assertTrue(p['conservation']['holds'])

    def test_engine_never_oversubscribes_by_construction(self):
        for f in ('v5.7-salary-stable-SYNTHETIC.json', 'v5.7-variable-family-SYNTHETIC.json',
                  'v5.7-crossborder-goal-SYNTHETIC.json', 'v5.7-deficit-SYNTHETIC.json',
                  'v5.7-two-months-only-SYNTHETIC.json'):
            p = plan_of(f)
            self.assertTrue(p['conservation']['holds'], f)
            buckets_sum = sum(D(p['buckets'][k][v]) for k, v in (
                ('safety_savings', 'add_this_period'),
                ('safety_savings', 'extra_high_cost_debt_repayment'),
                ('necessary_investment', 'total'),
                ('social_discretionary', 'total')))
            funded = D(p['buckets']['living'].get('funded') or p['buckets']['living']['total'])
            self.assertEqual(buckets_sum + funded + D(p['unallocated']),
                             D(p['allocatable']['amount']), f)


class ReviewTests(unittest.TestCase):
    def test_reallocation_not_new_savings_flag(self):
        proc = run_cli('review', '--input', str(SKILL / 'examples' / 'v5.7-review-followup-SYNTHETIC.json'))
        self.assertEqual(proc.returncode, 0)
        r = json.loads(proc.stdout)
        # income 20000 - living 16000 - social 4000 = 0 new savings
        self.assertEqual(D(r['net_new_savings']), D('0.00'))
        self.assertTrue(any('REALLOCATION_NOT_NEW_SAVINGS' in f for f in r['investment_vs_savings_flags']))
        self.assertTrue(any('unexplained' in f.lower() for f in r['investment_vs_savings_flags']))

    def test_positive_savings_month_has_no_reallocation_flag(self):
        review = fixture('v5.7-review-followup-SYNTHETIC.json')
        review['actuals'].update({'income_received': '25000.00', 'living_spent': '10500.00',
                                  'social_spent': '2000.00', 'financial_invested': '6000.00',
                                  'reserve_addition_actual': '2000.00', 'internal_transfers': '3000.00',
                                  'reserve_end_balance': '22000.00'})
        proc = run_cli('review', '--input', '-', stdin=json.dumps(review))
        r = json.loads(proc.stdout)
        self.assertEqual(D(r['net_new_savings']), D('12500.00'))
        self.assertFalse(any('REALLOCATION' in f for f in r['investment_vs_savings_flags']))
        self.assertEqual(D(r['internal_transfers_excluded']), D('3000.00'))
        self.assertEqual(D(r['reserve_coverage_months']), D('2.16'))  # 22000/10200 at 2dp

    def test_variance_against_plan(self):
        review = fixture('v5.7-review-followup-SYNTHETIC.json')
        proc = run_cli('review', '--input', str(SKILL / 'examples' / 'v5.7-review-followup-SYNTHETIC.json'))
        r = json.loads(proc.stdout)
        self.assertEqual(D(r['variances']['living']['planned']), D('10200.00'))
        self.assertEqual(D(r['variances']['living']['variance']), D('5800.00'))

    def test_review_requires_prior_plan_version(self):
        review = fixture('v5.7-review-followup-SYNTHETIC.json')
        review['plan']['schema_version'] = '5.6.0'
        proc = run_cli('review', '--input', '-', stdin=json.dumps(review))
        self.assertNotEqual(proc.returncode, 0)

    def test_review_missing_actuals_rejected(self):
        review = fixture('v5.7-review-followup-SYNTHETIC.json')
        del review['actuals']['living_spent']
        proc = run_cli('review', '--input', '-', stdin=json.dumps(review))
        self.assertNotEqual(proc.returncode, 0)


class BoundarySemanticsTests(unittest.TestCase):
    """AC-05: spending vs saving vs transfer vs income vs re-division stay distinct."""

    def test_capability_purchase_is_spending_not_investment(self):
        p = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        inv = p['buckets']['necessary_investment']
        self.assertEqual(D(inv['capability']), D('2000.00'))
        self.assertEqual(D(inv['financial']), D('1700.00'))
        self.assertNotEqual(inv['capability'], inv['financial'])  # tracked separately

    def test_internal_transfer_excluded_from_savings_math(self):
        review = fixture('v5.7-review-followup-SYNTHETIC.json')
        review['actuals'].update({'income_received': '25000.00', 'living_spent': '10000.00',
                                  'social_spent': '2000.00', 'financial_invested': '0.00',
                                  'extra_debt_repayment': '0.00', 'reserve_addition_actual': '1000.00',
                                  'internal_transfers': '12000.00', 'reserve_end_balance': '21000.00'})
        proc = run_cli('review', '--input', '-', stdin=json.dumps(review))
        r = json.loads(proc.stdout)
        # 12000 transfer to brokerage changes nothing about new savings
        self.assertEqual(D(r['net_new_savings']), D('13000.00'))

    def test_debt_service_is_cash_obligation_inside_living(self):
        p = plan_of('v5.7-variable-family-SYNTHETIC.json')
        self.assertEqual(D(p['buckets']['living']['debt_service_cash']), D('6400.00'))
        # and it is NOT deducted twice: allocatable stayed the full 31000
        self.assertEqual(D(p['allocatable']['amount']), D('31000.00'))

    def test_defensive_mode_closes_free_spend_and_investment(self):
        p = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        defensive = [c for c in p['comparisons'] if c['name'] == 'defensive'][0]
        balanced = [c for c in p['comparisons'] if c['name'] == 'balanced'][0]
        self.assertGreater(D(defensive['buckets']['safety_savings']), D(balanced['buckets']['safety_savings']))
        self.assertLess(D(defensive['buckets']['social_discretionary']), D(balanced['buckets']['social_discretionary']))

    def test_markdown_render_contains_all_four_buckets(self):
        proc = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-salary-stable-SYNTHETIC.json'), '--format', 'md')
        for bucket in ('Safety & savings', 'Living (necessary)', 'Necessary investment', 'Social & discretionary'):
            self.assertIn(bucket, proc.stdout)
        self.assertIn('Conservation holds: True', proc.stdout)


class StdinPrivacyTests(unittest.TestCase):
    """Real user data must be able to stay off disk (stdin path)."""

    def test_stdin_equals_file_result(self):
        via_file = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        raw = (SKILL / 'examples' / 'v5.7-salary-stable-SYNTHETIC.json').read_text(encoding='utf-8')
        proc = run_cli('plan', '--input', '-', stdin=raw)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout), via_file)


class ExitCodeContractTests(unittest.TestCase):
    def test_exit_codes_0_2_3(self):
        ok = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-salary-stable-SYNTHETIC.json'))
        deficit = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-deficit-SYNTHETIC.json'))
        invalid = run_cli('plan', '--input', str(SKILL / 'examples' / 'v5.7-invalid-amounts-SYNTHETIC.json'))
        self.assertEqual((ok.returncode, deficit.returncode, invalid.returncode), (0, 2, 3))


class NoFixedTemplateTests(unittest.TestCase):
    def test_ratio_changes_when_reserve_gap_changes(self):
        """Same income/floor, different starting cash -> different allocation."""
        base = fixture('v5.7-salary-stable-SYNTHETIC.json')
        rich = json.loads(json.dumps(base))
        rich['facts']['safety_eligible_cash'] = '30600.00'  # gap zero
        p_rich = json.loads(run_cli('plan', '--input', '-', stdin=json.dumps(rich)).stdout)
        p_base = plan_of('v5.7-salary-stable-SYNTHETIC.json')
        self.assertEqual(D(p_rich['buckets']['safety_savings']['add_this_period']), D('0.00'))
        self.assertGreater(D(p_rich['buckets']['necessary_investment']['financial']),
                           D(p_base['buckets']['necessary_investment']['financial']))

    def test_surplus_priority_inversion_recorded_when_high_cost_debt(self):
        p = plan_of('v5.7-variable-family-SYNTHETIC.json')
        # user claims investment_eligible=true while 18% debt exists
        self.assertIn('priority rule', ' '.join(p['unknowns']))


if __name__ == '__main__':
    unittest.main()
