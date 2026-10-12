# Wealth Planner Skill v5.3 — offline test and architectural difference report

**Date:** 2026-10-12. **Version:** v5.3.0, Developer Preview. **Original baseline:** `docs/BASELINE_ORIGINAL_v0.4.md` SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`. **Source revision:** inspected GitHub `bojing951-hash/wealth-planner-skills` main commit `074960da584a043b0be9c5a2e6c31c76fb0aa487` (v5.2; repository tool permission read only). Current GitHub's customized README not overwritten by the incremental patch.

## Real execution (not promises)

| Gate | Executed method | Actual result | What it proves / cannot prove |
|---|---|---|---|
| Baseline immutability | SHA256 of exact original v0.4 plan | **PASS**: SHA unchanged | Original requirements preserved, not business feature completion |
| 10-domain and 12-state structure | `python tools/check_architecture.py --strict` | **PASS**, D01–D10 10/10, state 12/12 | Structure and text links only, not professional advice quality |
| Legacy Skill tests | `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` | **PASS 46/46** | Original math/evidence regional precheck regression |
| Repository tests (including new v5.3) | `python -m unittest discover -s tests -p 'test_*.py' -q` | **PASS 164/164** | Old release/memory tests plus **26 new** professional planning validations |
| **Total unit tests** | Two suites above | **PASS 210/210** | Not an actual live Codex/Claude consultation |
| Professional sample quality | `plan_quality.py --input .../v5.3-consultation-shenzhen-SYNTHETIC.json` | **PASS** | Structural and limited arithmetic contract, not evidence of financial suitability |
| Generic weak mock | `plan_quality.py --input .../v5.3-generic-failure-SYNTHETIC.json` | **EXPECTED FAIL** | Validator catches intentionally incomplete generic mock; not a blinded same-model A/B |
| Reserve-first goal math | `consultation_math.py --input .../v5.3-shenzhen-math-input-SYNTHETIC.json` | **PASS** | In hypothetical CNY scenario: protected cash 48k, long-term start 52k, monthly surplus 9k, at 5% fixed return goal monthly 13,767.61 and gap 4,767.61; these are not forecasts |
| Legacy five smoke cases | optional `wealth_v5.py run` for Shenzhen, Shanghai, NYC, Chicago, CN/HK PF | **PASS 5/5** | Input parsing/conditional scenario math, not live 2026 tax law or verified income |
| Code compilation | `python -m compileall` | **PASS** | Syntax and imports in tested environment |
| JSON schema | `jsonschema.Draft202012Validator.check_schema` and synthetic valid case | **PASS** in local dev environment | Third-party schema lint, not required to use standalone Skill |
| Standalone Skill directory installed as actual real client | Local ZIP extracted + CLI portability check | **PASS** (local CLI); **CLIENT HOST NOT_TESTED** | Independent Skill folder math works; not real host tool selection or response judgment |
| GitHub Actions on v5.3 patch | Actual GitHub run | **NOT_TESTED**; patch not pushed | Local CI commands run; public main unchanged |
| Real Codex / Claude Code complete-plan E2E | Manual client run with official research and authorizations | **NOT_TESTED** | User reports prior Skill basic functionality, not a dated test of this new release |
| Same-model Skill ON/OFF blinded comparison | `tests/skill_vs_baseline/README.md` protocol | **NOT_RUN** | No measured advantage over plain AI may be asserted |
| Client suitability, exact tax law, investment model calibration | Independent qualified and market validation | **NOT_TESTED** | v5.3 does not claim licensed professional advice or calibrated probabilities |

## Original architecture difference summary

- **Preserved** D01–D10, exact state names/order, Skill-first host executes, primary-source law gate, money/FX/PF safeguards, L1/L2 privacy and L3 no autonomous trades/transfers/filings.
- **Enhanced** D01 high-value intake, D03 reconcile + protected cash, D04 time-bound goal feasibility, D09 root-cause advice/choice/action hierarchy, D10 review/status protocol, D08 only small reserve-first arithmetic checking.
- **Deferred by design** D07 deep investment portfolio/product personalization, certified local tax, currency-specific macro forecasts, retirement and legal expert sign-off.
- **Known external blocker:** current GitHub `MANIFEST.sha256` is stale vs later edited README/deleted Chinese README. New `tools/manifest.py` provides rebuild/verify; run `--write` on the actual GitHub checkout after applying the patch and commit the regenerated manifest. **Never overwrite the GitHub product README from an old ZIP**.
- **No architecture drift found in structural audit**; there are still ten partially implemented domains and many real-world gaps. A static guard cannot establish the decision process achieves the desired professional improvement.

## Release quality judgment

**PASS for local developer-preview implementation and synthetic professional-plan contract; NOT PASSED for real-host or outcome-improvement certification.** Real user value must be tested by identical scenarios with Skill on/off in the same model/runtime, blinded raters and audit of mathematics, material problem discovery, action feasibility and tax/privacy risk. Track that evidence before marketing "professional-planner-level" performance.

Full ten-domain and twelve-state mapping: [`ARCHITECTURE_ALIGNMENT_v5.3.0.md`](ARCHITECTURE_ALIGNMENT_v5.3.0.md).
