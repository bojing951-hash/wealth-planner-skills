# Professional Financial Planning Protocol — v5.3 (HOST-driven)

## Purpose and scope

**Trigger:** The user wants a *complete* financial plan, holistic audit, "what should I do with my money", a wealth-building path or a follow-up on a prior plan. Do NOT force this protocol on a narrow definitional or arithmetic question. This is a professional **decision-support workflow**; the host researches and reasons, the Skill specifies the standard, optional tools validate numbers. No independent Agent, credential collection or autonomous financial transactions.

**Differentiation test:** If the answer could have been produced without the client's numbers and goals ("save regularly; buy diversified ETFs"), it **fails**. For each material recommendation the final deliverable must reveal (1) client-specific trigger/evidence, (2) diagnosed mechanism or constraint, (3) a quantified or bounded alternative, (4) why it ranks above other options, (5) who does what by when and how success is checked. Generic advice can be a sidebar but never the core of a comprehensive plan.

## End-to-end 6-phase consultation (mapped to original 12-state flow)

1. **Discover / contract (INTAKE → CAPABILITY_CHECK):** Reframe the client's requested outcome and scope; identify decision horizon, jurisdiction(s), income/ownership, key obligations and what advice is outside scope. Read `consultation-interview.md`. Only ask high-value questions that could change the next decision. Never demand exact account identifiers. If client requests hypothetical analysis, honor that with labels.
2. **Reconcile / diagnose (FACT_VERIFICATION → JURISDICTION_GATE → HOUSEHOLD_SOLVENCY → GOAL_AND_LIFECYCLE):** Build a dated *financial baseline*, separate money owned and received from simulated or restricted balances, and tax paid from tax unknown. Verify cash-flow arithmetic; identify solvency, debt, insurance, short-term obligations and possible conflicts with goals. Apply `diagnosis-prioritization.md`. Capture root cause, evidence, severity and materiality. If no important issue exists, say so; do not invent a deficit to fill the template.
3. **Research / challenge (EVIDENCE_RESEARCH → MACRO_SCENARIOS):** Research **only material** theory, laws, tax and slow macro variables with real host tools if available. Record applicability, effective dates and conflicts; distinguish mathematical identity, empirical observation, conditional estimate and professional judgment. Missing legal facts block definitive tax advice but need not block a clearly conditional cash-flow model.
4. **Develop alternatives (CANDIDATE_PLANS):** Produce at least TWO materially different feasible/conditional actions for a substantive plan (including status quo as a comparator when relevant). Show the decision lever and *opportunity cost*: savings, earnings, horizon, spending, debt costs, tax/legal restrictions. Do not manipulate investment-return assumptions merely to manufacture goal feasibility. A funding increase larger than current surplus requires a named source/conditional change. Rank issues and alternatives with `diagnosis-prioritization.md`.
5. **Verify / decide (DETERMINISTIC_AND_STOCHASTIC_VALIDATION → POLICY_CHECK):** Recalculate each important financial claim using the host calculator or optional `scripts/consultation_math.py`; check cash-flow conservation and comparable nominal/real units, liquidity, horizon, adverse cases, and plausible execution. Use `scripts/plan_quality.py` (optional) on a structured report to catch missing links and simple numerical inconsistencies. **Quality gate checks structure, not substantive suitability.** No uncalibrated MC probability presented as real odds. No unverified jurisdiction-specific implementation instructions.
6. **Hand off / revisit (EXPLAIN_AND_MONITOR):** Issue an **executive diagnosis** and personal master plan: ranked problems, chosen conditional policy, rejected alternative and reasons, 30/90/365-day actions with owners/metrics, verification blockers and material change triggers. Provide the next smallest reversible action. Refer for licensed tax/legal/insurance advice when needed. Only store facts, decisions and progress in optional encrypted memory **after specific opt-in / per-change approval**; never imply ongoing monitoring without a scheduler.

## Report acceptance — full-plan mode

A user-visible plan must include, in this order (labels may vary, do not overproduce irrelevant detail):

1. **One-page finding:** client aim, constraints, TOP 1–3 issues and what most improves the plan. Status of facts and tax assumptions.
2. **Reconciled financial dashboard:** currency-by-currency net realized money, essential/discretionary expense, debt payments, cash reserve, short-term liabilities and safe investable bounds; if figures unverified mark provisional.
3. **Diagnostic issue cards:** observed condition -> WHY it matters -> root cause hypothesis vs verified cause -> quantified impact/importance -> evidence + uncertainty.
4. **Goal feasibility and shortfall:** desired amount, time, starting *eligible long-term* capital (not emergency reserve), feasible monthly contribution, required contribution at stated *assumed* return, shortfall, sensitivity to lower return and income interruption where relevant.
5. **At least two defensible choices:** mechanism, approximate quantified effect, implementation cost, risk/limitations, suitability under client's constraints, reasons a proposal is deferred or rejected.
6. **Recommended sequence:** what to prioritize NOW vs later with dependency gates. Do not give a complex allocation when cash runway or legal status blocks it.
7. **30 / 90 / 365-day action plan:** observable action, named human owner, deadline/window, measurable success condition, contingencies, approval required, current status (PROPOSED vs DONE).
8. **Follow-up + audit:** what to measure, when to revisit, events triggering replan, sources actually checked, tax/year law status, unresolved questions and opt-in memory status.

**If inputs are materially missing:** ask no more than five high-impact questions at once; optionally present a **conditional** partial diagnosis using clearly labeled scenarios and the specific fields needed to finalize. Do NOT manufacture completeness by assuming net salary, jurisdiction, debt APR, age, tax treatment, risk tolerance or exact account values.

**Quality gate before sending:** for every top issue the recommendation has a traceable cause, an alternative with trade-offs, and at least one linked action. A report made of generic tips, unsourced precision, unrealistic objective probabilities or action items without verifiable outcomes fails and must be rewritten before completion. Failure of a tool is disclosed, not concealed.

## Boundaries and original architecture

This is **a cross-cutting protocol, not an eleventh domain or thirteenth state**. Primary improvement: D01, D03, D04, D09, D10. D02, D05, D06, D07 and D08 retain their constraints. The original D01–D10 and twelve states remain untouched. This protocol does not replace `SKILL.md`, original source verification gates, the existing legal-tax research process or the local memory permissions. Investment product depth remains deliberately deferred.
