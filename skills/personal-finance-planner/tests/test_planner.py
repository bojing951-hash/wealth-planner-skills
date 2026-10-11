import copy
import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finance_planner_script', ROOT/'scripts'/'planner.py')
assert spec and spec.loader
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


def profile(**changes):
    result = {
        'monthly_cash_receipts': 20000,
        'monthly_essential_spending': 8000,
        'monthly_discretionary_spending': 2000,
        'financial_assets': 100000,
        'liquid_cash': 100000,
        'income_type': 'stable',
        'target_net_worth': 1000000,
        'target_years': 5,
        'annual_investment_return_assumption': 0.0,
    }
    result.update(changes)
    return planner.validate(result)


class FinanceMathTest(unittest.TestCase):
    def test_monthly_surplus_and_no_returns_conservation(self):
        p = profile(financial_assets=0, liquid_cash=0, monthly_essential_spending=0, monthly_discretionary_spending=0)
        r = planner.simulate(p, 12)
        self.assertAlmostEqual(r['ending_net_worth'], 240000)

    def test_reserve_not_double_counted(self):
        p = profile()
        r = planner.simulate(p, 12)
        self.assertAlmostEqual(r['ending_net_worth'], 220000)
        self.assertAlmostEqual(r['ending_cash'] + r['ending_invested'] - r['ending_debt'], 220000)

    def test_liquid_cash_cannot_exceed_financial_assets(self):
        with self.assertRaises(planner.ProfileError):
            profile(liquid_cash=200000, financial_assets=100000)

    def test_negative_spending_rejected(self):
        with self.assertRaises(planner.ProfileError):
            profile(monthly_essential_spending=-1)

    def test_income_types_change_default_emergency_buffer(self):
        stable = profile(income_type='stable')
        variable = profile(income_type='variable')
        self.assertEqual(stable['emergency_months'], 6)
        self.assertEqual(variable['emergency_months'], 12)

    def test_investment_return_compounding_is_annualized(self):
        p = profile(monthly_cash_receipts=0, monthly_essential_spending=0, monthly_discretionary_spending=0,
                    financial_assets=100000, liquid_cash=0, annual_investment_return_assumption=0.05)
        r = planner.simulate(p, 12)
        self.assertAlmostEqual(r['ending_net_worth'], 105000, delta=0.01)

    def test_debt_payment_not_double_counted(self):
        p = profile(monthly_cash_receipts=5000, monthly_essential_spending=0, monthly_discretionary_spending=0,
                    financial_assets=0, liquid_cash=0, outstanding_debt=5000, monthly_debt_payment=5000,
                    debt_annual_rate=0)
        r = planner.simulate(p, 1)
        self.assertEqual(r['ending_debt'], 0)
        self.assertEqual(r['ending_net_worth'], 0)
        # Initial net worth -5000; net worth improves by the earned 5000.

    def test_interest_arrears_growth_warned(self):
        p = profile(outstanding_debt=100000, monthly_debt_payment=100, debt_annual_rate=0.20,
                    financial_assets=0, liquid_cash=0,
                    monthly_cash_receipts=100, monthly_essential_spending=0, monthly_discretionary_spending=0)
        r = planner.simulate(p, 1)
        self.assertGreater(r['ending_debt'], 100000)

    def test_no_cash_creation_after_interruption(self):
        p = profile(monthly_cash_receipts=0, monthly_essential_spending=15000, monthly_discretionary_spending=0,
                    financial_assets=10000, liquid_cash=10000)
        r = planner.simulate(p, 2)
        self.assertEqual(r['first_unfunded_shortfall_month'], 1)
        self.assertAlmostEqual(r['ending_net_worth'], -20000)

    def test_goal_shortfall_can_be_reproduced(self):
        p = profile(monthly_cash_receipts=10000, monthly_essential_spending=10000, monthly_discretionary_spending=0,
                    target_net_worth=220000, target_years=1,
                    financial_assets=100000, liquid_cash=100000)
        expected_extra = 10000.0
        actual = planner.calculate_required_extra_monthly_surplus(p)
        self.assertAlmostEqual(actual, expected_extra, delta=0.01)
        r = planner.simulate(p, 12, extra_monthly_cashflow=actual)
        self.assertGreaterEqual(r['ending_net_worth'], 220000 - 0.01)

    def test_base_goal_met_vs_unmet(self):
        p = profile(target_net_worth=100000, target_years=1)
        report = planner.build_report(p)
        self.assertTrue(report['goal']['base_case_met'])
        self.assertEqual(report['goal']['additional_monthly_net_surplus_needed_base_case'], 0.0)

    def test_interruption_flags_shortfall(self):
        p = profile(monthly_cash_receipts=4000, monthly_essential_spending=10000,
                    monthly_discretionary_spending=0, financial_assets=20000, liquid_cash=20000,
                    income_interruption_months=[3,4,5])
        result = planner.simulate(p, 12)
        self.assertIsNotNone(result['first_unfunded_shortfall_month'])

    def test_returns_not_claimed_probabilities(self):
        report = planner.build_report(profile())
        self.assertIn('确定性', report['model_type'])
        self.assertEqual(len(report['deterministic_scenarios']), 3)
        self.assertFalse('success_probability' in report)

    def test_high_cost_debt_acceleration_priority(self):
        p = profile(monthly_cash_receipts=20000, monthly_essential_spending=5000, monthly_discretionary_spending=0,
                    financial_assets=100000, liquid_cash=100000,
                    outstanding_debt=50000, monthly_debt_payment=1000, debt_annual_rate=0.18)
        r = planner.simulate(p, 12)
        self.assertLessEqual(r['ending_debt'], 0.01)
        self.assertGreaterEqual(r['ending_net_worth'], 0)


if __name__ == '__main__':
    unittest.main()
