# v5.1 Skill-first maturity — Developer Preview

## What actually changed from v5.0

- The **Skill** is now authoritative: professional workflow, evidence policy, legal/household hard gates, macro and dynamic reviews direct the **host** to call its actual tools. No homegrown `host-queue` step is mandatory for normal use.
- The optional v5 calculator backend remains **backward-compatible**; the profile schema stays `5.0.0` and the calculator identifies as `5.0.0` even when the packaging Skill release is `5.1.0`.
- The exact v0.4 architecture plan is preserved as an immutable baseline; structural assertions and a mandatory release comparison enforce its ten domains and twelve states.
- Added release gates and host E2E manual acceptance cases; NOT a claim that live host testing occurred.

## Explicit limitations

1. **Real cross-country tax and law:** no certified region/tax-year tax plugins; primary-law retrieval is delegated to actual host, unverified cases blocked or hypothetical.
2. **Investment / portfolio:** conditional model and evidence instructions with optional math; not a personalized licensed investment product recommendation.
3. **Macro and theory:** curated references with conditional literature interpretation; no live academic-source freshness proof without host retrieval.
4. **Stochastic paths:** uncalibrated user-assumed Monte Carlo, no predictive claim.
5. **Private finance:** no connector permission on install; no auto-sync or secure cloud account database; L1/L2 require consent.
6. **Monitoring:** review is on demand; no always-on task or automated order placement.
7. **Host interoperability:** SKILL.md follows open standard, but real Codex and Claude Code end-to-end installation, tool permissions, source retrieval and user-facing report output **remain NOT_TESTED** in this environment.

**Release status**: `Developer Preview`; structural guard + unit and offline smoke pass as recorded in `docs/ARCHITECTURE_ALIGNMENT_v5.1.0.md`. The guard is not a substitute for real financial/legal expertise or host E2E evaluation.
