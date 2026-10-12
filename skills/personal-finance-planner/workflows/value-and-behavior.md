# Financial Planning Value Protocol (v5.4) — from advice to behavior to outcomes

**Owner: host Agent.** This guide is an execution contract for a professional financial plan and subsequent review, NOT a new Agent, monitoring service, investment optimizer or demand to maximize savings at the expense of wellbeing. Cross-cutting D03/D04/D08/D09/D10, subordinate to the original v0.4 ten domains and twelve-state process.

## Success criterion

A good financial plan creates **decision value** even if it recommends *no change*: clarify true constraints, compare feasible options, protect essential living needs, reveal trade-offs, and help the user choose and execute a reversible action. **Do not confuse model projection with wealth already created.** Use a counterfactual with the same assets, currency, time horizon and market assumptions; isolate what comes from additional retained earnings or lower consumption versus what comes from investing those sums.

A substantive recommendation must complete **all seven links**:

| Link | Question | Required evidence/output |
|---|---|---|
| 1. Client-specific constraint | What's actually holding this client back? | Dated financial snapshot, level of certainty, constraints, not a generic finance quote |
| 2. Decision lever | Exactly what can the user choose/change? | Baseline behavior, proposed behavior, amounts, authorization/eligibility |
| 3. Mechanism | What financial channel does that change affect? | Net retained cash, debt cost, safety reserve, tax/fee *conditional* saving, goal funding, life quality |
| 4. Counterfactual | What would happen **without** the intervention? | Same inflation/return/fees/tax assumptions; include **status quo** with cash alongside investments |
| 5. Incremental value | What actually differs? | Extra contributed *new* funds vs assumed growth/reallocation vs avoided cost vs protection; no double count |
| 6. Execution | What concrete user behavior changes? | 30/90/365 action, owner, preconditions, consent, success metric, fallback |
| 7. Observation/review | Did the behavior occur and did outcomes change? | Implementation status, period-aligned data, actual-vs-forecast, external confounders, freshness |

## Financial value classification (not every benefit is a higher portfolio value)

1. **Cash flow / principal formation:** net income less actual consumption and other outflows increases assets; saving an extra 3,000 CNY/month means 36,000 CNY of additional retained funds in one *full* year **only if implemented and maintained**. A transfer from idle cash to a brokerage account is **NOT** a new contribution to household net worth.
2. **Potential compounding / opportunity cost:** only the *additional* invested capital earns projected incremental returns, and trading cash for equities also raises market risk. Show 0% and conservative/downside scenarios when material; hypothetical return is not a guarantee.
3. **Cost / debt / tax efficiency:** quantify verified loan interest, real after-fee expense differentials or lawful, applicable after-tax savings only with matched date, source, rates, taxes and costs. Mortgage principal repayments reclassify wealth, not simply consumption; avoid counting reductions in loan interest twice. No invented tax savings.
4. **Liquidity and risk management:** improved emergency runway and reduced probability *of forced liquidation* may be valuable even if expected future net worth falls. Do **not** invent avoided-loss amounts/probabilities without calibrated evidence and a reasonable counterfactual.
5. **Goal funding and wellbeing:** shorter shortfall/greater liability coverage, reduced financial stress, more time, protected lifestyle; treat subjective changes as an explicit user preference or qualitative observation, not monetized without evidence.
6. **Behavioral implementation:** automatic savings, pay-rise escalation, low-frequency review and spending friction can improve adherence. Research illustrates mechanisms; effectiveness for *this particular user* remains to be observed.

## Critical accounting and causality checks

- **Same scope:** baseline and proposal must use same currency, starting personally owned *eligible* financial assets, month timing and assumed returns; official tax/fee rules must match jurisdiction and tax year. No income jump from PF simulated or unreceived profit.
- **Compare all modeled assets:** investments + non-reserved cash. Holding 3,000 CNY in a deposit and placing that same 3,000 into equities does not create another 3,000 of new household principal. Different *modeled returns* may affect projected wealth, with additional downside risk.
- **No double counting:** incremental unconsumed cash (= delta net owned income − delta necessary/discretionary expenditure − delta other cash outflows); financial value bridge = new retained principal − any upfront outlay + modeled growth/reallocation residual. If reducing consumption has a cost to life satisfaction, record the cost even if not readily monetized.
- **Protect restricted money:** emergency/short-goal funds remain segregated, never treated as investable; debt principal needs its own liability amortization schedule. If reserve is below target or essential costs cannot be paid, block an unconditional invest recommendation. Compute the alternative as CONDITIONAL only if useful.
- **No automatic causal attribution:** merely observing that savings increased after advice does not establish that the Skill *caused* the increase. Pay rises, refunds, inheritance, business losses, timing and market returns are confounders. Classify *hypothetical / user-reported observed difference / documented observed difference / rigorous attributed effect* separately; the bundled `review` utility **never** claims causal proof.
- **No manufactured changes:** if a client's current arrangements are defensible, issue a *maintain + monitor* plan. Do not create spurious spending cuts or active investments to appear valuable.
- **No automatic actions:** no money moves, brokerage orders, filings, outbound private data or new background jobs. Run read/write memory only with relevant L1/L2 consent. Store brief behavior action ID and outcome summary in the opt-in vault's allowed plan/decision fields; no full financial feeds.

## Required value card in a comprehensive client report

For **each top-priority recommendation** report, in compact form:

> **Constraint:** personal financial issue with source/status.  **Behavior:** baseline → proposed; human owner, approval and date. **Mechanism:** cash, taxes, fees, debt, liquidity, goal coverage or wellbeing. **Counterfactual:** what happens without action, holding economic assumptions constant. **Projected value:** newly retained principal, assumed returns/reallocation effect, risk/wellbeing trade-off, and when effects would be realized. **Proof:** status PROPOSED/CONFIRMED/EXECUTED/OBSERVED, concrete metric/data source, monthly/quarterly review. **Alternative:** no change or differently constrained solution.

For the illustrative 20,000 CNY/month example: reducing *truly low-value* discretionary spend by 3,000 while preserving needs could retain **720,000 CNY** of additional principal over 240 months (3,000 × 240); if assumed 5% effective annual growth applies to monthly new investments, the additional modeled portfolio growth is separate. Do not assume lifestyle-neutral consumption cuts are possible for everyone. When comparing 5,000/month invested to 8,000/month, explicitly check if the extra 3,000 comes from *lower consumption* or merely *formerly retained cash* — those are different financial mechanisms.

A complete plan should show: **(a) value that is mathematically possible; (b) behavior that has been authorized and done; (c) financial effects actually observed; (d) what remains unproved.** It must not label (a) as (c).

## Optional host-invoked deterministic tools

- `scripts/value_math.py project --input <PRIVATE_JSON>`: compare status quo vs proposed **modeled liquid financial assets**, splitting incremental unconsumed cashflow from conditional growth/reallocation. Same hypothetical asset returns, inflation and initial assets. NEVER a real-world return estimate.
- `scripts/value_math.py review --input <PRIVATE_JSON>`: calculate period-aligned *observed input differences*. No causal identification; account for pay change, timing, expenses, hidden debts and market gains in professional interpretation.
- `scripts/value_quality.py --input <PRIVATE_VALUE_CARD_JSON>`: checks that every proposed change has an intervention, baseline, plausible financial mechanism, projected-vs-observed labels, observable metric, risk/wellbeing constraint, and next action. Failing an audit blocks calling the plan a **complete** professional report; passing is NOT proof of financial suitability.

Use them only if the host has an authorized local execution tool. Otherwise perform a transparent smaller-scope analysis using available tools; never claim scripts ran if they did not. Never write private financial inputs into the Skill install directory, public repo, shell history or logs.

## Follow-up questions that expose real utility

1. What recommendations were *implemented* versus merely proposed? Who confirmed, and on what date?
2. How did net owned income, genuine consumption, tax reserves, debt obligations and net retained cash change? Was income volatility or a one-time event the cause?
3. How did owned **total** liquid assets (investment + cash), outstanding liabilities and goal coverage change after correcting for transfers and ownership?
4. Are projections more/less feasible under updated but consistent assumptions? What was the forecast error? Which uncertainty dominates?
5. Did liquidity, financial stress, time commitment or quality of life improve, deteriorate or remain unknown?
6. What is the **smallest next safe decision**? If nothing needs to change, document why and schedule review *only where the host actually has scheduling tools/authorization*.

## Evaluation against the unmodified host

See `tests/skill_vs_baseline/MEASURE_VALUE_v5.4.md` for an independent blinded protocol: same underlying model, same research/file tools and synthetic cases, Skill ON/OFF, assess concrete decision value, math correctness, false precision, behavioral traceability and user wellbeing. The benchmark remains **NOT_RUN** until real paired sessions and independent scoring occur.
