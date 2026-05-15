# Success Pattern: landscape — Asia LLM API product/pricing analyst (OpenAI-compatible + tool-calling/structured-output focus)

## Strategy
Expert type "Asia LLM API product/pricing analyst (OpenAI-compatible + tool-calling/structured-output focus)" for landscape question.
Question: Which Asia/China-origin LLM APIs or gateways in April 2026 are credible cheap SEA runners through minimal-harness? Evaluate z.ai / GLM, Moonshot Kimi K2.6, DeepSeek, Alibaba DashScope / Qwen, MiniMax, SiliconFlow, Baidu ERNIE, Tencent Hunyuan, ByteDance Volcano / Doubao, and any credible gateways that expose these models. For each: current price, context window, OpenAI-compatible endpoint availability, tool/function-calling support, structured-output or JSON-schema support, streaming behavior, account/geography/payment constraints, quality evidence for agentic research/tool use, and whether it should be promoted above or below GPT-5.4 mini / Gemini Flash / subscription CLI routes from F957.

## When It Works
- Question type: landscape
- Converged in 5/5 iterations

## Evidence
- Dispatch: D38
- Question: LQ057
- Findings produced: 77
- Iterations: 5/5
- Status: answered

## Key Decisions
Desk research converges that the only Asia/China-origin providers that should be tested *ahead* of GPT-5.4 mini for cheap SEA minimal-harness runs are Z.AI (very low token prices plus OpenAI-style streaming + function calling + tool-streaming) and DeepSeek direct (OpenAI-compatible base_url + tool calling + JSON output mode at materially lower cost than GPT-5.4 mini). [DERIVED: F999, F998] Kimi K2.6 has the best documented contract fit (ToolCalls + JSON schema mode + SSE streaming), but its list pricing is near/above GPT-5.4 mini unless cache-hit dominates, and it has top-up/rate-limit constraints. [SOURCE: https://www.kimi.com/resources/kimi-k2-6-pricing] Alibaba Model Studio (DashScope/Qwen) remains the cheapest on paper in International mode, but its documented tools+stream incompatibility conflicts with minimal-harness’s lowest-friction streamed tool loop (usable only if the harness can accept non-stream tool turns). [DERIVED: F999] Tencent Hunyuan and Baidu Qianfan/ERNIE can be extremely cheap on their RMB pricing tables, but they add real-name / billing-mode friction (Tencent) and still have unconfirmed tool/structured-output behavior in their OpenAI-compatible surfaces (Baidu), so treat them as experimental until smoke-tested. [SOURCE: https://cloud.tencent.com/document/product/1729/97731] In practice, SiliconFlow (gateway; OpenAI-style `tools`/`response_format`) and other gateways (e.g., TokenHub, ZenMux) are valuable when direct provider signup/payment is blocked, but they can introduce extra KYC/recharge friction. [SOURCE: https://docs.siliconflow.com/en/faqs/misc_finance]