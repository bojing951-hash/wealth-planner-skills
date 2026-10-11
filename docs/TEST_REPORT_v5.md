# v5 本地测试报告（2026-10-11）

**Release tested**: `Wealth Planner Skills v5.0.0 — Developer Preview`。

## Automatic tests

- Legacy old Skill tests: **46 passed** (v0.1–0.3 CLI/math and jurisdiction/theory regression).
- Repository tests including v0.4 and new v5: **86 passed** (27 legacy v0.4 + 59 v5 and additional boundary tests).
- **Combined 132 unittest cases passed locally**.
- Python compileall on new libs and CLI: passed.
- JSON Schema draft 2020-12: profile + model schemas valid. Five synthetic profile samples and two scenario bundles validated.
- Five synthetic city/PF CLI runs: passed. Single-folder portability v5 CLI: tested without repo root.

### Covered failure modes

- PF simulated nominal funds incorrectly treated as income/owned net wealth; gross-only income;
- cross-currency money aggregation and missing income currency;
- fake source receipts, unavailable permissions, dubious official domains or future law effective dates;
- theoretical conflict context, multi-country tax residence checks;
- non-finite/incompatible covariance, user-assumption validation, mis-specified tax schedule;
- seed replay, FI heuristic arithmetic, annuity targets, model-created probabilities guarded;
- changed income/region/tax year/model assumptions trigger review; unchanged run id remains stable;
- portability of standalone Skill directory, both old and new CLIs.

### Not covered and NOT claimed

- Live Claude Code and Codex host E2E (separate checklist, **not run**).
- Live official tax-law fetching/interpretation and audit of actual tax return calculations.
- Real bank/portfolio integrations, production penetration testing, legal counsel sign-off.
- Historical forecast calibration, market regime and fat-tail backtesting, empirical retirement success odds.

See `tests/host_e2e/README.md` and `docs/MATURITY_AND_GAPS.md`. Passing local tests is not a professional financial advice certification.
