# Success Pattern: design-space — SEA observability-layer architect (consumer-side Span/event design, provider-protocol boundaries)

## Strategy
Expert type "SEA observability-layer architect (consumer-side Span/event design, provider-protocol boundaries)" for design-space question.
Question: If SEA later adds a per-tool-call HOLLOW_ANSWER detector or real-time dispatcher kill-switch, what consumer-side prototype (Span extension + per-tool-call event) unlocks protocol-aware observability without inverting the ProviderConfig layer?

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D29
- Question: LQ034
- Findings produced: 11
- Iterations: 3/4
- Status: answered

## Key Decisions
LQ034 answered: the minimal consumer-side prototype that unlocks per-tool-call HOLLOW_ANSWER detection AND real-time dispatcher kill-switch without inverting ProviderConfig has 5 components (~130 LOC over-estimated): type-level additions (ToolCallEvent + Span.toolCallEvents? + ConductorMetric.hollowToolCallCount?), runner-level observerOpts with readline+SIGTERM wiring, two-mode parser (stream-native JSON.parse OR prose-fallback regex), AbortController-based kill composition reusing SEA's crash gate, and a 5-step migration with per-step rollback triggers. Three concrete invariants (F960) prove ProviderConfig is not inverted: provider/config/RunResult shapes unchanged, opt-in per dispatch. The design fulfils F353's prescribed ordering (consumer schema first) and remains compatible with keeping Claude on --output-format text indefinitely — future stream-json adoption becomes a pure baseArgs edit with no consumer change. Converged in 3 iterations without needing the 4th.