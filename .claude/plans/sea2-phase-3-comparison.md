# SEA2 Phase 3+4 — Tier 2/3, scoring, comparison harness

**Date:** 2026-05-15
**Status:** Approved, ready to execute
**Prerequisites:** Phase 2 closed (commit 754213a). Comparison pre-registration locked (commit 7aa3fe2).

## Context

The user's request: "finish everything and then do the comparison." Phase 1 + 2 left a skeleton that can run a real research trajectory end-to-end on au-token. Phase 3+4 closes the remaining gap to the comparison-protocol pre-registration:

- **Tier 2 isolated cross-family verifier** (drives M3 — verifier disagreement rate).
- **Span events + token tracking** (drives M8 token cost, M9 wall-clock).
- **Tier 3 adversarial falsifier** — stretches but the plan calls for it. Pragmatic Phase 3 scope: a lightweight contradiction-finder that doesn't require retrieve to loop back. Defer the full adversarial falsifier to Phase 4 unless it lands cheaply.
- **Citation Grounding Score** — deterministic aggregate over Tier 0/1/2 per finding.
- **Comparison harness** — scorers for SEA2 and SEA, report exporter, A/B blinding tool.
- **Conformal abstention** — uncalibrated stub; calibration data comes FROM the comparison run.

## Deliverables

### D1. Span events + token tracking (~2 hours)

**Files:** `src/sea2/spans.py`, wire into `SubprocessSearcher.search()` and `extract()`.

- `Span(BaseModel)` per article §10: `span_id`, `step`, `parent_id?`, `start_ts`, `end_ts`, `duration_ms`, `prompt_chars`, `output_chars`, `prompt_tokens_est`, `output_tokens_est`, `exit_code`, `metadata`.
- `spans_path(project_dir) -> Path`; `record_span(...)` appends atomically.
- `default_runner` (and the extract subprocess wrapper) gets a `span_recorder: Callable | None` so test runners can skip. Production code wires it.
- Token estimate is chars/4 (consistent with SEA).

### D2. Tier 2 isolated cross-family verifier (~half day)

**File:** `src/sea2/verification/tier2.py`.

- `Tier2Backend` Protocol mirrors Tier 1's shape — `verify(claim, premise) → (agreement: bool, score: float, notes: str)`.
- Default backend is `AnthropicSDKBackend` — calls the Anthropic SDK directly (uses `anthropic-sdk` provider from D3 of Phase 1). Prompt is intentionally different from the extract prompt — asks the model to take a sceptical position. Feature-flagged by `SEA2_TIER2_ENABLED`.
- Sampling: configured via `SEA2_TIER2_SAMPLE_FRAC` (default 0.3 per the pre-registration §5).
- New EventTypes: `TIER2_AGREE`, `TIER2_DISAGREE`, `TIER2_SKIPPED`.
- Wired into `integrate()` as one more signal feeding `_aggregate_signals`.

### D3. Tier 3 adversarial falsifier — lightweight (~3 hours)

**File:** `src/sea2/verification/tier3.py`.

- `find_contradictions(finding, chunks)` — uses Tier 1 NLI in CONTRADICTION mode on the same admitted chunk. If the entailment label is `contradiction` rather than `neutral`/`entailment`, we have an in-chunk contradiction without a separate adversarial retrieval loop.
- Optional `adversarial_retrieve` — given a finding and a Searcher, query for the negation of the claim and run Tier 1 on the top result. Skipped by default to avoid quota burn.
- New EventType: `TIER3_REFUTED`.
- Feature-flagged: `SEA2_TIER3_ENABLED`.

### D4. Citation Grounding Score (~2 hours)

**File:** `src/sea2/verification/cgs.py`.

- `compute_cgs(finding, events_for_finding) → CitationGroundingScore`:
  - Three axes: **resolvability** (URL/DOI/arXiv resolves), **quote-supported** (TIER0_QUOTE_OK), **entailment** (TIER1_ENTAILED) — each 0/1.
  - Aggregate score in [0, 1]: weighted sum. Article §11 hints at equal weights initially.
- The aggregate sits beside `verifier_status` — `verifier_status` is the gate, `cgs` is the continuous score for ranking/reporting.
- `compute_all_cgs(project_dir)` runs over the store + events and writes one CGS row per finding to `cgs.jsonl`.

### D5. Conformal abstention scaffold (~2 hours)

**File:** `src/sea2/verification/conformal.py`.

- `compute_abstention(findings, *, calibration_set=None)` — if no calibration set, marks every finding as `uncalibrated` and returns the CGS as the confidence proxy.
- When a calibration set is supplied (CGS → human-judged correctness per finding), compute the conformal threshold at α=0.1 and mark findings below threshold as `ABSTAIN`.
- Phase 4 will use the comparison run itself as the calibration set; this module is the shape that consumes it.

### D6. Comparison scorers (~half day)

**Files:** `src/sea2/comparison/score_sea2.py`, `src/sea2/comparison/score_sea.py`, `src/sea2/comparison/protocol.py`.

- `score_sea2(project_dir, *, sample_seed=17) → ComparisonScores` — computes M1–M10 from SEA2's store + events + spans. M11/M12 are operator-supplied later.
- `score_sea(sea_project_dir, *, sample_seed=17) → ComparisonScores` — same metrics computed against SEA's TS-shape data layout (knowledge/findings.jsonl, metrics/spans.jsonl, metrics/conductor-metrics.jsonl).
- Output is JSON matching a single `ComparisonScores` schema; downstream tooling reads the JSON.

### D7. Domain keyword mapping (~1 hour)

**File:** `docs/comparison-domain-keywords.json`.

- 11 WP→keyword sets pre-listed in the pre-registration §M5. Committed before any SEA2 comparison dispatch; never altered after.

### D8. Report exporter + M6 sampler + A/B blinding tool (~half day)

**Files:** `src/sea2/comparison/report.py`, `scripts/blind_compare.py`.

- `report.export_summary(project_dir, output_path)` — write a single markdown summary from the store. Format mirrors SEA's `output/integrated-strategy.md` so the operator's M11 reading is fair.
- `report.sample_findings(project_dir, *, n=50, seed=17)` — RNG-stratified random sample for M6 labelling. Writes `comparison-blind/findings_sample.csv` with `system: hidden` column.
- `scripts/blind_compare.py` — coin-flips A/B assignment, copies SEA's and SEA2's exported summaries into `comparison-blind/A.md` and `comparison-blind/B.md`, writes the mapping to `comparison-blind/.mapping` (gitignored), and prints the reading order for the operator.

### D9. Run the comparison

Once D1–D8 land and the corpus + smoke test from the prior session are done:

1. Build au-token corpus index (`scripts/download_corpus.py` + `index_corpus`).
2. Smoke run (`scripts/smoke_run.py --max-iterations 1`) to validate the subprocess path.
3. Author the expected-differences memo to `comparison-blind/expected.md`.
4. Full SEA2 dispatch:
   ```
   python -m sea2 run au-token \
       --project-dir projects/au-token \
       --corpus corpora/au-token-regulatory/index.sqlite \
       --goal sea/projects/au-token/goal.md \
       --max-iterations 60 \
       --token-budget 1000000
   ```
5. Score both systems and run blinded comparison:
   ```
   python -m sea2.comparison.score_sea2 projects/au-token > sea2.json
   python -m sea2.comparison.score_sea sea/projects/au-token > sea.json
   python -m sea2.comparison.report export projects/au-token --output sea2-final.md
   cp sea/projects/au-token/output/integrated-strategy.md sea-final.md
   python scripts/blind_compare.py sea-final.md sea2-final.md --out-dir comparison-blind/
   ```
6. Operator reads A then B (sealed order), assigns confidence + flag counts, commits.
7. Unseal, run final decision rule per pre-registration §3.

## Explicitly DEFERRED

- Full Tier 3 adversarial-retrieval loop — Phase 4 if the lightweight in-chunk contradiction is insufficient.
- Calibrated conformal abstention — needs the comparison run to produce calibration data.
- Three-tier evaluation harness — operationalised separately from the comparison-protocol's M11.

## Verification

Phase 3 is "done" when:
1. `uv sync && pytest && ruff check && mypy --strict src/sea2` clean.
2. `python -m sea2.comparison.score_sea2 <dir>` produces M1–M10 JSON output on a fixture project.
3. `python -m sea2.comparison.score_sea <sea_dir>` produces the same shape against SEA's data layout.
4. A/B blinding tool produces masked copies with mapping sealed.
5. CGS, conformal stubs are present and tested.
