# Success Pattern: synthesis — memory-schema synthesis architect

## Strategy
Expert type "memory-schema synthesis architect" for synthesis question.
Question: Design the per-child knowledge schema. What entities (developmental profile, learning-pattern observations, attunement signals, session-by-session findings, doctrinal-formation notes, parent-coaching log, age-band markers, passion signals)? What relationships? What's the file/table structure? How does it support both a 3yo's session and a 9yo's session with the same shapes?

## When It Works
- Question type: synthesis
- Converged in 3/5 iterations

## Evidence
- Dispatch: D6
- Question: JQ020
- Findings produced: 17
- Iterations: 3/5
- Status: answered

## Key Decisions
[DERIVED: synthesis over F1019-F1023] Stage 3 completed the move from taxonomy to implementable schema. The per-child store should be rooted in one child subject graph with first-class participant links, append-only sessions and evidence, maintained pattern/state objects, and explicit obligations. The correct persistence split is not notes versus profile; it is append-only evidence plus versioned current-state objects with provenance and evidence refs. That layout supports both a 3-year-old and a 9-year-old with the same schema because age differences live in values and metadata, not in separate table families. JQ065 remains downstream for the minimum telemetry fields inside each event, but it no longer blocks the JQ020 schema answer.