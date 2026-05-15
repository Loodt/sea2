# Anti-patterns SEA2 commits not to reproduce

Four patterns from SEA's failure-patterns library — the ones the spec article
does not name but which the SEA postmortem identified as the high-impact
recurring failures. Each one becomes a regression-test target as Phase 2
adds the surrounding stages. The Phase 1 work named in **Mitigation** is
already in place.

References:
- SEA failure-patterns library: `C:\Users\mtlb\code\sea\failure-patterns\`
- Postmortem: [`sea-postmortem.md`](sea-postmortem.md)
- Article alignment audit: [`article-alignment-audit.md`](article-alignment-audit.md)

---

## 1. heuristic-layer-ceiling

**Source:** `sea/failure-patterns/heuristic-layer-ceiling.md`

A behavioral heuristic written into the persona prompt cannot fix a problem
that lives in the pipeline or harness layer. Across SEA's sewage-gold
iterations 001–004, three increasingly emphatic prompt-level rules
("own your writes", "NEVER reference IDs that don't exist", "synthesis
blocked until research exits 0") all failed to prevent the same store-update
miss because the failing behavior was *execution-order*, not
*agent-decision*.

**Why it matters in SEA2:** this is the meta-pattern. It motivates commitment
5 ("code-enforced or nonexistent"): a rule that lives only in prose is
indistinguishable from a rule that does not exist.

**Mitigation already in place:**
- The completion gate, halt-reason reader, reflection-veto parser, selection
  guards, question caps, and DAG validation are all *code paths*, not prompt
  text. See `sea2/conductor/selector.py`, `sea2/conductor/caps.py`,
  `sea2/verification/dag.py`.
- `CLAUDE.md` is short by design — no behavioral mandates, only architectural
  commitments. Any future "rule" must land as code or it does not land.

**Regression test (Phase 2):** add a CI rule that rejects any new entry
under `docs/mandates/` (or similar prose-rules directory) without a
corresponding `src/sea2/*.py` enforcement reference.

---

## 2. closeout-drift

**Source:** `sea/failure-patterns/closeout-drift.md`

When every question reaches a terminal status (resolved + exhausted +
empirical-gate, with `open == 0` and `activeQuestionId == null`), the
conductor kept dispatching iterations and the producer kept re-surfacing
prior research as "new" work — apparent yield, zero store delta — driving
the iteration score down across closeout.

**Mitigation already in place:**
- `select()` in `sea2/conductor/selector.py` runs a completion gate as one
  of three early-exit conditions: if `open_questions == []` and
  `state.active_question_id is None`, the outcome is `COMPLETED` and a
  `HALT_REQUESTED` event is emitted with `source="completion-gate"`. No LLM
  call is made.
- Tested in `tests/test_selector.py::test_completion_gate_fires_on_empty_queue`.

---

## 3. operator-kill-ignored-cascade

**Source:** `sea/failure-patterns/operator-kill-ignored-cascade.md`

The evolve-step set `state.haltReason='terminal-iteration-loop'`, the
lineage recorded the marker — and the next operator tick relaunched the
project anyway, because no code path in the conductor's select step
actually *read* `haltReason` before choosing to enter the LLM ranking.

**Mitigation already in place:**
- `select()` reads `state.halt_reason` as the *first* gate (ahead of the
  completion gate and the veto parser). A non-empty value short-circuits
  the loop with outcome `HALTED` and an event payload of
  `{source: "operator", reason: <halt_reason>}`.
- Tested in `tests/test_selector.py::test_halt_reason_short_circuits_everything`.

---

## 4. pipeline-step-deferral

**Source:** `sea/failure-patterns/pipeline-step-deferral.md`

A producing step that "defers to summarize" loses its writes. Findings the
research step intended to commit never reached the store because the
intent was passed downstream rather than persisted at the producer.

**Mitigation already in place:**
- The integrate step in `sea2/conductor/integrate.py` is the *only* writer
  into `findings.jsonl`. It is invoked synchronously from the produce-side
  call site and persists each finding atomically via `atomic_append_jsonl`
  before returning. There is no "summarize-side persistence" path.
- Summary regeneration in `sea2/store.py:regenerate_summary` is a pure
  read-and-render — it cannot create findings. The store IS the source of
  truth; the summary derives from it.

**Regression test (Phase 2):** assert that no LLM-generated stage other
than `integrate` calls `atomic_append_jsonl(findings_path(...))`.

---

## 5. fix-resistant-identical-failure

**Source:** `sea/failure-patterns/fix-resistant-identical-failure.md`

A diagnostic-discipline pattern, not an execution one: after two
consecutive iterations fail with the *same* symptom, the diagnosis is
wrong. Continuing to patch at the same layer reproduces the same failure
with a different patch.

**How SEA2 honors this:** when a Phase 2+ component fails twice with
identical symptoms in CI or in an au-token run, the next action is to
re-diagnose the *layer*, not write a third patch. This pattern is the
guardrail on the response to the other four.
