"""Shared helpers for parsing and formatting time inputs for FFmpeg filters."""

from __future__ import annotations

from typing import Optional


def parse_time_to_seconds(value: Optional[str]) -> Optional[float]:
    """Return seconds represented by ``value`` or ``None`` if empty."""

    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if ":" in text:
            parts = [float(part) for part in text.split(":")]
            seconds = 0.0
            for part in parts:
                seconds = seconds * 60 + part
            return seconds
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Invalid time value: '{value}'") from exc


def format_seconds(value: float) -> str:
    """Format a seconds value compactly for FFmpeg expressions."""

    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")
