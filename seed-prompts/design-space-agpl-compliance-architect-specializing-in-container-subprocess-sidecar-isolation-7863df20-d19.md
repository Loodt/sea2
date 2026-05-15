# Success Pattern: design-space — AGPL compliance architect specializing in container/subprocess/sidecar isolation patterns and MIT-AGPL boundary analysis for redistributable binaries

## Strategy
Expert type "AGPL compliance architect specializing in container/subprocess/sidecar isolation patterns and MIT-AGPL boundary analysis for redistributable binaries" for design-space question.
Question: What is the safest runtime isolation pattern for AGPL-3.0 components (MinerU, possibly skyvern) when SEA is itself distributed as a redistributable binary/image? Container boundary vs subprocess vs gRPC sidecar - which combinations satisfy the AGPL network-service source-disclosure clause without tainting SEA core MIT posture?

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D19
- Question: LQ029
- Findings produced: 15
- Iterations: 3/4
- Status: answered

## Key Decisions
LQ029 answered: P2 (separate-image gRPC-sidecar + docker-compose reference to unmodified upstream AGPL images) is the recommended default — SEA never conveys AGPL bytes, section 13 never triggers for SEA (FSF FAQ confirms section 13 is modification-scoped), total burden lowest across 7 axes. P1/P4/P3 also compliant with progressively higher burden. Container vs subprocess vs gRPC-sidecar are license-equivalent; the process boundary is what matters, not the container. Fatal patterns: in-process FFI (no section 7 rescue in either upstream) and bundled-with-SEA-modifications.