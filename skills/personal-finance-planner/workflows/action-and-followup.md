# Implementable financial plan, human handoff and follow-up — v5.3

## Action register and owner

Every action should include: `action_id`, related `issue_id`, actual owner (`USER` / `LICENSED_PROFESSIONAL` / `HOST_RESEARCH_ONLY`), horizon `D30`, `D90` or `D365`, concrete action, objectively observable success test, budget or cost if applicable, prerequisites/approvals, and status `PROPOSED` / `USER_CONFIRMED` / `DONE` / `BLOCKED` / `DEFERRED`. **Never assign `DONE` unless the user or an authorized source confirms completion.** A researched idea is not a completed tax change, asset purchase or cash transfer.

- **30 days:** financial fact reconciliation, resolve high-risk unknowns, implement reversible budgeting/cash-reserve choices approved by the user; next measurable milestone.
- **90 days:** verify whether reserve/debt/goal changes happened, update actual income-spend, review legal professional handoffs, check whether choices are affordable.
- **365 days:** annual tax-year/life-event review, compare actual financial progress to prior *dated* assumptions, update long-horizon goals and financial policy rather than daily market tactical adjustments.

Never preallocate money via an unauthorized automated transfer, invest a model projection, file a tax return, or create an account. If the host has no timer, describe the review cadence as a **user calendar recommendation**, not an active automated monitor.

## Persistence and truthful continuity

The v5.2 optional local encrypted vault may store only permitted **brief** financial facts, goals, decisions and reviews; don't store a whole bank statement or long free-text report. L1 is required before each private read; every write needs a **separate L2 approval of the exact preview** (see `workflows/local-memory.md`). A summary in chat is not authorization to write memory. Do not create user data folders within the public Skill/Git repo.

At follow-up, compare last **reported** state with newly confirmed state. State whether the action was executed, the expected and realized differences, alternate explanations and whether the original financial recommendation should be revised. Recompute any formula whose inputs changed. Record unsuccessful forecasts; do not rewrite history. If prior authorized state is unavailable, report no previous audit rather than invent one.

## Client-facing style

Lead with highest-impact finding and the **next actionable decision**, not an essay about investing. Separate: *Now / conditional / deferred / refer to specialist*. Prefer numbers with one visible derivation to pages of generic warnings. Keep all important unsupported conclusions explicitly provisional.
