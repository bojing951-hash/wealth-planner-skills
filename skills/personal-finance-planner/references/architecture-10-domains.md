# Ten-domain reference — original v0.4 architecture (normative)

This is a **faithful implementation index**, not a claim that any domain is production-ready. Full governing baseline is `docs/BASELINE_ORIGINAL_v0.4.md` in the GitHub repository. The Skill is portable without it because the relevant scope and gates are repeated here.

| ID | Domain | Key inputs | Required decision/output | Important limit |
|---|---|---|---|---|
| D01 | `profile_and_data_quality` | as-of, currency, residency claims, ownership and source of income, portfolio holdings | Verified/user-reported/assumed/unknown fact record, data gaps | simulated PF balances and nonowned account capital never increase personal wealth |
| D02 | `jurisdiction_and_compliance` | tax residence, citizenship, country/state/city, days, source/activity/bank/asset, tax year | jurisdiction map and legal-tax issues; allow/needs review/blocked | no invented tax amounts; no "bank in Hong Kong means no tax" |
| D03 | `personal_cashflow` | owned collected income, expenses, tax provision, loans, reserves | cash flow, runway, liquidity, investable surplus after obligations | gross receipts are not net investable cash |
| D04 | `life_cycle_and_goals` | age, family, housing, retirement, care, education, currency, dates | liability and goal schedule by required cash date; funding shortfall | short-term obligations should not mechanically be placed in long-duration equities |
| D05 | `economics_and_evidence` | mathematical models, primary studies, books, behavioral findings, law | claim-level evidence ratings, theory applicability and unresolved tensions | published philosophy is not proof; current law must be official and effective |
| D06 | `long_term_macro` | currency-matched real rates, inflation, valuation, productivity, returns, sources | time-stamped observations vs 5–30y assumptions and stress conditions | today's US TIPS real yield is not RMB risk-free return; news is not an allocation signal |
| D07 | `investment_policy` | permitted securities, horizon, tax, fees, cash safety, risk budget | multiple asset-policy candidates, cost and rebalancing rationale | no trade automation; asset weights require stated investor conditions |
| D08 | `simulation_and_risk` | model parameters, joint market/income shocks, cashflow timing | reproducible math, real wealth ranges, loss/survival checks, conditional MC | no calibrated objective probability without model/data validation |
| D09 | `decision_and_execution` | candidates, constraints, user goals, evidence status | exclude illegal/insolvent options, compare remaining, seek approvals | legal/financial safety gates are not traded against forecast return |
| D10 | `audit_and_monitoring` | snapshots, citations, effective dates, assumptions, version | report provenance, unresolved issues, change triggers and re-evaluation plan | no private state persistence or recurring execution without consent and host capability |

## Reconciliation priority

1. Applicable law + authorization; if unresolved, **block** legally actionable conclusion.
2. Liquidity, household survival, debt and essential protection.
3. Liabilities and time horizon; separate 0–3y goals from 10–30y allocations.
4. Evidence applicability, model limitations and data quality.
5. Tax/fee/inflation-adjusted risk-reward, simplicity, behavioral feasibility.
6. Present multiple defensible choices with trade-offs; users own final decision.

**Runtime boundary:** Host Agent = thinking, external tool calls, file/simulation execution, final report. Skill = policy and methods. Bundled Python = optional deterministic check. External APIs and legal sources = require actual tools + authorization. Persisted state/timer = only if provided and enabled separately.
