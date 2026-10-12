# Wealth Planner 5.6.1: targeted validator hotfix, not a new Agent

The current project is a **Skill-First Developer Preview**. The **original v0.4 plan** is the only architecture baseline. This patch does not claim that investment or tax services are complete.

## Why this patch exists

v5.6's optional `master_plan_quality.py` accepted a `balance_sheet.net_worth_status` or `fact_basis.asset_completeness` enum that wasn't in the schema, and it could accept a reconciled claim despite unknown balances. A user must not interpret such a passing validation result as verified net worth. This patch enforces the entire bundled data schema using Python's standard library, then separately checks cross-field truthfulness. The amount and date types, unsupported schema keywords, and source/permission contradictions now have negative regression cases.

The JSON document schema **remains 5.6.0** for backward compatibility with existing valid DRAFT and CONDITIONAL plans; the *Skill release* is **5.6.1**. Only plans claiming complete reconciliation or client approval have extra provenance requirements: `fact_basis.reconciliation_reference` and `permissions.plan_approval_reference` respectively. These strings are **neither independently verified evidence nor authenticated consent**.

## Included evaluation kit, not a completed experiment

- A real-host acceptance checklist for actual Codex and Claude Code clients.
- A same-model, blinded Skill-vs-plain-AI human evaluation protocol and optional score summarizer.
- Sample scores deliberately fabricated to test aggregation. **There is no real paired model result** and no evidence yet that the Skill outperforms ordinary AI.

## Existing architecture preserved

Professional interview, source evaluation, multi-jurisdiction issue spotting, cash-flow diagnosis, ownership reconciliation, planned wealth policies, 30/90/365 human action tracking and consented memory are unchanged. Host performs the research and tools; the Skill provides methods and optional deterministic validation. There is no autonomous brokerage or tax execution, no new server, no unauthorized financial data storage.
