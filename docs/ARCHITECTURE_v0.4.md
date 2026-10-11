# Wealth Planner Skill — v0.4 implementation architecture

Date: 2026-10-11. This document records what *exists in code*; it is not a speculative roadmap.

## Three-layer model

```text
Claude Code / Codex host Agent  [understands request, permissions, host tools]
                 |
          Skill SKILL.md         [intake/research/model/evidence workflow]
                 |
          wealth_cli.py         [stdlib validation/router/local conditional math]
                 |
       lib/wealth_core/
       profile.py               [strict data contract]
       capabilities.py          [declaration validation + conservative states]
       orchestration.py         [jurisdiction map + required host actions + receipts]
       finance.py               [Decimal currency-isolated finance snapshot]
       report.py                [human-readable explainable output]
       data/official_domains    [domain allowlist ONLY, not current law]
```

## Data flow

```text
User question + private profile (synthetic example as test)
 -> parse profile/schema v0.4, facts vs assumptions
 -> report declared capability manifest (offline is default)
 -> derive country/state/city and bank/income/asset contacts
 -> emit needed actions [research law / macro / read files only when requested]
 -> deterministic cashflow in currency-separated buckets
 -> inspect externally supplied receipts (optional, metadata only)
 -> 12 workflow-stage statuses + blocked decisions + source/amount audit hashes
 -> host converts to user-facing explanation and invokes REAL tools where permitted
```

### Hand-off protocol

`python scripts/wealth_cli.py plan --input X --capabilities Y --format json` returns:

- `requested_host_actions[].{id,kind,requires,scope,state,fallback}`: what a host with those declarations should consider doing. **This is not execution.**
- `host_action_receipts.items[]`: source metadata provided by the host, checked for action ID, date, hash, apparent official-domain match, tax year. The program DOES NOT parse the source content or conclude law applicability.
- `financial_snapshot.currency_buckets`: conditional declared personal cash flow, not definitive tax-adjusted investable wealth.
- `blocked_decisions`: fixed safety constraints that cannot be removed by a citation or tool manifest alone.
- `audit` SHA256 IDs to compare identical inputs and declared capabilities across runs; no private persistent store.

### Why the core is inside Skill

Copying just `SKILL.md` or just `skills/personal-finance-planner/` should preserve portable execution. A root-level `wealth_core/` package would disappear when a Skill installer fetches only the Skill subfolder. Canonical code is therefore `skills/personal-finance-planner/lib/wealth_core` in v0.4; a future service can import or publish this package separately with proper packaging.

## Boundaries

The Skill is NOT a scheduler or independent Agent; it has no web/network method and doesn't know what tools Codex/Claude really have. The host must map logical capabilities to actual tool calls and give consent and outputs. The financial snapshot includes only realized, bank-received net amounts, not untransferred PF simulated profits. If tax is unknown, the account's available invested income is unverified. Cross-currency units never silently convert. Debt payments are counted exactly once from liabilities. No automatic external side effects.

## Next version dependencies

- v0.5: effective-dated tax, payroll and jurisdiction-specific calculators, authoritative evidence interpretation, official source replay fixtures.
- v0.6: portfolios, social security/401(k) and pensions, multi-currency ledger with dated FX, goals-based asset-liability matching and estate/insurance review.
- v0.7: long-term calibrated capital market models, historical scenarios, loss/sequence risks and sensitivity analysis.
- v0.8+: authorized private account integrations, local/private persistence, controlled scheduling, security and compliance evaluation.

## Manual real-host acceptance (not yet done)

See `tests/host_e2e/README.md`. CI does NOT certify real Claude/Codex invocation, latest laws or internet access. All external host capabilities are simulated by input manifests in unit tests.
