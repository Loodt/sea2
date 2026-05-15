# Success Pattern: kill-check — quantization-stack benchmark researcher (BFCL V4 + combined weight+KV-cache quantization degradation on Qwen3-8B Q4_K_M)

## Strategy
Expert type "quantization-stack benchmark researcher (BFCL V4 + combined weight+KV-cache quantization degradation on Qwen3-8B Q4_K_M)" for kill-check question.
Question: For Stack-A' consumer-8GB deployment tier, does Qwen3-8B-FC Q4_K_M with q8_0 KV-cache quantization at 16K context preserve the BFCL V4 advantage over Llama-3.1-8B-Prompt baseline, or does the combined weight+KV quantization stack drop the score below 25.83%?

## When It Works
- Question type: kill-check
- Converged in 3/5 iterations

## Evidence
- Dispatch: D28
- Question: LQ044
- Findings produced: 8
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ044 ANSWERED — VERDICT: PASS. Qwen3-8B-FC Q4_K_M + q8_0 KV at 16K context projects to 40.1-42.6% BFCL V4 Overall, leaving +14.3 to +16.8pp margin over the 25.83% Llama-3.1-8B-Prompt floor. Two risk inversions emerged this iteration: (1) bf16-native q8_0 KV actually outperforms f16 KV on Qwen3.5 (llama.cpp #20035 — q8_0 PPL 6.5489 vs f16 6.5511), closing the F913 concern; (2) Qwen3 BFCL V4 baseline already uses YARN to 64K, so LQ044's 16K target is within the fp16 evaluation envelope, making context amplification ≤1.0. Stack-A' consumer-8GB tier is VIABLE at 16K with Q4_K_M + q8_0 KV. Empirical-gate remains open for production commit.