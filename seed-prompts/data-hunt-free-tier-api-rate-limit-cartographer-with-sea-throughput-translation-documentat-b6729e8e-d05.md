# Success Pattern: data-hunt — free-tier API rate-limit cartographer with SEA-throughput translation (documentation sweep + token-band × RPM/TPM/RPD arithmetic grounded in local-llm-stack F944 85k+10k band)

## Strategy
Expert type "free-tier API rate-limit cartographer with SEA-throughput translation (documentation sweep + token-band × RPM/TPM/RPD arithmetic grounded in local-llm-stack F944 85k+10k band)" for data-hunt question.
Question: Document current (April 2026) rate limits and free-quota structure for the top Western free tiers: Google AI Studio / Gemini API (per-model RPM/TPM/RPD for 2.5 Flash, 2.5 Flash-Lite, 2.5 Pro; free-tier data-use-for-training policy), Groq Cloud (per-model RPM/TPM/daily tokens for Llama-3.3, Qwen, GPT-OSS, Kimi variants; tool-calling support), Cerebras Inference (Llama / Qwen / GPT-OSS TPM), Mistral La Plateforme (free experimentation tier model list + limits), GitHub Models (Azure AI) (models exposed + per-model caps + whether a paid Azure sub is required), Cloudflare Workers AI (neuron quota + models hosted). For each, translate the rate limit into 'SEA outer iterations per hour/day' at 85k input + 10k output tokens (local-llm-stack F944). Cite each limit to the provider's own current doc URL.

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D5
- Question: FLQ004
- Findings produced: 20
- Iterations: 3/5
- Status: answered

## Key Decisions
FLQ004 closed with primary-doc evidence for 5 of 6 providers (Cerebras, Cloudflare, Groq, GitHub Models, Gemini-training-policy) plus Mistral primary-doc-stated admin-gate. Key finding from stage-4 synthesis: three Western free tiers (Groq, GitHub Models, Cloudflare) are hard-blocked at F944 per-request size — the tier-stack strategy cannot aggregate hard-blocked providers. Only Cerebras (admission-semantics TBD), Mistral (ESTIMATED), and Gemini (billing-attached for training-opt-out) remain plausible for F944-band SEA workloads, reducing the 6-provider free stack to 3.