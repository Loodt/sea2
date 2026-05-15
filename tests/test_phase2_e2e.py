"""End-to-end Phase 2: index → retrieve → extract → integrate.

Builds a fixture corpus on disk, indexes it with `LocalCorpusSearcher`,
runs retrieve, feeds the admitted chunks into the extract stage (with
a fake subprocess runner that returns JSON tied to the chunks), and
integrates. Verifies the full chain end-to-end without network access.

This is the Phase 2 "done" verification criterion #2.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from sea2.conductor.extract import extract
from sea2.conductor.integrate import integrate
from sea2.conductor.retrieve import retrieve
from sea2.events import EventType
from sea2.models import VerifierStatus
from sea2.retrieve.index_corpus import index_corpus
from sea2.retrieve.local_corpus import LocalCorpusSearcher
from sea2.store import read_chunks, read_events, read_findings

if TYPE_CHECKING:
    from pathlib import Path


def _ok_client() -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200))
    )


def _populate_corpus(corpus_dir: Path) -> None:
    """Three regulatory-ish fixtures with distinct subject matter."""
    (corpus_dir / "mprda.md").write_text(
        "# MPRDA\n\nThe Mineral and Petroleum Resources Development Act regulates "
        "active mining rights in South Africa. Pre-2004 dumps are not governed "
        "by MPRDA following the Ataqua judgment of 2007.",
        encoding="utf-8",
    )
    (corpus_dir / "fsca.md").write_text(
        "# FSCA Crypto Declaration\n\nIn October 2022 the Financial Sector Conduct "
        "Authority declared crypto assets to be financial products under FAIS. "
        "This brought CASP licensing into the regulatory perimeter.",
        encoding="utf-8",
    )
    (corpus_dir / "nema.md").write_text(
        "# NEMA s28\n\nSection 28 of NEMA establishes a duty of care for the "
        "environment that runs with the activity rather than the mining right.",
        encoding="utf-8",
    )


def _fake_extract_runner(findings_json: list[dict]):  # type: ignore[no-untyped-def]
    def run(provider, prompt):  # type: ignore[no-untyped-def]
        return json.dumps(findings_json)

    return run


def test_phase2_end_to_end(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _populate_corpus(corpus_dir)

    # ── 1. Index the corpus ────────────────────────────────────────────────
    corpus_sqlite = tmp_path / "corpus.sqlite"
    files, chunks_indexed = index_corpus(corpus_dir, corpus_sqlite)
    assert files == 3
    assert chunks_indexed >= 3

    # ── 2. Retrieve via LocalCorpusSearcher ────────────────────────────────
    searcher = LocalCorpusSearcher(corpus_sqlite)
    result = retrieve(
        project_dir,
        "FSCA crypto declaration",
        searchers=[searcher],
        refetch_short_text=False,
    )
    assert len(result.admitted_chunk_ids) >= 1
    # Re-run is idempotent — same chunks deduped.
    rerun = retrieve(
        project_dir,
        "FSCA crypto declaration",
        searchers=[searcher],
        refetch_short_text=False,
    )
    assert rerun.admitted_chunk_ids == ()
    assert len(rerun.duplicates) >= 1

    stored_chunks = read_chunks(project_dir)
    assert any("FSCA" in c.text for c in stored_chunks)
    admitted_id = result.admitted_chunk_ids[0]
    target_chunk = next(c for c in stored_chunks if c.chunk_id == admitted_id)

    # ── 3. Extract via fake subprocess ─────────────────────────────────────
    finding_json = {
        "id": "f-001",
        "claim": (
            "In October 2022 the FSCA declared crypto assets to be financial products."
        ),
        "tag": "SOURCE",
        "fact_type": "citation",
        "source": {
            "id": "url:" + target_chunk.url,
            "page": None,
            "section": None,
            "paragraph_id": None,
        },
        "verbatim_quote": (
            "Financial Sector Conduct Authority declared crypto assets to be "
            "financial products under FAIS"
        ),
        "confidence": 0.9,
        "domain": "regulation",
        "iteration": 1,
        "admitted_chunk_id": target_chunk.chunk_id,
        "derived_from": [],
    }
    ex_res = extract(
        project_dir,
        "FSCA crypto declaration",
        [target_chunk],
        runner=_fake_extract_runner([finding_json]),
    )
    assert len(ex_res.findings) == 1
    assert ex_res.findings[0].admitted_chunk_id == target_chunk.chunk_id

    # ── 4. Integrate (real chunk store + Tier 0 quote check) ───────────────
    int_res = integrate(
        project_dir,
        list(ex_res.findings),
        http_client=_ok_client(),
    )
    assert len(int_res.admitted) == 1
    persisted = int_res.admitted[0]
    # url=OK + quote=OK → VERIFIED
    assert persisted.verifier_status is VerifierStatus.VERIFIED

    # ── 5. Read-back roundtrip from the store ──────────────────────────────
    stored = read_findings(project_dir)
    assert [f.id for f in stored] == ["f-001"]

    # ── 6. Events ledger has the expected types ───────────────────────────
    events = read_events(project_dir)
    types = [e["event_type"] for e in events]
    # Retrieve emitted STORE_APPEND_OK for chunks. Integrate emitted
    # TIER0_QUOTE_OK and STORE_APPEND_OK for the finding. URL check is
    # passively skipped because the source is file:// (LocalCorpusSearcher).
    assert types.count("STORE_APPEND_OK") >= 2  # ≥1 chunk + 1 finding
    assert EventType.TIER0_QUOTE_OK.value in types


def test_extract_rejects_finding_with_unknown_chunk(tmp_path: Path) -> None:
    """The smuggling guard: even if the extract subprocess invents a
    chunk_id, the extract stage rejects it because it's not in the
    explicitly-provided chunks list."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _populate_corpus(corpus_dir)
    corpus_sqlite = tmp_path / "corpus.sqlite"
    index_corpus(corpus_dir, corpus_sqlite)

    searcher = LocalCorpusSearcher(corpus_sqlite)
    result = retrieve(
        project_dir,
        "FSCA",
        searchers=[searcher],
        refetch_short_text=False,
    )
    stored_chunks = read_chunks(project_dir)
    target_chunk = next(
        c for c in stored_chunks if c.chunk_id == result.admitted_chunk_ids[0]
    )

    smuggled = {
        "id": "f-001",
        "claim": "x",
        "tag": "SOURCE",
        "fact_type": "qualitative",
        "source": {"id": "url:" + target_chunk.url},
        "confidence": 0.5,
        "domain": "d",
        "iteration": 0,
        "admitted_chunk_id": "0123456789abcdef",  # not in input set
        "derived_from": [],
    }
    ex = extract(
        project_dir,
        "FSCA",
        [target_chunk],
        runner=_fake_extract_runner([smuggled]),
    )
    assert len(ex.findings) == 0
    assert "not in input set" in ex.rejections[0][1]
