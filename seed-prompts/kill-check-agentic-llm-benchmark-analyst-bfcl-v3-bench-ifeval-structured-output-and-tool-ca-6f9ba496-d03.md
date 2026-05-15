# Success Pattern: kill-check — agentic-LLM benchmark analyst (BFCL v3 / τ-bench / IFEval, structured-output and tool-call reliability on 7B–14B open-weight models)

## Strategy
Expert type "agentic-LLM benchmark analyst (BFCL v3 / τ-bench / IFEval, structured-output and tool-call reliability on 7B–14B open-weight models)" for kill-check question.
Question: At what rate do 7B-class open-weight models (Qwen 2.5 7B Instruct Q4_K_M, Phi-4-mini, Llama 3.1 8B Instruct Q4_K_M) fail to produce SEA-compliant structured output at 16K context? Specifically: correct emission of [SOURCE: url] / [DERIVED] / [ESTIMATED] tags, valid JSON when requested, coherent finding objects matching the Finding interface in src/types.ts, non-hallucinated source URLs. Failure-rate threshold: if >20% of dispatches produce malformed output, 7B is below the practical floor for SEA and the shortlist must start at 14B.

## When It Works
- Question type: kill-check
- Converged in 4/5 iterations

## Evidence
- Dispatch: D3
- Question: LQ006
- Findings produced: 30
- Iterations: 4/5
- Status: answered

## Key Decisions
LQ006 ANSWERED. 4-stage kill-check: Stage 1 IFEval baseline (F940-F949), Stage 2 BFCL/TAU cohort (F950-F955), Stage 3 RULER 16K degradation (F956-F961), Stage 4 Q4_K_M+GBNF+URL (F962-F969). Verdict: 7B fails the 20% threshold WITHOUT harness rescue on TWO independent axes — format compliance (Qwen 61-66%, Llama 31-36%, Phi-4-mini 49-61%) AND URL veracity (HalluLens shows Qwen 85% / Llama 48% extrinsic hallucination). WITH harness rescue (GBNF for tag-shape + tool-mediated URL emission + integration-time URL resolution), Qwen 2.5 7B and Llama 3.1 8B can plausibly cross threshold; Phi-4-mini killed by vendor-disclosed URL fabrication + BFCL projection ≤40%. Q4_K_M tax negligible (~1pp, persona estimate of 2-5pp was high). Shortlist should enumerate 7B-with-rescue AS A DISTINCT ARCHITECTURAL OPTION alongside 14B-without-rescue rather than starting at 14B unconditionally.