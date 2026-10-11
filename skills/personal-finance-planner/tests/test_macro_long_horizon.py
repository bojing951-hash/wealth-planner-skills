import copy
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def load(script, alias):
    spec = importlib.util.spec_from_file_location(alias, SKILL/'scripts'/script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


macro = load('macro_context.py', 'macro_test_module')
horizon = load('long_horizon.py', 'long_horizon_test_module')
fred = load('fetch_fred.py', 'fred_test_module')


def snapshot():
    return json.loads((SKILL/'examples'/'macro-snapshot-sourced-dated-example.json').read_text(encoding='utf-8'))


def person(**overrides):
    p = {
        'monthly_cash_receipts': 0,
        'monthly_essential_spending': 0,
        'monthly_discretionary_spending': 0,
        'financial_assets': 100_000,
        'liquid_cash': 0,
        'income_type': 'stable',
    }
    p.update(overrides)
    return p


class MacroValidationTest(unittest.TestCase):
    def test_breakeven_10y_and_date(self):
        r = macro.build_context(snapshot())
        b = r['calculations']['us_breakeven_inflation_10y_pct_approx']
        self.assertAlmostEqual(b['value_pct'], 2.4)
        self.assertEqual(b['observations_days_apart'], 0)
        self.assertEqual(b['quality'], 'sourced')

    def test_stale_indicator_warning(self):
        r = macro.build_context(snapshot())
        self.assertTrue(any(o['id'] == 'US_TIPS_REAL10Y' and o['age_days'] > 30 for o in r['observed_evidence']))
        self.assertFalse('success_probability' in r)

    def test_no_inference_from_current_cpi(self):
        r = macro.build_context(snapshot())
        self.assertTrue(any('不能直接相减' in w for w in r['warnings']))
        self.assertNotIn('cn_long_term_real_yield_pct', r['calculations'])
        self.assertIn('scenario_sensitivity_not_observed_real_rate',
                      r['calculations']['cn_nominal_10y_bond_yield_vs_inflation_assumptions']['quality'])

    def test_cross_currency_rejected(self):
        p = snapshot()
        p['observations'][0]['currency'] = 'CNY'
        with self.assertRaises(macro.MacroInputError):
            macro.validate_snapshot(p)

    def test_observation_future_rejected(self):
        p = snapshot()
        p['observations'][0]['observed_on'] = '2027-10-11'
        with self.assertRaises(macro.MacroInputError):
            macro.validate_snapshot(p)

    def test_source_required_for_sourced_data(self):
        p = snapshot()
        del p['observations'][0]['source_url']
        with self.assertRaises(macro.MacroInputError):
            macro.validate_snapshot(p)

    def test_date_gap_stops_breakeven_mixing(self):
        p = snapshot()
        p['observations'][1]['observed_on'] = '2026-08-10'
        r = macro.build_context(p)
        self.assertNotIn('us_breakeven_inflation_10y_pct_approx', r['calculations'])

    def test_scenarios_are_not_observations(self):
        s = snapshot()
        s['planning_assumptions']['scenarios']['base']['annual_net_return'] = .054
        r = macro.build_context(s)
        self.assertEqual(r['planning_assumptions']['scenarios']['base']['annual_net_return'], .054)
        self.assertFalse('estimated_market_return' in r['calculations'])


class LongHorizonTest(unittest.TestCase):
    def test_compounding_and_real_purchasing_power(self):
        p = person()
        r = horizon.build_long_horizon_report(p, snapshot())
        row = r['results']['base']['10']
        self.assertAlmostEqual(row['ending_nominal_net_financial_worth_cny'], 100_000 * 1.05**10, delta=0.03)
        self.assertAlmostEqual(row['ending_purchasing_power_today_cny'], 100_000 * (1.05/1.025)**10, delta=0.03)
        self.assertNotIn('success_probability', r)

    def test_expenses_inflate_and_income_can_lag(self):
        p = person(monthly_cash_receipts=10000, monthly_essential_spending=8500,
                   monthly_discretionary_spending=1500, liquid_cash=100_000,
                   financial_assets=100_000)
        s = snapshot()
        s['planning_assumptions']['scenarios']['adverse'] = {
            'annual_net_return': 0,
            'annual_inflation': .1,
            'annual_nominal_income_growth': 0,
        }
        r = horizon.build_long_horizon_report(p, s)
        self.assertLess(r['results']['adverse']['20']['ending_nominal_net_financial_worth_cny'],
                        r['results']['base']['20']['ending_nominal_net_financial_worth_cny'])

    def test_no_creation_money(self):
        p = person(monthly_cash_receipts=0, monthly_essential_spending=1000,
                   financial_assets=0, liquid_cash=0)
        s = snapshot()
        for sc in s['planning_assumptions']['scenarios'].values():
            sc.update({'annual_net_return':0,'annual_inflation':0,'annual_nominal_income_growth':0})
        r = horizon.build_long_horizon_report(p, s)
        row = r['results']['base']['10']
        self.assertAlmostEqual(row['ending_nominal_net_financial_worth_cny'], -120_000, delta=0.01)
        self.assertEqual(row['first_unfunded_shortfall_month'], 1)

    def test_10_and_20_years(self):
        r = horizon.build_long_horizon_report(person(), snapshot())
        self.assertEqual(set(r['results']['base']), {'10','20'})


class FredCsvParserTest(unittest.TestCase):
    def test_ignore_missing_cells(self):
        csv = 'DATE,DFII10\n2026-10-06,2.20\n2026-10-07,.\n2026-10-08,2.30\n'
        self.assertEqual(fred.latest_csv_point('DFII10', csv), ('2026-10-08',2.30))

    def test_malformed_columns(self):
        with self.assertRaises(ValueError):
            fred.latest_csv_point('DFII10','DATE,DGS10\n2026-10-08,5.3\n')


if __name__ == '__main__':
    unittest.main()
