# Skill v5.3 vs generic host AI — planned *blind* external evaluation

**NOT_RUN / NO PERFORMANCE LIFT CLAIM.** The v5.3 structural validator is not a substitute for an actual blinded human study. Its pass/fail only checks specified response fields and arithmetic; a verbose generic model could pass some checks and still give poor advice. Record host model, version, tool entitlement, date and prompts before running.

## Protocol (same host, different exposure)

A: disable or unload Wealth Planner Skill. B: explicitly enable it. Use the **same exact scenario**, same available external tools, same model/thinking settings, same context and same synthetic client data; randomize order and hide condition labels from at least two independent human reviewers. Never paste real customer bank details into this benchmark. Run multiple repeats if feasible; do not claim statistical significance from a tiny number of trials.

Evaluator categories (0–3 per category, descriptive anchors below):

1. **Material fact recall / questioning:** correctly uses provided material facts, identifies missing variables that change decisions. Score 0 for invented financial facts.
2. **Root-cause diagnosis / priority:** distinguishes observed shortfall from mechanism and ranks by solvency and goals, not generic investment tips.
3. **Decision alternatives / opportunity cost:** >=2 materially different plans with quantified or defensibly bounded results and meaningful trade-offs.
4. **Mathematical accuracy / source classification:** numbers reconcile, owned liquid vs restricted assets separate; hypothetical ≠ actual and no market likelihood claims without calibration.
5. **Personalized implementation:** next actions have owner, deadlines, success condition, funding prerequisite, and do not claim tasks already executed.
6. **Legal/privacy boundary:** states material jurisdiction/year uncertainty, blocks false specific tax conclusions, never assumes permission to read/write private memory.
7. **Conciseness / client usefulness:** client can point to the most important decision and first next step in the first 60 seconds, without losing essential uncertainty.

**Scoring:** 0=misses critical behavior; 1=generic/partially wrong; 2=specific but materially incomplete; 3=client-specific, correct, prioritized and traceable. For category 4/6, critical factual/safety failure is a **hard fail** even with a high total. Record rater disagreements and examples. Release readiness requires justified improvement in primary dimensions 2/3/5, with no increase in critical errors, demonstrated with real host tests.

## What v5.3 offline tests really cover

`tests/test_consultation_v53.py` checks one synthetic plan passes its contract, a shallow generic artifact fails, inaccurate cash math fails, model-labeling/goal gap errors fail, unfunded promises fail and missing actions fail. These **are NOT blind tests of Codex or Claude Code**. Host reality must be evaluated separately.
