"""Record M11/M12 ratings + unseal + update the scorecard.

Reads `comparison-blind/m11-m12.json` (operator-filled) and
`comparison-blind/.mapping` (sealed by `blind_compare.py`), maps the
A/B ratings to SEA/SEA2, and patches the scores JSON for each system
so `build_comparison_report.py` can produce the final scorecard with
M11/M12 filled in.

Refuses to run if `m11-m12.json` still has null fields — operator
must commit a rating to both before unsealing.

Usage::

    # 1. Operator reads B.md then A.md, writes ratings into
    #    comparison-blind/m11-m12.json (copy from the .template).
    # 2. Run:
    python scripts/record_m11_m12.py
    # 3. Then rebuild the scorecard:
    python scripts/build_comparison_report.py \\
        --sea2 comparison-blind/sea2-scores.json \\
        --sea comparison-blind/sea-scores.json \\
        --sea-m1-retrofit comparison-blind/sea-m1-retrofit.json \\
        --output comparison-blind/scorecard.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unseal A/B and patch scores with M11/M12")
    parser.add_argument(
        "--dir", type=Path, default=Path("comparison-blind"),
        help="Comparison-blind directory (default: comparison-blind/)",
    )
    args = parser.parse_args(argv)

    ratings_path = args.dir / "m11-m12.json"
    mapping_path = args.dir / ".mapping"
    sea_scores_path = args.dir / "sea-scores.json"
    sea2_scores_path = args.dir / "sea2-scores.json"

    if not ratings_path.is_file():
        print(f"ERROR: {ratings_path} not found. Copy m11-m12.template.json -> m11-m12.json and fill in ratings first.", file=sys.stderr)
        return 2
    if not mapping_path.is_file():
        print(f"ERROR: {mapping_path} not found. Run scripts/blind_compare.py first.", file=sys.stderr)
        return 2

    ratings = json.loads(ratings_path.read_text(encoding="utf-8"))
    a = ratings.get("A", {})
    b = ratings.get("B", {})

    for label, side in (("A", a), ("B", b)):
        for f in ("confidence_1_to_10", "flagged_followup_count"):
            if side.get(f) is None:
                print(f"ERROR: {label}.{f} is null. Fill it in {ratings_path} before unsealing.", file=sys.stderr)
                return 3

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    a_system = mapping["A"]
    b_system = mapping["B"]
    print("Mapping unsealed:")
    print(f"  A = {a_system}")
    print(f"  B = {b_system}")
    print()

    by_system: dict[str, dict] = {a_system: a, b_system: b}

    for system_name, scores_path in (
        ("sea", sea_scores_path),
        ("sea2", sea2_scores_path),
    ):
        if not scores_path.is_file():
            print(f"WARN: {scores_path} not found; skipping {system_name}", file=sys.stderr)
            continue
        side = by_system[system_name]
        s = json.loads(scores_path.read_text(encoding="utf-8"))
        s["m11_operator_confidence"] = float(side["confidence_1_to_10"])
        s["m12_flagged_for_followup"] = int(side["flagged_followup_count"])
        notes = s.get("notes", [])
        if side.get("notes"):
            notes.append(f"M11/M12 operator note: {side['notes']}")
        s["notes"] = notes
        scores_path.write_text(json.dumps(s, indent=2), encoding="utf-8")
        print(f"  patched {scores_path.name}: M11={s['m11_operator_confidence']}, M12={s['m12_flagged_for_followup']}")

    print()
    print("Now rebuild the scorecard:")
    print("  uv run python scripts/build_comparison_report.py \\")
    print(f"      --sea2 {sea2_scores_path} \\")
    print(f"      --sea {sea_scores_path} \\")
    print(f"      --sea-m1-retrofit {args.dir}/sea-m1-retrofit.json \\")
    print(f"      --output {args.dir}/scorecard.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
