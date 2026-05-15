# Success Pattern: kill-check — citation-integrity auditor — methodical fact-checker who can resolve each phantom F-id by either (a) locating the substantive claim it was meant to support, retrieving a real source URL, and writing a properly-tagged finding, or (b) marking the claim [UNKNOWN] / removing it from the deliverable when no source exists

## Strategy
Expert type "citation-integrity auditor — methodical fact-checker who can resolve each phantom F-id by either (a) locating the substantive claim it was meant to support, retrieving a real source URL, and writing a properly-tagged finding, or (b) marking the claim [UNKNOWN] / removing it from the deliverable when no source exists" for kill-check question.
Question: Audit and remediate F434's inline citation list by creating distinct F-id findings for each of the 14 phantom references (F1021, F1102, F1111, F1114, F1115, F1121, F1325, F1326, F1329, F1607, F1609, F1610, F1611, F1706) so each substantive fact in the LQ047 deliverable has one-to-one F-id traceability.

## When It Works
- Question type: kill-check
- Converged in 5/5 iterations

## Evidence
- Dispatch: D32
- Question: LQ050
- Findings produced: 14
- Iterations: 5/5
- Status: answered

## Key Decisions
LQ050 ANSWERED. 14/14 LQ047-phantom F-ids remediated across 5 iterations via 4-stage persona workflow: iter-1 taxonomy (all taxonomy-(c) renumber-drift, 0 hallucinations), iter-2 anchor-mapping with F434->F886 supersede and F970 follow-up scoping, iter-3 anchor-verification with F972 upgrade (new llama.cpp-server SOURCE), iter-4 Stage-4 file-edit execution against output/lq047-final-shortlist.md (~80 inline call sites + section-10 citation index rewrite + section-12 caveat flip + pre-patch snapshot preservation), iter-5 consolidated audit-trail finding F976 + LQ051 filing for residual F886-internal phantoms + lineage. Every LQ050-scope phantom now carries one-to-one F-id traceability to a real finding in knowledge/findings.jsonl. Key surprise: 13/14 phantoms were pure renumber-drift from iter-027 F-id renumbering event, not hallucinations — existing store fully covered the claims, only the labels needed remapping.