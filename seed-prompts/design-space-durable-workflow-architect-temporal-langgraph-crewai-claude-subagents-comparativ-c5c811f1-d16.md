# Success Pattern: design-space — durable-workflow architect (Temporal/LangGraph/CrewAI/Claude-subagents comparative)

## Strategy
Expert type "durable-workflow architect (Temporal/LangGraph/CrewAI/Claude-subagents comparative)" for design-space question.
Question: Given Option B (stateful hybrid) as Q003's default topology, which conductor implementation framework (Claude Code subagents pattern, Temporal workflow + entities, CrewAI role-agents + tool layer, LangGraph declarative graph) best fits HERALD's constraints for durable agent persistence, snapshot/restore of SA2 identity state, centralized routing-service injection, and 4-checkpoint operator mediation?

## When It Works
- Question type: design-space
- Converged in 4/4 iterations

## Evidence
- Dispatch: D16
- Question: Q006
- Findings produced: 16
- Iterations: 4/4
- Status: answered

## Key Decisions
Q006 ANSWERED. Primary recommendation: LangGraph >= 0.2 with langgraph-checkpoint-sqlite SqliteSaver as HERALD's VMA conductor framework. Selected via 4-stage funnel: CrewAI killed in Stage 1; LangGraph / Temporal / hand-rolled Claude Code conductor characterised in Stage 2 deep-evals; Stage 3 ordinal matrix showed no row-sum dominator but LangGraph is the only framework viable across all three branches of a tri-modal solo-operator pause-SLA distribution (40/40/20 sub-hour/sub-day/multi-day) without bolt-on -- lowest-regret. Stage 4 emitted conditional fallbacks (Temporal if T3>50% or multi-tenant; hand-rolled if T1>80% and solo-only forever) plus 5 rollback triggers. Iter-4 web-search validated the load-bearing API claims: interrupt() / Command(resume=) / SqliteSaver are public-API GA as of 2026-01 per LangChain reference docs and PyPI release 2026-01-19. Q025 emitted to operator to collapse the conditional but the primary recommendation does NOT block on operator response.