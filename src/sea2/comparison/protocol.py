"""ComparisonScores: the schema both SEA and SEA2 scorers produce.

Pre-registration §M1..M12 defines what's measured; this module is the
serialisable Python representation. M11 (operator confidence) and M12
(flagged-for-followup) are operator-supplied — fields exist but are
None when scoring without operator input.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

System = Literal["sea", "sea2"]


class ComparisonScores(BaseModel):
    """All 12 metrics from `docs/comparison-protocol.md`."""

    model_config = ConfigDict(extra="forbid")

    system: System
    project_dir: str
    scored_at: str
    rng_seed: int = 17

    # Output quality
    m1_citation_resolvability: float | None = None
    m1_denominator: int = 0
    m2_quote_supported_rate: float | None = None
    m2_denominator: int = 0
    m3_verifier_disagreement_rate: float | None = None
    m3_denominator: int = 0
    m4_dag_orphan_rate: float | None = None
    m4_denominator: int = 0
    m5_domain_coverage_rate: float | None = None
    m5_subtopics_covered: int = 0
    m5_subtopics_total: int = 11
    m6_operator_accuracy: float | None = None  # operator-supplied
    m6_sample_size: int = 0

    # Process quality
    m7_iterations_to_convergence: int | None = None
    m7_stop_reason: str | None = None
    m8_token_cost_per_verified: float | None = None
    m8_total_tokens: int = 0
    m8_verified_count: int = 0
    m9_median_iteration_wallclock_ms: float | None = None
    m10_silent_failure_count: int = 0

    # Decision quality
    m11_operator_confidence: float | None = None  # operator-supplied
    m12_flagged_for_followup: int | None = None  # operator-supplied

    # Bookkeeping
    findings_total: int = 0
    findings_verified: int = 0
    chunks_total: int = 0
    notes: list[str] = Field(default_factory=list)
