# SEA vs SEA2 — Comparison Protocol (Pre-Registration)

**Status:** Locked at `commit 55f9498` on 2026-05-15. Any change after this commit must be explicit and timestamped (see §6).

**Purpose:** Pre-register the 12 metrics, run conditions, and decision rule for the apples-to-apples au-token comparison **before** SEA2's first dispatch. Mitigates comparison contamination (§risks in `~/.claude/plans/see-the-research-done-cozy-diffie.md`).

---

## 1. Run conditions

| | SEA (incumbent) | SEA2 (challenger) |
|---|---|---|
| Project | `~/code/sea/projects/au-token/` (already run) | `~/code/sea2/projects/au-token/` (cold start) |
| Goal | `goal.md` verbatim | Same `goal.md` verbatim, copied unchanged |
| Endpoint at lock | conductor iter 58, dispatches 60, ~888K tokens, 916 findings, 117 questions | not started |
| Hardware/network | operator's workstation | operator's workstation |

### 1.1 Budget caps (SEA2 only — SEA's run is fixed history)

SEA2 stops at the **first** of:
- Completion gate fires (`open_questions == 0` AND `active_question_id is None`).
- `conductor_iteration ≥ 60`.
- Cumulative prompt + output tokens ≥ **1,000,000**. (Matches SEA's observed spend +12% to avoid under-budgeting SEA2 vs reality.)
- Wall-clock ≥ 96 hours of compute.

The first cause-of-stop is recorded as the endpoint and used in metric #7.

### 1.2 Equivalent inputs

- Same `goal.md`. Hash recorded at lock time:
  - SHA-256 of `sea/projects/au-token/goal.md` to be captured before SEA2 dispatch.
- Same operator. No mid-run prompt edits to SEA2's persona/CLAUDE.md once first dispatch is made.

### 1.3 What is explicitly different (by design — does not constitute contamination)

- Architecture: generation-first (SEA) vs retrieval-first (SEA2).
- Verification: none (SEA) vs Tier 0–3 (SEA2 as Phase 2+ ships).
- Conductor heuristics: SEA's accumulated CLAUDE.md vs SEA2's code-enforced commitments.
- Persona library: SEA's vs SEA2's `seed-prompts/` re-curation.

---

## 2. The 12 metrics

Each metric is defined as `(name, formula, source-of-truth, win-direction, win-margin)`. A metric is a "win for SEA2" only if SEA2's value crosses the win-margin against SEA's, not on tied or noise-level differences.

### Output quality

**M1. Citation resolvability.**
- *Formula:* (# findings with `tag=SOURCE` AND `source.id` matches `^(url:|https?:)` AND HEAD resolves to 200–399) ÷ (# findings with `tag=SOURCE` AND `source.id` matches `^(url:|https?:)`).
- *Source:* SEA2 `findings.jsonl` (Tier 0 already labels these); SEA's run re-scored offline via the same Tier 0 URL checker.
- *Win:* higher. *Margin:* SEA2 must beat SEA by ≥ 10 percentage points absolute.
- *Note:* DOI / arXiv resolution is scored separately as M1b once Phase 2 ships those resolvers; M1b is a tie-breaker, not one of the 12.

**M2. Quote-supported rate.**
- *Formula:* (# findings with non-null `verbatim_quote` AND quote substring-matches the content of `admitted_chunk_id`) ÷ (# findings with non-null `verbatim_quote`).
- *Source:* SEA2 `findings.jsonl` join the chunk store (Phase 2 deliverable). SEA does not produce verbatim quotes consistently — SEA's denominator may be ~0; in that case M2 is recorded as `N/A for SEA` and counts as a SEA2 win **iff** SEA2's rate ≥ 60%.
- *Win:* higher. *Margin:* ≥ 10 pp, or SEA2 ≥ 60% if SEA is N/A.

**M3. Verifier disagreement rate.**
- *Formula:* (# findings where Tier 2 isolated-cross-family verifier verdict ≠ extractor verdict) ÷ (# findings audited by Tier 2). Audited subset = 30% random sample, RNG seed pinned at §5.
- *Source:* SEA2 `events.jsonl` (`VALIDATE_FAIL` + Tier 2 events). SEA has no Tier 2; re-run SEA's findings through SEA2's Tier 2 verifier post-hoc using the same sample size.
- *Win:* **lower** disagreement = system's extractor is more reliable. *Margin:* ≥ 5 pp.

**M4. DAG orphan rate.**
- *Formula:* (# findings with `tag=DERIVED` AND ≥1 premise in `derived_from` that does not resolve in the store) ÷ (# findings with `tag=DERIVED`).
- *Source:* SEA2 `findings.jsonl` (integrate rejects these by construction, so SEA2 = 0). SEA's `derivationChain.premises` re-scored against SEA's `findings.jsonl`.
- *Win:* lower. *Margin:* any non-zero difference (this metric is binary in practice).

**M5. Domain coverage.**
- *Formula:* (# of the 11 pre-listed au-token sub-topics with ≥ 3 verified findings) ÷ 11. Verified = `status=verified` for SEA; `verifier_status=VERIFIED` for SEA2.
- *Sub-topics (pre-listed from `goal.md`):*
  1. WP1 — token architecture & legal classification
  2. WP2 — stage-gated valuation algorithm
  3. WP3 — transparency & disclosure framework
  4. WP4.a — financial-sector / tokenisation regulation
  5. WP4.b — environmental & operational permitting
  6. WP4.c — property/ownership acquisition
  7. WP4.d — legislative-change risk (2025 Bill)
  8. WP5 — redemption, liquidity, exit
  9. WP6 — comparative benchmarking
  10. WP7 — governance, rights, dispute resolution
  11. WP8 — oracle / production verification
- *Sub-topic assignment:* a finding belongs to a sub-topic if its `domain` exact-matches the sub-topic's keyword set (keyword sets fixed in `docs/comparison-domain-keywords.json` before first dispatch).
- *Win:* higher. *Margin:* ≥ 2 sub-topics absolute.

**M6. Operator-labeled accuracy.**
- *Formula:* (# findings labeled `correct` by operator) ÷ (# findings labeled `correct` OR `wrong`). `unclear` excluded from denominator.
- *Sampling:* random sample of **50** findings from each system, no replacement, stratified by sub-topic when possible. RNG seed pinned at §5.
- *Procedure:* labels recorded **before** the operator sees which system produced which finding. Findings are shuffled into a single 100-row sheet with system column hidden until labelling is closed (§4).
- *Win:* higher. *Margin:* ≥ 8 pp (corresponds to ≥ 4/50 finding difference, above expected sampling noise).

### Process quality

**M7. Iterations to convergence.**
- *Formula:* `conductor_iteration` at the moment the budget cap fires (§1.1). For SEA, this is 58. For SEA2, recorded from `ProjectState`.
- *Win:* **lower** (faster to convergence). *Margin:* ≥ 10% relative.
- *Edge case:* SEA2 hits token/wall-clock cap before completion gate → record actual `conductor_iteration` and flag "cap-stop" in the result; the system that ran the longer effective trajectory is not penalised on this metric alone.

**M8. Token cost per verified finding.**
- *Formula:* (cumulative prompt + output tokens) ÷ (# findings with `verifier_status=VERIFIED` for SEA2; `status=verified` for SEA).
- *Source:* SEA2 `events.jsonl` (span events to be added in Phase 2 deliverable D-Phase2-spans) + `findings.jsonl`. SEA: `metrics/spans.jsonl` + `knowledge/findings.jsonl`.
- *Win:* lower. *Margin:* ≥ 20% relative.

**M9. Wall-clock time per iteration.**
- *Formula:* median of `(iteration_end_ts − iteration_start_ts)` over all conductor iterations.
- *Win:* lower. *Margin:* ≥ 20% relative.

**M10. Silent-failure event count.**
- *Formula:* count of events of types `STORE_APPEND_FAIL`, `PRODUCE_FAIL` without follow-up retry, plus any infra-debt markers (PERSISTENCE_GAP, counter-drift, SCORE_FIELD_LOSS) detected by the offline scorer.
- *Source:* SEA2 `events.jsonl` (built-in). SEA: re-scored by scanning SEA's logs + diffing `findings.jsonl` against `metrics/conductor-metrics.jsonl` for `findingsAdded` vs persisted delta (existing audit-loop logic ports as the scorer).
- *Win:* lower. *Margin:* ≥ 1 absolute (any difference, but SEA2 = 0 is the design target).

### Decision quality (the actual point)

**M11. Operator confidence in final report.**
- *Formula:* Likert 1–10 rating ("how usable is this for the au-token go/no-go decision?").
- *Procedure (blinded):*
  1. Both systems' final summaries (`output/integrated-strategy.md` for SEA; SEA2's regenerated summary + structured report) are exported to `comparison-blind/A.md` and `comparison-blind/B.md`, randomly assigned to A and B by a coin flip recorded out-of-band.
  2. Operator reads each in randomised order, takes notes, assigns a confidence rating per document **before** unmasking.
  3. Mapping {A,B}→{SEA,SEA2} unsealed only after both ratings are written.
- *Win:* higher. *Margin:* ≥ 2 points. **Required for the overall decision rule (see §3).**

**M12. Flagged-for-followup count.**
- *Formula:* count of findings/claims the operator flags during M11 reading as "need to re-verify before acting." Flagging happens on the blinded version.
- *Win:* lower. *Margin:* ≥ 25% relative.

---

## 3. Decision rule

Same as plan §D.5:
- **SEA2 wins ≥ 7 of 12 metrics including M11** → SEA2 supersedes; SEA enters maintenance.
- **SEA wins ≥ 7 of 12** → fork was wrong; revert to `sea/.claude/plans/reliability-uplift-fallback.md`.
- **Mixed (≤ 6–6) or M11 tied** → re-run on `sa-tax-loophole-agent` before deciding.

"Ties" within the win-margin count as a tie, not a win for either side.

---

## 4. Operator-confidence elicitation protocol

To minimise contamination (operator authored SEA2 and knows what SEA produced):

1. Before SEA2's first dispatch, the operator writes a one-paragraph "expected differences" memo to `comparison-blind/expected.md`. This is not used to score; it lets us check post-hoc whether the rating moved in the predicted direction (which would be a contamination signal).
2. SEA's final report is locked at `comparison-blind/sea-final.md` (sha-pinned) before SEA2 finishes.
3. Once SEA2 reaches its endpoint, an assistant (not the operator) does the A/B masking by a single coin flip and writes the mapping to `comparison-blind/.mapping` (gitignored locally; the file just records `A=SEA, B=SEA2` or vice versa).
4. Operator reads A then B (or B then A — sealed reading order also chosen by coin flip, recorded), rating + flagging on each.
5. Mapping unsealed only after both ratings + flag counts are committed.

---

## 5. Pinned constants

```
RNG_SEED                = 17  # used for M3, M6 sampling
TIER2_AUDIT_FRACTION    = 0.30
M6_SAMPLE_SIZE          = 50
GOAL_HASH_SHA256        = <captured at first dispatch into ./projects/au-token/goal.sha256>
SEA_TOKEN_SPEND_BASELINE = 887924  # approximate, used for §1.1 budget sizing
```

`docs/comparison-domain-keywords.json` — the WP→keyword mapping for M5 — will be committed before first SEA2 dispatch and never altered after.

---

## 6. Amendment record

| Date | Commit | Change | Reason |
|---|---|---|---|
| 2026-05-15 | 55f9498 | Initial pre-registration. | Phase 1 close. |

Any change to §2, §3, or §5 after first SEA2 dispatch invalidates the run for comparison purposes; the run can still be useful for development but cannot supersede SEA via §3.

---

## 7. References

- Plan: `~/.claude/plans/see-the-research-done-cozy-diffie.md` Part D.
- Phase 1 plan: `~/code/sea2/.claude/plans/sea2-phase-1-foundation.md`.
- au-token goal: `~/code/sea/projects/au-token/goal.md`.
- SEA postmortem (failure-mode catalogue): `docs/sea-postmortem.md`.
- Article alignment audit: `docs/article-alignment-audit.md`.
