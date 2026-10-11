# Jurisdiction gate and regulatory boundaries

1. Identify residence, tax residence claim, citizenship/US person status, activities' actual locations, payer country, bank/custodian country, income tax year, asset situs, and target retirement location separately.
2. For U.S. residents distinguish **federal**, state and city rules; research local tax existence instead of assuming it. For CN distinguish central tax rules, local social insurance/housing fund conditions. An EU location requires a named member state.
3. Verify effective legal text via host current-source research. `jurisdictions/*.json` and `policies/authority_sources.json` are bookmarks and *may be out-of-date*; a URL or old article is not a verified tax computation.
4. Do not hardcode annual tax rates into a universal finance calculator. No tax rate used in v0.4. Net wages in examples are hypothetical user-provided after-withholding amounts.
5. If unresolved cross-border residency, treaty applicability, source classification, investment eligibility, estate/situs rules or licensing: block definite recommendations; offer specific questions for an appropriately qualified local accountant/lawyer.
6. Illegal actions, evasion or automatic transactions are prohibited. Funding and withdrawal operations require a separately licensed/authorized system and additional review beyond this Skill.

Guide to prior research: `references/jurisdiction-workflow.md` and the legacy `scripts/jurisdiction_router.py` preflight. `lib/wealth_core/data/official_domains.json` is only a receipt-domain sanity check; **it does not prove what law says**.
