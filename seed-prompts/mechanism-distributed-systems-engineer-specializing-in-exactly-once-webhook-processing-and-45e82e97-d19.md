# Success Pattern: mechanism — distributed-systems engineer specializing in exactly-once webhook processing and pre-effect deduplication

## Strategy
Expert type "distributed-systems engineer specializing in exactly-once webhook processing and pre-effect deduplication" for mechanism question.
Question: What is the minimal idempotency-key strategy for HERALD's webhook receiver — does outbox.status='terminal' check suffice, or is a separate webhook_events(provider, event_id) UNIQUE table needed to dedupe provider-side retries before graph.invoke?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D19
- Question: Q032
- Findings produced: 12
- Iterations: 3/5
- Status: answered

## Key Decisions
Q032 ANSWERED with confidence 0.9. Outbox.status='terminal' check is INSUFFICIENT alone — fails pre-effect on webhook×2 concurrent races (read-then-act TOCTOU) and on multi-writer webhook+poll paths (F1301). Required minimal strategy: separate webhook_events(provider, event_id) PRIMARY KEY table using INSERT ... ON CONFLICT DO NOTHING RETURNING as the atomic claim primitive (F1303), with outbox.status='terminal' kept as a secondary backstop after inbox claim (handles poll→webhook ordering where poll has no event_id). Schema locked: composite PK, nullable intent_hash, payload JSONB, received_at index, no status column (F1310). Retention = 7 days with daily prune — exceeds Stripe 3d + Svix 5d retry tails with safety margin (F1311). Webhook-vs-poll concurrent in-flight race (F1306 case 2) deferred to new question on poll-lease primitive — separable from receiver design.