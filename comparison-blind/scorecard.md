# SEA vs SEA2 — au-token Comparison Scorecard

SEA scored at:  `2026-05-15T19:23:24.677855+00:00` (C:\Users\mtlb\code\sea\projects\au-token)
SEA2 scored at: `2026-05-15T19:25:17.840171+00:00` (projects\au-token)

## Headline numbers

- SEA findings: 916 total, 308 verified
- SEA2 findings: 133 total, 37 verified

## Per-metric scorecard

| Metric | SEA | SEA2 | Verdict |
|---|---|---|---|
| M1 Citation resolvability | 50.3% | 78.7% | SEA2 |
| M2 Quote-supported rate | N/A | 99.2% | SEA2 (SEA N/A) |
| M3 Verifier disagreement rate | N/A | N/A | — |
| M4 DAG orphan rate | 85.8% | 0.0% | SEA2 |
| M5 Domain coverage | 36.4% | 9.1% | SEA |
| M6 Operator accuracy | N/A | N/A | — |
| M7 Iterations to convergence | 58.000 | 10.000 | SEA2 |
| M8 Token cost per verified | 2038.295 | 2699.432 | SEA |
| M9 Wall-clock per iteration (ms) | 219295.000 | 136324.779 | SEA2 |
| M10 Silent-failure event count | 0.0% | 0.0% | TIE (within margin) |
| M11 Operator confidence | N/A | N/A | — |
| M12 Flagged-for-followup | N/A | N/A | — |

## Decision rule check

- SEA2 wins: **4 of 12**
- SEA wins:  **2 of 12**
- Ties:      **6 of 12**

**Decision rule:** No outcome yet. M11 + M12 are operator-supplied; run `scripts/blind_compare.py` next.

## Notes from scorers

- [SEA] M1 denominator: 376 URL-sourced findings (resolver not yet wired for SEA)
- [SEA] M2 N/A for SEA — no verbatim_quote in TS schema
- [SEA] M3 N/A for SEA — Tier 2 audit not run against SEA findings
- [SEA] M10 SEA proxy: findingsAdded>0 but findingsPersisted==0 in metrics/conductor-metrics.jsonl
- [SEA2] M9 fell back to metrics.jsonl inter-row deltas (spans missing durations)