"""Text chunker.

Splits text into overlapping chunks of roughly `target_tokens` tokens
(approximated as 4 characters per token, the OpenAI rule of thumb that
SEA used historically). Splits at paragraph boundaries first, then
sentence boundaries within paragraphs that are too large.

Returns char-offset spans so the chunker is fully reversible — every
chunk maps back to a (start, end) in the source text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CHARS_PER_TOKEN_EST = 4
DEFAULT_TARGET_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 50
DEFAULT_MIN_CHUNK_CHARS = 80


_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


@dataclass(frozen=True)
class ChunkSpan:
    text: str
    start_offset: int
    end_offset: int


def chunk_text(
    text: str,
    *,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    min_chars: int = DEFAULT_MIN_CHUNK_CHARS,
) -> list[ChunkSpan]:
    """Split `text` into overlapping chunks; return their (text, start, end)."""
    if not text.strip():
        return []
    target_chars = target_tokens * CHARS_PER_TOKEN_EST
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN_EST
    if target_chars <= 0:
        return []

    segments = _paragraph_segments(text)
    if not segments:
        return []

    # Split oversized paragraphs further by sentence.
    fine: list[tuple[str, int, int]] = []
    for seg, start, end in segments:
        if len(seg) <= target_chars:
            fine.append((seg, start, end))
        else:
            fine.extend(_split_sentence(seg, start, target_chars))

    # Greedy merge into target-sized chunks with overlap.
    chunks: list[ChunkSpan] = []
    buf: list[tuple[str, int, int]] = []
    buf_len = 0
    for seg, s, e in fine:
        seg_len = e - s
        if buf and buf_len + seg_len > target_chars:
            chunks.append(_emit(buf, text))
            buf = _carry_overlap(buf, overlap_chars)
            buf_len = sum(e2 - s2 for _, s2, e2 in buf)
        buf.append((seg, s, e))
        buf_len += seg_len
    if buf:
        chunks.append(_emit(buf, text))

    # Drop undersized chunks only when at least one large-enough chunk
    # remains. For genuinely short inputs we still return the one chunk we
    # produced — silently dropping it would lose information.
    big = [c for c in chunks if (c.end_offset - c.start_offset) >= min_chars]
    return big if big else chunks


def _paragraph_segments(text: str) -> list[tuple[str, int, int]]:
    out: list[tuple[str, int, int]] = []
    cursor = 0
    for m in _PARAGRAPH_RE.finditer(text):
        seg = text[cursor : m.start()]
        if seg.strip():
            out.append((seg, cursor, m.start()))
        cursor = m.end()
    tail = text[cursor:]
    if tail.strip():
        out.append((tail, cursor, len(text)))
    return out


def _split_sentence(seg: str, base: int, target_chars: int) -> list[tuple[str, int, int]]:
    pieces: list[tuple[str, int, int]] = []
    breaks = [(m.start(), m.end()) for m in _SENTENCE_RE.finditer(seg)]
    breaks.append((len(seg), len(seg)))
    cur_start = 0
    for cut_start, cut_end in breaks:
        if cut_start - cur_start >= target_chars:
            pieces.append((seg[cur_start:cut_start], base + cur_start, base + cut_start))
            cur_start = cut_end
    if cur_start < len(seg):
        pieces.append((seg[cur_start:], base + cur_start, base + len(seg)))
    if not pieces:
        return [(seg, base, base + len(seg))]
    return pieces


def _emit(buf: list[tuple[str, int, int]], text: str) -> ChunkSpan:
    start = buf[0][1]
    end = buf[-1][2]
    return ChunkSpan(text=text[start:end], start_offset=start, end_offset=end)


def _carry_overlap(
    buf: list[tuple[str, int, int]], overlap_chars: int
) -> list[tuple[str, int, int]]:
    """Drop the front of `buf` until total length ≤ overlap_chars."""
    if overlap_chars <= 0:
        return []
    out: list[tuple[str, int, int]] = []
    total = 0
    for seg, s, e in reversed(buf):
        seg_len = e - s
        if total + seg_len > overlap_chars and out:
            break
        out.append((seg, s, e))
        total += seg_len
    out.reverse()
    return out


__all__ = [
    "CHARS_PER_TOKEN_EST",
    "DEFAULT_MIN_CHUNK_CHARS",
    "DEFAULT_OVERLAP_TOKENS",
    "DEFAULT_TARGET_TOKENS",
    "ChunkSpan",
    "chunk_text",
]
