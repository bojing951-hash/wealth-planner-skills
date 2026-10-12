# v5.4 GitHub sync note — IMPORTANT

**Remote repository:** `bojing951-hash/wealth-planner-skills`; last observed default branch `main` had v5.2 on 2026-10-12. The user's product `README.md` was edited directly on GitHub and **must be preserved**. Full-source ZIP contains a reproducible source snapshot, but may differ from customized remote documentation. Do not replace the entire remote tree.

**Recommended sync:** on a fresh checkout, check version in `skills/personal-finance-planner/SKILL.md`. If v5.2, apply existing `v5.2_to_v5.3.patch` and then `v5.3_to_v5.4.patch` (supplied in the patch bundle). If v5.3, apply only second patch. Stop and inspect diffs if the branch has additional independent changes. Neither patch modifies repository root `README.md`, `README.zh-CN.md` or `docs/DEVELOPMENT.md`.

After applying: `python tools/manifest.py --write` in the actual checkout; `python tools/check_architecture.py --strict`; run both unit suites and smoke cases; inspect and commit regenerated MANIFEST. If a patch does not apply cleanly, stop rather than forcing or overwriting users' changes.

**GitHub write status:** current tool connection has read-only permissions (`push=false`); this work was not pushed by this environment. Updating GitHub requires an authorized user/workstation workflow.

Only synthetic JSON cases in public examples/tests. Financial private memory vault and keys must never be copied into Git.
