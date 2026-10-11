# Intake, normalized amounts and financial ownership

Schema: `schemas/profile-v0.4.schema.json` in this Skill directory, or use `scripts/wealth_cli.py validate` when installed standalone. For stand-alone distribution the Python input validation is the executable contract; the repo JSON Schema is for clients and future adapters.

Minimum: as_of, residence (country+region+city), self-claimed tax residencies where known, each monthly income (bank_received, realized, gross vs net_received, tax_status), expense categories, user-owned vs restricted vs simulated assets, liabilities/debt payment, goals, income stability, consents.

Numbers must be decimal strings and ISO currency. NEVER add USD and CNY directly. NEVER count PF nominal funding, challenge balance or simulated P&L as owned personal assets. PF realized payout may be recorded as cash but tax still unknown until determined. Payroll net deposited by an employer may still require annual tax reconciliation; do not assume all tax obligations settled. Expenses with category `tax_reserve` represent extra reserves from already-deposited cash; do not re-subtract payroll withholding from net receipts. Debt payments belong only in `liabilities[].monthly_payment`, not duplicated as expenses.

Reserve target uses 6 months for stable income and 12 months for volatile/unknown, adjustable via `risk.reserve_months`—**pure heuristics, not evidence of optimality**.

`source_status` is provenance (user claim vs document vs independently verified). The actual contract for profile and event structure is in `lib/wealth_core/profile.py`. An unknown fact remains unknown; the host may propose clarification or conditional alternatives.
