# Success Pattern: design-space — LinkedIn content pipeline architect with AI-generated-text detection and human-review-gate design experience

## Strategy
Expert type "LinkedIn content pipeline architect with AI-generated-text detection and human-review-gate design experience" for design-space question.
Question: How should the LinkedIn Social Operator spec incorporate the anti-ai-slop writing layer (findings F3001-F3003) — as generator system-prompt constraint, post-generation lint pass with rewrite, reviewer checklist in the human-review gate, or rejected entirely? Evaluate against LinkedIn-specific failure modes: 'AI-generated content without substantial rewriting is detected and down-ranked', profile-content alignment scoring, and the 60-90 day calibration period. Decide placement in the Social Operator pipeline, calibrate strength of F3002 (vocab) vs F3003 (structural) independently, and specify the rewrite loop contract (max passes, acceptance criteria).

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D11
- Question: QQ010
- Findings produced: 7
- Iterations: 2/4
- Status: answered

## Key Decisions
Architecture C' selected: F3002 auto-swap via deterministic regex + pre-approved substitution map (no LLM in loop); F3003 flag-only with reviewer adjudication. Placement = new Stage 2.5 between F989's Stage 2 and Stage 3, feeding F945 Dimension-5 penalties and Stage 4 reviewer UI. C' Pareto-dominates the original C (which had F3003 auto-rewrite) by removing the 60%-confidence structural rewrite that risked voice collapse. Rewrite loop contract: max_passes=1, zero F3002 matches = acceptance, unmapped tokens escalate to reviewer. Full telemetry schema + re-tune triggers + 60-90d exit criteria specified; initial numeric thresholds tagged [ESTIMATED] with tune mechanism. All 5 answered-criteria met; 5 architectures compared (A, B, C, D, C').