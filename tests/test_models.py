"""Schema roundtrip + validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from sea2.models import (
    ConductorMetric,
    EpistemicTag,
    FactType,
    Finding,
    LineageEntry,
    ProjectState,
    Question,
    Source,
    VerifierStatus,
)


def _base_finding_kwargs() -> dict:
    return {
        "id": "f-001",
        "claim": "Water boils at 100 C at 1 atm.",
        "tag": EpistemicTag.SOURCE,
        "fact_type": FactType.QUANTITATIVE,
        "source": Source(id="doi:10.1/abc", page=12),
        "confidence": 0.95,
        "domain": "physics",
        "iteration": 0,
    }


def test_finding_roundtrip_via_json() -> None:
    f = Finding(**_base_finding_kwargs())
    raw = f.model_dump_json()
    parsed = Finding.model_validate_json(raw)
    assert parsed == f


def test_source_tag_requires_source_pointer() -> None:
    kw = _base_finding_kwargs()
    kw["source"] = None
    with pytest.raises(ValidationError) as exc:
        Finding(**kw)
    assert "SOURCE" in str(exc.value)


def test_derived_from_rejects_self_reference() -> None:
    kw = _base_finding_kwargs()
    kw["tag"] = EpistemicTag.DERIVED
    kw["derived_from"] = ["f-001"]
    with pytest.raises(ValidationError) as exc:
        Finding(**kw)
    assert "self-reference" in str(exc.value)


def test_confidence_bounds_enforced() -> None:
    kw = _base_finding_kwargs()
    kw["confidence"] = 1.5
    with pytest.raises(ValidationError):
        Finding(**kw)


def test_verifier_status_defaults_pending() -> None:
    f = Finding(**_base_finding_kwargs())
    assert f.verifier_status is VerifierStatus.PENDING


def test_question_jsonl_roundtrip() -> None:
    q = Question(
        id="q-001",
        question="What is the BPR of the Pratt & Whitney PW1100G?",
        priority="high",
        context="au-token engine review",
        domain="aerospace",
        iteration=0,
    )
    raw = q.model_dump_json()
    assert q == Question.model_validate_json(raw)


def test_lineage_entry_score_fields_required() -> None:
    # score_before/score_after have no default — must be supplied explicitly,
    # even as None. (Infra-debt #5: prevents silent score loss.)
    with pytest.raises(ValidationError):
        LineageEntry(  # type: ignore[call-arg]
            iteration=1,
            timestamp="2026-05-15T00:00:00Z",
            target="persona.md",
            version_before="v001",
            version_after="v002",
            change_type="behavioral",
            change_summary="x",
            reasoning="y",
        )


def test_conductor_metric_attrition_bounds() -> None:
    with pytest.raises(ValidationError):
        ConductorMetric(
            conductor_iteration=1,
            question_id="q-001",
            expert_status="answered",
            findings_added=3,
            attrition_rate=1.5,
            questions_resolved=1,
            inner_iterations_run=2,
            timestamp="2026-05-15T00:00:00Z",
        )


def test_project_state_halt_reason_default_none() -> None:
    s = ProjectState(
        name="au-token",
        iteration=0,
        created_at="2026-05-15T00:00:00Z",
        updated_at="2026-05-15T00:00:00Z",
    )
    assert s.halt_reason is None
    assert s.status == "active"


def test_finding_extra_fields_rejected() -> None:
    kw = _base_finding_kwargs()
    raw = json.loads(Finding(**kw).model_dump_json())
    raw["mystery_field"] = "x"
    with pytest.raises(ValidationError):
        Finding.model_validate(raw)
