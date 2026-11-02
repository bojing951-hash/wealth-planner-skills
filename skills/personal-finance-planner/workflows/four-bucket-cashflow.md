# Four-Bucket Cashflow System (v5.7) — monthly budget as cashflow allocation

**Owner: host Agent.** This workflow turns one period's *received* income into a priority-ordered allocation across four buckets — **A. Safety & savings, B. Living (necessary), C. Necessary investment, D. Social & discretionary** — with exact Decimal conservation and no fixed ratios. It is a budgeting layer for D03 cashflow and D06 lifestyle, NOT a new Agent, not a monitoring service, and never an instruction to move money, place orders or automate anything. It produces a plan the user executes themselves.

## When to load this workflow (progressive disclosure)

Load **only** this file (plus the calculator below) when the request is about the *current month's money*: 预算管理 / 日常消费控制 / 收入分配 / 储蓄计划 / 四账户管理 / "这个月该花多少钱" / 不稳定收入怎么安排 / 财务月度复盘. Do **not** load the Master Plan (L3) or portfolio workflows for a simple budget question; a full-net-worth review (D01–D10) still routes through the v0.4 ten-domain process.

## Three layers — never sum them (anti-double-count)

| Layer | Question | Source | Aggregation rule |
|---|---|---|---|
| **L1 fact ledger** | What actually exists / happened? | Dated statements, balances, actual spend | Facts only; no goals mixed in |
| **L2 four-bucket budget** (this workflow) | How do we allocate *this period's* received income? | L1 facts + user preferences | `allocatable = Σ buckets + unallocated` — exact, every time |
| **L3 purpose pool / Master Plan** (v5.6) | What are these assets *for*, long-term? | `personal-wealth-master-plan` workflow | Referenced by name (emergency_reserve → bucket A funding source); **never re-added** into L2 amounts |

Counting an emergency fund once inside bucket A's *existing eligible cash* and again in an L3 purpose pool is the classic double count. L2 computes **this period's additions**; existing balances enter only as the starting point for gap math.

## The six-step decision method (summary; full version in `references/budget-decision-method.md`)

1. **Received income** — only money actually received this period, after tax where known. Multi-stream and multi-currency allowed with dated FX; unreceived receivables are excluded and listed.
2. **Living floor** — contractual obligations (rent, debt service) + fixed necessities + variable necessities. This is bucket B's claim, a *requirement*, not a preference.
3. **Reserve gap** — target months (heuristic: 3 stable, 6 variable or dependents, 9 variable+dependents; user override always wins) × floor, minus *safety-eligible* cash only (no PF simulated funds, no restricted investments, no unreceived amounts). Gap drives bucket A.
4. **High-cost debt check** — any APR ≥ 8% (editable) blocks bucket C financial investment; surplus after floor + safety + committed social goes to extra repayment first.
5. **Investment eligibility & priority** — capability (real spending, user-declared plans) is a *necessity-class* claim; financial investment is *conditional* — zero when ineligible, liquidity-first, or tax unknown.
6. **Allocate, compare, keep unallocated honest** — priority order: living floor → safety gap fill → committed social → high-cost repayment → capability → free social → conditional financial investment. Everything unclaimed stays `unallocated` (the user's buffer), shown alongside defensive/balanced/status-quo comparisons. `no_change_recommended` may honestly be `true` within a 5% band.

## Deterministic calculator (host-invoked, offline, stdlib only)

- `scripts/four_bucket_math.py plan --input <PRIVATE_JSON|->` — full allocation; `--format md` for a readable table. Exit 0 = OK/CONDITIONAL, 2 = DEFICIT (gap reported, never "negative savings"), 3 = invalid input.
- `scripts/four_bucket_math.py review --input <PRIVATE_JSON|->` — month-end复盘: planned-vs-actual variance, **net new savings** (income − consumption), internal-transfer exclusion, and the `REALLOCATION_NOT_NEW_SAVINGS` flag when invested amounts exceed retained cash.
- Schemas: `schemas/fourbucket-input-v5.7.schema.json`, `schemas/fourbucket-plan-v5.7.schema.json`. Examples under `examples/v5.7-*-SYNTHETIC.json` are synthetic — **never** put real personal data in the repo; prefer `--input -` (stdin) so private figures stay out of the working directory.

Every output carries: `allocatable.tax_status` (KNOWN_NET vs UNKNOWN_TAX_CONDITIONAL), `income_basis.classification` (STABLE_SALARY / VARIABLE_HISTORY with low-typical-high band / INSUFFICIENT_HISTORY / SINGLE_PERIOD), exact `conservation`, assumption list with USER_INPUT / HEURISTIC_EDITABLE / CALCULATED sources, and an `unknowns` section. Two months of history never produces a "normal income" or retention-rate claim.

## Output statuses and what the host must do

- **OK** — present the allocation, comparisons and unallocated; ask which assumption the user wants to edit (any HEURISTIC_EDITABLE value).
- **CONDITIONAL** — same, plus read the `unknowns` aloud; investable amounts stay conditional until tax / history / balances are known.
- **DEFICIT** — the floor exceeds allocatable income. Report the gap and optional reserve draw; do **not** fabricate negative savings or silently borrow from other buckets. This is a spending-structure or income problem, not an allocation problem.

## Behavioral contract

No automatic transfers, orders, or scheduled jobs. The plan is a proposal with explicit assumptions; the user owns every execution decision. Monthly review re-runs `review`, comparing planned vs actual per bucket and reporting net new savings — transfers between own accounts and market gains are never savings. If the user's reported current pattern already sums within the allocatable band, `no_change_recommended: true` is a legitimate, honest answer.
