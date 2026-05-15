"""Schema for SEA2.

Article §4.3 reference schema + SEA carry-overs. All article fields land here
even if no producer fills them yet (commitment 2: schema-enforced, and avoid a
Phase 2 schema migration).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ── Epistemic / fact classification ──────────────────────────────────────────


class EpistemicTag(StrEnum):
    SOURCE = "SOURCE"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


# Article §11.4: weakest-premise propagation. Lower rank = stronger.
EPISTEMIC_RANK: dict[EpistemicTag, int] = {
    EpistemicTag.SOURCE: 0,
    EpistemicTag.DERIVED: 1,
    EpistemicTag.ESTIMATED: 2,
    EpistemicTag.ASSUMED: 3,
    EpistemicTag.UNKNOWN: 4,
}


class FactType(StrEnum):
    QUANTITATIVE = "quantitative"
    LOGICAL = "logical"
    CITATION = "citation"
    QUALITATIVE = "qualitative"
    INFERRED = "inferred"


class VerifierStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    FLAGGED = "flagged"


FindingStatus = Literal["provisional", "verified", "refuted", "superseded"]
QuestionStatus = Literal["open", "resolved", "deferred", "empirical-gate", "exhausted"]
QuestionPriority = Literal["high", "medium", "low"]
QuestionType = Literal[
    "landscape",
    "kill-check",
    "data-hunt",
    "mechanism",
    "synthesis",
    "first-principles",
    "design-space",
    "divergence",
]


class EngineeringType(StrEnum):
    MEASUREMENT = "MEASUREMENT"
    STANDARD = "STANDARD"
    DERIVED = "DERIVED"
    DESIGN = "DESIGN"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"


# ── Sub-models ───────────────────────────────────────────────────────────────


class Source(BaseModel):
    """Structured source pointer. `id` is a canonical identifier such as
    `doi:10.1000/xyz`, `arxiv:2503.12345`, or `url:https://...`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    page: int | None = None
    section: str | None = None
    paragraph_id: str | None = None


class NeedsReview(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: str
    flagged_at: str


class DerivationChain(BaseModel):
    """Legacy 1-deep premise list (SEA shape). The first-class provenance DAG
    lives on `Finding.derived_from` — keep this only for carry-over data.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    premises: list[str] = Field(default_factory=list)
    method: str
    assumptions: list[str] = Field(default_factory=list)
    uncertainty_note: str | None = None


# ── Finding ──────────────────────────────────────────────────────────────────


class Finding(BaseModel):
    """A single atomic claim with provenance.

    Article §4.3 reference schema. SOURCE-tagged findings require a `source`
    pointer (validation enforced — see `_require_source_for_source_tag`).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    claim: str
    tag: EpistemicTag
    fact_type: FactType
    source: Source | None = None
    verbatim_quote: str | None = None
    paraphrase_of_quote: str | None = None
    char_range: tuple[int, int] | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    domain: str
    iteration: int = Field(ge=0)
    status: FindingStatus = "provisional"
    verified_at: int | None = None
    superseded_by: str | None = None
    # First-class provenance graph. Premise IDs MUST resolve to existing
    # findings; cycle/orphan detection enforced at integrate-time (see
    # sea2.verification.dag).
    derived_from: list[str] = Field(default_factory=list)
    verifier_status: VerifierStatus = VerifierStatus.PENDING
    # Ties this finding back to the retrieve step's admitted chunk.
    # Commitment 1 (retrieval-first): extract output without an
    # admitted_chunk_id is rejected by the integrate step in Phase 2+.
    admitted_chunk_id: str | None = None
    needs_review: NeedsReview | None = None

    # Carry-over from SEA — optional engineering classification.
    engineering_type: EngineeringType | None = None
    derivation_chain: DerivationChain | None = None

    @model_validator(mode="after")
    def _require_source_for_source_tag(self) -> Finding:
        if self.tag is EpistemicTag.SOURCE and self.source is None:
            raise ValueError(
                f"finding {self.id}: tag=SOURCE requires a structured source pointer"
            )
        return self

    @model_validator(mode="after")
    def _derived_from_consistency(self) -> Finding:
        if self.id in self.derived_from:
            raise ValueError(f"finding {self.id}: self-reference in derived_from")
        return self


# ── Question ─────────────────────────────────────────────────────────────────


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    priority: QuestionPriority
    context: str
    domain: str
    iteration: int = Field(ge=0)
    status: QuestionStatus = "open"
    question_type: QuestionType | None = None
    resolved_at: int | str | None = None
    resolved_by: str | None = None
    exhausted_at: str | None = None
    exhaustion_reason: str | None = None
    notes: str | None = None


# ── Lineage ──────────────────────────────────────────────────────────────────


LineageTarget = Literal["persona.md", "CLAUDE.md", "AGENTS.md", "pipeline.json"]


class LineageEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iteration: int
    timestamp: str
    target: LineageTarget
    version_before: str
    version_after: str
    change_type: str
    change_summary: str
    reasoning: str
    # Score-piping fix (D8 / infra-debt #5 SCORE_FIELD_LOSS): scores must
    # actually be populated at the write site, not left None by default.
    score_before: float | None
    score_after: float | None


# ── ConductorMetric ──────────────────────────────────────────────────────────


ExpertStatus = Literal["answered", "killed", "narrowed", "exhausted", "crashed"]
ExhaustionReason = Literal["data-gap", "strategy-limit", "infrastructure"]


class ConductorMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str | None = None
    conductor_iteration: int
    question_id: str
    expert_status: ExpertStatus
    findings_added: int = Field(ge=0)
    findings_persisted: int | None = None
    attrition_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    questions_resolved: int = Field(ge=0)
    open_questions_delta: int | None = None
    inner_iterations_run: int = Field(ge=0)
    timestamp: str
    exhaustion_reason: ExhaustionReason | None = None
    question_type: QuestionType | None = None


# ── Project state ────────────────────────────────────────────────────────────


ProjectStatus = Literal["active", "paused", "completed"]


class ProjectState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    iteration: int = Field(ge=0)
    status: ProjectStatus = "active"
    active_question_id: str | None = None
    conductor_iteration: int = 0
    created_at: str
    updated_at: str
    completed_at: str | None = None
    completion_reason: str | None = None
    # Operator kill switch (article §10; commitment 6). When set with a
    # non-empty reason, the conductor short-circuits before any LLM call.
    halt_reason: str | None = None


__all__ = [
    "EPISTEMIC_RANK",
    "ConductorMetric",
    "DerivationChain",
    "EngineeringType",
    "EpistemicTag",
    "ExhaustionReason",
    "ExpertStatus",
    "FactType",
    "Finding",
    "FindingStatus",
    "LineageEntry",
    "LineageTarget",
    "NeedsReview",
    "ProjectState",
    "ProjectStatus",
    "Question",
    "QuestionPriority",
    "QuestionStatus",
    "QuestionType",
    "Source",
    "VerifierStatus",
]
