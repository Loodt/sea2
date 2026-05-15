# Success Pattern: first-principles — payment network architecture analyst with deep knowledge of four-party card-network models (Visa/Mastercard authorization-clearing-settlement) and experience mapping network-topology privacy to non-payment exchange domains

## Strategy
Expert type "payment network architecture analyst with deep knowledge of four-party card-network models (Visa/Mastercard authorization-clearing-settlement) and experience mapping network-topology privacy to non-payment exchange domains" for first-principles question.
Question: How does Visa's four-party network model (cardholder, merchant, issuer, acquirer) map to a neutral freight capacity exchange, and does the authorization/clearing/settlement architecture resolve the shipper-side gap, the privacy mechanism gap (replacing ZK proofs with network-topology privacy), and the settlement integration gap better than the current SWIFT-like message-routing model?

## When It Works
- Question type: first-principles
- Converged in 1/3 iterations

## Evidence
- Dispatch: D14
- Question: Q016
- Findings produced: 7
- Iterations: 1/3
- Status: answered

## Key Decisions
The full Visa four-party model fails the structural transplantability test for the SA freight exchange. The issuer role — the load-bearing element enabling trust between strangers — has no viable freight instantiation. None of the three gaps (shipper-side, privacy, settlement) are resolved by the four-party model. The SWIFT analogy should be refined to acknowledge blind counterparty discovery (a Visa-like function), and the acquirer-to-funder structural correspondence validates the existing external-funder design. Recommendation: retain SWIFT-like model, refine the analogy, do not adopt the four-party framework.