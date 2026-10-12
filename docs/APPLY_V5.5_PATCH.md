# How to apply v5.5 incremental patch to the REAL GitHub checkout

**Repository:** `bojing951-hash/wealth-planner-skills`. **Observed source** at design start: `main` HEAD `ae0f043f0e19ef49c8915fd2a53e324d10561245`, Skill `5.4.0` as of 2026-10-12. Recheck live HEAD and carefully review local modifications before applying. The developer environment cannot write to the repository. **Do not claim this update is published before you commit and verify Actions.**

## Safe manual route (Codex/Claude Code can do these steps on the local repo)

1. `git clone https://github.com/bojing951-hash/wealth-planner-skills.git` (or open the already-cloned folder). Inspect `git status`, `git branch --show-current` and the current `skills/personal-finance-planner/SKILL.md` version. Save or commit local edits separately if needed.
2. Unzip the **incremental patch** in a **private staging directory** and inspect its file list. It has paths relative to repository root. It deliberately **does not include `README.md` or `MANIFEST.sha256`**: keep the customized GitHub product homepage unchanged, and compute the manifest only after copy.
3. Copy updated/new files from the patch into the repository, preserving relative directories. Review the diff before staging. Verify original `docs/BASELINE_ORIGINAL_v0.4.md` is UNCHANGED and not present in patch.
4. In the actual repo checkout, run exactly:

   ```bash
   python tools/manifest.py --write
   python tools/manifest.py --verify
   python tools/check_architecture.py --strict
   python -m unittest discover -s skills/personal-finance-planner/tests -p 'test_*.py' -q
   python -m unittest discover -s tests -p 'test_*.py' -q
   python skills/personal-finance-planner/scripts/trader_wealth_reconcile.py \
     --input skills/personal-finance-planner/examples/v5.5-crossborder-mixed-trader-SYNTHETIC.json
   ```

5. Run synthetic quality gate using the reconciliation JSON to check the accompanying public example. Verify Git diff is restricted to v5.5 work, new docs/CI, metadata and newly regenerated manifest. **Never stage `/tmp`, real user finance JSON, keys, vaults or statements.**
6. Create a feature branch, commit, open a PR; inspect CI and complete the original-v0.4 alignment checklist. Do not state 'production' or 'actual host E2E passed' merely because unit tests pass.
7. Update the **installed** Codex and Claude Code Skill copies separately: GitHub `main` and already-installed Skill directories are distinct. Verify `metadata.version: "5.5.0"` from the actual loaded Skill before concluding it has changed behavior.

## Files in patch

New professional workflow + asset-accounting reference + optional deterministic/review validators + standardized synthetic cases; modifies `SKILL.md`, original-v0.4 contract, consultation/report decision rules, CI, CHANGELOG. Includes per-release comparison and executed test report, **no actual personal records**.

**Authority scope:** tax/legal and investment calculations require actual host primary-source retrieval and user-specific data; v5.5 does not implement certified tax law or investment product advice.
