# Success Pattern: synthesis — canonical interlink export synthesizer

## Strategy
Expert type "canonical interlink export synthesizer" for synthesis question.
Question: Which already-resolved class-A interlinks should be emitted first into `interlinks.jsonl`, and what category/source-shape coverage and exclusion rules are required to turn the current store into a faithful first-pass database export?

## When It Works
- Question type: synthesis
- Converged in 2/5 iterations

## Evidence
- Dispatch: D7
- Question: Q009
- Findings produced: 11
- Iterations: 2/5
- Status: answered

## Key Decisions
[DERIVED: F1908-F1911] Q009 converged: the faithful first-pass export should be phased, not flat. [SOURCE: https://www.biblegateway.com/passage/?search=Romans+15%3A9-12&version=ESV] Romans 15:9-12 confirmed that database rows must stay at interlink granularity even when a passage functions as one catena note in a human-facing brief. [SOURCE: https://www.biblegateway.com/passage/?search=Luke+4%3A16-21&version=ESV] [SOURCE: https://www.biblegateway.com/passage/?search=John+3%3A14-15&version=ESV] Luke 4 and John 3 verified the export-critical distinction between composite and broad-source rows. [DERIVED: F1909-F1911] The file should therefore lead with schema-hardening exact exemplars, bulk-emit the remaining resolved exact pool, then append resolved broad-source and quarantined class-A rows with explicit metadata, without waiting for Q005 or Q007.