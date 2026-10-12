# Wealth Planner Skill v5.3.0 — original-v0.4 architecture alignment and difference report

**Baseline (immutable):** `docs/BASELINE_ORIGINAL_v0.4.md`, SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`.
**Reference repository:** `bojing951-hash/wealth-planner-skills`, main commit `074960da584a043b0be9c5a2e6c31c76fb0aa487` (inspected 2026-10-12). Source base: v5.2 repository ZIP, main SKILL.md/blob and baseline verified matching the current GitHub tree. GitHub README has been separately edited and is **not** modified by the v5.3 incremental patch. **Current GitHub connector is read-only**, so this report is for a local patch release, not an assertion that GitHub main was updated.

**Release:** v5.2.0 → v5.3.0 Developer Preview. Scope: **professional financial diagnosis + options and measurable implementation**, not new financial-product recommendations, actual tax calculator, licensed advice, or a new autonomous Agent. Whole-plan mode is mandatory when appropriate; narrow questions can choose small workflows.

## A. Original architecture alignment — D01–D10

| Original ID / mandate | v5.2 baseline | v5.3 implemented evidence | Status | Remaining material gap / risk |
|---|---|---|---|---|
| **D01** client profile + data quality | Dated hypothetical/user reported/verified categories; minimal local memory | `workflows/consultation-interview.md`: ask up to five questions based on decision impact, facts sourced/dated; `professional-consultation.md` | **PARTIAL — enhanced** | Real income, liabilities, insurance, marriage and residency still require client or authorized-source verification; no automated account reconciliation |
| **D02** jurisdiction/law/tax | Jurisdiction issue spotter & official-sources instruction | Retained unchanged; professional workflow makes tax identity an explicit decision gate | **PARTIAL — preserved** | No operative regional tax legal calculations nor expert certification; precise legal conclusions still blocked when source unknown |
| **D03** household cashflow/liquidity | Conditional financial snapshot | `diagnosis-prioritization.md`, optional `consultation_math.py` separates emergency and near-term funds; `plan_quality.py` reconciles cashflow | **PARTIAL — enhanced** | Tax unknown blocks final investability, real spending and debts not independently reconciled; simplified single-currency math only |
| **D04** life cycle/goal matching | Goal/liability rules + basic scenario math | Interview for life events and short-term liabilities; goal contribution gap and alternative deadline in synthetic example | **PARTIAL — enhanced** | Pension, household insurance, inheritance, education and country-specific protected accounts remain missing |
| **D05** economics/evidence disagreements | Curated theory graph + evidence workflow | Preserved; mandate that each consultation diagnosis references observed facts/actual theory, not guru quote or invented quantitative certainty | **PARTIAL — preserved** | No systematic source-quality meta-analysis/real academic retrieval in a host test |
| **D06** slow macro 10–30 years | Conditional real-rate, inflation study | Preserved; macro research only when likely to affect 10–30y policy, not daily trading news | **PARTIAL — preserved** | Market assumptions not estimated/calibrated by real datasets; returns in example are scenario inputs |
| **D07** investment policy | High-level portfolio theory, simple fees and risk math | **Deliberately not expanded**; no forced ETF specificity; report differentiator concerns financial goals and household decisions | **PARTIAL — deferred by user preference** | Tax-after-fee asset allocation, fund/product selection, locale eligibility, investment policy statement remain future scope |
| **D08** simulations and risk | Existing optional goal algebra/Monte Carlo | New optional simple `consultation_math.py` checked against independent constants; structural validator ensures assumption labels/gap | **PARTIAL — enhanced (math checks only)** | No income-market joint tail model validation, stochastic calibration, formal investment-suitability test |
| **D09** professional decision and execution | Generic alternatives and hard gates | `professional-consultation.md` 6-phase method; `diagnosis-prioritization.md` issue cards, >=2 meaningful options and trade-offs; `plan_quality.py` traceability gate | **PARTIAL — main v5.3 focus** | Actual Codex/Claude consultation improvement vs base host unproven until blinded real-host test; judgment not automatable by schema alone |
| **D10** audit/dynamic review | Opt-in encrypted memory + revision tracking | `action-and-followup.md` status/owner/deadline/proof and truthful prior/actual variance; explicit L1/L2 boundary | **PARTIAL — enhanced** | No real recurring scheduler, OS-secure cross-client E2E, account sync or independent financial compliance audit |

**Domain accounting: 10/10 preserved; 0/10 declared completely implemented; 5 explicitly strengthened (D01/D03/D04/D09/D10), D08 optional arithmetic strengthened, D07 intentionally deferred, rest preserved.** The Skill remains a professional instruction layer relying on the host for external execution; optional Python has no LLM, network crawler, trade executor or daemon.

## B. Exact twelve-state mapping (ordering unchanged)

| Original state | Owner | v5.3 consultation behavior / output | Fallback / completion boundary |
|---|---|---|---|
| `INTAKE` | Host | Clarify real decision and high-value missing inputs via adaptive interview | <=5 material questions; hypothetical label |
| `CAPABILITY_CHECK` | Host | Discover tools/permissions, memory OFF without opt-in | No fake account/source read |
| `FACT_VERIFICATION` | Host | Dated owned/realized/gross/net currencies and conflict log | Unknown facts remain unknown |
| `JURISDICTION_GATE` | Host + official sources | Tax year/residency blockers identified | No invented taxes/eligibility |
| `HOUSEHOLD_SOLVENCY` | Host + optional math | Reserve/debt/near-term cash preflight and ranked critical issues | Do not recommend risky money use when insolvent |
| `GOAL_AND_LIFECYCLE` | Host | Liability timing, target amount, date, goal gap | Unrealistic timelines produce options, not promises |
| `EVIDENCE_RESEARCH` | Host | Client-specific evidence for issue mechanism, theory boundary | No guru-only recommendation |
| `MACRO_SCENARIOS` | Host | Relevant slow macro and conditional returns only when material | Do not invent forecasts or change strategy from news |
| `CANDIDATE_PLANS` | Host | >=2 distinct, funded/conditional routes and opportunity costs | No source for >surplus action ⇒ CONDITIONAL |
| `DETERMINISTIC_AND_STOCHASTIC_VALIDATION` | Host + optional calculator | Money reconciliation; scenario goal gap; structural quality check | Uncalibrated probabilities remain illustrative |
| `POLICY_CHECK` | Host | Correct currencies, income ownership, permissions, sources, budget feasibility | Fail closed for legally consequential unknowns |
| `EXPLAIN_AND_MONITOR` | Host | 1-page findings, 30/90/365 actions and review triggers | No ongoing monitor unless real scheduler authorized |

**States preserved 12/12. No thirteenth state, no replacement of the original state machine.**

## C. Scope of actual new functions

- **Host-facing rules:** problem classification; high-value interview; diagnosis cards with cause-vs-hypothesis and user-goal effect; alternative financing mechanism and trade-offs; honest recommendations and completion status; 30/90/365 measurable actions.
- **Optional deterministic checks:** `scripts/consultation_math.py` uses only a supplied, same-currency, explicitly net cash scenario for reserve-first fixed-return algebra; it is not a tax estimator or 5% return forecast. `scripts/plan_quality.py` checks specified JSON structure and basic arithmetic/traceability, does NOT produce actual expert judgment.
- **Machine contract + synthetic demonstration:** `schemas/consultation-v5.3.schema.json`, `examples/v5.3-consultation-shenzhen-SYNTHETIC.json`, `docs/EXAMPLE_PROFESSIONAL_PLAN_v5.3_SHENZHEN.md`.
- **Comparative evaluation:** `tests/skill_vs_baseline/README.md` and synthetic benchmark cases prescribe a future same-model blind A/B; currently `NOT_RUN`. Tests that reject a generic mock are **not proof** that v5.3 beats vanilla Codex.
- **Preserved v5.2 memory:** explicit user opt-in, every read/write authorization gate and no storage in Git. No added automatic new memory operations.

## D. Deviations and release safety

| Potential departure from original architecture | Decision |
|---|---|
| "New consultation protocol" could imply eleventh domain | **No**: cross-domain workflow within D01/D03/D04/D09/D10 and original twelve states |
| "Quality agent" could be another LLM/runtime | **No**: small on-demand stdlib data validator run by Host only; not a new Agent |
| Under pressure to recommend concrete ETFs/tax strategies without enough evidence | **Explicitly rejected**: D07 depth deferred; current law blocks remain in force |
| Local financial memory could be activated without consent | **No**: v5.2 default OFF and L1/L2 separate consent retained |
| Classifying test-score as real consulting efficacy | **No**: blind real-host A/B and professional suitability remain `NOT_TESTED` |
| Release without GitHub push | **Clear**: local v5.3 patch only; repository main SHA remains v5.2 at check; no claim of remote publication |

## E. Test evidence, limits and next step

Detailed commands/results: `docs/TEST_REPORT_v5.3.md` (recorded after execution). Original baseline SHA intact. Mandatory offline architecture/test cases, five smoke cases and **new** professional quality-contract tests must pass. Genuine Codex/Claude client A/B testing and local-law expert validation are **NOT_TESTED** until demonstrated, never infer pass from code coverage. The pre-existing `MANIFEST.sha256` on GitHub contains a removed `README.zh-CN.md` and old README hash; refresh it on the actual checked-out GitHub files before a formal release. The incremental patch purposely does not overwrite the user's later-edited product README.

**Next blocking success measure:** In the SAME AI environment, blind judges can identify materially more root-cause-based, feasible, actionable client-specific plans using the Skill, with no uptick in invented tax/maths or privacy violations. v5.3 provides the rules and observable test protocol, not that experimental result.
