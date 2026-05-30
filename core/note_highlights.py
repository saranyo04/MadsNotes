from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HIGHLIGHT_COLOR_OPTIONS: tuple[tuple[str, str, str], ...] = (
    ("yellow", "Yellow", "#FFF2A8"),
    ("green", "Green", "#CFECC8"),
    ("pink", "Pink", "#F8CAD8"),
    ("blue", "Blue", "#C9DDF7"),
)
HIGHLIGHT_COLORS = {key: value for key, _label, value in HIGHLIGHT_COLOR_OPTIONS}
DEFAULT_HIGHLIGHT_COLOR = "yellow"


@dataclass(frozen=True)
class HighlightSpan:
    start: int
    end: int
    color: str = DEFAULT_HIGHLIGHT_COLOR


def highlight_spans_from_value(value: Any) -> list[HighlightSpan]:
    if not isinstance(value, list):
        return []

    spans: list[HighlightSpan] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            start = int(item.get("start", 0))
            end = int(item.get("end", 0))
        except (TypeError, ValueError):
            continue
        color = str(item.get("color") or DEFAULT_HIGHLIGHT_COLOR).casefold()
        spans.append(HighlightSpan(start=start, end=end, color=_valid_color(color)))
    return normalize_highlight_spans(spans)


def highlight_spans_to_dicts(spans: list[HighlightSpan]) -> list[dict[str, object]]:
    return [
        {"start": span.start, "end": span.end, "color": span.color}
        for span in normalize_highlight_spans(spans)
    ]


def normalize_highlight_spans(
    spans: list[HighlightSpan],
    *,
    text_length: int | None = None,
) -> list[HighlightSpan]:
    cleaned: list[HighlightSpan] = []
    for span in spans:
        start = max(0, int(span.start))
        end = max(0, int(span.end))
        if text_length is not None:
            start = min(start, text_length)
            end = min(end, text_length)
        if end <= start:
            continue
        cleaned.append(HighlightSpan(start=start, end=end, color=_valid_color(span.color)))

    cleaned.sort(key=lambda span: (span.start, span.end))
    return cleaned


def set_highlight(
    spans: list[HighlightSpan],
    *,
    start: int,
    end: int,
    color: str,
    text_length: int,
) -> list[HighlightSpan]:
    start, end = _selection_bounds(start, end, text_length)
    if end <= start:
        return normalize_highlight_spans(spans, text_length=text_length)

    next_spans = _remove_range(spans, start=start, end=end, text_length=text_length)
    next_spans.append(HighlightSpan(start=start, end=end, color=_valid_color(color)))
    return normalize_highlight_spans(next_spans, text_length=text_length)


def clear_highlight(
    spans: list[HighlightSpan],
    *,
    start: int,
    end: int,
    text_length: int,
) -> list[HighlightSpan]:
    start, end = _selection_bounds(start, end, text_length)
    if end <= start:
        return normalize_highlight_spans(spans, text_length=text_length)
    return _remove_range(spans, start=start, end=end, text_length=text_length)


def _remove_range(
    spans: list[HighlightSpan],
    *,
    start: int,
    end: int,
    text_length: int,
) -> list[HighlightSpan]:
    next_spans: list[HighlightSpan] = []
    for span in normalize_highlight_spans(spans, text_length=text_length):
        if span.end <= start or span.start >= end:
            next_spans.append(span)
            continue
        if span.start < start:
            next_spans.append(HighlightSpan(span.start, start, span.color))
        if span.end > end:
            next_spans.append(HighlightSpan(end, span.end, span.color))
    return normalize_highlight_spans(next_spans, text_length=text_length)


def _selection_bounds(start: int, end: int, text_length: int) -> tuple[int, int]:
    lower = max(0, min(start, end, text_length))
    upper = max(0, min(max(start, end), text_length))
    return lower, upper


def _valid_color(color: str) -> str:
    return color if color in HIGHLIGHT_COLORS else DEFAULT_HIGHLIGHT_COLOR
