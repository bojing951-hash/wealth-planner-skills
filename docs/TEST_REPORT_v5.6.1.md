# v5.6.1 — executed offline test and truthful completion log

**Date:** 2026-10-12 (test environment); **scope:** portable Skill v5.6.1 integrity patch based on public GitHub `main` SHA `f7d64e24c5ef77bc4752e707c12523659a13e811` plus user-supplied local archive. The archive's original README is *not the current GitHub product README*, so the overlay deliberately preserves and minimally updates the actual GitHub README when applied. GitHub cannot be pushed from this read-only connection.

## Execution categories

| Category | Meaning | Status |
|---|---|---|
| Original v0.4 architecture source SHA | Unmodified `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb` | PASS |
| `tools/check_architecture.py --strict` | Ten domains, twelve states, release comparison, Skill-First invariants | PASS (structure) |
| Legacy tests | `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | PASS |
| Repo regression + new v5.6.1 | `python -m unittest discover -s tests -p 'test_*.py' -q` | PASS |
| Synthetic four cities + cross-border PF smoke | Existing CLI examples; no actual bank/account access | PASS (offline synthetic) |
| v5.6 Master Plan positive/negative JSON fixtures | CLI static checks, plus new v5.6.1 invalid enums/false reconciliation/false approval | PASS (offline synthetic) |
| Synthetic blinded-score aggregator | `evaluate_blind.py` reads **invented** reviewer scores | PASS (math only; NOT outcome study) |
| SHA256 content manifest | Regenerate/verify on this local source archive; remote README differs | PASS (local only) |
| Actual installed Codex executing Skill to client-facing report | No Codex executable / authenticated host in current build | **NOT_TESTED** |
| Actual installed Claude Code executing Skill | No Claude Code executable / authenticated host | **NOT_TESTED** |
| Controlled same-model, same-tool Skill-vs-plain-AI blind outcome test | Cannot launch isolated authenticated identical hosts with this build | **NOT_RUN** |
| Expert financial planner/tax counsel independent review | No licensed expert retained | **NOT_RUN** |
| GitHub PR merge and post-merge CI for v5.6.1 | GitHub connection is read-only (pull=true, push=false) | **NOT_PUBLISHED** |

**Why a passing `master_plan_quality.py` isn't a financial guarantee:** this optional code validates a local JSON contract and certain accounting/permission contradictions. It does not independently prove completeness of client statements, legal classification of income, suitability, actual user assent, causal wealth creation or forecasting performance.

## Specific v5.6 shortcomings fixed

1. Invalid `net_worth_status` enums no longer pass unnoticed.
2. `asset_completeness=RECONCILED` while own brokerage NAV and vehicle-loan balance are unknown is rejected even if a `reconciliation_reference` text is supplied.
3. Valid numeric balances, user-confirmed account inventory and explicit reference are now required **before a static completeness claim can pass**, although this is not proof the account information is true.
4. `USER_APPROVED` status is rejected without a `plan_approval_reference`. Such text is not a permission grant; host must obtain approval in real conversation.
5. Schema validations work with Python standard library (no `jsonschema` runtime requirement) across required fields, enum domains, amount strings, dates, nested types and extra properties. Unsupported schema keywords trigger fail-closed diagnostics; invalid nested types no longer crash the validator.

## Real-host run kit

`tests/host_e2e/ACCEPTANCE_MASTER_PLAN_v5.6.1.md` provides exact actual Codex/Claude acceptance conditions. `tests/skill_vs_baseline/AB_PROTOCOL_v561.md` provides a controlled same-model no-Skill versus Skill study with 10 professional score dimensions, critical safety errors and conditional human-entered score aggregation; sample data are **fictional fixture values**. Until those real executions are independently documented, no claim of greater wealth/quality attributable to this Skill can be made.

## Known residual weaknesses

- Static references do not authenticate human approval or historical bank/stock values. A missing real-world account can remain unknown to the program even if the user marks the inventory 'complete'.
- No regulated tax calculation, funds transfer, licensed securities recommendation or fully calibrated asset-return model was added. Unknown tax blocks specific tax amounts, not all nontax planning.
- `.git` branch protection, host integration, macOS/Windows ACL validation, long-running task scheduler and real client feedback remain out of scope and untested.
- The remote `main` version remains v5.6.0 until the user's authorized PR is applied and merged; neither ZIP construction nor synthetic test results are evidence of remote publication.

**Repeatable release commands** and results must be recorded after applying this overlay to the **actual** repository checkout and merging:

```bash
python tools/check_architecture.py --strict
python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q
python -m unittest discover -s tests -p 'test_*.py' -q
python tools/manifest.py --write
python tools/manifest.py --verify
```
