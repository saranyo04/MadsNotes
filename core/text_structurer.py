import re
from typing import Any

CONFIG = {
    "sentence_endings": r"[。！？!?]",
    "closing_quotes": r"[”’\"'）】》』〕]*",
    "sentences_per_paragraph": 3,
    "remove_whitespace_between_chinese": True,
    "collapse_multiple_spaces": True,
    "title": "Chinese Study",
    "lang": "zh-CN",
    "font_family": '"Microsoft YaHei", "PingFang SC", sans-serif',
    "padding": "40px",
    "line_height": "1.9",
    "font_size": "18px",
    "max_width": "900px",
    "margin": "0",
    "background": "#fff",
    "color": "#111",
    "paragraph_margin_bottom": "1em",
    "paragraph_text_indent": "2em",
}

# Chinese / CJK characters
_CJK = r"\u4e00-\u9fff"

# Remove whitespace between Chinese characters only
_CJK_SPACE_RE = re.compile(rf"(?<=[{_CJK}])\s+(?=[{_CJK}])")

# Sentence detection for Chinese and English punctuation
_SENTENCE_RE = re.compile(
    rf".+?[{CONFIG['sentence_endings']}]+{CONFIG['closing_quotes']}"
)

# Collapse repeated spaces/tabs but keep single spaces for English text
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def clean_ocr_text(text: str) -> str:
    """
    Keeps English spacing readable while fixing broken Chinese OCR line splits.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    # Join with a space so English doesn't get smashed together.
    merged = " ".join(lines)

    # Remove spaces inserted inside Chinese text.
    if CONFIG["remove_whitespace_between_chinese"]:
        merged = _CJK_SPACE_RE.sub("", merged)

    # Collapse excessive spaces, but preserve normal English word spacing.
    if CONFIG["collapse_multiple_spaces"]:
        merged = _MULTI_SPACE_RE.sub(" ", merged)

    return merged.strip()


def split_into_sentences(text: str) -> list[str]:
    if not text.strip():
        return []

    sentences = []
    last_end = 0

    for match in _SENTENCE_RE.finditer(text):
        sentence = match.group(0).strip()
        if sentence:
            sentences.append(sentence)
        last_end = match.end()

    tail = text[last_end:].strip()
    if tail:
        sentences.append(tail)

    return sentences


def group_into_paragraphs(sentences: list[str]) -> list[str]:
    if not sentences:
        return []

    n = max(1, int(CONFIG["sentences_per_paragraph"]))
    paragraphs = []

    for i in range(0, len(sentences), n):
        chunk = sentences[i:i + n]
        paragraphs.append(" ".join(chunk) if _looks_english(chunk) else "".join(chunk))

    return paragraphs


def _looks_english(chunk: list[str]) -> bool:
    text = " ".join(chunk)
    return bool(re.search(r"[A-Za-z]", text)) and not bool(re.search(rf"[{_CJK}]", text))


def build_document(text: str) -> dict[str, Any]:
    cleaned = clean_ocr_text(text)
    if not cleaned:
        return {
            "meta": CONFIG.copy(),
            "paragraphs": [],
        }

    sentences = split_into_sentences(cleaned)

    if sentences:
        paragraphs = group_into_paragraphs(sentences)
    else:
        paragraphs = [cleaned]

    return {
        "meta": CONFIG.copy(),
        "paragraphs": paragraphs,
    }