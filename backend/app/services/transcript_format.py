"""
Pure formatting helpers for transcript segments.
"""

from typing import Any


def _format_time(seconds: float) -> str:
    """Convert a float number of seconds to MM:SS string."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_transcript(
    segments: list[dict[str, Any]], include_timestamps: bool = True
) -> str:
    """
    Format raw transcript segments into a human-readable string.

    Args:
        segments:           List of dicts with ``start`` and ``text`` keys.
        include_timestamps: When True, each line is prefixed with ``[MM:SS]``.

    Returns:
        Formatted transcript text with one segment per line.
    """
    if not segments:
        return ""

    lines: list[str] = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        if include_timestamps:
            ts = _format_time(float(segment.get("start", 0)))
            lines.append(f"[{ts}] {text}")
        else:
            lines.append(text)

    return "\n".join(lines)
