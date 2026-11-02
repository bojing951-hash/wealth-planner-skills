# Wealth Planner Skill 5.7.0 — ORIGINAL v0.4 baseline comparison and differential audit

**This is a feature-layer release, not a new architecture.** Original immutable source: `docs/BASELINE_ORIGINAL_v0.4.md`, SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`. Based on GitHub `main` commit `9eb67f9e42b19e0c20187b8ac21582fa9a0b8825` (merge of PR #4, v5.6.1), developed on branch `feat/four-bucket-v5.7`.

**Preserved contract:** the HOST Agent executes reasoning, authorized search, code/file tools and the actual report. The Skill supplies methodology, gates and optional deterministic helpers. v5.7 adds a **four-bucket monthly cashflow layer** (A safety & savings, B living floor, C necessary investment, D social & discretionary) with exact Decimal conservation, priority-based allocation instead of fixed ratios, fail-closed multi-currency handling, and a month-end review that separates net new savings from internal transfers. No new Agent, backend, scheduler, account access or L3 authority is introduced; v5.3→v5.6 layers are untouched except for routing.

## A. Ten-domain item-by-item comparison

| ID | Original v0.4 responsibility | v5.7 actual implementation/evidence | Status | Remaining material gap and next check |
|---|---|---|---|---|
| D01 | Profile, asset ownership, source freshness | `facts` input block separates safety-eligible cash from PF simulated funds, restricted investments, brokerage NAV and unreceived amounts; each counted exactly once | **PARTIAL / strengthened** | Still user-reported facts; no bank-document verification by code. |
| D02 | Jurisdiction/tax legality | `tax_status` carries KNOWN_NET vs UNKNOWN_TAX_CONDITIONAL end-to-end; pre-tax figures make every investable amount conditional instead of being silently spent | **PARTIAL / preserved+** | No new tax law or formula; exact real-world tax remains host/professional scope. |
| D03 | Cashflow, debt, reserves, investable funds | **Core of this release:** allocatable = Σ buckets + unallocated (exact, every run); obligations inside the living floor exactly once; high-cost debt (APR ≥ threshold) blocks risk investing; reserve gap uses eligible cash only | **PARTIAL / significantly extended** | No live account feeds, no amortization engine, no automated repayment. |
| D04 | Life-cycle goals | near-term goals link to the L3 purpose pool via `master_plan_links` (funded_from existing-assets earmarks) without re-summing L2; goal deadlines not met by fabrication | **PARTIAL / preserved** | Long-horizon actuarial matching remains Master Plan scope. |
| D05 | Evidence and conflicting theories | `references/budget-decision-method.md` cites 50/30/20-style fixed ratios as the rejected strawman; ordering conventions attributed as conventions, not outcome promises | **PARTIAL / preserved** | No new empirical claims introduced. |
| D06 | Macro scenarios | variable income handled by 6–12 month history → low/typical/high quartile band; <6 months ⇒ INSUFFICIENT_HISTORY with explicit refusal of "normal income"/retention claims | **PARTIAL / improved for income** | Market return calibration unchanged and still absent. |
| D07 | Investment policy, eligibility | financial investment is a *conditional ceiling* gated on eligibility, high-cost debt, liquidity and tax status; capability (human capital) tracked as separate real spending, never double-counted | **PARTIAL / improved gating** | Product suitability explicitly out of scope. |
| D08 | Reproducible math | `four_bucket_math.py` stdlib+Decimal, quantized cents, conservation asserted in every plan; CLI exit codes 0/2/3 for OK-CONDITIONAL/DEFICIT/invalid | **PARTIAL / extended** | Deterministic only; no stochastic layer (by design for budgeting). |
| D09 | Conditional decisions, ownership | assumption list with USER_INPUT/HEURISTIC_EDITABLE/CALCULATED sources; DEFICIT outputs gap + reserve draw option, never "negative savings"; `no_change_recommended` honest within 5% band | **PARTIAL / improved** | Execution remains 100% user-owned; no automated transfers. |
| D10 | Audit, review, memory | month-end `review` command: planned-vs-actual variance, net new savings (income − consumption), internal-transfer exclusion, REALLOCATION_NOT_NEW_SAVINGS flag; memory unchanged (OFF by default) | **PARTIAL / extended** | Review depends on user-entered actuals; no account scraping. |

**Disposition:** 10/10 domains preserved; NONE newly marked COMPLETE; no deletion or downgrade. The four-bucket layer strengthens D03/D06/D07/D08/D09/D10 without altering the v0.4 process.

## B. The original 12 states — owner, contribution, fallback

| State | Original owner & expected outcome | v5.7 contribution |
|---|---|---|
| `INTAKE` | Host classifies scope and private facts | New budget-intent routing (预算管理/收入分配/月度复盘…) loads only the four-bucket workflow (progressive disclosure). |
| `CAPABILITY_CHECK` | Host discovers real tools | Calculator remains optional, stdlib-only, offline; stdin preferred for privacy. |
| `FACT_VERIFICATION` | Host separates reported vs verified money | Fact block hard-separates eligible cash / PF simulated / restricted / brokerage / unreceived. |
| `JURISDICTION_GATE` | Host researches applicable law | Untouched; unknown tax ⇒ conditional investable ceilings. |
| `HOUSEHOLD_SOLVENCY` | Host checks spending/debts/reserves | Now structurally computed: floor vs allocatable, DEFICIT gap, reserve-gap months heuristic (3/6/9, user-editable). |
| `GOAL_AND_LIFECYCLE` | Dated goals, dependencies | Goals arrive as L3 links; earmarks from existing assets excluded from this-period savings. |
| `EVIDENCE_RESEARCH` | Credible sources | Budget method reference added; no fabricated evidence. |
| `MACRO_SCENARIOS` | Slow-variable assumptions | Income scenario band (low/typical/high) for volatile earners. |
| `CANDIDATE_PLANS` | Baseline and alternatives | defensive / balanced / status_quo comparison per plan; status-quo may be flagged UNSUSTAINABLE. |
| `DETERMINISTIC_AND_STOCHASTIC_VALIDATION` | Auditable arithmetic | Exact Decimal conservation asserted per run; exit-code semantics. |
| `POLICY_CHECK` | Legal safety, permissions | No automatic actions of any kind; user owns execution. |
| `EXPLAIN_AND_MONITOR` | Presentation, review | Markdown render + month-end review protocol with anti-double-count flags. |

**Outcome:** 12/12 original states preserved in order. No replacement state, no new controller, no L3 authority.

## C. Negative regression and claim boundaries

- Fixed-ratio templates are *structurally impossible to output as truth*: every number derives from the priority cascade over user facts; the only constants (8% APR threshold, 0.5 gap-fill share, 3/6/9 months) are surfaced as HEURISTIC_EDITABLE assumptions in every output.
- DEFICIT conserves on `living.funded` (money actually available), not on the unfunded floor total — the invariant holds even mid-shortfall.
- Cross-currency addition without dated FX **fails closed** (exit 3); NaN/Infinity/negative amounts, invalid months and wrong schema_version all reject with named errors.
- Two-month histories cannot produce "normal income" or retention-rate claims (asserted by test); the word "retention" may appear only inside the rejection sentence.
- Passing every check is **NOT** proof of financial suitability, tax correctness or behavioral improvement; synthetic fixtures are illustrative only.

## D. Tested vs untested

**Verified locally:** `tests/test_four_bucket_v57.py` 40/40 (persona differentiation, conservation on every plan, deficit, conditionality, fail-closed rejections, review flags, stdin≡file, override precedence, oversubscription blocking, no-fixed-ratio evidence); smoke of all 8 synthetic fixtures; architecture checker `--strict`; full regression of prior suites and manifest (see `docs/TEST_REPORT_v5.7.md`).

**NOT TESTED / NOT RUN:** authenticated Codex or Claude Code host end-to-end with a real user's private data; independent Skill-vs-no-Skill A/B for budget adherence; licensed CFP review; live bank/broker integration (prohibited by design); automated scheduling (prohibited). The 3/6/9-month reserve heuristics are ordering conventions, not calibrated optima.
