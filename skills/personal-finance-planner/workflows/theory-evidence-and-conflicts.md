# Evidence-to-decision workflow: claims, applicability, disagreement

The canonical unit is a **claim**, not a guru, book title, or author. The source index in `references/classic-books-and-primary-works.md` and `policies/theory_graph.json` is curated background, not proof of what is current or universally valid.

## Step 1 — State the financial decision and find only relevant claims

Example: 20-year household portfolio with high but volatile business income. Relevant mechanisms: Modigliani lifecycle consumption, asset/liability matching, Markowitz covariance, Bogle/Sharpe costs, Fisher real vs nominal, Thaler automatic saving, tail risk and local tax constraints. Unrelated biographies are not required.

## Step 2 — Evidence class (DO NOT force a single ordinal ranking)

- **Identity/accounting/math:** logically true given definitions and assumptions; prove input consistency and algebra.
- **Conditional model:** Markowitz, lifecycle, stochastic simulations; explicitly state assumptions and parameter error.
- **Empirical/behavioral:** studies such as Thaler/Benartzi; quantify sample, methods, region, time, selection bias, robustness and replications.
- **History/backtest:** SPIVA, safe withdrawal history; disclose survivorship, regime, asset mix, tax and currency transferability.
- **Practice rule/philosophy:** Graham's margin of safety or Bogle-style low-cost indexing; evaluate implementability and evidence, do not assert a universal optimum.
- **Legal rule:** independent category. Current enacted and applicable law requires primary source; never vote against it using research papers.

## Step 3 — Claim card (use structure; store privately only if authorized)

| Field | Purpose |
|---|---|
| `claim_id` and `statement` | falsifiable or conditionally testable proposition |
| `evidence_kind` / `source` / `locator` | paper, book section, primary law, official statistic, data release |
| `publication_date` / `effective_date` / `retrieved_on` | edition or tax year validity |
| `sample_geography` / `sample_period` / `population` | limits of transferring the result |
| `assumptions` / `counterexamples` | identify scenarios where it fails |
| `decision_applicability` / `confidence_notes` | why use it for this person, and limits |
| `competing_claims` / `resolution_status` | complement, conditional tension, genuine disputed finding |

See machine-readable example at [../assets/claim-card-example.json](../assets/claim-card-example.json).

## Step 4 — Adjudication: contradiction is NOT a vote

- **Graham vs Bogle:** active price-value analysis needs a verifiable skill/fee/time advantage; broad low-cost indexing may be a baseline. Both can be presented with evidence thresholds; cannot claim all active investing is impossible.
- **Markowitz vs Taleb/tail risk:** standard covariance describes ordinary dependence; supplement severe stress/tail uncertainty. Related, not logically incompatible.
- **Modigliani vs volatile PF/business income:** lifecycle planning remains useful but needs income shock, liquidity, and ruin scenarios; don't project one good trading week indefinitely.
- **Bengen vs global retirement:** US sample withdrawal percentages are historic contingent reference points, not universal 30-year safe annuities; re-evaluate in user's currency and tax regime.
- **Thaler automatic savings vs user control:** proposals for authorized, revocable budgeting automation only, never automatic trades/transfers without permitted regulated product and approval.

## Step 5 — Convert evidence into a decision **condition**, not an order

Represent each conclusion as: `WHEN (verified conditions) → CONSIDER (candidate policy) → VERIFY (costs/risks/legality) → IF NOT (fallback/blocked)`. Do not silently replace missing data with typical returns. A claim with weak external validity can motivate a sensitivity test but must not lock the user's long-term portfolio.

The legal/tax gate and household liquidity gate outrank preferences in asset theories. Where primary researchers disagree, show competing interpretations and uncertainty rather than manufacturing “a harmonious consensus.”
