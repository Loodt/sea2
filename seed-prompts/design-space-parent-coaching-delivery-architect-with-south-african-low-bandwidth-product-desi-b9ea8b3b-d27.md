# Success Pattern: design-space — parent-coaching delivery architect with South African low-bandwidth product design context

## Strategy
Expert type "parent-coaching delivery architect with South African low-bandwidth product design context" for design-space question.
Question: Through what channel does Jarvis reach the parent — a WhatsApp message, a section of the canvas the parent opens later, a separate app, an email digest? Constraints: must keep Jarvis visibly on the child's side, must be reliable in low-bandwidth, must work when parent and child are not co-located.

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D27
- Question: JQ030
- Findings produced: 8
- Iterations: 2/4
- Status: answered

## Key Decisions
[DERIVED: architecture-synthesis] The prior iteration already eliminated canvas-only and app-only primaries and narrowed JQ030 to push-primary designs. This iteration resolved the remaining comparison by ranking WhatsApp-first above email-led: WhatsApp-class messaging best fits low-bandwidth, asynchronous, non-co-located parent contact while preserving the child-side 'projection not surveillance' rule. [DERIVED: cadence-splitting] Email survives only as an optional routine digest, not as the main rail, and [DERIVED: fallback-design] SMS survives only as a degradation or escalation path when the primary push rail fails or urgency is high. The resulting answer is a layered stack: WhatsApp-class push primary, SMS fallback/escalation, archive surface secondary, optional email digest tertiary.