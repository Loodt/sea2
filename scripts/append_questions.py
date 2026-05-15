"""Append more au-token questions to an existing project.

Adds 25 additional questions covering WP1-WP8 sub-questions and the
remaining Known-Unknowns from goal.md that the initial 10-question
seed didn't cover. Idempotent on `id` collisions — silently skips
questions that already exist in the project.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

from sea2.models import Question
from sea2.store import atomic_append_jsonl, questions_path

EXTRA: list[dict[str, object]] = [
    {
        "id": "AUQ011",
        "question": (
            "Which token standard (ERC-20, ERC-1400, ERC-3643, or bespoke) "
            "best supports SAMVAL-aligned valuation feeds, transfer "
            "restrictions for non-public placement, and on-chain rights "
            "registers under the FMA?"
        ),
        "priority": "high",
        "domain": "token-architecture",
        "question_type": "design-space",
        "context": "WP1 — token standard selection",
    },
    {
        "id": "AUQ012",
        "question": (
            "What SPV structure (single-SPV-per-TSF vs master-fund-of-SPVs "
            "vs cell company) optimises for SARS tax efficiency, investor "
            "ring-fencing, and per-asset capital raising in the SA context?"
        ),
        "priority": "high",
        "domain": "spv-structuring",
        "question_type": "design-space",
        "context": "WP1 — SPV architecture",
    },
    {
        "id": "AUQ013",
        "question": (
            "What stage-specific discount-rate ranges and probability "
            "weights are defensible for a gold tailings retreatment project "
            "moving from scoping through PFS, FS, BFS to commissioning?"
        ),
        "priority": "high",
        "domain": "valuation-discount-rates",
        "question_type": "first-principles",
        "context": "WP2 — stage-gated discount rates",
    },
    {
        "id": "AUQ014",
        "question": (
            "How should the algorithmic NAV oracle source gold price for "
            "real-time token valuation — spot, monthly average, or "
            "forward-curve interpolation — and what manipulation-resistance "
            "guarantees does each provide?"
        ),
        "priority": "medium",
        "domain": "valuation-oracle",
        "question_type": "design-space",
        "context": "WP2 — NAV pricing input",
    },
    {
        "id": "AUQ015",
        "question": (
            "What disclosure cadence does NEMA s24N require for an EMP "
            "update on a tailings retreatment SPV, and how should "
            "milestone-linked disclosures map to token tranche issuance?"
        ),
        "priority": "medium",
        "domain": "disclosure-cadence",
        "question_type": "data-hunt",
        "context": "WP3 — disclosure cadence",
    },
    {
        "id": "AUQ016",
        "question": (
            "Does SARB exchange-control approval (Excon) require additional "
            "registration for non-resident investors holding tokens denominated "
            "in ZAR over a tokenised SA mineral asset?"
        ),
        "priority": "high",
        "domain": "sarb-excon",
        "question_type": "kill-check",
        "context": "WP4.a — SARB exchange control",
    },
    {
        "id": "AUQ017",
        "question": (
            "Under the FIC Act, what accountable-institution registration "
            "and STR thresholds apply to a CASP-licensed exchange listing "
            "an SA mineral-asset-backed token?"
        ),
        "priority": "medium",
        "domain": "fic-aml",
        "question_type": "data-hunt",
        "context": "WP4.a — AML/CTF",
    },
    {
        "id": "AUQ018",
        "question": (
            "What VAT, CGT, and dividend-withholding treatment applies to "
            "(a) primary token issuance, (b) secondary token trades, and "
            "(c) token-to-gold or token-to-ZAR redemption?"
        ),
        "priority": "high",
        "domain": "sars-tax",
        "question_type": "data-hunt",
        "context": "WP4.a — tax treatment",
    },
    {
        "id": "AUQ019",
        "question": (
            "Which Gauteng / Mpumalanga / Free State province is the "
            "fastest path for a NEMA EA on a pre-2004 tailings retreatment "
            "site, and what is the realistic timeline + cost range?"
        ),
        "priority": "medium",
        "domain": "ea-permitting",
        "question_type": "data-hunt",
        "context": "WP4.b — EA pathway",
    },
    {
        "id": "AUQ020",
        "question": (
            "What is the empirical timeline for a DWS Water Use Licence "
            "on a tailings reprocessing operation in 2025, and which "
            "mitigations reliably accelerate it?"
        ),
        "priority": "medium",
        "domain": "wul-permitting",
        "question_type": "data-hunt",
        "context": "WP4.b — WUL pathway",
    },
    {
        "id": "AUQ021",
        "question": (
            "What conveyancing path transfers title in an orphan pre-2004 "
            "tailings dump where the original owner is liquidated and the "
            "Master of the High Court has no nominated buyer?"
        ),
        "priority": "high",
        "domain": "orphan-acquisition",
        "question_type": "mechanism",
        "context": "WP4.c — orphan dump acquisition",
    },
    {
        "id": "AUQ022",
        "question": (
            "What redemption mechanisms (cash, allocated bullion, NAV "
            "redemption, perpetual royalty) align best with SA retail "
            "investor preferences, and how does each interact with FAIS "
            "FSP Cat-II licensing?"
        ),
        "priority": "medium",
        "domain": "redemption-mechanism",
        "question_type": "design-space",
        "context": "WP5 — redemption design",
    },
    {
        "id": "AUQ023",
        "question": (
            "How do JSE gold ETFs (NewGold, 1nvest Gold) and JSE-listed "
            "junior gold equities (Pan African Resources, DRDGOLD) compare "
            "on Sharpe, Sortino, max drawdown, and correlation with gold "
            "spot over 2020-2025?"
        ),
        "priority": "medium",
        "domain": "benchmarking",
        "question_type": "data-hunt",
        "context": "WP6 — benchmark comparators",
    },
    {
        "id": "AUQ024",
        "question": (
            "What voting rights should token holders retain over major "
            "capex overruns, change of operator, offtake renegotiation, "
            "and abandonment decisions, given the FMA's prohibition on "
            "delegation of certain shareholder powers?"
        ),
        "priority": "medium",
        "domain": "governance-rights",
        "question_type": "design-space",
        "context": "WP7 — governance rights matrix",
    },
    {
        "id": "AUQ025",
        "question": (
            "What multi-oracle design (Chainlink, UMA, in-house attestation) "
            "produces verifiable on-chain production reports while keeping "
            "operational costs below 0.5% of gross revenue?"
        ),
        "priority": "medium",
        "domain": "production-oracle",
        "question_type": "design-space",
        "context": "WP8 — production verification oracle",
    },
    {
        "id": "AUQ026",
        "question": (
            "Under the proposed 2025 Bill's State-reversion provisions, "
            "what constitutional s25 property-rights arguments would defeat "
            "an attempted reversion of a pre-2004 tailings SPV acquired "
            "before the Bill's commencement?"
        ),
        "priority": "high",
        "domain": "constitutional-s25",
        "question_type": "first-principles",
        "context": "Open Loop #3 — constitutional defence to 2025 Bill",
    },
    {
        "id": "AUQ027",
        "question": (
            "What are the documented precedents (DRDGOLD, Pan African, "
            "Harmony) for residue-to-residue waste classification under "
            "NEM:WA, and how did each operator obtain their WML?"
        ),
        "priority": "medium",
        "domain": "precedent-wml",
        "question_type": "data-hunt",
        "context": "WP4.b — operator precedents",
    },
    {
        "id": "AUQ028",
        "question": (
            "How does Rand Refinery's gold settlement / receipt issuance "
            "process serve as an authoritative oracle for on-chain "
            "production reporting, and what are its rejection conditions?"
        ),
        "priority": "low",
        "domain": "rand-refinery-oracle",
        "question_type": "mechanism",
        "context": "WP8 — settlement oracle path",
    },
    {
        "id": "AUQ029",
        "question": (
            "What anti-dilution mechanism (full ratchet, weighted average, "
            "convertible structures) best aligns early-stage token holder "
            "economics with later-tranche pricing as the project advances "
            "through stage-gates?"
        ),
        "priority": "medium",
        "domain": "anti-dilution",
        "question_type": "design-space",
        "context": "Open Loop #5 — dilution across stages",
    },
    {
        "id": "AUQ030",
        "question": (
            "What capital-stack composition (token-only vs senior-debt + "
            "mezzanine + IDC grants) optimises returns for token holders "
            "while keeping the operator's incentive aligned through "
            "production?"
        ),
        "priority": "low",
        "domain": "capital-stack",
        "question_type": "design-space",
        "context": "Open Loop #10 — capital stack",
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append additional au-token questions")
    parser.add_argument("--project-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    qs_path = questions_path(args.project_dir)
    existing_ids: set[str] = set()
    if qs_path.exists():
        for line in qs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing_ids.add(json.loads(line).get("id", ""))

    timestamp = _dt.datetime.now(_dt.UTC).isoformat()
    appended = 0
    for entry in EXTRA:
        if entry["id"] in existing_ids:
            continue
        q = Question(
            id=str(entry["id"]),
            question=str(entry["question"]),
            priority=entry["priority"],  # type: ignore[arg-type]
            context=str(entry["context"]),
            domain=str(entry["domain"]),
            iteration=0,
            status="open",
            question_type=entry["question_type"],  # type: ignore[arg-type]
            notes=f"appended {timestamp}",
        )
        atomic_append_jsonl(qs_path, q)
        appended += 1

    print(f"appended {appended} new questions to {qs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
