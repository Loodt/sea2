"""Extract stage tests with injected fake subprocess runner."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sea2.chunks import Chunk
from sea2.conductor.extract import PROMPT_TEMPLATE, _format_chunks, extract
from sea2.events import EventType
from sea2.store import read_events

if TYPE_CHECKING:
    from pathlib import Path


def _chunk(idx: int) -> Chunk:
    text = f"Text body for chunk {idx}. " * 5
    return Chunk.make(
        url=f"https://example.com/{idx}",
        title=f"Doc {idx}",
        fetched_at="2026-05-15T00:00:00Z",
        searcher="test",
        query="q",
        text=text,
        start_offset=0,
        end_offset=len(text),
        source_hash="a" * 64,
        mime="text/html",
    )


def _well_formed_finding(chunk: Chunk, *, idx: int) -> dict:
    return {
        "id": f"f-test-{idx:03d}",
        "claim": "This is a well-grounded atomic claim.",
        "tag": "SOURCE",
        "fact_type": "qualitative",
        "source": {"id": chunk.url, "page": None, "section": None, "paragraph_id": None},
        "verbatim_quote": "Text body for chunk",
        "confidence": 0.8,
        "domain": "test",
        "iteration": 0,
        "admitted_chunk_id": chunk.chunk_id,
        "derived_from": [],
    }


def _fake_runner(output: str):  # type: ignore[no-untyped-def]
    def run(provider, prompt):  # type: ignore[no-untyped-def]
        return output

    return run


def test_well_formed_findings_admitted(tmp_path: Path) -> None:
    ch = _chunk(0)
    findings = [_well_formed_finding(ch, idx=i) for i in range(2)]
    res = extract(
        tmp_path,
        "what is this?",
        [ch],
        runner=_fake_runner(json.dumps(findings)),
    )
    assert len(res.findings) == 2
    assert res.findings[0].admitted_chunk_id == ch.chunk_id


def test_smuggled_chunk_id_rejected(tmp_path: Path) -> None:
    ch = _chunk(0)
    bad = _well_formed_finding(ch, idx=0)
    bad["admitted_chunk_id"] = "0123456789abcdef"  # not in input set
    res = extract(
        tmp_path,
        "q",
        [ch],
        runner=_fake_runner(json.dumps([bad])),
    )
    assert len(res.findings) == 0
    assert len(res.rejections) == 1
    assert "not in input set" in res.rejections[0][1]
    events = read_events(tmp_path)
    assert any(
        e["event_type"] == EventType.VALIDATE_FAIL.value for e in events
    )


def test_missing_admitted_chunk_id_rejected(tmp_path: Path) -> None:
    ch = _chunk(0)
    bad = _well_formed_finding(ch, idx=0)
    del bad["admitted_chunk_id"]
    res = extract(
        tmp_path,
        "q",
        [ch],
        runner=_fake_runner(json.dumps([bad])),
    )
    assert len(res.findings) == 0
    assert "admitted_chunk_id missing" in res.rejections[0][1]


def test_schema_invalid_rejected(tmp_path: Path) -> None:
    ch = _chunk(0)
    bad = {"id": "f-test-000", "claim": "x"}  # missing required fields
    res = extract(
        tmp_path,
        "q",
        [ch],
        runner=_fake_runner(json.dumps([bad])),
    )
    assert len(res.findings) == 0
    assert res.rejections[0][1].startswith("schema:")


def test_runner_exception_handled(tmp_path: Path) -> None:
    def boom(provider, prompt):  # type: ignore[no-untyped-def]
        raise RuntimeError("subprocess died")

    res = extract(tmp_path, "q", [_chunk(0)], runner=boom)
    assert len(res.findings) == 0
    assert len(res.rejections) == 1
    assert "runner" in res.rejections[0][1]
    events = read_events(tmp_path)
    assert any(e["event_type"] == EventType.PRODUCE_FAIL.value for e in events)


def test_malformed_json_rejected(tmp_path: Path) -> None:
    res = extract(tmp_path, "q", [_chunk(0)], runner=_fake_runner("not json"))
    assert len(res.findings) == 0
    assert any("parse" in r[0] or "JSON" in r[1] for r in res.rejections)


def test_markdown_fences_stripped(tmp_path: Path) -> None:
    ch = _chunk(0)
    findings = [_well_formed_finding(ch, idx=0)]
    body = "```json\n" + json.dumps(findings) + "\n```"
    res = extract(tmp_path, "q", [ch], runner=_fake_runner(body))
    assert len(res.findings) == 1


def test_empty_chunks_input_returns_empty(tmp_path: Path) -> None:
    res = extract(tmp_path, "q", [], runner=_fake_runner("[]"))
    assert res.findings == ()
    assert res.rejections == ()


def test_prompt_includes_chunk_text() -> None:
    ch = _chunk(7)
    block = _format_chunks([ch])
    assert ch.chunk_id in block
    assert "Text body for chunk 7" in block
    # Sanity: prompt template includes the chunks block
    p = PROMPT_TEMPLATE.format(
        question_id="q1",
        question="?",
        iteration=0,
        chunks_block=block,
    )
    assert "WebSearch" in p  # the prohibition is in the prompt
    assert ch.chunk_id in p
