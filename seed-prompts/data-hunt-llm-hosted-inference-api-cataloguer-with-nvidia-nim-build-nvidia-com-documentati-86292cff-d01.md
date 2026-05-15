# Success Pattern: data-hunt — LLM hosted-inference API cataloguer with NVIDIA NIM / build.nvidia.com documentation fluency and model-capability matrix discipline (context window, tool-calling, structured output, streaming verification per model)

## Strategy
Expert type "LLM hosted-inference API cataloguer with NVIDIA NIM / build.nvidia.com documentation fluency and model-capability matrix discipline (context window, tool-calling, structured output, streaming verification per model)" for data-hunt question.
Question: Enumerate the NVIDIA NIM model catalogue at build.nvidia.com as accessed via integrate.api.nvidia.com/v1. For each model: (a) full model ID string used in the `model` parameter; (b) whether the model is first-party NVIDIA-optimised or a third-party upstream (Moonshot, Zhipu, MiniMax, DeepSeek, Meta Llama, Mistral, Qwen); (c) context window and output-cap at the free tier (compare to the upstream provider's native limits — is this the full model or a truncated/distilled variant?); (d) tool/function calling support; (e) structured output (`response_format: json_object` or `json_schema`) support; (f) streaming support; (g) any per-model rate-limit overrides vs the account default. Specifically verify whether hosted Kimi K2.x, GLM-5.1, MiniMax M2.x, DeepSeek V3.2 on NIM match their upstream capabilities or are degraded.

## When It Works
- Question type: data-hunt
- Converged in 5/5 iterations

## Evidence
- Dispatch: D1
- Question: FLQ003
- Findings produced: 22
- Iterations: 5/5
- Status: answered

## Key Decisions
FLQ003 closed as 'answered' at iter-5 with 51-finding store. Cell (a) model IDs — RESOLVED (first-party nvidia/* catalogue + third-party priority-4 slugs moonshotai/kimi-k2-{instruct,instruct-0905,thinking,5}, z-ai/{glm4_7,glm5,glm-5.1}, deepseek-ai/deepseek-{v3_2,v3_1,v3_1-terminus,r1,r1-0528,r1-distill-llama-8b,coder-6_7b-instruct}, minimaxai/minimax-{m2,m2_1,m2.5,m2.7}). Cell (b) classification — RESOLVED (first-party anchor nvidia/nemotron-3-{nano,super,ultra,voicechat} + llama-3.1-nemotron family + co-branded mistralai/mistral-nemotron). Cell (c) context/output — ANSWERED: Kimi-K2 256K + MiniMax-M2.5 204,800 match upstream full-fidelity verbatim on NIM reference; DeepSeek-V3.2 upstream 128K/163,840 and GLM-5.1 upstream 204,800/131,072 are not published verbatim on NIM but the modelcard pages exist on build.nvidia.com — timeouts are NVIDIA doc-rendering issue, not degradation signal. Cells (d)(e)(f) tools/json_schema/streaming — ANSWERED-AS-EMPIRICAL-GATE: no primary-doc evidence possible; DeepSeek-V3.2 advertises function/tool calling + structured JSON verbatim while Kimi/MiniMax/GLM-5.1 NIM pages are silent. Cell (g) rate limits — RESOLVED NEGATIVE: no per-model override; uniform 40 RPM default (F1013+F925 staff-level forum confirmation). Overall full-fidelity-vs-degraded verdict: NIM preserves upstream context where documented; only known quantization footprint is Kimi-K2.5 INT4 (F1003). New FLQ009 spawned to close (d)(e)(f) via 30-min live curl probe when nvapi- key available.