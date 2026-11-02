# Four-Bucket Monthly Budget — Fill-in Template (v5.7)

Fill locally, run locally. Prefer piping this JSON to the calculator via stdin
(`four_bucket_math.py plan --input -`) so private figures never land in any
public or shared directory. All numbers are **your own**; the repo's example
files are synthetic on purpose. Amounts as strings, e.g. `"25000.00"`.

```json
{
  "schema_version": "5.7.0",
  "as_of": "YYYY-MM",
  "currency": "CNY",
  "profile": {"income_stability": "stable|variable", "adults": 1, "dependents": 0, "notes": ""},

  "current_period_income": {
    "amount": "0.00", "currency": "CNY", "received": true,
    "recurring": true, "one_off": false, "after_tax": true, "nature": "salary|business|rental|other"
  },
  "current_period_income_extra": [],

  "income_history": [
    {"month": "YYYY-MM", "amount": "0.00", "recurring": true}
  ],

  "fx": [
    {"from": "USD", "to": "CNY", "rate": "0.0000", "as_of": "YYYY-MM-DD", "source": "bank statement"}
  ],

  "facts": {
    "safety_eligible_cash": "0.00",
    "pf_simulated_funds": "0.00",
    "restricted_investment_assets": "0.00",
    "known_tax_due_this_period": "0.00",
    "business_operating_reserve_required": "0.00",
    "brokerage_nav_owned": "0.00",
    "opening_balance_before_period": null
  },

  "obligations": [
    {"name": "rent", "monthly_payment": "0.00", "apr": null, "months_remaining": 12}
  ],
  "high_cost_debt": [],

  "necessary_living": {
    "fixed": [{"name": "utilities", "amount": "0.00"}],
    "variable": [{"name": "food", "amount": "0.00"}]
  },

  "goals": [
    {"name": "emergency_reserve", "purpose_pool": "liquidity", "amount": "0.00", "deadline": "YYYY-MM",
     "already_earmarked_from_existing_assets": "0.00"}
  ],

  "preferences": {
    "social_committed_floor": "0.00",
    "social_free_preference": "0.00",
    "reserve_months_target": null,
    "investment_eligible": false,
    "capability_plans": [{"name": "course", "monthly_amount": "0.00"}],
    "business_capital_plan": null,
    "surplus_priority": "balanced",
    "lifestyle_protection": "keep current lifestyle"
  },

  "current_pattern": {
    "living": "0.00", "savings_add": "0.00", "capability": "0.00",
    "financial_investment": "0.00", "social": "0.00", "unallocated": "0.00"
  },

  "assumption_overrides": {}
}
```

## Field notes (the ones people get wrong)

- **`received: true` only when the money actually arrived.** Expected bonuses go in `notes`, not the amount.
- **`safety_eligible_cash`** = cash you could withdraw within days. NOT your provident-fund balance (`pf_simulated_funds`), NOT brokerage holdings, NOT money owed to you.
- **`apr`** — fill the real APR for every debt. Anything ≥ 8% (editable) changes the plan: extra repayment first, risk investing blocked.
- **`fx`** — a dated rate with a source. No rate → the run intentionally refuses; two currencies are never added without conversion.
- **`already_earmarked_from_existing_assets`** — money already set aside in *existing* assets for a goal. Saying it again as this month's savings double-counts it.
- **`reserve_months_target: null`** lets the heuristic pick (3/6/9 by stability and dependents); your explicit number always overrides.
- **`assumption_overrides`** — e.g. `{"balanced.safety_gap_fill_share": "0.3"}`. Every default the engine used appears in the output with an EDITABLE marker; change it there, re-run, see the difference.

## Reading the output

1. `conservation.holds: true` — buckets + unallocated sum exactly to allocatable. If it were ever false, the run is wrong, not your life.
2. `allocatable.tax_status` — `UNKNOWN_TAX_CONDITIONAL` means treat investable figures as ceilings, not commitments.
3. `status` — `OK` / `CONDITIONAL` (read `unknowns`) / `DEFICIT` (gap + optional reserve draw; this is an income-or-floor problem).
4. `unallocated` — your buffer. It is allowed to be large.
5. Month-end: fill `actuals` inside a `{"plan": <the plan JSON>, "actuals": {...}}` wrapper and run `review --input -` — net new savings (income − consumption), planned-vs-actual variance, and the flag that catches "invested 8,000 while saving 0" (reallocation, not new savings).
