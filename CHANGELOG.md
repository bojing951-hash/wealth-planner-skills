# Changelog

## v5.2.0 — Optional persistent local memory, no new Agent (2026-10-11)

- Added opt-in, **off by default** encrypted local state: dated minimal profile, financial facts, short planning decisions, revision snapshots and on-demand differences. Independent of host Agent runtime.
- Separate private key and encrypted vault paths; AES-256-GCM, no plaintext fallback, restrictive POSIX file permissions, no repo writes, atomic updates, cross-process lock and compare-and-swap revisions.
- Consent-first host instructions (L1 read, L2 every save/delete); preview with change digest to prevent accidental payload mismatch; encrypted wipe/field-forget/category purge and opt-in plaintext export with warnings. This is not cryptographic proof of human approval.
- Added security/privacy negative tests, two-session same-directory CLI demonstration, portable Skill references and original-v0.4 architecture comparison gate.
- Kept ten domains, twelve states, financial safety boundaries and optional calculators; real Codex/Claude Code host E2E is **NOT_TESTED**. No background daemon or account sync.


## v5.1.0 — Skill-first refactor, original-architecture gate (2026-10-11)

- Re-aligned with the *original v0.4 overall architecture and gap plan* without deleting any of the original ten professional domains or twelve workflow states.
- New concise `SKILL.md`: **host-agent executes tools directly**; legacy `host-queue` optional only, not a required host execution engine.
- Added claim-based empirical/theoretical evidence workflow, localized legal/tax gates, capability and consent routing instructions, dynamic re-planning protocol, report contract and ten-domain normative index.
- Preserved existing v5 deterministic helper CLI and backward compatible `5.0.0` schema. Report package version `5.1.0` separately from optional calculator version `5.0.0`.
- Archived exact original baseline and SHA256; added machine structural release guard, mandatory post-release comparison, and manual host E2E rubric (`NOT_TESTED`).
- No new licensed financial/tax product or autonomous bank/trading services; no claim of calibrated forecasting or live host verification.

---

# Change Log

## 5.0.0 (2026-10-11) — developer preview

Real, tested source-code changes, not a release-certification claim:

- Host action queue is included in the integrated output and remains declarative; v0.4 manifest/receipt validation reused (no false tool execution).
- Existing v0.3 cross-disciplinary theory graph now selected and compared in normal `run` workflow.
- Effective date/official domain/scope preflight for externally supplied law packets; lifetime/tax-residency issue spotting across legal contact points, with no pretend legal certification.
- Lifecycle, savings, liabilities, insurance and inheritance issue screening.
- Portfolio weights/fees/covariance/distance from targets diagnostics and PSD checks.
- Pure annuity math for targets; emergency funds separated from investable assets.
- 10–50 year seeded Monte Carlo scenario model with incomes, expenses, optional retirement/income interruption and inflation, and explicit limitations.
- FI initial withdrawal heuristic screen. Returns and source assumptions remain user-provided, uncalibrated.
- Manual comparison of prior/current reports with material changes and tax year/jurisdiction triggers; user authorizes storage separately. Versioned input/model/evidence hashes.
- Multicurrency separation and explicit FX converter helper; never infer tax or cross-border permissions from account location.
- New standalone `wealth_v5.py`, five synthetic test profiles, documents, tests and CI. Old 73 v0.4/v0.3 tests remain.

### Explicitly **not** implemented or certified

- No complete current-year binding local tax engine, treaty calculator, Social Security or 401(k) eligibility calculator.
- No accurate real-time macro data calibration, fat-tail/stochastic regime forecasting, or independently verified probability of financial independence.
- No host-independent agent, automatic cross-account syncing, background scheduler, brokerage trades or automatic tax filings.
- No true end-to-end installation/research execution on user Claude/Codex host or GitHub publishing.

## 0.4.0

Legacy portable Python profile + capability declarations + source-receipt task protocol and five cross-jurisdiction hypothetical cases. See `docs/ARCHITECTURE_v0.4.md`.

## 5.1.0 (2026-10-11) — Skill-first alignment, original-architecture audit

- Pinned the **exact original v0.4 architecture** under `docs/BASELINE_ORIGINAL_v0.4.md` with recorded SHA256; did not replace or dilute ten domains or twelve states.
- Rewrote `SKILL.md` to delegate discovery, retrieval, reasoning and tool use directly to authorized **host agents**; `host-queue` is explicitly optional, not an autonomous runtime or a required first step.
- Added separate focused workflow and reference protocols for host source research, evidence-to-policy conflicts, jurisdiction rules, risk/liquidity gates, dynamic **on-demand** reviews and report/audit contract.
- Kept the v5.0.0 deterministic backend for optional reproducible mathematics; reported Skill v5.1.0 separately from math version v5.0.0 to avoid falsely claiming upgraded forecasting.
- Added original architecture structural guard and **per-release comparison requirement**; extended CI to run release guard alongside unit tests.
- Published honest maturity, remaining gaps and manual real-host E2E acceptance specification. **No claim of successful live Codex/Claude Code tests**.
