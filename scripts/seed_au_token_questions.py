"""Seed the au-token project with questions extracted from goal.md.

Reads SEA's au-token goal.md, picks one Question per WP deliverable plus
the explicit "known unknowns / open loops" section (§190+), and writes
them to `<project_dir>/questions.jsonl`. Question domains are aligned
with the comparison-domain-keywords mapping so M5 (domain coverage)
scores fairly.

Usage::

    python scripts/seed_au_token_questions.py \
        --project-dir projects/au-token \
        --goal sea/projects/au-token/goal.md
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

from sea2.models import Question
from sea2.store import atomic_append_jsonl, questions_path


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


# Pre-curated seed questions for au-token. These mirror the goal.md
# "Known unknowns / open loops" section + the WP deliverables. Order
# matters: highest priority first per pre-registration §1.1 fairness.
SEED_QUESTIONS: list[dict[str, object]] = [
    {
        "id": "AUQ001",
        "question": (
            "How does the FSCA Crypto Asset Declaration of October 2022 interact "
            "with the Financial Markets Act for tokens that are simultaneously "
            "crypto assets and securities — is dual licensing (CASP + FMA) "
            "actually required for a tokenised gold tailings SPV?"
        ),
        "priority": "high",
        "domain": "fsca-crypto",
        "question_type": "data-hunt",
        "context": "WP4.a critical-path — FSCA + FMA dual-regulation",
    },
    {
        "id": "AUQ002",
        "question": (
            "Under the Ataqua ruling (De Beers v Ataqua Mining 2007), what "
            "ownership status applies to pre-2004 gold tailings dumps, and what "
            "acquisition mechanism transfers ownership of an orphan dump whose "
            "original mining company was liquidated?"
        ),
        "priority": "high",
        "domain": "ataqua-property",
        "question_type": "mechanism",
        "context": "WP4.c — property acquisition for pre-2004 dumps",
    },
    {
        "id": "AUQ003",
        "question": (
            "Does the Mineral and Petroleum Resources Royalty Act apply to gold "
            "extracted from pre-2004 tailings dumps that are not regulated under "
            "the MPRDA, given that the MPRRA taxes 'mineral resources' as defined "
            "by the MPRDA?"
        ),
        "priority": "high",
        "domain": "mprra-royalty",
        "question_type": "first-principles",
        "context": "Open Loop #14 — MPRRA applicability to non-MPRDA outputs",
    },
    {
        "id": "AUQ004",
        "question": (
            "What is the structure of the Mineral Resources Development Bill 2025's "
            "'historic residue stockpiles' category, and how would the State-reversion "
            "and 2-year regularisation provisions apply to a tailings SPV whose "
            "acquisition predates the Bill's commencement?"
        ),
        "priority": "high",
        "domain": "bill-2025",
        "question_type": "kill-check",
        "context": "Open Loop #3 — 2025 Bill grandfathering",
    },
    {
        "id": "AUQ005",
        "question": (
            "Under NEM:WA's GN R634 / R635 / R636 regime, how is residue from "
            "modern cyanide-leach retreatment of pre-2004 gold tailings classified "
            "for landfill disposal, and what TCLP / SPLP leachability thresholds "
            "apply?"
        ),
        "priority": "high",
        "domain": "nemwa-waste",
        "question_type": "data-hunt",
        "context": "WP4.b — waste classification of retreatment output",
    },
    {
        "id": "AUQ006",
        "question": (
            "How does NEMA section 28 (duty of care) apportion historic-contamination "
            "liability between a new SPV acquiring a pre-2004 tailings dump and the "
            "successor-in-title of the original mining right?"
        ),
        "priority": "high",
        "domain": "nema-liability",
        "question_type": "mechanism",
        "context": "Open Loop #2 — environmental liability allocation",
    },
    {
        "id": "AUQ007",
        "question": (
            "Under the SAMVAL 2016 Code, what valuation method is appropriate for "
            "a pre-PFS gold tailings SPV at the scoping stage, and what discount-rate "
            "ranges are defensible per SAMREC-classification level?"
        ),
        "priority": "medium",
        "domain": "samval-valuation",
        "question_type": "data-hunt",
        "context": "WP2 — stage-gated valuation algorithm",
    },
    {
        "id": "AUQ008",
        "question": (
            "What disclosure cadence and content does the FMA require for a security "
            "token sold via private placement under section 96 of the Companies Act, "
            "versus a CASP-licensed public offer of a crypto asset?"
        ),
        "priority": "medium",
        "domain": "fma-disclosure",
        "question_type": "data-hunt",
        "context": "WP3 — transparency framework + WP4.a financial regulation",
    },
    {
        "id": "AUQ009",
        "question": (
            "Under the NEMA Financial Provisioning Regulations (GN R1147 of 2015), "
            "what quantum methodology applies to a *retreatment* operation whose "
            "footprint is reducing rather than expanding?"
        ),
        "priority": "medium",
        "domain": "nema-fp",
        "question_type": "mechanism",
        "context": "WP4.b + WP2 — closure provision in valuation",
    },
    {
        "id": "AUQ010",
        "question": (
            "Does the Mining Charter III's 30% historically-disadvantaged-persons "
            "ownership requirement apply to a pre-2004 tailings retreatment SPV "
            "given that such operations are not regulated under the MPRDA (Ataqua)?"
        ),
        "priority": "medium",
        "domain": "bee-charter",
        "question_type": "kill-check",
        "context": "Open Loop #13 — BEE applicability under non-MPRDA framing",
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed an au-token SEA2 project with questions")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--limit", type=int, default=len(SEED_QUESTIONS),
        help="Seed only the first N questions (default: all)",
    )
    args = parser.parse_args(argv)

    args.project_dir.mkdir(parents=True, exist_ok=True)
    out_path = questions_path(args.project_dir)
    if out_path.exists() and out_path.read_text(encoding="utf-8").strip():
        print(
            f"ERROR: {out_path} already non-empty. Refusing to re-seed. "
            "Delete the project dir first if you want a fresh seed.",
            file=sys.stderr,
        )
        return 1

    timestamp = _now_iso()
    for entry in SEED_QUESTIONS[: args.limit]:
        q = Question(
            id=str(entry["id"]),
            question=str(entry["question"]),
            priority=entry["priority"],  # type: ignore[arg-type]
            context=str(entry["context"]),
            domain=str(entry["domain"]),
            iteration=0,
            status="open",
            question_type=entry["question_type"],  # type: ignore[arg-type]
            notes=f"seeded {timestamp}",
        )
        atomic_append_jsonl(out_path, q)

    n = min(args.limit, len(SEED_QUESTIONS))
    print(f"seeded {n} questions to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
