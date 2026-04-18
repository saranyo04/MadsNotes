import re
from typing import Any

CONFIG = {
    "title": "Chinese Study",
    "lang": "zh-CN",
    "font_family": "Microsoft YaHei, PingFang SC, sans-serif",
    "padding": "40px",
    "line_height": "1.9",
    "font_size": "18px",
    "max_width": "100%",
    "margin": "0",
    "background": "#fff",
    "color": "#111",
    "paragraph_margin_bottom": "1em",
    "paragraph_text_indent": "2em",
    "remove_whitespace_between_chinese": True,
    "collapse_multiple_spaces": True,
}

_CJK = r"\u4e00-\u9fff"
_CJK_RE = re.compile(rf"[{_CJK}]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_CJK_SPACE_RE = re.compile(rf"(?<=[{_CJK}])\s+(?=[{_CJK}])")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_SCRIPT_SWITCH_RE = re.compile(
    rf"(?<=[{_CJK}])(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])(?=[{_CJK}])"
)

_BULLET_RE = re.compile(r"^\s*(?:[•·\-–—*]|(?:\d+[\.\)]))\s+(.*\S.*)$")
_HEADING_RE = re.compile(
    r"^\s*(?:第[一二三四五六七八九十百千0-9]+章|[一二三四五六七八九十]+、)\s*$"
)

_KNOWN_LABELS = (
    "中文要点：",
    "中文要点:",
    "English (translation):",
    "English translation:",
    "English Translation:",
    "翻译：",
    "翻译:",
    "要点：",
    "要点:",
    "重点：",
    "重点:",
)


def _kind(text: str) -> str:
    has_cjk = bool(_CJK_RE.search(text))
    has_lat = bool(_LATIN_RE.search(text))

    if has_cjk and not has_lat:
        return "cjk"
    if has_lat and not has_cjk:
        return "latin"
    if has_cjk and has_lat:
        return "mixed"
    return "other"


def _normalize_cjk(text: str) -> str:
    text = text.strip()
    if CONFIG["remove_whitespace_between_chinese"]:
        text = _CJK_SPACE_RE.sub("", text)
    if CONFIG["collapse_multiple_spaces"]:
        text = _MULTI_SPACE_RE.sub(" ", text)
    return text.strip()


def _normalize_latin(text: str) -> str:
    text = text.strip()
    if CONFIG["collapse_multiple_spaces"]:
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_by_kind(text: str, kind: str) -> str:
    if kind == "cjk":
        return _normalize_cjk(text)
    return _normalize_latin(text)


def _is_heading(line: str) -> bool:
    s = line.strip()
    return bool(s) and bool(_HEADING_RE.match(s))


def _split_bullet(line: str) -> str | None:
    m = _BULLET_RE.match(line)
    if not m:
        return None
    return m.group(1).strip()


def _split_script_switch(text: str) -> list[str]:
    parts = [p for p in _SCRIPT_SWITCH_RE.split(text) if p and p.strip()]
    return parts if parts else [text]


def _split_label_prefix(line: str) -> tuple[str, str] | None:
    s = line.strip()

    for known in _KNOWN_LABELS:
        if s.startswith(known):
            return known, s[len(known):].strip()

    if ":" not in s and "：" not in s:
        return None

    idx = s.find(":") if ":" in s else s.find("：")
    prefix = s[: idx + 1].strip()
    suffix = s[idx + 1 :].strip()

    if not suffix:
        return None
    if len(prefix) > 40:
        return None
    if any(ch in prefix for ch in "。！？!?"):
        return None

    if re.fullmatch(r"[A-Za-z\u4e00-\u9fff0-9（）()·\s,\-\/&]+[:：]", prefix):
        return prefix, suffix

    return None


def _flush_paragraph(
    blocks: list[dict],
    paragraphs: list[str],
    current_kind: str | None,
    current_parts: list[str],
) -> tuple[str | None, list[str]]:
    if not current_parts:
        return None, []

    if current_kind == "cjk":
        text = "".join(current_parts)
    else:
        text = " ".join(current_parts)

    text = _normalize_by_kind(text, current_kind or "other")
    text = text.strip()

    if text:
        blocks.append(
            {
                "type": "paragraph",
                "kind": current_kind or "other",
                "text": text,
            }
        )
        paragraphs.append(text)

    return None, []


def _flush_list(
    blocks: list[dict],
    paragraphs: list[str],
    current_items: list[str],
) -> list[str]:
    if not current_items:
        return []

    blocks.append({"type": "list", "items": current_items[:]})
    for item in current_items:
        if item.strip():
            paragraphs.append(f"• {item.strip()}")

    return []


def build_document(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines()]

    blocks: list[dict] = []
    paragraphs: list[str] = []

    current_kind: str | None = None
    current_parts: list[str] = []

    current_list_items: list[str] = []
    in_list_block = False

    def flush_paragraph():
        nonlocal current_kind, current_parts
        current_kind, current_parts = _flush_paragraph(
            blocks, paragraphs, current_kind, current_parts
        )

    def flush_list():
        nonlocal current_list_items
        current_list_items = _flush_list(blocks, paragraphs, current_list_items)

    def process_text_segment(segment: str):
        nonlocal current_kind, current_parts

        for piece in _split_script_switch(segment):
            piece = piece.strip()
            if not piece:
                continue

            piece_kind = _kind(piece)
            normalized = _normalize_by_kind(piece, piece_kind)

            if not normalized:
                continue

            if current_kind is None:
                current_kind = piece_kind
                current_parts = [normalized]
            elif piece_kind != current_kind:
                flush_paragraph()
                current_kind = piece_kind
                current_parts = [normalized]
            else:
                current_parts.append(normalized)

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            flush_paragraph()
            flush_list()
            in_list_block = False
            continue

        if _is_heading(line):
            flush_paragraph()
            flush_list()
            in_list_block = False

            heading = _normalize_latin(line)
            if heading:
                blocks.append({"type": "heading", "text": heading})
                paragraphs.append(heading)
            continue

        label_split = _split_label_prefix(line)
        if label_split:
            flush_paragraph()
            flush_list()
            in_list_block = False

            label_text, remainder = label_split
            label_text = _normalize_latin(label_text)

            if label_text:
                blocks.append({"type": "label", "text": label_text})
                paragraphs.append(label_text)

            if remainder:
                process_text_segment(remainder)

            continue

        bullet_text = _split_bullet(line)
        if bullet_text is not None:
            flush_paragraph()

            item = _normalize_latin(bullet_text) if _kind(bullet_text) == "latin" else _normalize_cjk(bullet_text)
            if item:
                current_list_items.append(item)

            in_list_block = True
            continue

        if in_list_block and current_list_items:
            continuation = _normalize_latin(line) if _kind(line) == "latin" else _normalize_cjk(line)
            if continuation:
                current_list_items[-1] = f"{current_list_items[-1]} {continuation}".strip()
            continue

        process_text_segment(line)

    flush_paragraph()
    flush_list()

    return {
        "meta": CONFIG.copy(),
        "blocks": blocks,
        "paragraphs": paragraphs,
    }