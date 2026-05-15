# Success Pattern: landscape — agentic UI protocol architect — evaluates AG-UI/MCP-UI/A2UI/CopilotKit against child-facing voice+dynamic-canvas requirements, with bias toward OSS + vendor-neutral stacks

## Strategy
Expert type "agentic UI protocol architect — evaluates AG-UI/MCP-UI/A2UI/CopilotKit against child-facing voice+dynamic-canvas requirements, with bias toward OSS + vendor-neutral stacks" for landscape question.
Question: Map the agentic UI protocol landscape: AG-UI (CopilotKit), A2UI, MCP-UI, CopilotKit Cloud, custom protocols. For each: maturity, vendor lock-in, streaming/dynamic-canvas support, voice integration, language-model agnosticism, open-source license. Recommend one (or 'build custom borrowing from N').

## When It Works
- Question type: landscape
- Converged in 4/5 iterations

## Evidence
- Dispatch: D20
- Question: JQ040
- Findings produced: 24
- Iterations: 4/5
- Status: answered

## Key Decisions
JQ040 answered. Scorecard (8 Jarvis-fit axes): MCP Apps 20/24 > AG-UI 19/24 > A2UI 14/24. Recommendation: 'build custom borrowing from N=2' — MCP Apps UI substrate + AG-UI sync/INTERRUPT contract, wired via CopilotKit's `@ag-ui/mcp-apps-middleware` (canonicalized hybrid per Microsoft Learn + CopilotKit). Hybrid cost is near-zero glue, not custom engineering. Kid-safety + voice are protocol-orthogonal — Jarvis owns those layers regardless of protocol choice. Rejected A2UI (weak critic, LLM-gravitational), CopilotKit Cloud (proprietary, violates standalone), and build-from-scratch (negative ROI).