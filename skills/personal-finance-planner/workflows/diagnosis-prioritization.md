# Root-cause financial diagnosis and decision prioritization — v5.3

## Issue record (required for material issues)

For each material issue, build a decision card:

- `issue_id`: stable ID (e.g. `I-01`); `observed_condition`: specific client fact / discrepancy / conditional assumption.
- `root_cause`: mechanism or **hypothesis explicitly marked not verified**; do not confuse the observed outcome with its cause.
- `mechanism`: cause -> constraint -> expected goal effect. State alternative explanations and unknowns where material.
- `evidence`: user source and as-of date, legal source with jurisdiction/effective tax year if used, or exact mathematical formula; prefer actual retrieved sources.
- `impact`: amount/range or qualitative bound; do not invent point estimates where inputs are missing.
- `urgency`, `reversibility`, `dependencies`, `user_control`: explain in prose; transparent priority, not a pseudoscientific numeric score.
- `decision`: proposed intervention + rejected/alternative strategy, trade-off, prerequisite and measurable check.

## Triage order (not every question needs all layers)

1. **Critical hard block:** negative household cash flow, overdue/high-cost debt threatening solvency, near-term bills uninsured/underfunded, legal uncertainty making a specific action impermissible. Do not recommend a risky investment as the solution to a cash-flow hole.
2. **Material feasibility gap:** target dates and amounts inconsistent with attainable savings, future large obligations ignored, reserves mistaken for investable capital. Quantify savings/horizon/income/spending levers and show a non-levered path.
3. **Efficiency leakage:** duplicated fees, avoidable high-cost borrowing, unclaimed benefits (only where verified eligible), fragmented currencies/assets; tax optimization requires current valid law and usually professional review.
4. **Long-term robustness:** single-income concentration, poor behavioral adherence, retirement withdrawal uncertainty, excessive portfolio concentration; identify but defer deep product selection unless user requests it.

Rank by **hard constraint first**, then expected importance relative to user goals, timing and confidence. A large but highly uncertain benefit should not automatically outrank a certain and urgent cash shortfall. Document the priority reason so another host can replicate the judgment.

## From issue to option

Create a cause-to-action linkage: `issue → changeable lever → financing source → time horizon → numerical effect (or justified nonnumeric bound) → risk/trade-off → next action`. Each recommended action must link to at least one ranked issue or explicitly to a preventive objective. Actions beyond monthly free cash flow are **CONDITIONAL** on a named source: higher take-home income, lower spending, change in goal/time horizon, or user-approved use of available unrestricted capital. Do not casually assume increased investment returns will finance the gap.

## Affordability and actual investability

- Net deposits minus essential/discretionary spending, contracted debt, operating/tax reserves = **conditional cash surplus**; unresolved taxes mean not a final available-to-invest number.
- Emergency reserve is for bills, not equity risk; short-term goal funds are separate from 10–30y capital. If reserves are not met, show the replenishment path before allocating long-horizon capital.
- Existing **owned cash**, investments and retirement/restricted accounts have different liquidity; `cash - required emergency reserve` is at best a conditional long-term starting amount before other goals and taxes.
- PF challenge or simulated balances are not personal capital; unrealized model gain ≠ received income. Multi-currency outputs stay separated without sourced dated FX.
- Goal shortfall at constant hypothetical return is an **identity**, not a predictive estimate; clearly label what is excluded (tax, fees if not net, shocks, income disruption, sequence effects).

## Stop conditions

Missing deadline, ownership or net income can make precision impossible. Output the best safe partial result, identify the missing facts and the narrowest next step. Do not write "financially healthy" based on one unverified cashflow ratio. Do not turn absence of identifiable problems into an invented negative diagnosis.
