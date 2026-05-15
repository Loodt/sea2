# Success Pattern: mechanism — SEA integration-layer mechanism analyst (reads src/knowledge.ts SOURCE_URL_MISSING / needsReview paths against realistic 7B-emitted finding samples)

## Strategy
Expert type "SEA integration-layer mechanism analyst (reads src/knowledge.ts SOURCE_URL_MISSING / needsReview paths against realistic 7B-emitted finding samples)" for mechanism question.
Question: Does SEA's existing needsReview/SOURCE_URL_MISSING gate behave correctly when fed 7B-emitted findings, or does it require enhancement (HEAD-request URL resolution + claim-match LLM judge) to make 7B-with-rescue viable?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D10
- Question: LQ016
- Findings produced: 18
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ016 answered: existing needsReview/SOURCE_URL_MISSING gate does NOT behave correctly on 7B-emitted findings — it catches ~15% of URL-error weight via null/malformed regex only. Three defects confirmed: syntactic-only URL regex, dead needsReview writer, and summary/references leaks that ignore needsReview even if set. Enhancement is required AND feasible: HEAD-resolution pass at 1-5% dispatch budget closes fabricated-domain/path modes (estimated 55-75% of URL-error weight); claim-match LLM-judge is cost-viable (10-27% budget for 14B cascaded) but deferred until residual mode-5/6 weight measured empirically. The minimum-viable patch is ~200 LOC in src/knowledge.ts: HEAD pass with per-domain rate queue + production needsReview writer + reference/summary filters. Empirical sub-question LQ027 spawned.