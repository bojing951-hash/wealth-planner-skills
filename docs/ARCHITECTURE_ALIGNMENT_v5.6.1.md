# Wealth Planner Skill 5.6.1 — ORIGINAL v0.4 baseline comparison and differential audit

**This is a corrective Developer Preview release, not a new architecture.** Original immutable source: `docs/BASELINE_ORIGINAL_v0.4.md`, SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`. Based on GitHub `main` commit `f7d64e24c5ef77bc4752e707c12523659a13e811`; this local patch is **NOT pushed**. Source archive used for local testing has an older *product README*, so apply patch to the actual repository without overwriting the live README and regenerate `MANIFEST.sha256` there.

**Preserved contract:** Codex/Claude Code host executes reasoning, authorized search, code/file tools and the actual report. The Skill supplies professional methods, evidence/quality gates, and optional deterministic helpers. User L1 reads require consent, L2 memory writes require exact fresh approval, L3 autonomous trades/transfers/tax filing are prohibited. No new agent/backend or live financial account operation is introduced.

## A. Ten-domain item-by-item comparison

| ID | Original v0.4 responsibility | This patch's actual implementation/evidence | Status | Remaining material gap and next check |
|---|---|---|---|---|
| D01 | Profile, asset ownership, source/data freshness | `master_plan_quality.py` now checks nested schema and prevents `RECONCILED` with unknown personally owned balances/liabilities; explicit `reconciliation_reference` required for completeness claims | **PARTIAL / improved** | A source reference is not bank-document verification; host must verify actual complete inventory with authorized sources. |
| D02 | Jurisdiction/tax legality, tax year | No new tax law or tax formula; unknown tax remains blocker to exact investable cash | **PARTIAL / preserved** | Actual local law must be sourced and interpreted by qualified professional when material. |
| D03 | Cashflow, debt, reserves, available investable funds | Preserves v5.5 cash/PF/broker reconciliation and v5.6 purpose-earmark consistency; rejects invalid monetary inputs across schema | **PARTIAL / strengthened guard** | No live account reconciliation, debt amortization or genuine tax reserve calculation. |
| D04 | Life-cycle goals and future liabilities | Goal amount/priority/currency/date/real-vs-nominal enums and required fields now enforced in full plan JSON | **PARTIAL / strengthened guard** | No full household lifetime actuary or credible pension model. |
| D05 | Economics, empirical evidence and conflicting theories | Existing evidence workflow unchanged; no fabricated research | **PARTIAL / preserved** | Academic source adjudication depends on host retrieval and subject experts. |
| D06 | Slow macro inputs, inflation and long-horizon stress | Existing macro discipline preserved without changes | **PARTIAL / preserved** | Calibrated currency-matched capital market expectations absent. |
| D07 | Investment policy, eligibility, costs | Existing purpose-first policy retained, no specific product recommendation functionality added | **PARTIAL / preserved** | Suitability, local after-tax investment policies and ETF selection remain pending. |
| D08 | Reproducible math, scenarios and downside | Bundled master-plan Schema enforced with stdlib checks even without `jsonschema`; invalid types/fields/amounts/dates rejected | **PARTIAL / improved** | Schema guard cannot guarantee econometric calibration, correct cash projections or actual financial suitability. |
| D09 | Conditional decisions, approvals, execution responsibility | `USER_APPROVED` plans require explicit `plan_approval_reference`; missing or contradictory validation flags rejected | **PARTIAL / improved** | Reference text isn't authentication; only actual host-user conversation/approval can authorize. |
| D10 | Audit, memory, source, review | Adds repeatable error regression, controlled real-host acceptance procedure and blind comparative scoring kit | **PARTIAL / improved tooling** | No independently observed model superiority, actual Codex/Claude E2E, production-grade memory security or automatic monitoring. |

**Disposition:** 10/10 domains preserved; NONE newly marked COMPLETE; no deletion or downgrade. Patches strengthen v5.6 checking without falsely certifying professional correctness.

## B. The original 12 states — owner, contribution, fallback

| State | Original owner & expected outcome | v5.6.1 validation/fallback |
|---|---|---|
| `INTAKE` | Host classifies planning scope and private facts | Same, no skill-driven account access. |
| `CAPABILITY_CHECK` | Host discovers actual search/files/Python/memory | Same; real tools not bundled; Codex/Claude E2E NOT_TESTED. |
| `FACT_VERIFICATION` | Host separates user-reported vs verified assets & money | Stronger schema and reconciliation truthfulness; invalid claims blocked. |
| `JURISDICTION_GATE` | Host researches applicable law/year | Unverified law remains explicitly NOT_VERIFIED; no tax inference by code. |
| `HOUSEHOLD_SOLVENCY` | Host checks spending/debts/reserves | Unknown debt amounts prevent reconciled statement. |
| `GOAL_AND_LIFECYCLE` | Host identifies dated goals, currencies and dependencies | Nested goal schema strictly checked; incomplete facts stay conditional. |
| `EVIDENCE_RESEARCH` | Host retrieves credible theory and legal sources | Preserved; no new source-proven claim. |
| `MACRO_SCENARIOS` | Host chooses slow-variable material assumptions | Preserved; cannot claim forecasts calibrated. |
| `CANDIDATE_PLANS` | Host develops baseline and alternatives | Existing status-quo check preserved; reviewed with plan quality gate. |
| `DETERMINISTIC_AND_STOCHASTIC_VALIDATION` | Host runs auditable arithmetic when material | More reliable plan schema/static gate; probabilistic calibration absent. |
| `POLICY_CHECK` | Host checks legal safety, ownership and permissions | Reconciliation/approval reference guard added; user consent still external. |
| `EXPLAIN_AND_MONITOR` | Host presents plan, followups, auditable versions | Human A/B scoring protocol added; no unattended tracking. |

**Outcome:** 12/12 original states preserved in order. No replacement task state, L3 authority or new controller.

## C. Negative regression and claim boundaries

- Old failure: invalid `balance_sheet.net_worth_status='APPROVED_BY_MODEL'` or `fact_basis.asset_completeness='SURE'` could pass static checker. New mandatory schema gate rejects both.
- Old failure: `asset_completeness='RECONCILED'` despite unknown broker NAV/auto loan balances could pass. New consistency gate rejects.
- Old failure: a plan could claim `USER_APPROVED` without an explicit approval trail. New checker requires a reference, but **cannot verify that the user approved**.
- New schema fields are **optional for existing DRAFT/CONDITIONAL v5.6.0** documents; `schema_version` remains `5.6.0` while the Skill package release becomes `5.6.1`.
- Every optional helper remains a *static validator*. Passing is NOT proof of client asset ownership, tax legality, professional suitability, or real-world improvement.

## D. Tested vs untested

**Verified in local build:** baseline hash, architecture checks, existing regressions, new v5.6.1 negative checks, existing synthetic five-scenario smoke, positive and failing Master Plan fixtures, standalone Skill resource resolution, synthetic blind-scoring CLI, Python syntax and content manifest for the **local archive**. Count/details: `docs/TEST_REPORT_v5.6.1.md`.

**NOT TESTED / NOT RUN:** authenticated Codex host end-to-end, Claude Code host end-to-end, independent controlled Skill-vs-no-Skill A/B on identical model/tool/time, licensed planner review, any real client tax/broker/finance accounts, production Windows/macOS ACLs and automatic continuous monitoring. Bundled synthetic scoring must never be reported as effectiveness proof.

**Remote release requirement:** because GitHub connection is read-only here, use the packaged overlay on a clean clone of the specified HEAD, preserve the remote customized README, run `tools/manifest.py --write` and `--verify` **on that checkout**, run all local & CI tests, open a PR and review. Until the PR is merged and GitHub CI success verified, remote release is **NOT PUBLISHED**.
