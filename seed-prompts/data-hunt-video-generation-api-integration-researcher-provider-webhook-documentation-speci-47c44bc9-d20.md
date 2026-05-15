# Success Pattern: data-hunt — video-generation API integration researcher (provider webhook documentation specialist)

## Strategy
Expert type "video-generation API integration researcher (provider webhook documentation specialist)" for data-hunt question.
Question: What is Kling's and Runway's documented webhook signature header format and timestamp convention (does either match the assumed 'sha256=<hex>' + X-Timestamp shape, or do they use bespoke schemes requiring per-provider verifier classes)?

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D20
- Question: Q033
- Findings produced: 13
- Iterations: 3/5
- Status: answered

## Key Decisions
Disproved the HERALD assumption of a shared 'sha256=<hex>' + X-Timestamp verifier. Runway's workspace product delegates webhooks to Svix, which uses a bespoke scheme: svix-id / svix-timestamp / svix-signature headers, 'v1,<base64-HMAC-SHA256>' signature format, and signed content '${id}.${timestamp}.${body}' (NOT raw body alone). Runway's developer (model-inference) API does not publicly document any webhook signature scheme — recommended path is polling /v1/tasks/{id}. Kling AI uses JWT for outbound auth and per-task {endpoint, secret} for callbacks, but the callback signature specification is gated behind authenticated dev-portal access and not publicly retrievable. Conclusion: per-provider verifier classes are mandatory; SvixVerifier handles Runway-via-Svix, polling adapter handles Runway dev API, KlingVerifier is blocked on dev-portal access (empirical gate).