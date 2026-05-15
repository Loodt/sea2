"""Idempotent corpus downloader.

Reads a manifest.json (see `corpora/au-token-regulatory/manifest.json` for
the shape) and downloads each entry's `source_url` into the same directory
as the manifest, using the entry's `filename`. Files already present are
skipped — re-runs are safe.

Skips entries with `source_url: null` (the operator hasn't supplied a URL
yet). Failures are reported but don't abort the run; the script exits
nonzero if any download failed.

Usage::

    python scripts/download_corpus.py corpora/au-token-regulatory/manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

DEFAULT_TIMEOUT_S = 60.0
USER_AGENT = "sea2-corpus-downloader/0.1 (+research)"


def _download(client: httpx.Client, url: str, dest: Path) -> None:
    """Stream the response to `dest`. Atomic via .tmp + rename."""
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in response.iter_bytes(chunk_size=64 * 1024):
                fh.write(chunk)
    tmp.replace(dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download corpus documents from a manifest")
    parser.add_argument("manifest", type=Path, help="Path to manifest.json")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the destination file exists",
    )
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    base_dir = args.manifest.parent
    documents = manifest.get("documents", [])

    skipped: list[str] = []
    downloaded: list[str] = []
    failed: list[tuple[str, str]] = []

    with httpx.Client(
        follow_redirects=True,
        timeout=DEFAULT_TIMEOUT_S,
        headers={"user-agent": USER_AGENT},
    ) as client:
        for entry in documents:
            filename = entry.get("filename")
            url = entry.get("source_url")
            if not filename:
                continue
            dest = base_dir / filename
            if url is None:
                skipped.append(f"{filename} (no source_url)")
                continue
            if dest.exists() and not args.force:
                skipped.append(f"{filename} (already present)")
                continue
            print(f"  ↓ {filename} ← {url}")
            try:
                _download(client, url, dest)
                downloaded.append(filename)
            except (httpx.HTTPError, OSError) as e:
                failed.append((filename, str(e)))
                print(f"    ! failed: {e}", file=sys.stderr)

    print()
    print(f"Downloaded: {len(downloaded)}")
    print(f"Skipped:    {len(skipped)}")
    if skipped:
        for s in skipped:
            print(f"  - {s}")
    if failed:
        print(f"Failed:     {len(failed)}")
        for name, msg in failed:
            print(f"  - {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
