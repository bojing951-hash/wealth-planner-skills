# Output report quality gate

Every material numeric result requires: as_of, currency, gross/net/realized and ownership basis, tax-treatment confidence, formula or CLI version and data assumptions. Legal and tax claims require effective tax year, jurisdiction, primary source and interpretation limitations. Macro data require observation date, series ID, units, currency, and no confusion with long-horizon return projections.

The v0.4 output fields are `run_id`, `audit`, `host`, `jurisdiction_map`, `requested_host_actions`, `host_action_receipts`, `financial_snapshot.currency_buckets`, `goals_registered_not_forecast`, `workflow`, `blocked_decisions`, `missing_facts`, `monitoring_triggers`. These are machine-readable for future Agent/MCP integration.

A report MUST NEVER claim a portfolio probability, tax amount or verified eligibility simply because its template includes the field. If an input is gross-only, render financial surplus as not computable; if tax status is uncertain, mark the available cash number provisional and never produce `monthly_investable_final`.

For user-facing advice, compare multiple conditional paths only when the data support doing so; otherwise provide a next-data checklist. Preserve contradictory credible evidence instead of inventing consensus. Write personal data only to user-authorized local/private destination and do not claim an ongoing monitor was set up without a real scheduling call.
