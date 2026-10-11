# Dynamic planning — finite, event-driven, versioned re-evaluation

**This Skill is not a daemon.** A review only runs when the user re-invokes it or a separately supported, authorized host/external scheduler does so. No background work may be promised on installation.

## Triggers by materiality

| Tier | Condition (examples, not guaranteed universal thresholds) | Action |
|---|---|---|
| Immediate / gate | different tax residence or jurisdiction; filing year or enacted material law change; job loss; dependent/care event; large debt; liquidity breach; permission revoked | halt affected conclusions, retrieve current official rules as authorized, reconstruct feasible plan |
| Monthly | actual take-home and necessary expense deviation, PF *bank payout* vs simulated account equity, reserve runway | update fact provenance and cashflow; avoid mechanical strategy change |
| Quarterly / material | portfolio policy drift beyond user-approved bands, bond yield regime, persistent inflation shift, major capital requirement | research assumptions and consider *review*, not a trade order |
| Annual | retirement horizon, household changes, long-term return estimates, benefits/pension status, currency spending needs | full goal/scenario review including after-tax/fee/real purchasing power |
| Noise / no trigger | one-day rate move, single month's stock returns or news headline, minor unverified market story | record if material to user's question; don't alter strategic allocation by default |

## Review algorithm conducted by host

1. Obtain the **prior authorized snapshot** only after explicit L1 consent, or label `NO_PRIOR_STATE`. For opt-in stored local context follow [local-memory.md](local-memory.md); an existing vault is NOT blanket consent. If persistence was not permitted or host storage is inaccessible, ask user to supply prior plan without inventing history.
2. Gather new date-stamped facts and current legal/macro evidence. Separate data update, **law or rule change**, assumption update, and user preference change.
3. Classify each difference as `FACT_CHANGE`, `LEGAL_CHANGE`, `MODEL_CHANGE`, `PREFERENCE_CHANGE`, `EVIDENCE_CORRECTION`, or `NO_MATERIAL_CHANGE`.
4. Recalculate only impacted domains, but enforce all hard constraints; state what remained fixed and why. A changed macro input first calls for sensitivity review, not automatic rebalancing.
5. Output `old_value → new_value`, cause, evidence, effective date, estimated consequence, reliability, approval needed; record snapshot hash if saved privately by consent.
6. For complex law/tax disputes stop actionable optimization pending local professional review. Do not automatically file taxes, trade or move money.

**Optional offline comparer:** `python3 <SKILL_DIR>/scripts/wealth_v5.py review --previous <private_prior.json> --current <private_current.json>` compares two *provided* reports. It does not observe bank accounts or verify new laws. Only use if host can run it and inputs exist.

### v5.2 opt-in memory bridge

On an authorized subsequent session, read a dated summary, flag stale/future-dated values, verify material changes with the user, then run relevant regular 12-state workflow gates. Show a preview of *only* the normalized changed fields (and optional short plan/decision abstracts). After L2 approval of the exact preview, use revision compare-and-swap and change fingerprint to commit. The record is never independent evidence of current account balances, tax law or investment prices; do not trade, file tax returns or automatically modify assets. If no local memory is available, continue as a one-off Skill.
