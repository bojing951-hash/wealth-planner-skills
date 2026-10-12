# Changelog

## v5.6.1 — Master Plan integrity hotfix + controlled user-experience evaluation kit (2026-10-12)

- Fix a demonstrated validator gap: `RECONCILED` or arbitrary invalid enumeration values could pass despite unknown balances. Enforce the shipped JSON Schema without an external dependency and cross-check unknown owned assets/liabilities and reconciliation claims.
- Plans marked `USER_APPROVED` now need a non-empty separately obtained approval reference; the reference is an audit note, **not** user authentication. Existing DRAFT and CONDITIONAL Master Plan JSON remains backward compatible (`schema_version=5.6.0`).
- Add synthetic regression cases for invalid nested enums/types, extra fields, missing required fields, impossible dates, unresolved debts, unsupported schema changes and false completion/approval flags; extend GitHub CI.
- Add reproducible human-reviewed, blinded same-host Skill-vs-plain-AI evaluation **scoring kit** and real-host acceptance checklist. Only a **SYNTHETIC harness dry-run** is performed here; genuine Codex/Claude Code E2E and independent A/B remain **NOT_RUN**. No claim of demonstrated model performance improvement.
- Preserve original v0.4 architecture (ten domains and twelve states), Skill-First, safety gates, optional private memory, and existing professional planning methods. Neither algorithms nor financial services are materially expanded.

## v5.6.0 — Personal Wealth Master Plan & Governance (2026-10-12)

- **Flagship deliverable, not a new Agent:** a comprehensive user-owned wealth charter: one asset/liability ledger, dated lifetime goal obligations, non-double-counted purpose earmarks, conditional decision rules, matched options + stress, accountable 30/90/365 actions, review scorecard and approvals.
- Methods synthesise **public** CFP process and purpose-based liquidity/lifestyle/growth/legacy vs liquidity/longevity/legacy organizational concepts; not affiliated, not a copy of proprietary models, and no implication of proven superior returns.
- Added optional `master_plan_quality.py` static/ownership/currency/purpose-overallocation/unknown-tax/action-evidence safety checks, matching JSON Schema, client-facing Markdown template, two synthetic positive cases and intentional negative fixture with tests.
- Preserved **Skill-First** and original v0.4 ten domains/twelve states, with optional validators only; no independent Agent, fund picker, transfers, tax filing, new external connection or background monitor.
- Requires renewed original-architecture alignment and reports genuine tested vs untested, not a false claim of professional certification.


## v5.5.0 — Cross-border trader wealth structuring and real-plan quality (2026-10-12)

- **Skill-First** optional professional branch for clients with material PF cash payouts, personally owned brokerage P&L/equity, offshore bank payments and leveraged vehicle debt. No external account write, independent Agent, hidden transfer, background daemon or investment product picker.
- New accounting/evidence guard: bank credits (user-reported vs documented), personal brokerage NAV (owned) vs realized/unrealized P&L, internal bank-broker transfers, PF simulated non-owned funds, and vehicle-loan cash service vs principal reduction. Previous discretionary expenses are shown as a reconfirmation scenario, not silently dropped or duplicated.
- Explicit policy to **continue useful non-tax planning despite unknown taxes**: cash waterfall, 2+ conditional options, simultaneous payout loss and broker drawdown, 30/90/365 measurable actions. No arbitrary tax percentage treated as tax law; no presumed reserve funded from a good income month.
- Added optional stdlib-only `trader_wealth_reconcile.py` + `trader_plan_quality.py`, synthetic (not client) fixture and negative tests. Helpers validate arithmetic/report structure only and are not autonomous financial/tax advisors.
- Skill must disclose **actually loaded installed Skill version**, since an old v5.1.0 host copy may coexist with newer GitHub source. `/tmp` does not guarantee restart deletion; avoid writing sensitive finance input into public projects or unprotected temporary files.
- The original v0.4 architecture SHA256 is unchanged; updated mandatory ten-domain/twelve-state alignment contract and release comparison. **Real host E2E and Skill-vs-no-Skill blinded advantage remain NOT_TESTED.**

## v5.4.0 — Financial planning behavior-to-value attribution (2026-10-12)

- Required behavior → financial mechanism → matched counterfactual → observed review metric for material full financial plans, separating new savings, reallocation and hypothetical return. Added optional v5.4 arithmetic/quality utilities and synthetic tests. No actual causal value or live host validation asserted.

## v5.3.0 — Professional Financial Planning Consultation protocol (2026-10-12)

- Strengthened **Skill-First** professional-client planning: decision-focused interviewing, diagnostic issue cards, root-cause vs hypothesis, material priorities, >=2 materially distinct feasible/conditional options, quantitative savings/goal gap, 30/90/365 user-owned action register and truthful review.
- Integrated the workflow in `SKILL.md` and the reporting/state protocols **without** adding an eleventh domain, thirteenth workflow state, standalone Agent or new mandatory network backend. User-requested advanced ETF/product recommendations remain deferred.
- Added optional reserve-first `consultation_math.py`, `plan_quality.py`, JSON report schema, synthetic Shenzhen client example, and regression tests explicitly separating structural quality from actual expertise.
- Added **blind Skill-vs-plain-host** evaluation protocol (NOT_RUN) and real Codex/Claude Code E2E acceptance documentation (NOT_TESTED).
- Added manifest regenerating/checking utility for the actual GitHub checkout; intentionally do not overwrite a separately edited GitHub product README.
- Original v0.4 architecture remains immutable; report `docs/ARCHITECTURE_ALIGNMENT_v5.3.0.md`; no claim of licensed financial advice or performance improvement before independent tests.


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
