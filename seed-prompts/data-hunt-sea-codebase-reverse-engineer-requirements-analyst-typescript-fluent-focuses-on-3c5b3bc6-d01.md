# Success Pattern: data-hunt — SEA codebase reverse-engineer / requirements analyst (TypeScript-fluent, focuses on Provider/ProviderConfig contract, context budgets, dispatch lifecycle in conductor + expert-loop)

## Strategy
Expert type "SEA codebase reverse-engineer / requirements analyst (TypeScript-fluent, focuses on Provider/ProviderConfig contract, context budgets, dispatch lifecycle in conductor + expert-loop)" for data-hunt question.
Question: What does SEA minimally require from an LLM + harness combination, derived from the codebase? Read src/types.ts (CONTEXT_BUDGETS, CONDUCTOR_CONTEXT_BUDGETS, Provider, ProviderConfig, Finding, Question, ExpertHandoff, HybridResult), src/conductor.ts, src/hybrid-agent.ts, src/expert-loop.ts. Output: (a) minimum context window in tokens, (b) required output formats (free text vs structured JSON vs both), (c) required tool surface (web search, file read/write, bash?), (d) instruction-file convention assumptions (CLAUDE.md-style loading?), (e) single-shot vs multi-turn dispatch pattern. This forms the specification every candidate stack must meet.

## When It Works
- Question type: data-hunt
- Converged in 2/5 iterations

## Evidence
- Dispatch: D1
- Question: LQ007
- Findings produced: 10
- Iterations: 2/5
- Status: answered

## Key Decisions
SEA's harness contract derived from src/types.ts + src/hybrid-agent.ts + src/runner.ts: (a) ≥80-128K token context window practical floor (16K from SEA prompt + harness overhead + tool returns + output); (b) BOTH free-text Markdown with bracketed epistemic tags AND a fenced ```json``` HybridResult block, fixed status enum; (c) web search + web fetch + file read + file append-write — bash not required, permission-bypass flag mandatory; (d) auto-discovered instruction file in cwd (CLAUDE.md/AGENTS.md), harness's responsibility not SEA's; (e) single-shot per LLM call via stdin-pipe + stdout-collect, 15-min timeout, multi-turn agentic loop hidden inside the single shot. 10 findings written F901-F910.