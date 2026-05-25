from __future__ import annotations

import re

from core.models import Block, Document

DEFAULT_STRUCTURING_MODE = "strict"
STRUCTURING_MODE_OPTIONS = (
    ("simple", "Simple"),
    ("strict", "Strict"),
    ("none", "None"),
)
STRUCTURING_MODES = {mode for mode, _label in STRUCTURING_MODE_OPTIONS}
STRUCTURING_MODE_ALIASES = {
    "conservative": "strict",
}

_CJK_SPACE_RE = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_BULLET_RE = re.compile(r"^\s*(?:[\u2022\u00b7\-\u2013\u2014*]|\d+[\.\)])\s+(.*\S.*)$")
_PUNCTUATION_RE = re.compile(r"[。！？；：，、.!?;:,]")
_SENTENCE_END_RE = re.compile(r"[。！？.!?]$")
_CHAPTER_HEADING_RE = re.compile(
    r"^\s*第[一二三四五六七八九十百千万0-9]+[章节篇回部卷]\s*[:：]?\s*\S.*$"
)
_NUMBERED_HEADING_RE = re.compile(r"^\s*[一二三四五六七八九十0-9]+[、.．]\s*\S.*$")
_MAX_HEADING_LENGTH = 18
_MAX_LIST_LINE_LENGTH = 120


def normalize_structuring_mode(mode: str | None) -> str:
    if not mode:
        return DEFAULT_STRUCTURING_MODE

    normalized = mode.strip().lower()
    normalized = STRUCTURING_MODE_ALIASES.get(normalized, normalized)

    if normalized not in STRUCTURING_MODES:
        raise ValueError(f"Unsupported structuring mode: {mode}")

    return normalized


def _base_meta(mode: str) -> dict[str, str]:
    return {"structuring_mode": mode}


def _normalize_line(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    text = _CJK_SPACE_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    return text.strip()


def _normalize_raw_line(text: str) -> str:
    return text.strip()


def _split_list_item(line: str) -> str | None:
    match = _BULLET_RE.match(line)
    if not match:
        return None
    return _normalize_line(match.group(1))


def _is_label(line: str) -> bool:
    return line.endswith(":") or line.endswith("：")


def _is_heading(line: str) -> bool:
    if _CHAPTER_HEADING_RE.match(line):
        return True
    if _NUMBERED_HEADING_RE.match(line):
        return True
    if line.startswith(("(", "（", "[", "【")) and line.endswith((")", "）", "]", "】")):
        return len(line.replace(" ", "")) <= 30

    compact = line.replace(" ", "")
    if not compact:
        return False
    if _PUNCTUATION_RE.search(line):
        return False
    return len(compact) <= _MAX_HEADING_LENGTH


def _last_visible_char(text: str) -> str:
    for char in reversed(text):
        if not char.isspace():
            return char
    return ""


def _first_visible_char(text: str) -> str:
    for char in text:
        if not char.isspace():
            return char
    return ""


def _is_cjk_char(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def _should_join_without_space(left: str, right: str) -> bool:
    left_char = _last_visible_char(left)
    right_char = _first_visible_char(right)
    return _is_cjk_char(left_char) and _is_cjk_char(right_char)


def _join_lines(lines: list[str]) -> str:
    if not lines:
        return ""

    text = lines[0]
    for line in lines[1:]:
        if _should_join_without_space(text, line):
            text = f"{text}{line}"
        else:
            text = f"{text} {line}"

    return _normalize_line(text)


def _split_line_groups(
    text: str,
    *,
    normalizer,
) -> list[list[str]]:
    groups: list[list[str]] = []
    current_group: list[str] = []

    for raw_line in text.splitlines():
        line = normalizer(raw_line)
        if not line:
            if current_group:
                groups.append(current_group[:])
                current_group.clear()
            continue
        current_group.append(line)

    if current_group:
        groups.append(current_group)

    return groups


def _build_simple_document(text: str) -> Document:
    blocks: list[Block] = []
    for group in _split_line_groups(text, normalizer=_normalize_line):
        paragraph_text = _join_lines(group)
        if paragraph_text:
            blocks.append(Block.paragraph(paragraph_text))
    return Document(meta=_base_meta("simple"), blocks=blocks)


def _build_none_document(text: str) -> Document:
    blocks: list[Block] = []
    for group in _split_line_groups(text, normalizer=_normalize_raw_line):
        paragraph_text = "\n".join(group).strip()
        if paragraph_text:
            blocks.append(Block.paragraph(paragraph_text))
    return Document(meta=_base_meta("none"), blocks=blocks)


def _build_strict_document(text: str) -> Document:
    blocks: list[Block] = []
    current_paragraph: list[str] = []
    current_list: list[str] = []
    prefer_plain_list = False

    def looks_like_plain_list_block(lines: list[str]) -> bool:
        normalized_lines = [line for line in lines if line and line.strip()]
        if len(normalized_lines) < 2:
            return False
        if any(_is_label(line) or _is_heading(line) for line in normalized_lines):
            return False
        if any(len(line) > _MAX_LIST_LINE_LENGTH for line in normalized_lines):
            return False

        sentence_like_count = sum(
            1 for line in normalized_lines if _SENTENCE_END_RE.search(line)
        )
        return sentence_like_count >= max(2, len(normalized_lines) - 1)

    def flush_paragraph() -> None:
        nonlocal prefer_plain_list

        if not current_paragraph:
            prefer_plain_list = False
            return

        if prefer_plain_list and looks_like_plain_list_block(current_paragraph):
            items = [normalized for line in current_paragraph if (normalized := _normalize_line(line))]
            current_paragraph.clear()
            prefer_plain_list = False
            if items:
                blocks.append(Block.list_block(items))
            return

        paragraph_text = _join_lines(current_paragraph)
        current_paragraph.clear()
        prefer_plain_list = False
        if paragraph_text:
            blocks.append(Block.paragraph(paragraph_text))

    def flush_list() -> None:
        if not current_list:
            return

        items = [item for item in current_list if item]
        current_list.clear()
        if items:
            blocks.append(Block.list_block(items))

    for raw_line in text.splitlines():
        line = _normalize_line(raw_line)
        if not line:
            flush_paragraph()
            flush_list()
            continue

        list_item = _split_list_item(line)
        if list_item is not None:
            flush_paragraph()
            current_list.append(list_item)
            continue

        flush_list()

        if _is_label(line):
            flush_paragraph()
            blocks.append(Block.label(line))
            prefer_plain_list = True
            continue

        if _is_heading(line):
            flush_paragraph()
            blocks.append(Block.heading(line))
            prefer_plain_list = False
            continue

        current_paragraph.append(line)

    flush_paragraph()
    flush_list()
    return Document(meta=_base_meta("strict"), blocks=blocks)


def build_document(
    text: str,
    mode: str = DEFAULT_STRUCTURING_MODE,
) -> Document:
    normalized_mode = normalize_structuring_mode(mode)
    if normalized_mode == "simple":
        return _build_simple_document(text)
    if normalized_mode == "none":
        return _build_none_document(text)
    return _build_strict_document(text)


class StructuredDocumentBuilder:
    def build(self, text: str, mode: str = DEFAULT_STRUCTURING_MODE) -> Document:
        return build_document(text, mode=mode)
