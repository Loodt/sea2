# Success Pattern: synthesis — HERALD workflow state-machine synthesizer (consolidates CP1-CP4 transition + invalidation-DAG semantics from verified workflow-architecture findings into a formal state-machine spec)

## Strategy
Expert type "HERALD workflow state-machine synthesizer (consolidates CP1-CP4 transition + invalidation-DAG semantics from verified workflow-architecture findings into a formal state-machine spec)" for synthesis question.
Question: CP4 send-back-to-CP3 state-machine semantics: does CP3 re-entry preserve existing CP1/CP2 approvals or re-open them for re-approval?

## When It Works
- Question type: synthesis
- Converged in 3/5 iterations

## Evidence
- Dispatch: D12
- Question: Q022
- Findings produced: 12
- Iterations: 3/5
- Status: answered

## Key Decisions
Q022 answered via a scope-gated-hybrid state-machine policy: CP1/CP2 approvals PRESERVED by default on CP3 re-entry from CP4-send-back, with three declared policy switches (PS1 R5-route-legality=forbidden, PS2 CP1-literal-vs-directional=literal, PS3 per-shot-ref-override=supported) governing the invalidation cases. The 5-row by 4-column send-back matrix resolves to 8 unconditional-preserve cells, 8 policy-conditional cells, and 4 route-forbidden cells. Preserve-default is grounded in Temporal durable-signal and LangGraph checkpointer-resume semantics; invalidation fires only when send-back scope conflicts with stored approval scope_hash per AX3. Resume_token + invalidation_lineage schema v1 specified as append-only event-sourced DAG with per-CP approval ledger and frozen policy_snapshot for stable audit replay. Two follow-up questions raised: SA2 rendering-time-override feasibility and scope_hash canonicalisation algorithm.