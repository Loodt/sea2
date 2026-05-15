# Success Pattern: data-hunt — API rate-limit empirical prober (runs curl against hosted LLM endpoints, interprets 429 vs 200 + Retry-After + x-ratelimit-* headers, distinguishes per-request admission gates from rolling-window averaging)

## Strategy
Expert type "API rate-limit empirical prober (runs curl against hosted LLM endpoints, interprets 429 vs 200 + Retry-After + x-ratelimit-* headers, distinguishes per-request admission gates from rolling-window averaging)" for data-hunt question.
Question: Empirical probe of Cerebras free-tier TPM admission semantics at F944 band: does a single 85K-input request against qwen-3-235b-a22b-instruct-2507 (TPM=60K) get admitted (rolling-window average) or rejected (per-request admission gate like Groq)? 30-minute curl probe with api.cerebras.ai/v1/chat/completions.

## When It Works
- Question type: data-hunt
- Converged in 2/5 iterations

## Evidence
- Dispatch: D6
- Question: FLQ014
- Findings produced: 18
- Iterations: 2/5
- Status: answered

## Key Decisions
FLQ014 answered via secondary evidence after iter-1 revealed the literal 85K probe is shape-infeasible (context=65K) and credentials absent. Cerebras docs verbatim (F911) resolve the admission regime: pre-flight estimator = input+max_completion, rejected before processing if exceeds current bucket — this is a per-request admission gate, not debt-mode averaging. The bucket itself replenishes continuously (F910), so Cerebras is a third regime distinct from both Groq's fixed windows and from rolling-window averaging. F1138's rolling-window assumption flips (F916); SEA dispatch must set max_completion_tokens explicitly to pass the gate (F917). Three new questions surface: reshape throughput envelope, deprecation successor, and Retry-After semantics.