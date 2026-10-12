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
- **`behavior_value_bridge` (v5.4 substantive plans):** top-action constraint → baseline/proposed behavior → mechanism → same-assumption counterfactual → *new retained principal* versus *hypothetical market growth/reallocation* → liquidity/wellbeing cost → concrete month-to-month proof and next review. Observed differences must be distinguished from causal attribution; no action may be fabricated when maintaining the current plan is appropriate.
- `uncertainties`, `blocked_decisions`, `monitoring_triggers`, `reproducibility`: assumptions, official source snapshots, tool actions actually executed, model version, private-state policy.

Failure modes that MUST be surfaced: source unavailable, law not proven current, tax residence unknown, missing bank ownership, unstable income, unknown fees, FX date missing, unrealistic investment assumptions or uncalibrated stochastic sample fraction.

It is acceptable for a truthful partial report to say **"Cannot calculate precise local tax until X is verified"**; it is NOT acceptable to fill gaps with invented authoritative numbers.

## v5.3 mandatory professional-delivery gate (only when user requests a COMPLETE financial plan)

Follow [professional-consultation.md](professional-consultation.md). The final user-facing deliverable **MUST go beyond** the generic fields above: top 1–3 client-specific diagnostic findings + root-cause hypotheses; reconciled cash flow; goal's monthly savings requirement versus feasible amount and shortfall; at least two differentiated choices and financing/constraint trade-offs; a ranked conditional decision; **30/90/365-day** proposed tasks each with human owner, observable success check and dependencies; material unknowns and triggers for next review. Where data are missing, show a conditional partial plan plus <=5 prioritized follow-up questions—not invented full personalization.

The optional schema `../schemas/consultation-v5.3.schema.json`, synthetic example `../examples/v5.3-consultation-shenzhen-SYNTHETIC.json`, `../scripts/plan_quality.py` and `../scripts/consultation_math.py` demonstrate verifiable report format and basic math. Neither a formal-looking table nor a passing structural validator is evidence that the plan is legally/tax-wise correct, empirically calibrated or better than the base host model. No background reminders, private memory writes or transactions without relevant separately established permissions.

**v5.4 material report failure:** A plan that asserts "$X wealth created" merely from 20-year compound-interest projections, mislabels a transfer from uncommitted cash to investments as new savings, lacks user-owned behavioral actions, assumes every spending cut is beneficial, or never defines a real-world review metric is **INCOMPLETE**. The host can validate arithmetic with `scripts/value_math.py` and optional v5.4 value cards with `scripts/value_quality.py`; neither is certified advice or mandatory to answer a narrow question.

## v5.5 high-income / cross-border full-plan acceptance

When the relevant workflow triggers, require: (a) reported PF *settled bank receipts* vs own brokerage P&L separated with ownership, proof and availability flags, (b) a **dated balance sheet** showing explicit UNKNOWN net worth if NAV / liability missing (do not throw away an owned brokerage account), (c) current and historically referenced spending ranges with a confirmation flag, (d) tax/legal blocked items separated from non-tax financial planning that can proceed, (e) an obligations/tax/operating-capital/short-goal/long-term cash waterfall with **no fixed investment percentage without inputs**, (f) simultaneous stop-income + falling-NAV stress, only asserting survival when liquid assets documented, (g) concrete 30/90/365 next decisions and observed metrics.

Never call an assumed tax escrow % an applicable statutory rate. Treat brokerage withdrawal as INTERNAL TRANSFER and distinguish debt payment from consumption. Read `high-income-crossborder-trader.md` and `../references/wealth-ownership-ledger.md` as applicable. Disclose the installed skill version (GitHub version alone is insufficient) and do not promise ephemeral `/tmp` data is auto-wiped on restart.

## v5.6 complete-wealth-plan acceptance gate

A client asking for a **full lifetime / comprehensive wealth plan** needs a **Personal Wealth Master Plan**, not only the above sections. Read [personal-wealth-master-plan.md](personal-wealth-master-plan.md) and deliver its seven-section client-owned charter: whole-wealth ledger, goal/liability register, non-overlapping purpose earmarks, funding/decision policy, compared options with stress, 30/90/365 actions, review/evidence/authority. Distinguish bank and broker accounts from the conceptual funding pools; a purpose earmark is **not** an executed transfer. Use [../assets/personal-wealth-master-plan-template.md](../assets/personal-wealth-master-plan-template.md) as a format, not as a ready-made recommendation. Optional structural validation: [../scripts/master_plan_quality.py](../scripts/master_plan_quality.py); never mistake PASS for evidence of regulated suitability or real user benefit.
