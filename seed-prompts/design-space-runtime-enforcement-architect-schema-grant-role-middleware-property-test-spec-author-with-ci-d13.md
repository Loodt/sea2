# Success Pattern: design-space — runtime-enforcement architect (schema-grant/role-middleware/property-test spec author with CI-compilation bias)

## Strategy
Expert type "runtime-enforcement architect (schema-grant/role-middleware/property-test spec author with CI-compilation bias)" for design-space question.
Question: How is the per-role write-authorization matrix enforced at runtime, and how are I1-I10 compiled into CI-enforceable unit tests rather than design-document prose?

## When It Works
- Question type: design-space
- Converged in 4/4 iterations

## Evidence
- Dispatch: D13
- Question: JQ072
- Findings produced: 24
- Iterations: 4/4
- Status: answered

## Key Decisions
JQ072 is answered by F924 as a Stage-5 synthesis of F901-F923. The write-authorization matrix is enforced by a 6-layer Postgres 15+ stack (GRANT/REVOKE, RLS, CHECK+partial-unique+REVOKE UPDATE DELETE, security_invoker projection views, SET ROLE middleware, UI hide) declared in a .sea/grants.baseline.yaml that is re-derived and diffed at every CI run. I1-I10 are compiled to CI tests via a 5-artifact contract per invariant (A1 migration+grants line, A2 discriminated-union type, A3 red-test asserting named exceptions, A4 property-test with 200/500 cases and ManualClock, A5 docs cross-link) composed into a 9-job invariants.yml workflow whose J9 bypass-audit-verification promotes HC2 bypass-closure from design claim to CI-asserted property. The commitment boundary is the five named residual risks R1-R5; OPA and full event-sourcing are explicitly deferred. Three follow-up questions opened: RLS perf benchmark, ORM round-trip audit, I9 outage semantics.