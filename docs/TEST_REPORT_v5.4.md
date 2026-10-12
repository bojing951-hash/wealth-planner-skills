# Wealth Planner Skill v5.4.0 — executed local test report

**Date:** 2026-10-12. **Branch/source:** development snapshot deriving from local v5.3.0 (the observed public GitHub `main` was v5.2, SHA `074960d`). **Original v0.4 architectural baseline:** unchanged SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`.

## Tests actually run in this development environment

| Test | Result | Important scope |
|---|---|---|
| `python tools/check_architecture.py --strict` | **PASS**, 10/10 domains and 12/12 states | Static file/instruction checks; not professional completeness |
| `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | **46 PASS** | Legacy program unit tests |
| `python -m unittest discover -s tests -p 'test_*.py' -q` | **208 PASS** | v5, v5.2, v5.3 + **44 v5.4** synthetic behavior/value tests |
| **Total** | **254 PASS** | Does not prove real clients become wealthier |
| Synthetic five financial cases | **5/5 PASS** | Four cities + PF mock; NOT verified real tax rules |
| v5.4 fixed-return status quo vs change | **PASS** | Own cash+investments comparison; 0% / 5% hypothetical behavior example |
| v5.4 cash→investment reallocation | **PASS** | 0 new retained principal, equity upside hypothetical; equal cash/equity returns => zero new wealth |
| v5.4 observed-before/after review | **PASS** | As-of/source rules, not causal attribution |
| v5.4 value quality: good vs deliberately fabricated | **PASS** | Mathematically inconsistent and proposed-as-observed example rejected |
| v5.4 income ownership, taxes and liquidity guards | **PASS** | PF-simulated income basis rejected, provisional tax flagged, reserves protected, invalid overinvestment refused |
| Python compile | **PASS** | Syntax only |
| Real Codex tool-retrieval + report value delivery | **NOT_TESTED** | Requires actual host and authorized tools |
| Real Claude Code behavior and memory follow-up | **NOT_TESTED** | Requires real installed host and user-approved read/write |
| Blinded Skill ON vs Skill OFF with same model | **NOT_RUN** | Future independent scoring required; see `tests/skill_vs_baseline/MEASURE_VALUE_v5.4.md` |
| Observed wealth growth attributable to this Skill | **NOT_PROVEN** | Projections and before-after snapshots do not identify causality |

## Exact numeric synthetic regression

Input: CNY20k monthly net, 8k necessary spending, 7k discretionary before/4k proposed, existing 50k invested and 50k segregated emergency cash, proposed 8k invested vs before 5k, annual **assumed** portfolio return 5%, idle cash 0%, 20-year horizon, inflation 2.5%. Result excluding same protected reserve in both arms: baseline CNY2,161,687.31; intervention CNY3,379,100.77; total illustrative delta CNY1,217,413.46 = CNY720,000 newly retained money + CNY497,413.46 **hypothetical** market growth. (At 0% annual return delta = CNY720,000.)

**No user implemented this example; these numbers do NOT demonstrate any actual return from this Skill.** Even properly functioning formulas do not establish that the behavior is appropriate, feasible, or causally induced.

## Evidence and risk limitations

- No live jurisdiction tax calculators or validated long-horizon capital market calibration; 5% is **not** a forecast.
- Fixed monthly owned flows and fixed annualized return assumptions omit market path risk, uncertainty, tax drag, household utility and all outstanding liability changes.
- Changes to wage/saving and asset balances can result from unrelated market return, gifts, family events, asset transfers and tax outcomes. The review command explicitly outputs `claim_of_causal_effect: NOT_ESTABLISHED`.
- `value_quality.py` checks structure and one identity only. It is possible for a well-formatted but unsuitable plan to pass. No blinded host comparison yet.
- Unit tests performed locally on the available Python interpreter. The GitHub Actions Python 3.10–3.13 matrix will only count as tested after a verified remote run on the actual pushed commit.

**Release label:** Developer Preview. Original architecture comparison in `docs/ARCHITECTURE_ALIGNMENT_v5.4.0.md`. Remaining real-host E2E and benchmark tasks explicitly open.
