# Success Pattern: data-hunt — BFCL V4 benchmark analyst with tool-calling quantization-sensitivity focus

## Strategy
Expert type "BFCL V4 benchmark analyst with tool-calling quantization-sensitivity focus" for data-hunt question.
Question: Does BFCL V4 multi-turn category (most KV-sensitive) specifically degrade more than Overall under Q4_K_M + q8_0 KV stack at 16K, even if Overall margin remains >14pp?

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D30
- Question: LQ045
- Findings produced: 13
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ045 resolves YES structurally: Multi-Turn MUST degrade more than Overall in pp terms under any KV-dominated perturbation by construction of BFCL V4's 0.30-weighted Overall formula (F972/F975). Iter 3 anchored magnitude via q8_0-KV empirical data (+0.0043 PPL on Qwen 2.5 Coder 7B, F977) and llama.cpp consensus that q8_0 is in the quality-safe band while sub-q8_0 triggers the multi-turn-specific repetition failure mode (F978, TurboQuant corroboration of F970). Derived bound: Multi-Turn ~2-6pp, Overall ~1-2.5pp (F979), both far below F922's 14-17pp shortlist margin — stack is safely acceptable. Residual: empirical BFCL V4 local run recommended as verification but not blocking.