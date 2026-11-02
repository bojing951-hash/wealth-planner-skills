# Personalized Budget Decision Method (v5.7) — priority order over fixed ratios

**Why this reference exists:** popular budgeting heuristics (50/30/20, "pay yourself first 10%", three-account rules) apply one ratio to every household. Real households differ in income stability, dependents, debt APR, reserve coverage, near-term goals and professional constraints — a freelance parent with 18% credit-card debt and a single salaried graduate with no debt must not receive the same split. This method replaces the fixed ratio with a **six-step priority cascade plus editable assumptions**, grounded in standard budgeting practice (needs-before-wants ordering, emergency-fund-first liquidity, high-cost-debt precedence over discretionary investing — the ordering used by U.S. CFPB / Consumer Reports style guidance and the CFP Board's cashflow-management learning objectives, cited as *ordering conventions*, not as promises of outcomes).

## Step 1 — Establish received income (bucket input, not a guess)

- Count **only money actually received** in the budgeted period. Receivables, expected year-end bonuses, undrawn business profit are *excluded* and listed in `unknowns`/`excluded_not_received`.
- Tax: if the amount is after-tax, `tax_status = KNOWN_NET`. If pre-tax or unclear, the tool keeps the gross figure and marks **every** investable amount CONDITIONAL (`UNKNOWN_TAX_CONDITIONAL`) — a budget that silently spends pre-tax money as if it were net overstates the household's real capacity.
- Multi-stream: salary + business + rental may each carry `recurring` / `one_off` flags; one-off windfalls increase *this period's* allocatable but never the "normal income" claim.
- Multi-currency: amounts in a currency other than the plan's base are converted **only** with dated FX supplied in the input; absent a dated rate the run fails closed (rejects) rather than adding apples to oranges.

## Step 2 — Set the living floor (bucket B)

`floor = contractual obligations (rent, debt service payments) + fixed necessities + variable necessities`

- Contractual obligations are facts from L1 (lease, loan schedule), not aspirations.
- Fixed necessities recur monthly at stable amounts (utilities, insurance premiums, commuting pass); variable necessities are needed but lumpy (food, medical, transport).
- The floor is a **requirement**, the first claim on income. If the floor exceeds allocatable income the status is DEFICIT — the tool reports a gap and available reserve draw, never "negative savings" or silent borrowing from other buckets.

## Step 3 — Size the safety reserve and its gap (bucket A)

`target months × floor = target amount`; `gap = target − safety-eligible cash`.

- Target months heuristic: **3** (stable income, no dependents), **6** (stable + dependents, or variable income alone), **9** (variable income + dependents). Editable; a user's explicit `reserve_months_target` is USER_INPUT and always wins.
- *Safety-eligible* cash only: current-account/deposit balances the user can actually reach. **Excluded by definition:** provident-fund simulated balances (PF), restricted investment assets, brokerage NAV, business operating reserve, unreceived amounts. Counting these is the classic phantom-reserve error.
- When eligible cash or history is unknown, the gap is reported as not computable in `unknowns` — not guessed.

## Step 4 — High-cost debt precedence

Any obligation with APR ≥ `high_cost_apr_threshold` (default 8%, editable): after floor + safety-gap fill + committed social, **extra repayment comes before capability and free social**, and financial investment is **blocked** (risk premium vs guaranteed 18% APR is a losing comparison for almost every household). Mortgage principal-vs-interest split stays an L3/net-worth question; the *cash* service amount sits inside the floor, exactly once.

## Step 5 — Necessary investment eligibility (bucket C)

- **Capability** (courses, certifications, tools, health): real spending tied to a user-declared plan; it is consumption *classified as investment in earning power*, funded as a necessity-class claim, and never counted again as financial investment.
- **Financial investment:** only when `investment_eligible` is true, no high-cost debt, reserve gap handled, and tax status known; otherwise 0 with the reason in `unknowns`.
- **Business capital:** only from a declared business plan with its operating reserve already set aside.

## Step 6 — Allocate, compare, and keep unallocated honest

Priority order: **floor → safety gap fill (default share 0.5 of the post-floor surplus, editable) → committed social → high-cost repayment → capability → free social → conditional financial investment → unallocated.**

- Free social (bucket D free part) is the **last discretionary claim**, not the first reward; committed social (family obligations, standing relationships) is preserved ahead of it — a budget that starves real obligations creates the failure modes users actually abandon.
- Unallocated is not a failure: it is the user's buffer against forecast error. The tool never forces the last cent into a bucket to look "complete".
- The output carries three comparisons — **defensive** (gap-first, free spend and risk investment closed), **balanced** (the default cascade), **status_quo** (user's reported pattern; may be flagged UNSUSTAINABLE) — and `no_change_recommended` is legitimately true when status quo sits within a 5% band of balanced.

## What this method deliberately does NOT do

- No fixed ratios anywhere; the only constants are ordering rules and editable defaults, every one surfaced in the output's assumption list with its source.
- No "normal income" or savings-retention claim from <6 months of history; 6+ recurring months yield a low/typical/high band (quartile-based), never a single blessed number.
- No double counting across layers (see the L1/L2/L3 table in `workflows/four-bucket-cashflow.md`), no market-gain or self-transfer counted as new savings, no invented tax savings, no automatic execution.
