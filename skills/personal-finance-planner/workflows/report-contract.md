# Reporting contract — claims, calculations, risks, continuity

For a complete financial plan, include these headings or machine-readable equivalents; for a narrow question mark irrelevant sections `NOT_APPLICABLE` and any unverified section `NOT_VERIFIED`.

- `run_id`, `as_of`, `skill_version`, chosen jurisdictions and relevant tax year, model version and data date.
- `user_facts` with status: `VERIFIED`, `USER_REPORTED`, `ASSUMED`, `UNKNOWN`; show currencies separately and distinguish collected vs projected income.
- `jurisdiction_map` and `legal_tax_review`: operative primary law URLs actually **opened** (or `NOT_RETRIEVED`); applicability and effective date, exceptions and professional referral if needed.
- `financial_health`: realized cash income, known taxes vs reserved unknown taxes, essential/discretionary expense, loans, runway, pension vs liquid owned money, investable monthly only after reserves.
- `asset_liability_schedule`: future goals in spending currency with horizon, expected available funding and shortfall.
- `capital_market_assumptions`: observed vs research estimate vs scenario parameter; currency, horizon, period, publication/retrieval date and uncertainty.
- `scenarios`: deterministic and conditional stressed outcomes; no model probability without explicit calibration/validation; real/nominal and costs distinguished.
- `policy_options`: multiple viable candidate budgets/investment policies where useful, costs, liquidity, risks, permitted investment channels and need for user approval.
- `evidence_and_conflicts`: relevant mathematical/emprical/historical/book claims, limits, conditional conflicts, undecided questions.
- `action_plan`: reversible research and budgeting steps, approvals and handoff. No autonomous L3 money/tax/broker actions.
- `uncertainties`, `blocked_decisions`, `monitoring_triggers`, `reproducibility`: assumptions, official source snapshots, tool actions actually executed, model version, private-state policy.

Failure modes that MUST be surfaced: source unavailable, law not proven current, tax residence unknown, missing bank ownership, unstable income, unknown fees, FX date missing, unrealistic investment assumptions or uncalibrated stochastic sample fraction.

It is acceptable for a truthful partial report to say **"Cannot calculate precise local tax until X is verified"**; it is NOT acceptable to fill gaps with invented authoritative numbers.
