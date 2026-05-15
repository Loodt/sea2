# Success Pattern: mechanism — child-safe UI sandbox and content-governance architect

## Strategy
Expert type "child-safe UI sandbox and content-governance architect" for mechanism question.
Question: Minimum-viable Jarvis kid-safety layer on top of MCP Apps remoteDom: what component whitelist + output sanitizer architecture handles Afrikaans/English copy-deck enforcement without blocking legitimate pedagogy UI?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D34
- Question: JQ082
- Findings produced: 17
- Iterations: 3/5
- Status: answered

## Key Decisions
Iteration 3 closed JQ082 by turning the earlier threat taxonomy into a concrete v0 policy. The answer is a narrow host-owned semantic component whitelist, not raw HTML rendering, and a four-stage host pipeline that separates structural gating, markup sanitization, URI/action policy, and Afrikaans/English copy-deck enforcement. The key design move is to preserve semantic teaching structures that pedagogy actually needs while removing hidden, styling, overlay, outbound-link, and tool-call channels. The child-safety boundary therefore lives in the Jarvis host renderer, not in MCP Apps itself or in prompt wording alone.