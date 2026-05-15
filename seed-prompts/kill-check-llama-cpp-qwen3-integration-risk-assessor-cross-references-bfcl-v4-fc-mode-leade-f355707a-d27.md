# Success Pattern: kill-check — llama.cpp Qwen3 integration risk assessor — cross-references BFCL V4 FC-mode leaderboard deltas against open llama.cpp Qwen3 bug-tracker issues, Q4_K_M VRAM envelope on 6 GB Pascal, and regression risk vs Llama-3.1-8B-Prompt baseline to render a PROMOTE / REJECT / CONDITIONAL verdict with explicit falsifiers.

## Strategy
Expert type "llama.cpp Qwen3 integration risk assessor — cross-references BFCL V4 FC-mode leaderboard deltas against open llama.cpp Qwen3 bug-tracker issues, Q4_K_M VRAM envelope on 6 GB Pascal, and regression risk vs Llama-3.1-8B-Prompt baseline to render a PROMOTE / REJECT / CONDITIONAL verdict with explicit falsifiers." for kill-check question.
Question: Does Qwen3-8B-FC qualify as a Stack-A' alternative to Llama-3.1-8B-Prompt given its BFCL V4 Overall 42.57% (vs 25.83%) on same 2025-12-16 snapshot, after accounting for llama.cpp Qwen3 active-bug hazards (F1323/F1327/F1328) and Q4_K_M memory envelope?

## When It Works
- Question type: kill-check
- Converged in 3/5 iterations

## Evidence
- Dispatch: D27
- Question: LQ042
- Findings produced: 14
- Iterations: 3/5
- Status: answered

## Key Decisions
Qwen3-8B-FC qualifies as Stack-A' alternative to Llama-3.1-8B-Prompt under four conditions: (1) llama.cpp build post-PR#20385 and post-PR#20213 (Nov-Dec 2025+); (2) CUDA backend (Vulkan triggers #13310); (3) thinking disabled per SEA F1202; (4) ≥12GB VRAM devbox (8GB tier feasible only with q8_0 KV quantization). BFCL V4 advantage (+16.74pp raw) survives conservative Q4_K_M quantization estimate with ≥12pp headroom over baseline. Memory envelope at 16K context = ~7.9 GiB total (5.03 weights + 2.25 f16 KV + 0.6 compute). Primary residual uncertainty: Q4_K_M BFCL score is projected, not measured — spawned empirical-gate follow-up.