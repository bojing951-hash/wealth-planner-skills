# Claude Code integration — Wealth Planner Skill v5.3 Developer Preview

Place the entire `skills/personal-finance-planner/` directory under a Claude Code-supported user (`~/.claude/skills/personal-finance-planner/`) or project Skill location. Check documentation for your actual Claude Code version and available permissions.

**The host executes; the Skill advises.** For a comprehensive financial planning prompt, Claude should load `SKILL.md` and `workflows/professional-consultation.md`, then perform scoped client interview, root-cause diagnosis, two or more materially different decisions, conditional financial math, 30/90/365-day actionable handoff and on-demand review. It should NOT blindly summarize the theory reference directory as its deliverable.

Example synthetic client prompt:

> Use `personal-finance-planner` for a **full professional financial diagnosis** of a 28-year-old in Shenzhen: hypothetical net income CNY20,000/month, essential expenses CNY8,000, discretionary CNY3,000, no debts, unrestricted cash CNY100,000, goal CNY1 million in five years. What is the true constraint? Compare keeping the timeline vs extending it, including emergency liquidity, math assumptions and observable next actions.

If authorized, Claude can run bundled `scripts/consultation_math.py` and `scripts/plan_quality.py` for arithmetic/quality checks. These scripts do **not** constitute an independent model or legal/financial consultant. No network/account tool permission, data persistence, trading or recurring scheduling is granted by installing a Skill.

True Claude Code host E2E and blind skill-vs-baseline evaluation: **NOT_TESTED** until actually run and documented.
