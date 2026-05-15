# Success Pattern: synthesis — interlink artifact publication synthesist

## Strategy
Expert type "interlink artifact publication synthesist" for synthesis question.
Question: What stable ID assignment, row ordering, and provenance-fill rules are still needed to emit the first `interlinks.jsonl` artifact from the already-resolved class-A ledger without reopening exploratory branches?

## When It Works
- Question type: synthesis
- Converged in 2/5 iterations

## Evidence
- Dispatch: D15
- Question: Q016
- Findings produced: 13
- Iterations: 2/5
- Status: answered

## Key Decisions
[DERIVED: F9958] The first artifact should use minted append-only `il_` IDs, not whole-row content hashes, because whole-row hashes would churn on benign publication edits and require extra canonicalization machinery beyond the resolved ledger. [DERIVED: F9960] File order is now explicit: preserve the settled three phases, keep the resolved Phase-A leader block first, then sort replayably by canonical `from_ref`, family, and stored source signature. [DERIVED: F9959] Attachment arrays are ordered data and must preserve their resolved textual/primary-parallel sequence rather than being auto-sorted. [DERIVED: F9961] Provenance fill is already closable from the store with non-empty finding/question arrays plus artifact-context `discovered_by` and `run_id`, and conditional fields should be omitted when not applicable instead of using ambiguous nulls. [DERIVED: F9962] No exploratory branch needs to be reopened to emit the first deterministic `interlinks.jsonl`.