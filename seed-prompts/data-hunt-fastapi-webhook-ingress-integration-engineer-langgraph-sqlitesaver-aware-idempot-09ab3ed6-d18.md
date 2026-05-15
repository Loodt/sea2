# Success Pattern: data-hunt — FastAPI + webhook-ingress integration engineer (LangGraph SqliteSaver-aware, idempotency/replay-safe handler patterns)

## Strategy
Expert type "FastAPI + webhook-ingress integration engineer (LangGraph SqliteSaver-aware, idempotency/replay-safe handler patterns)" for data-hunt question.
Question: What is the minimal HERALD webhook-receiver service shape (FastAPI route signature, auth, threadId-by-intentHash lookup table schema, retry/backoff for graph.invoke failures) given LangSmith Deployment cannot push interrupts (F929)?

## When It Works
- Question type: data-hunt
- Converged in 2/5 iterations

## Evidence
- Dispatch: D18
- Question: Q030
- Findings produced: 8
- Iterations: 2/5
- Status: answered

## Key Decisions
Q030 answered by composing two well-documented halves: greeden.me FastAPI HMAC+replay-window+ACK-fast pattern (F934/F935) and LangChain official interrupt() while-loop pattern (F936). The threadId-by-intentHash 'lookup table' is just the F930/F931 outbox keyed on intent_hash PK — no separate index required (F937). graph.invoke failures handled by two independent retry layers (provider-native via 5xx + reconcile-poll worker per F931); no in-handler retry beyond a single checkpointer-blip exception (F938). Re-interrupt after resume is expected control flow, not failure: log and ACK 200. Full minimal receiver shape composed in F939. Two follow-ups raised: pre-effect idempotency dedupe (Q-new-1) and per-provider signature header conventions (Q-new-2).