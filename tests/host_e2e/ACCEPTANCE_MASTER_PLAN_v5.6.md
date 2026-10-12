# Host real-use acceptance for v5.6 (NOT_TESTED until separately executed)

## Objective

Test whether Codex and Claude Code can both **discover the installed v5.6 Skill**, search appropriate official sources where needed, and deliver a complete Personal Wealth Master Plan rather than a generic advice checklist. The installed local `SKILL.md` version and path must be printed or stated; do not infer version from GitHub.

## Case A — synthetic Shenzhen 20k income

- Use `examples/v5.6-salary-shenzhen-SYNTHETIC.json` with explicit hypothetical framing.
- Require real owned-asset ledger (100k cash once), liabilities, 1m/10y goal, 48k illustrative cash earmark + 52k unassigned, no duplicate assets, 2 meaningful policies, human status, 30/90/365 measurable steps.
- Reject if the plan silently assumes taxes/current rules, claims 100k invested, implies the user already executed any action, or skips opportunity costs/life satisfaction.

## Case B — synthetic cross-border PF + brokerage income

- Use `examples/v5.6-high-income-trader-SYNTHETIC.json`. Income and profit are NOT real records.
- Verify that brokerage NAV remains UNKNOWN until actually supplied; P&L is not independently owned capital to add to NAV; PF simulated nominal account is not personal wealth.
- Require separate conceptual pools for household liquidity, unresolved tax, operating capital and long-term living; no money transfer by pool labeling.
- If law lookup is enabled, capture actually opened official sources with tax year and retrieval date; if not, mark NOT_RETRIEVED and still generate conditional wealth policy.
- Run combined income-stop / broker drawdown hypothetical, 2 alternative policies, no forced 30–50% rule.

## Case C — second-session or second-host review (requires opt-in)

- Ask explicit L1 read consent, and separate L2 consent for any vault update, or run stateless if not authorized.
- Compare old/user-reported vs new/verified net wealth and decisions, no made-up new savings from internal transfers.
- Never claim ongoing background monitor unless a real authorized scheduler was created.

## Comparison with a plain model (still unrun)

Use same AI model, same prompts, source permissions and data; blind-score: unique asset reconciliation, specific non-overlapping funding policy, goal horizon, cash/legal blocking correctness, meaningful 2 options, precise owner/approval/metric, and no product hallucination. Score by qualified reviewers; do not assert performance advantage before measured trials.

**Record actual tool log, client version, model, test date, policy compliance and failures after running. This file is a checklist, not evidence of any real completed test.**
