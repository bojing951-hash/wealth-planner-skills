# Wealth Planner decision hierarchy (original architecture)

**Not all conflicts are trade-offs.** A plan is considered only if it passes hard constraints before preference comparisons.

1. **Legality / authorization (hard):** applicable law, current official source + year, tax-residency, asset access, financial account permissions. Missing material legal facts ⇒ `BLOCKED_FOR_SPECIFIC_TAX_OR_LEGAL_CONCLUSION`.
2. **Solvency / liquidity (hard):** owned bank-received cash, obligations, known/unknown taxes, emergency buffer, high-cost debt, insurance exposure. Non-owned and PF simulated balances excluded.
3. **Goal / liability matching (hard where payment date fixed):** spending currency, needed cash date, lifetime goals, dependents, transfer and inheritance constraints.
4. **Evidence / modeling validity (hard for claims of precision):** reliable data, math conservations, research study scope, documented real/nominal treatment and FX. Historical backtests do not guarantee forecasts.
5. **Tax-after-fee purchasing power / risk / simplicity (trade-off):** compare diversified alternatives, concentration and drawdowns, implementation workload, behavioral risks. Do not optimize expected yield without capacity to survive worst cases.
6. **Preference and user confirmation:** show defensible options, conditions and consequences; never impose one "scientifically optimal" mix. User may choose or refer licensed professionals.

## Default outcomes

| Situation | Required outcome |
|---|---|
| No live verified tax rule | conditional tax issue list, not precise current tax figure |
| Tool only listed in sample manifest | `NOT_AVAILABLE_UNTIL_HOST_CONFIRMS`; no claim it ran |
| Unknown goal horizon | general education only; no exact allocation |
| Income volatile / PF | separate trading earnings and actual authorized withdrawable/received income; stress interruptions |
| No model calibration | scenario illustration, never calibrated success probability |
| User asks for automated external transfer/trade/tax filing | out of scope for Skill; do not autonomously execute |
| Long-horizon macro news | update research assumptions/review thresholds, not tactical transactions |

## Approval tiers

- `L0`: read public sources only when host permits.
- `L1`: personal file/account reads require explicit consent and a specific scope.
- `L2`: private state write requires consent and an auditable, private destination.
- `L3`: placing trades, transferring assets, opening accounts, submitting returns or exporting sensitive data is outside autonomous Skill execution.

## Value discipline (v5.4, subordinated to all hard constraints)

The mathematical future value of a newly planned contribution is not realized profit. Evaluate actual human behavior, incremental after-tax **owned** funds, liquidity, risk and wellbeing. A cash-to-investment shift cannot be double-counted as new household principal. A useful **no-change** finding outranks a manufactured optimization. Require a credible status-quo comparator and separate observed facts from assumed compound growth. This augments D03/D04/D08/D09/D10 without adding a new architecture domain.
