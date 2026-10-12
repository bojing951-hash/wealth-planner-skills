# Wealth Planner v5.4.0 — original v0.4 architecture alignment

**Immutable original:** `docs/BASELINE_ORIGINAL_v0.4.md` SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`. **Project type:** Skill-First; the host executes research, calculations and file tasks. This release does not deploy a new Agent, external integration or autonomous scheduler. Source-level comparison is not a certification of advice.

## Original ten professional domains (all retained)

| Original | v5.4 implementation evidence | Status | Still missing |
|---|---|---|---|
| D01 Profile/data quality | v5.3 diagnosis and v5.4 dated user-specific behavior cards | PARTIAL/retained | Actual account ownership, verified full balance sheet |
| D02 Jurisdiction/compliance | Existing legal gates maintained; no fictional tax efficiency | PARTIAL/retained | Validated region/year tax computation; licensed advice |
| D03 Cashflow | `workflows/value-and-behavior.md`; `scripts/value_math.py` new retained cash vs transfers | PARTIAL/improved | Bank reconciliation, debt principal and tax verification |
| D04 Lifecycle/goals | Measured goal change, liquidity and wellbeing conditions, no-change option | PARTIAL/improved | Pension, insurance, family, estate liabilities |
| D05 Economics/evidence | Existing primary source/conflict workflow; `references/value-attribution-method.md` | PARTIAL/retained | Formal literature quality/causal evidence assessment |
| D06 Long-horizon macro | Identical hypothetical investment/cash/inflation assumptions for counterfactual | PARTIAL/retained | Calibrated long-horizon asset assumptions and host retrieval E2E |
| D07 Investment policy | Existing policy and hard gates; increased market exposure flagged | PARTIAL/deferred | Country-specific lawful investment selection and tax-after-fee optimizer |
| D08 Math/risk | `value_math.py`: cash+investments comparison, reserve gate, no double counting, inflation | PARTIAL/improved | Joint stress model, asset loss distributions, market calibration |
| D09 Decision/execution | Required behavior→mechanism→value→proof card, `value_quality.py` | PARTIAL/improved | Independent host quality test and advice suitability |
| D10 Audit/monitor | Two-dated-state difference review, never causal; optional v5.2 memory untouched | PARTIAL/improved | Real follow-up, causal evaluation, host E2E, OS security |

**Retention:** D01–D10 = **10/10 unchanged**, no newly named eleventh domain; none asserted COMPLETE.

## Original twelve state flow (order/IDs unchanged)

| State | Execution responsibility / v5.4 contribution |
|---|---|
| INTAKE | Host establishes facts, goal and user scope; value mode only for substantive plans |
| CAPABILITY_CHECK | Host checks its real tools; bundled calculators optional |
| FACT_VERIFICATION | Host distinguishes money owned vs PF simulated, behavior baselines dated |
| JURISDICTION_GATE | Existing primary-law and tax-year gate retained, unknown tax benefit blocked |
| HOUSEHOLD_SOLVENCY | Required reserve, actual net cash and affordable contribution checked |
| GOAL_AND_LIFECYCLE | Personal goal, time, wellbeing and opportunity-cost constraints |
| EVIDENCE_RESEARCH | Behavioral mechanisms distinguished from proven individual effects |
| MACRO_SCENARIOS | Compare alternatives with **same** assumed investment/cash returns and inflation |
| CANDIDATE_PLANS | Compare status quo and ≥1 meaningful alternative; do not manufacture change |
| DETERMINISTIC_AND_STOCHASTIC_VALIDATION | Host or optional math: new retained principal vs hypothetical growth/reallocation |
| POLICY_CHECK | Protect reserve/ownership, no invented tax, no internal-transfer 'new wealth' |
| EXPLAIN_AND_MONITOR | Projected vs executed vs observed, value card and review metrics; no automatic background jobs |

**Retention:** 12/12 statuses, sequence and owner boundaries unchanged. Narrow questions may use subset as original baseline allows.

## Implementation versus deviations

**PRESERVED:** Skill-First, original 10 domains and 12 workflow states, original protected baseline hash, L0 public read / L1 private read / L2 specific consented private write / L3 no autonomous money/tax operations, PF balances not user-owned, currencies separate, laws require official effective source, uncalibrated Monte Carlo not actual probability, memory OFF by default.

**NEW:** Full-plan value discipline in `SKILL.md`; value workflow + evidence register; optional **standard library only** matched counterfactual and observed change scripts, value card quality gate, synthetic positive/negative examples and regression tests. Intervention may be **maintain current strategy**.

**No new architecture deviation detected:** optional Python is arithmetic/validation, not LLM orchestration or host replacement. **Risk:** protocol may still be executed superficially by real host; client outcomes and causal value have not been validated. Numerical modeled improvements are NOT realized wealth.

**Explicit remaining original gaps:** actual tax/legal country sub-regimes, validated pensions/insurance/inheritance, portfolio suitability, observed macro return calibration, personal account reconciliation, sustained client behavior, host authorization and end-to-end load, cross-host private memory security, causal benefit evaluation. All remain PARTIAL or NOT_TESTED.

## Release evidence and gates

- Original hash exact: recheck with `sha256sum docs/BASELINE_ORIGINAL_v0.4.md`.
- `python tools/check_architecture.py --strict`: ensure 10/12 and new value protocol resources; static check **only**.
- Unit and synthetic smoke: see `docs/TEST_REPORT_v5.4.md` (do not fill 'PASS' until commands have run).
- Real Codex/Claude Code end-to-end and blinded **Skill ON/OFF**: **NOT_TESTED / NOT_RUN**; see `tests/skill_vs_baseline/MEASURE_VALUE_v5.4.md`.
- GitHub sync: produce patches without replacing the customized product README; regenerate `MANIFEST.sha256` on the actual checkout; GitHub write has **not** been performed here.

**Conclusion:** conforms to original v0.4 scope, adds measurable financial-planning decision standards but does not prove it creates client wealth or outperforms an unspecialized host in a blinded trial.
