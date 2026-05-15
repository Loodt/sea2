# Success Pattern: mechanism — provider-API integration engineer (async LRO + webhook + idempotency patterns across Vertex/Runway/Kling)

## Strategy
Expert type "provider-API integration engineer (async LRO + webhook + idempotency patterns across Vertex/Runway/Kling)" for mechanism question.
Question: What is the minimal correct webhook-vs-polling adapter implementation per provider (Vertex Veo long-running operation, Runway webhook, Kling sync/poll), and what session-state guarantees must the adapter enforce for HERALD's at-most-once dispatch semantics?

## When It Works
- Question type: mechanism
- Converged in 4/5 iterations

## Evidence
- Dispatch: D17
- Question: Q008
- Findings produced: 31
- Iterations: 4/5
- Status: answered

## Key Decisions
Stage 4 complete — Q008 answered. LangGraph integration of the F923 state machine requires a three-node split (submit / wait / resume) forced by the node-restart-from-top behavior on Command(resume) (F927), with the provider POST wrapped in @task as a happy-path optimization but with the outbox UNIQUE(intentHash) as the load-bearing correctness layer (F928). Because LangSmith Deployment cannot push interrupt events as webhooks (F929), HERALD must run its own FastAPI receiver that looks up threadId by intentHash from the outbox and calls graph.invoke(Command(resume), config={thread_id}) — the same path used by the reconcile-poll worker, with StatusWriter UNIQUE making whichever loses the race a no-op (F930). State partition rule: graph state holds replayable hints, adapter outbox holds authoritative per-attempt state including threadId (F931). Five findings (F927-F931), two new follow-up questions on receiver-service shape and outbox/checkpoint colocation.