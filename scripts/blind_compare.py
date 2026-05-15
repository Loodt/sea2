"""A/B blinding tool for the comparison-protocol M11 + M12 reading.

Takes two markdown summaries (SEA's and SEA2's), coin-flips A/B
assignment, and copies them into `comparison-blind/A.md` and
`comparison-blind/B.md`. The mapping is written to
`comparison-blind/.mapping` (gitignored) and unsealed only after the
operator commits ratings.

Also coin-flips the reading order (A→B or B→A) and prints it.

Usage::

    python scripts/blind_compare.py sea-final.md sea2-final.md \
        --out-dir comparison-blind

The script refuses to overwrite an existing `.mapping` unless `--reseal`
is passed — this protects against accidentally re-flipping mid-protocol.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import random
import shutil
import sys
from pathlib import Path


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A/B blind the two systems' reports for M11")
    parser.add_argument("sea_md", type=Path, help="SEA's final summary markdown")
    parser.add_argument("sea2_md", type=Path, help="SEA2's final summary markdown")
    parser.add_argument(
        "--out-dir", type=Path, default=Path("comparison-blind"),
        help="Destination directory (default: comparison-blind/)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Optional RNG seed for reproducibility. Default: system entropy",
    )
    parser.add_argument(
        "--reseal", action="store_true",
        help="Allow overwriting an existing .mapping file",
    )
    args = parser.parse_args(argv)

    if not args.sea_md.is_file():
        print(f"ERROR: SEA report not found: {args.sea_md}", file=sys.stderr)
        return 2
    if not args.sea2_md.is_file():
        print(f"ERROR: SEA2 report not found: {args.sea2_md}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    mapping_file = args.out_dir / ".mapping"
    if mapping_file.exists() and not args.reseal:
        print(
            f"ERROR: {mapping_file} already exists. Refusing to re-flip "
            "without --reseal (prevents accidentally restarting the protocol).",
            file=sys.stderr,
        )
        return 3

    # Use SystemRandom by default — the protocol is exactly the situation
    # the security advisory is about: an unpredictable outcome matters.
    # Seeded path is only for tests / reproducibility demos.
    coin = 0.5
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()  # noqa: S311
    sea_is_a = rng.random() < coin
    read_a_first = rng.random() < coin

    a_src = args.sea_md if sea_is_a else args.sea2_md
    b_src = args.sea2_md if sea_is_a else args.sea_md
    a_dst = args.out_dir / "A.md"
    b_dst = args.out_dir / "B.md"
    shutil.copyfile(a_src, a_dst)
    shutil.copyfile(b_src, b_dst)

    mapping = {
        "sealed_at": _now_iso(),
        "A": "sea" if sea_is_a else "sea2",
        "B": "sea2" if sea_is_a else "sea",
        "reading_order": "A,B" if read_a_first else "B,A",
        "sea_md_sha_path": str(args.sea_md.resolve()),
        "sea2_md_sha_path": str(args.sea2_md.resolve()),
    }
    import json as _json  # noqa: PLC0415

    mapping_file.write_text(_json.dumps(mapping, indent=2) + "\n", encoding="utf-8")

    print("Blinding sealed.")
    print(f"  read first:  {mapping['reading_order'].split(',')[0]}")
    print(f"  read second: {mapping['reading_order'].split(',')[1]}")
    print()
    print(f"  A: {a_dst}")
    print(f"  B: {b_dst}")
    print()
    print("Now read A then B (in the order shown above), assign confidence (1-10)")
    print("and flagged-for-followup count for EACH document, commit both before")
    print("looking at the .mapping file. The mapping is at:")
    print(f"  {mapping_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
