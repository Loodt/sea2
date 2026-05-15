# Success Pattern: landscape — LLM infrastructure cartographer — surveys hosted-inference provider landscape from primary developer docs (pricing/quota/rate-limit/auth pages), cross-checks against current community reports, tags every limit with a source URL and date, and flags provider-doc silence as [UNKNOWN] rather than guessing

## Strategy
Expert type "LLM infrastructure cartographer — surveys hosted-inference provider landscape from primary developer docs (pricing/quota/rate-limit/auth pages), cross-checks against current community reports, tags every limit with a source URL and date, and flags provider-doc silence as [UNKNOWN] rather than guessing" for landscape question.
Question: Map the free-tier LLM API landscape as of April 2026. Enumerate hosted providers that offer OpenAI-compatible chat completions at $0 cost to a solo developer: at minimum NVIDIA NIM (integrate.api.nvidia.com), Google AI Studio / Gemini API, Groq Cloud, Cerebras Inference, Mistral La Plateforme, HuggingFace Inference API + HF Inference Providers, Together.ai, Fireworks.ai, DeepInfra, OpenRouter `:free` models, GitHub Models (Azure AI), Cloudflare Workers AI, plus Asia/China free tiers (Z.AI GLM, Moonshot/Kimi vouchers, DeepSeek promos, SiliconFlow gift balance, Alibaba Model Studio free quota). For each: base URL, auth header shape, which models are free-accessible, documented rate limits (RPM / TPM / RPD), whether tool/function calling and structured output (json_object / json_schema) work at the free tier. Exclude paid-only tiers (local-llm-stack already mapped them).

## When It Works
- Question type: landscape
- Converged in 4/5 iterations

## Evidence
- Dispatch: D0
- Question: FLQ001
- Findings produced: 29
- Iterations: 4/5
- Status: answered

## Key Decisions
Iter 4 closed the capability-verification mechanism question (FLQ008) via primary-doc fetches: Cerebras tool calling + strict-mode structured args verified for gpt-oss-120b; Gemini OpenAI-compat tools + json_schema (Pydantic/Zod) verified with beta-risk flag; Mistral tier numbers remain admin-dashboard-gated so aggregator 1B TPM stays best-available; NVIDIA staff explicitly deny forum as a rate-limit-increase channel (falsifies seed X-post claim e); Z.AI direct function-call sub-pages 404 — recommended path is GLM-4.7 via Cerebras proxy. Landscape question FLQ001 is now ANSWERED: 13+ providers characterized, 7-archetype taxonomy, 4-tier SEA-fit shortlist with tool-calling overlay. Residual unknowns (streaming+tools simultaneity, json_object vs json_schema per provider, Alibaba 90-day claim, Cerebras qwen tool calling, Z.AI direct response_format) are integration-depth — testable in minimal-harness at adoption time, not landscape blockers.