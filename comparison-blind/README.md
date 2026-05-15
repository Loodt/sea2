# comparison-blind/

Artifacts for the SEA vs SEA2 au-token comparison protocol per
`docs/comparison-protocol.md`. The `.mapping` file is locally
gitignored once the blinding tool seals it.

## Files

- `sea-scores.json` — M1–M10 from SEA's au-token endpoint.
- `sea-m1-retrofit.json` — M1 from running `httpx.HEAD` against SEA's
  310 unique URL citations (`50.3% resolve`).
- `sea2-scores.json` — M1–M10 from SEA2's 30-iter au-token dispatch.
- `scorecard.md` — combined scorecard with per-metric verdicts.
- (Operator only, gitignored after run) `A.md`, `B.md`, `.mapping`.

## Operator workflow for M11 + M12

The operator confidence (M11) and flagged-for-followup count (M12)
require an honest blinded read of both systems' final summaries.

### 1. Export both summaries

```bash
# SEA2's summary
uv run python -c "from sea2.comparison.report import export_summary; \
    export_summary('projects/au-token', 'sea2-final.md')"

# SEA's already exists:
cp /c/Users/mtlb/code/sea/projects/au-token/output/integrated-strategy.md \
   sea-final.md
```

### 2. Write the expected-differences memo (FIRST, before reading either)

Open `comparison-blind/expected.md` and write 1 paragraph stating which
system you expect to win on M11 and why. This serves as the
contamination-detection signal: if your post-read rating matches your
expectation exactly, that's a yellow flag.

### 3. Seal the A/B mapping via the blinding tool

```bash
uv run python scripts/blind_compare.py sea-final.md sea2-final.md \
    --out-dir comparison-blind
```

This:
- coin-flips A vs B assignment
- coin-flips reading order
- copies the markdowns to `comparison-blind/A.md` and `B.md`
- writes the mapping to `comparison-blind/.mapping`
- prints the reading order

### 4. Read in the order shown

For each document:
- Read it fully without consulting the other.
- Rate confidence 1–10 ("how usable is this for the au-token go/no-go").
- Mark every claim you'd want to re-verify before acting; count them.
- Commit your rating + flag count to `comparison-blind/m11-m12.json`
  BEFORE looking at the other document.

`m11-m12.json` shape::

    {
      "A": {"confidence": <int>, "flagged": <int>, "notes": "..."},
      "B": {"confidence": <int>, "flagged": <int>, "notes": "..."}
    }

### 5. Unseal

```bash
cat comparison-blind/.mapping  # reveals which was SEA, which was SEA2
```

### 6. Rebuild scorecard with M11/M12 filled in

Edit `sea-scores.json` and `sea2-scores.json` to set
`m11_operator_confidence` and `m12_flagged_for_followup` on each. Then
re-run `scripts/build_comparison_report.py`. The decision rule §3 of
`docs/comparison-protocol.md` applies.
