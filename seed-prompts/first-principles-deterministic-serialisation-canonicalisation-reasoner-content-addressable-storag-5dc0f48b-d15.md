# Success Pattern: first-principles — deterministic-serialisation / canonicalisation reasoner (content-addressable storage + equivalence-class hashing background)

## Strategy
Expert type "deterministic-serialisation / canonicalisation reasoner (content-addressable storage + equivalence-class hashing background)" for first-principles question.
Question: Scope-hash canonicalisation algorithm per CP: what is the deterministic artifact-field serialisation that makes scope_hash stable across equivalent artifact states?

## When It Works
- Question type: first-principles
- Converged in 1/3 iterations

## Evidence
- Dispatch: D15
- Question: Q025
- Findings produced: 8
- Iterations: 1/3
- Status: answered

## Key Decisions
scope_hash_v1 is fully specified — 6-step algorithm over closed per-CP schemas with universal exclusion set, RFC-8785 JCS + UAX-15 NFC + SHA-256, strict unknown-field rejection, versioned via token_version. All 5 persona convergence criteria pass in iteration 1 (≡ explicit, per-field rules cited, exclusion enumerated, versioned, stress pairs demonstrated). Q025 closes answered; Phase-1 implementation prerequisites (P1 SA2 snapshot-id canonicalisation, P2 conformance tests, P3 streaming NFC, P4 side-channel instrumentation) and two follow-up questions (SA2 snapshot-id canonicalisation verification + override_payload closed schema) handed off.