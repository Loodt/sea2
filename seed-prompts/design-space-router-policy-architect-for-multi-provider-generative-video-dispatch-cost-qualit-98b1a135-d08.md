# Success Pattern: design-space — router-policy architect for multi-provider generative-video dispatch (cost/quality/tier composition with hard budget caps and fallback ordering)

## Strategy
Expert type "router-policy architect for multi-provider generative-video dispatch (cost/quality/tier composition with hard budget caps and fallback ordering)" for design-space question.
Question: What router-policy ordering and budget-cap enforcement rules should HERALD apply when stacking 'cheapest-meeting-capability' with 'quality-tier-first' and a per-job USD ceiling, given Veo Standard/Fast/Lite and Runway Gen-4.5/Gen-4 Turbo overlap on capability but diverge 5-10x on cost?

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D8
- Question: Q009
- Findings produced: 10
- Iterations: 2/4
- Status: answered

## Key Decisions
Q009 answered with a decision-tree router policy for HERALD. Three per-dispatch policies fully specified (P_A strict-lex, P_B quality-adjusted-cost, P_C epsilon-band) plus one orchestration meta-policy (P_D staged draft workflow) — each with filter → rank → tiebreak → cap-breach-behavior → fallback-DAG. All share a pre-commit cap invariant (A1), a capability-preserving fallback DAG with bounded depth (F1141), and a permanent audit-row schema (F1142) with policy_version_hash for replay. Final recommendation (F1145) is a 5-branch decision tree keyed on capability-cluster + N_variants + destination-viewport: P_A when capability pins the provider, P_B for single-shot standard jobs, P_D+P_B for hero-shots with N≥5 (50-70% savings per F1132+F1133), structural-rule override for mobile-viewport Lite, operator-override bypass. Cap-breach default is REJECT; DOWNGRADE-WITH-CONSENT and QUEUE-AND-ALERT are opt-in by policy and job-submission flag. Declared empirical gaps (Lite cinematic rank-transfer, Turbo quality parity, P_D auto-advance signal) are pushed to Q005 or flagged as new questions, not blocking on this design-space answer.