"""Retrofit M1 (citation resolvability) onto a SEA project.

SEA does not emit Tier 0 URL events. To compute M1 fairly for the
comparison, we read SEA's findings.jsonl, find every SOURCE-tagged
finding with a `url:` or `http(s)://` source, and run SEA2's
`check_url_resolves` against each via httpx (concurrent).

Output: a JSON object with `m1_citation_resolvability`,
`m1_denominator`, `successes`, `failures`, ready to merge into the
sea-scores.json blob from `score_sea.py`.

Usage::

    python scripts/retrofit_sea_m1.py /c/Users/mtlb/code/sea/projects/au-token --output sea-m1.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

TIMEOUT_S = 10.0
CONCURRENCY = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _extract_url(source: str | None) -> str | None:
    if not source:
        return None
    if source.startswith("url:"):
        rest = source[4:].strip()
        return rest if rest.startswith(("http://", "https://")) else None
    if source.startswith(("http://", "https://")):
        return source
    return None


async def _head(client: httpx.AsyncClient, url: str) -> tuple[str, bool, int | None]:
    try:
        r = await client.head(url, follow_redirects=True, timeout=TIMEOUT_S)
    except httpx.HTTPError:
        return url, False, None
    return url, _is_ok(r.status_code), r.status_code


HTTP_OK_LOW = 200
HTTP_OK_HIGH = 400  # exclusive — anything in [200, 400) counts as OK


def _is_ok(status: int) -> bool:
    return HTTP_OK_LOW <= status < HTTP_OK_HIGH


async def _check_all(urls: list[str]) -> list[tuple[str, bool, int | None]]:
    limits = httpx.Limits(
        max_keepalive_connections=CONCURRENCY,
        max_connections=CONCURRENCY * 2,
    )
    async with httpx.AsyncClient(
        timeout=TIMEOUT_S, limits=limits, headers={"user-agent": USER_AGENT}
    ) as client:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bounded(u: str) -> tuple[str, bool, int | None]:
            async with sem:
                return await _head(client, u)

        return await asyncio.gather(*(bounded(u) for u in urls))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrofit M1 citation-resolvability onto a SEA project")
    parser.add_argument("project_dir", type=Path, help="SEA project directory")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    findings_path = args.project_dir / "knowledge" / "findings.jsonl"
    if not findings_path.exists():
        print(f"ERROR: {findings_path} not found", file=sys.stderr)
        return 2

    urls: list[str] = []
    finding_ids: list[str] = []
    seen: set[str] = set()
    for line in findings_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = json.loads(line)
        if f.get("tag") != "SOURCE":
            continue
        url = _extract_url(f.get("source"))
        if url is None:
            continue
        # Dedupe same URL across multiple findings.
        if url not in seen:
            seen.add(url)
            urls.append(url)
            finding_ids.append(f.get("id", ""))

    if not urls:
        out = {
            "m1_citation_resolvability": None,
            "m1_denominator": 0,
            "successes": 0,
            "failures": 0,
            "unique_urls_checked": 0,
        }
    else:
        print(f"  checking {len(urls)} unique URLs (timeout {TIMEOUT_S}s, concurrency {CONCURRENCY})...", file=sys.stderr)
        results = asyncio.run(_check_all(urls))
        ok = sum(1 for _, success, _ in results if success)
        fail = sum(1 for _, success, _ in results if not success)
        out = {
            "m1_citation_resolvability": ok / len(results) if results else None,
            "m1_denominator": len(results),
            "successes": ok,
            "failures": fail,
            "unique_urls_checked": len(urls),
        }

    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
