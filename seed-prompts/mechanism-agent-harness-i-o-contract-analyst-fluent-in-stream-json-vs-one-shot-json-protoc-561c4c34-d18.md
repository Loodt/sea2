# Success Pattern: mechanism — agent-harness I/O contract analyst — fluent in stream-json vs one-shot-JSON protocols and SEA provider-adapter observability requirements

## Strategy
Expert type "agent-harness I/O contract analyst — fluent in stream-json vs one-shot-JSON protocols and SEA provider-adapter observability requirements" for mechanism question.
Question: Does the SEA harness-provider interface (src/types.ts) need extension to distinguish stream-json-native harnesses (Claude Code, Codex MCP) from one-shot-JSON harnesses (OpenHands --json, cn -p --json, Aider /yes-always) for observability parity?

## When It Works
- Question type: mechanism
- Converged in 2/5 iterations

## Evidence
- Dispatch: D18
- Question: LQ031
- Findings produced: 5
- Iterations: 2/5
- Status: answered

## Key Decisions
LQ031 resolves ANSWERED=NO. The 'stream-json-native vs one-shot-JSON' dichotomy is structurally false in current SEA because both Claude (F937) and Codex (F938) are configured in opaque-text mode — the stream-json capabilities exist in the CLIs but SEA explicitly opts out. The single consumer-side observability primitive (hybrid-agent.ts:139 regex on opaque stdout) is provider-agnostic, so no parity gap exists to close (F940). Extending ProviderConfig before extending the consumer schema would be architectural inversion: the correct ordering is consumer-first, provider-second (F941). Recommendation: keep types.ts:3 Provider string-union and ProviderConfig shape unchanged; revisit only if SEA flips claude baseArgs to stream-json OR a new stream-aware consumer is introduced.