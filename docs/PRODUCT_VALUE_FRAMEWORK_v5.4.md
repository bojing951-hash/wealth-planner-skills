# Wealth Planner v5.4 — measurable decision value, not finance platitudes

## Product acceptance objective

The differentiator between **a generic model response** and Wealth Planner is not how many theory citations appear, but whether it diagnoses a client's binding constraint, compares defensible alternatives and changes real human decisions under legal/liquidity/lifecycle constraints. **Value can be greater financial safety or an appropriate decision to maintain the current plan, not always higher investment return.**

A good full-plan deliverable has a measurable *Behavior → Mechanism → Value → Proof* card for each substantive recommendation. The card includes status quo, proposed action, who/when, plausible owner cash flow or nonmonetary risk benefit, at least one alternative and tradeoff, implementation state, observable metric and follow-up cadence. The consequence may be contingent on evidence/authorization and not personally suitable unless material gaps are resolved.

### Evaluation categories

1. **Diagnostic insight:** what limiting constraint was found that a generic answer might miss?
2. **Counterfactual impact:** what changes if the user does nothing? Show comparable budgets and assumptions.
3. **Correct mathematics:** cash-to-investment transfers are reallocation, not new wealth; new funds vs conditional investment growth separated.
4. **Decision quality:** covers opportunity cost, wellbeing, hidden obligations and personal risk capacity; refusing a dubious proposal is allowed.
5. **Execution quality:** observable owner/actions and milestones, not "improve money habits."
6. **Evidence integrity:** dated primary legal rules when needed, reported vs verified, scenario vs observed, no future model treated as income.
7. **Feedback:** at subsequent review measure observed income/spend/asset changes and forecast error without claiming causality from correlations.

The Skill does **not** estimate causal financial value without credible comparison design. It does not claim the classic behavioral-finance literature guarantees user adherence, nor that a fixed 5% return is forecast. Investment-product depth intentionally unchanged in this version.

### Responsibilities

Codex/Claude host researches, reasons, compares and produces client report using available tools. Skill instructions encode diagnostic and value method; optional standard-library-only `value_math.py` verifies matched future-value scenarios and `value_quality.py` audits structured value cards. All personal memory remains opt-in L1/L2 (no writes on install), and no autonomous broker/tax or finance actions.

**Real Skill ON versus Skill OFF blinded host benchmark:** `tests/skill_vs_baseline/MEASURE_VALUE_v5.4.md`; status **NOT_RUN** until paired sessions have been scored. Static gates/quality checks do not show end-user gains.
