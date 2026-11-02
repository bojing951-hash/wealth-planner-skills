# Test Report — v5.7.0 Four-Bucket Cashflow System

**Date:** 2026-11-02 · **Branch:** `feat/four-bucket-v5.7` (from `main` @ `9eb67f9`) · **Interpreter:** Python 3.12 (local macOS), CI matrix 3.10–3.13 (ubuntu-latest)

**Scope disclaimer:** all fixtures are **synthetic**. These are offline structural/deterministic tests, NOT real host end-to-end runs, NOT licensed-planner review, NOT evidence of financial outcomes. Every assertion checks actual numbers or hard invariants; no keyword-only assertions.

## 1. New suite — `tests/test_four_bucket_v57.py` (41 tests, 41 PASS)

| Class | Tests | What is actually asserted |
|---|---|---|
| PersonaDifferentiationTests | 2 | Three personas (stable / family-with-debt / crossborder-ample-reserve) produce pairwise-different bucket shares; family ⇒ financial=0, crossborder ⇒ safety top-up=0 while investment>0; conservation holds for each |
| StableSalaryTests | 2 | Exact amounts: floor 10200.00, safety 7400.00, social 2000.00, capability 2000.00, financial 1700.00, unallocated 1700.00; tax KNOWN_NET; stress coverage 1.96; status-quo viable |
| VolatileIncomeTests | 4 | Band low/typical/high = 16000/23000/35000; 18% debt blocks financial investment and free social; extra repayment 6650.00; dependents ⇒ 9-month heuristic target (143100.00) vs user override 6 = USER_INPUT |
| CrossborderTests | 3 | USD 1500 × 7.23 dated FX converted exactly once (allocatable 42845.00); ample reserve ⇒ zero top-up; goal earmark funded from existing assets, not re-saved |
| DeficitTests | 1 | Status DEFICIT, gap 500.00, reserve draw 500.00, all other buckets 0, conservation holds on **funded** living (8000.00 of 8500.00 floor) |
| UnknownDataTests | 4 | 2-month history ⇒ INSUFFICIENT_HISTORY, no scenario band, CONDITIONAL status, retention-rate claims rejected in unknowns; unknown tax ⇒ UNKNOWN_TAX_CONDITIONAL; missing safety cash ⇒ gap not computable; unreceived income excluded (allocatable 0.00, DEFICIT) |
| FailClosedTests | 8 | Mixed currency without dated FX rejected; negative/NaN/Infinity amounts rejected; invalid month `2026-13` rejected; invalid `as_of` rejected; wrong schema_version rejected; missing required field rejected with field name; PF funds never count as safety cash |
| OversubscriptionTests | 2 | Over-income reported pattern flagged UNSUSTAINABLE; engine output conserves exactly on all five plan fixtures (Σ buckets + funded living + unallocated = allocatable, Decimal equality) |
| ReviewTests | 5 | REALLOCATION_NOT_NEW_SAVINGS + unexplained flags on the overspend fixture; positive month: net new savings 12500.00, transfers 3000.00 excluded, coverage 2.16; variance vs plan 5800.00; wrong plan version and missing actuals rejected |
| BoundarySemanticsTests | 5 | Capability vs financial tracked separately; internal transfer excluded from savings math (net 13000.00 with 12000 transfer); debt service inside living exactly once (6400.00, allocatable still 31000.00); defensive < balanced social; markdown render shows all four buckets + conservation line |
| StdinPrivacyTests | 1 | `--input -` result identical to file result |
| NoFixedTemplateTests | 2 | Same income, different starting cash ⇒ safety 0 and higher financial (gap-driven, not ratio-driven); high-cost-debt priority inversion recorded |
| ExitCodeContractTests | 1 | exit 0 = OK, 2 = DEFICIT, 3 = invalid input |

**Regression-fix notes (honest record):** 3 initial test-side errors (2dp rounding expectations, one over-broad `assertNotIn`) were corrected in the tests, not the engine; the exit-code contract was *documented but unwired* in the first calculator draft and then implemented in the engine (`_die_exit` → 3, DEFICIT → 2) with CI and tests locking it.

## 2. Smoke of all 8 fixtures (CLI, matches CI step)

- 4 positive plans exit 0 (three personas + two-months-only CONDITIONAL); review exits 0; deficit exits **2**; both invalid fixtures exit **3** with named errors (mixed-currency names the missing dated FX; amounts name `>= 0`/finite violations).

## 3. Regression — existing suites

- `tools/check_architecture.py --strict`: **PASS** (10/10 domains, 12/12 states, baseline SHA256 `552ac0ae…`, all v5.2→v5.7 gates including new four-bucket markers).
- Full `tests/` + skill-internal unittest discovery and manifest verify: run in the release-gate step below (see §4) — **rerun before merge; results recorded here**.
- Not modified: v5.3–v5.6 layers, memory system, legacy calculator; `SKILL_RELEASE='5.1.0'` compat assertion still passes unchanged.

## 4. Release gate (to be executed on the final commit before PR)

| Step | Command | Result |
|---|---|---|
| Architecture | `python tools/check_architecture.py --strict` | **PASS** (10/10 domains, 12/12 states) |
| Repo tests | `python -m unittest discover -s tests -p 'test_*.py' -q` | **341 tests OK** (skipped=4: pre-existing optional-`jsonschema` skips, unchanged from prior releases) |
| Skill tests | `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | **46 tests OK** |
| Manifest | `python tools/manifest.py --write && python tools/manifest.py --verify` | **PASS — 259 files** |
| CI (GitHub) | matrix 3.10–3.13 incl. new v5.7 smoke step | **SUCCESS 4/4** on `80373c5` (first run `eeb8b5f` caught a stale MANIFEST digest — report edited after manifest write; fixed by rebuilding manifest, a real catch by CI) |

**NOT TESTED / NOT RUN:** authenticated Codex/Claude Code host E2E with private user data; Skill-vs-no-Skill budget-adherence A/B; licensed CFP review; live bank/broker integration and automated scheduling (both prohibited by design). Passing these tests is not proof of financial suitability or of behavioral improvement.
