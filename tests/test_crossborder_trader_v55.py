"""Offline negative, ownership and cashflow regressions for v5.5. Purely synthetic."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/personal-finance-planner'
SCRIPT = SKILL / 'scripts/trader_wealth_reconcile.py'
EXAMPLE = SKILL / 'examples/v5.5-crossborder-mixed-trader-SYNTHETIC.json'
spec=importlib.util.spec_from_file_location('wealth_reconcile_v55', SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def example():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))

class LedgerTests(unittest.TestCase):
    def test_synthetic_cashflow_reconciles_and_no_false_networth(self):
        a=module.analyze(example())
        c=a['cashflow'];r=a['reserves']
        self.assertEqual(c['reported_external_received_per_month_PROVISIONAL'],'24000.00')
        self.assertEqual(c['documented_external_received_per_month'],'0.00')
        self.assertEqual(c['current_essential_excluding_debt'],'3050.00')
        self.assertEqual(c['current_contractual_debt_service'],'900.00')
        self.assertEqual(c['current_cash_outflows'],'3950.00')
        self.assertEqual(c['higher_lifestyle_cash_outflows_if_prior_spend_continues'],'4650.00')
        self.assertEqual(c['monthly_surplus_BEFORE_unknown_tax_and_costs_current'],'20050.00')
        self.assertEqual(c['monthly_surplus_BEFORE_unknown_tax_and_costs_higher_lifestyle'],'19350.00')
        self.assertIsNone(c['conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals'])
        self.assertEqual(r['core_including_debt_service'],'47400.00')
        self.assertEqual(r['higher_lifestyle_if_prior_spend_continues'],'55800.00')
        self.assertIsNone(r['core_reserve_gap'])
        self.assertIsNone(r['runway_months_core'])
        self.assertEqual(a['balance_sheet']['personal_net_financial_assets'],'UNKNOWN')
        self.assertIn('HISTORICAL_DISCRETIONARY_SPENDING_NEEDS_RECONFIRMATION',a['review_flags'])
        self.assertIn('TAX_RESIDENCE_INCOME_CLASSIFICATION_AND_LIABILITY_UNVERIFIED',a['review_flags'])

    def test_brokerage_profit_not_bank_inflow(self):
        inp=example()
        inp['income_items'][1]['range']['high']='980000'
        self.assertEqual(module.analyze(inp)['cashflow']['reported_external_received_per_month_PROVISIONAL'],'24000.00')

    def test_negative_broker_performance_in_range_allowed(self):
        inp=example();inp['income_items'][1]['range']={'low':'-130000','high':'25000'}
        x=module.analyze(inp)
        self.assertEqual(x['recognition'][1]['reported_range']['low'],'-130000.00')

    def test_withdrawal_internal_not_earnings(self):
        inp=example()
        inp['income_items'].append({'id':'own_broker_cashout','kind':'BROKER_WITHDRAWAL_TRANSFER','currency':'USD',
                                    'period':'MONTHLY','amount':'150000','evidence':'USER_REPORTED'})
        result=module.analyze(inp)
        self.assertEqual(result['cashflow']['reported_external_received_per_month_PROVISIONAL'],'24000.00')
        self.assertIn('BROKER_TRANSFER_IS_NOT_NEW_HOUSEHOLD_EARNINGS',result['review_flags'])
        self.assertEqual(result['cashflow']['reported_broker_to_bank_transfers_per_month_NOT_NEW_WEALTH'],'150000.00')
        self.assertEqual(result['cashflow']['total_reported_bank_credits_external_plus_internal_transfers'],'174000.00')
        self.assertTrue(result['recognition'][-1]['bank_cash_inflow_included'])
        self.assertFalse(result['recognition'][-1]['new_external_household_cash_income_included'])

    def test_pf_simulated_not_bank_receipt_or_personal_assets(self):
        inp=example()
        inp['income_items'].append({'id':'pf_demo','kind':'PF_SIMULATED_PNL','currency':'USD','period':'MONTHLY',
                                    'amount':'1000000','evidence':'USER_REPORTED'})
        result=module.analyze(inp)
        self.assertEqual(result['cashflow']['reported_external_received_per_month_PROVISIONAL'],'24000.00')
        self.assertIn('PF_SIMULATED_IS_NOT_OWNED_PERSONAL_WEALTH',result['review_flags'])

    def test_pending_payout_not_cash(self):
        inp=example();inp['income_items'][0]['settlement_status']='PENDING'
        self.assertEqual(module.analyze(inp)['cashflow']['reported_external_received_per_month_PROVISIONAL'],'0.00')

    def test_no_false_verified_receipt(self):
        inp=example();inp['income_items'][0]['settlement_status']='DOCUMENTED_BANK_RECEIVED'
        with self.assertRaises(module.InputError):module.analyze(inp)
        inp['income_items'][0]['evidence']='DOCUMENTED'
        self.assertEqual(module.analyze(inp)['cashflow']['documented_external_received_per_month'],'24000.00')

    def test_hypothetical_bank_revenue_cannot_be_real(self):
        inp=example();inp['income_items'][0]['evidence']='HYPOTHETICAL'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_broker_net_equity_counted_not_discarded(self):
        inp=example();inp['balances']['broker_net_equity']='250000';inp['balances']['broker_nav_is_net_of_margin_debt']=True
        out=module.analyze(inp)
        self.assertEqual(out['balance_sheet']['broker_net_equity_if_supplied'],'250000.00')
        self.assertEqual(out['balance_sheet']['personal_net_financial_assets'],'UNKNOWN')

    def test_broker_nav_needs_margin_liability_disclosure(self):
        inp=example();inp['balances']['broker_net_equity']='250000'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_known_components_subtotal_not_misrepresented_as_total_wealth(self):
        inp=example()
        inp['balances']['unrestricted_cash_after_earmarks']='60000'
        inp['balances']['broker_net_equity']='250000'
        inp['balances']['broker_nav_is_net_of_margin_debt']=True
        inp['balances']['car_loan_balance']='20000'
        out=module.analyze(inp)['balance_sheet']
        self.assertEqual(out['known_components_subtotal_NOT_TOTAL_NET_WORTH'],'290000.00')
        self.assertEqual(out['personal_net_financial_assets'],'UNKNOWN')

    def test_cash_balance_absent_cannot_claim_reserve_funded(self):
        a=module.analyze(example())
        self.assertIsNone(a['reserves']['core_reserve_gap'])

    def test_cash_below_reserve_blocks_investable_ceiling_even_tax_known(self):
        inp=example();inp['balances']['unrestricted_cash_after_earmarks']='10000'
        inp['operating_costs_complete']=True
        inp['outflows_complete']=True
        inp['tax']={'status':'DOCUMENTED_LIABILITY','monthly_cash_requirement':'4000',
                    'source_date':'2026-10-12','verified_rule':'Synthetic authorized verification placeholder, not a real tax rule'}
        x=module.analyze(inp)
        self.assertEqual(x['reserves']['core_reserve_gap'],'37400.00')
        self.assertIsNone(x['cashflow']['conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals'])

    def test_all_conditions_still_only_conditional_cash_ceiling(self):
        inp=example();inp['balances']['unrestricted_cash_after_earmarks']='50000'
        inp['operating_costs_complete']=True
        inp['outflows_complete']=True
        inp['tax']={'status':'DOCUMENTED_LIABILITY','monthly_cash_requirement':'4000',
                    'source_date':'2026-10-12','verified_rule':'Synthetic tax packet; validator does not determine tax'}
        x=module.analyze(inp)
        self.assertEqual(x['cashflow']['conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals'],'16050.00')
        self.assertNotIn('verified_net_monthly_investable_ceiling',x['cashflow'])

    def test_historical_leisure_not_assumed_current(self):
        inp=example();inp['outflows'][-1]['amount']='2000'
        x=module.analyze(inp)
        self.assertEqual(x['cashflow']['current_cash_outflows'],'3950.00')
        self.assertEqual(x['cashflow']['higher_lifestyle_cash_outflows_if_prior_spend_continues'],'5950.00')

    def test_prior_and_current_same_leisure_not_double_counted(self):
        inp=example()
        inp['outflows'].append({'id':'leisure_current','reference_group':'leisure',
             'category':'DISCRETIONARY','amount':'500','period':'MONTHLY',
             'currency':'USD','evidence':'CURRENT_USER_REPORTED'})
        x=module.analyze(inp)
        self.assertEqual(x['cashflow']['higher_lifestyle_cash_outflows_if_prior_spend_continues'],'4450.00')
        self.assertEqual(x['cashflow']['current_cash_outflows'],'4450.00')
        self.assertIn('PRIOR_EXPENSE_SUPERSEDED_BY_CURRENT_SAME_CATEGORY',x['review_flags'])

    def test_unreconciled_other_spending_blocks_final_surplus(self):
        inp=example();inp['balances']['unrestricted_cash_after_earmarks']='50000'
        inp['operating_costs_complete']=True
        inp['tax']={'status':'DOCUMENTED_LIABILITY','monthly_cash_requirement':'4000',
            'source_date':'2026-10-12','verified_rule':'Synthetic tax input only'}
        self.assertIsNone(module.analyze(inp)['cashflow']['conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals'])

    def test_loan_service_cash_obligation_not_all_consumption(self):
        x=module.analyze(example())
        self.assertEqual(x['cashflow']['current_contractual_debt_service'],'900.00')
        self.assertTrue(x['cashflow']['debt_payment_partly_principal_not_pure_consumption'])
        self.assertIn('DEBT_INTEREST_PRINCIPAL_SPLIT_UNKNOWN',x['review_flags'])

    def test_no_default_tax_buffer(self):
        x=module.analyze(example())
        self.assertEqual(x['tax_sensitivity_HYPOTHETICAL_NOT_LAW'],[])
        self.assertIsNone(x['cashflow']['conditional_new_long_term_cashflow_ceiling_BEFORE_other_goals'])

    def test_tax_sensitivity_explicitly_hypothetical(self):
        inp=example();inp['hypothetical_provision_rates']=['0.35']
        out=module.analyze(inp)['tax_sensitivity_HYPOTHETICAL_NOT_LAW'][0]
        self.assertEqual(out['illustrative_earmark'],'8400.00')
        self.assertEqual(out['remainder_after_earmark_and_current_outflows_BEFORE_UNKNOWN_COSTS'],'11650.00')
        self.assertTrue(out['NOT_INVESTABLE_CASH'])

    def test_payment_currency_mismatch_requires_fx(self):
        inp=example();inp['outflows'][0]['currency']='CNY'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_no_unlabelled_weekly_income(self):
        inp=example();inp['income_items'][0]['period']='WEEKLY'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_no_historical_fixed_obligation_categorized_current(self):
        inp=example();inp['outflows'][0]['evidence']='PRIOR_NOT_RECONFIRMED'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_duplicates_rejected(self):
        inp=example();inp['outflows'].append(copy.deepcopy(inp['outflows'][0]))
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_inverted_pnl_range_rejected(self):
        inp=example();inp['income_items'][1]['range']={'low':'200','high':'-200'}
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_bad_money_and_date_rejected(self):
        for bad in ['NaN','-2','1.999',1.11,True]:
            with self.subTest(bad=bad):
                inp=example();inp['income_items'][0]['amount']=bad
                with self.assertRaises(module.InputError):module.analyze(inp)
        inp=example();inp['as_of']='2026-13-01'
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_refuses_negative_expense_and_overlong_reserve(self):
        inp=example();inp['outflows'][0]['amount']='-200';
        with self.assertRaises(module.InputError):module.analyze(inp)
        inp=example();inp['reserve_months']=999
        with self.assertRaises(module.InputError):module.analyze(inp)

    def test_cli_stdin_exec_and_does_not_create_files(self):
        p=subprocess.run([sys.executable,str(SCRIPT),'--input','-'],input=json.dumps(example()),
                         text=True,capture_output=True,cwd='/tmp',timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(d['schema_version'],'5.5')
        self.assertEqual(d['cashflow']['reported_external_received_per_month_PROVISIONAL'],'24000.00')

    def test_cli_invalid_json_rejects(self):
        p=subprocess.run([sys.executable,str(SCRIPT),'--input','-'],input='not-json',text=True,capture_output=True,timeout=20)
        self.assertNotEqual(p.returncode,0)
        self.assertNotIn('real_wealth',p.stderr)

    def test_skill_requires_high_income_workflow_and_privacy(self):
        s=(SKILL/'SKILL.md').read_text()
        for term in ['high-income-crossborder-trader.md','wealth-ownership-ledger.md','5.5.0','Version integrity']:
            self.assertIn(term,s)
        w=(SKILL/'workflows/high-income-crossborder-trader.md').read_text()
        self.assertIn('BLOCK',w.upper())
        self.assertIn('two-ledger',w.lower())
        self.assertIn('simultaneous',w.lower())
        self.assertIn('30 / 90 / 365',w)
        self.assertIn('not an executable instruction',w)

    def test_original_baseline_untouched(self):
        import hashlib
        content=(ROOT/'docs/BASELINE_ORIGINAL_v0.4.md').read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(),
             '552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb')

if __name__=='__main__':unittest.main()

# These are *additional* offline structural checks, not suitability or legal tests.
class ConsultationValueQualityTests(unittest.TestCase):
    def quality_audit(self, card):
        import importlib.util
        path = SKILL/'scripts/trader_plan_quality.py'
        spec=importlib.util.spec_from_file_location('trader_quality_v55',path)
        q=importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
        return q.audit(card,module.analyze(example()))

    def good(self):
        return json.loads((SKILL/'examples/v5.5-client-value-card-SYNTHETIC.json').read_text())

    def test_good_synthetic_contract(self):
        q=self.quality_audit(self.good())
        self.assertTrue(q['ok'],q['errors'])
        self.assertIn('tax law',q['does_not_validate'])

    def test_rejects_generic_risk_only_report(self):
        report=self.good();report['user_value']=[];report['strategy_options']=[]
        q=self.quality_audit(report)
        self.assertFalse(q['ok']);self.assertGreaterEqual(len(q['errors']),2)

    def test_rejects_broker_pnl_as_cash(self):
        report=self.good();report['stocks_monthly_profit_counted_as_bank_cash']=True
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_tax_and_cash_precision_when_unknown(self):
        report=self.good();report['exact_current_tax']='8000.00';report['safe_investable_cash']='10000.00'
        q=self.quality_audit(report);self.assertFalse(q['ok']);self.assertTrue(any('tax' in x.lower() for x in q['errors']))

    def test_rejects_false_reserve_runway(self):
        report=self.good();report['liquid_runway_claimed_without_balance']=True
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_false_balance_sheet(self):
        report=self.good();report['known_personal_net_worth']='1000000.00'
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_no_joint_stress(self):
        report=self.good();report['joint_stress']['broker_drawdown_same_period']=False
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_unapproved_vault_write(self):
        report=self.good();report['memory_write_authorized']=True
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_accepts_status_update_with_explicit_document_reference(self):
        report=self.good();report['actions'][0]['status']='DOCUMENTED_EXECUTED'
        report['actions'][0]['execution_evidence_ref']='host_read_approved_document_date_2026_10'
        self.assertTrue(self.quality_audit(report)['ok'])
        report['actions'][0].pop('execution_evidence_ref')
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_old_skill_version_as_latest(self):
        report=self.good();report['skill_version_loaded']='5.1.0'
        self.assertFalse(self.quality_audit(report)['ok'])

    def test_rejects_missing_30_90_365_actions(self):
        report=self.good();report['actions']=report['actions'][:1]
        self.assertFalse(self.quality_audit(report)['ok'])
