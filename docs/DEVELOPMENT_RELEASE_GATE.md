# Non-waivable development/release gate — comparison to ORIGINAL v0.4 architecture

**This file is normative for every future developer change.** The original source is `docs/BASELINE_ORIGINAL_v0.4.md` with locked SHA256 `552ac0ae1a7150fba23ae5a55a5fa6347b59d303a01b3517ed098a56a8a358bb`.

## Completion steps (perform **after** coding, before delivery)

1. **Baseline preserved:** compare exact v0.4 original (hash) and avoid silently editing its obligations. If actual requirements change, publish a documented amendment, not a replacement baseline.
2. **One-to-one domain audit:** for D01–D10 mark `implemented`, `partial`, `workflow-only`, `missing` or `blocked`; state file evidence and *remaining scope*. File existence is not behavioral completion.
3. **Twelve-state audit:** for each original state document owner (host/skill/math/external), trigger, output, fallbacks and gate. A narrow user task may deliberately skip nonmaterial states; the canonical workflow must remain covered.
4. **Role audit:** verify all ordinary research/decisions/tool calls belong to host; Skill only gives procedures and optional deterministic calculators; no private background Agent or unauthorised money/tax operations.
5. **Fact/evidence/tax audit:** no uncited legal claim presented as current, no PF simulated ≈ owned asset, no mixing currencies, no calibrated probability claim from uncalibrated MC. Validate prominent sample cases.
6. **Run static guard:** `python tools/check_architecture.py --strict` (structure checks only).
7. **Run tests:** `python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q` and `python -m unittest discover -s tests -p 'test_*.py' -q`; run offline smoke for four cities and PF case, record results. Any failure blocks release.
8. **Host E2E:** install into real Codex and Claude Code, confirm loading/appropriate trigger, actual official-source tool call and correct uncertainty fallback. Without a real client session, record `NOT_TESTED` (not passed).
9. **Update comparison:** create `docs/ARCHITECTURE_ALIGNMENT_vX.Y.Z.md`, including **original baseline requirement → actual implementation/evidence → gap → risk → next step**; update `docs/architecture_contract.json` version/status and release notes. User must receive the alignment report with the artifact.
10. **Check ZIP portability/privacy:** independent Skill folder contains all linked resources; public artifact contains only synthetic financial examples, no real receipts/credentials/PII. No secrets in `.git` or release archive.

## Release blocker vs pending scope

**Blocks release**: changed baseline hash, missing ten-domain/state coverage, broken Skill install files, violated L3 safety, invented legal conclusions, failed mandatory offline tests, reporting E2E as passed when absent.

**Allowed as explicit `Developer Preview` gap**: incomplete global tax plugin, lack of live connector, model calibration not completed, no secure account read, no tested cross-client E2E. These remain **documented gaps** and must not be called finished capabilities.

## Developer template for alignment table

| Baseline ID | Requirement | Files / observed run | Completion level | Material gap | Remediation / test |
|---|---|---|---|---|---|
| D01 | ... | ... | ... | ... | ... |

Each iteration appends new evidence; do not retroactively rewrite old test outcomes. The architecture guard tests manifest/file presence, **not professional correctness**.

## Additional v5.3 gates (Professional Financial Consultation)

11. For a **full** planning task, verify the host was directed to read `workflows/professional-consultation.md`; its final deliverable must contain a client-specific financial diagnosis, cause/evidence, quantified goal gap with emergency reserves excluded, >=2 differentiated alternatives and their opportunity costs, recommended conditional sequence, concrete 30/90/365 actions, and follow-up status. For narrower tasks, do not require irrelevant sections.
12. Run `python skills/personal-finance-planner/scripts/plan_quality.py --input skills/personal-finance-planner/examples/v5.3-consultation-shenzhen-SYNTHETIC.json`, and check that the mock generic response *fails*. This only tests the data/report contract; it cannot prove skill-vs-no-skill model quality.
13. Run `python tools/manifest.py --write` on the **actual GitHub checkout** after integrating changes; inspect the output to exclude personal finance data. Commit the updated `MANIFEST.sha256`, and run `python tools/manifest.py --verify` in CI. Do not blindly reuse stale v5.2 README hashes in a new release.
14. For an empirical product improvement claim, use real Codex and Claude Code same-host **blinded A/B** protocol in `tests/skill_vs_baseline/README.md`. Unless actual blinded runs are documented, mark `NOT_RUN` and do not claim superiority.
