# Success Pattern: design-space — runtime/harness architect for durable multi-year LLM agent systems (prior art: LangGraph, AutoGen, CrewAI, Claude Code, custom conductor+file-state patterns)

## Strategy
Expert type "runtime/harness architect for durable multi-year LLM agent systems (prior art: LangGraph, AutoGen, CrewAI, Claude Code, custom conductor+file-state patterns)" for design-space question.
Question: What runtime harness should Jarvis use? Claude Code (current SEA/MAESTRO pattern, but designer-CLI not child-product), custom (build-from-scratch borrowing the conductor+experts+file-state pattern), or a third option (LangGraph, AutoGen, etc.)? Trade-offs on durability, cost, vendor lock-in, hot-swap of model providers, and child-product fit.

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D17
- Question: JQ041
- Findings produced: 13
- Iterations: 2/4
- Status: answered

## Key Decisions
JQ041 ANSWERED. Option (B) custom conductor+file-state port of SEA is the v0 harness, dominating on all 6 axes (5.00 vs Temporal 3.85 vs LangGraph 2.70). Iter 1 killed Claude Code (designer-CLI ≠ product-runtime) and AutoGen/CrewAI (vendor-graveyard + invisible-expert conflict). Iter 2 showed the remaining empirical gate on LangGraph overhead is decision-moot (value-of-information = 0 because (C) loses on state-locus and porting regardless), and that Temporal's durable-execution advantage is small at v0 short-turn topology. Named migration triggers (T1 multi-step non-idempotent, T2 multi-hour guarantee) and kill-triggers (K1 Anthropic per-child primitive, K2 multi-region <100ms) turn the answer into a durable, reversible decision. Bounded-migration property formalizes why in-house dominates when alternatives are reachable by local wrapping but not vice-versa.