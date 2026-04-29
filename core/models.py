from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class Token:
    text: str
    start: int | None = None
    end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InlineText:
    text: str
    tokens: list[Token] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"text": self.text}
        if self.tokens:
            data["tokens"] = [
                {
                    "text": token.text,
                    "start": token.start,
                    "end": token.end,
                    "metadata": dict(token.metadata),
                }
                for token in self.tokens
            ]
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_value(cls, value: str | Mapping[str, Any]) -> "InlineText":
        if isinstance(value, str):
            return cls(text=value)

        tokens = [
            Token(
                text=str(token.get("text", "")),
                start=token.get("start"),
                end=token.get("end"),
                metadata=dict(token.get("metadata", {})),
            )
            for token in value.get("tokens", [])
        ]
        return cls(
            text=str(value.get("text", "")),
            tokens=tokens,
            metadata=dict(value.get("metadata", {})),
        )


@dataclass
class Block:
    kind: str
    text: InlineText | None = None
    items: list[InlineText] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def paragraph(cls, text: str, **metadata: Any) -> "Block":
        return cls(kind="paragraph", text=InlineText(text=text), metadata=metadata)

    @classmethod
    def heading(cls, text: str, **metadata: Any) -> "Block":
        return cls(kind="heading", text=InlineText(text=text), metadata=metadata)

    @classmethod
    def label(cls, text: str, **metadata: Any) -> "Block":
        return cls(kind="label", text=InlineText(text=text), metadata=metadata)

    @classmethod
    def list_block(cls, items: list[str], **metadata: Any) -> "Block":
        return cls(
            kind="list",
            items=[InlineText(text=item) for item in items],
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.kind}
        if self.text is not None:
            data["text"] = self.text.text
            if self.text.tokens:
                data["tokens"] = [
                    {
                        "text": token.text,
                        "start": token.start,
                        "end": token.end,
                        "metadata": dict(token.metadata),
                    }
                    for token in self.text.tokens
                ]
            if self.text.metadata:
                data["text_metadata"] = dict(self.text.metadata)
        if self.items:
            data["items"] = [item.text for item in self.items]
            if any(item.tokens for item in self.items):
                data["item_tokens"] = [
                    [
                        {
                            "text": token.text,
                            "start": token.start,
                            "end": token.end,
                            "metadata": dict(token.metadata),
                        }
                        for token in item.tokens
                    ]
                    for item in self.items
                ]
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Block":
        kind = str(value.get("type", "paragraph"))
        if kind == "list":
            items = [
                InlineText.from_value({"text": item_text, "tokens": item_tokens})
                for item_text, item_tokens in zip(
                    value.get("items", []),
                    value.get("item_tokens", [[] for _ in value.get("items", [])]),
                )
            ]
            if not items:
                items = [
                    InlineText.from_value(item_text)
                    for item_text in value.get("items", [])
                ]
            return cls(kind=kind, items=items, metadata=dict(value.get("metadata", {})))

        inline_payload: dict[str, Any] = {"text": value.get("text", "")}
        if "tokens" in value:
            inline_payload["tokens"] = value.get("tokens", [])
        if "text_metadata" in value:
            inline_payload["metadata"] = value.get("text_metadata", {})
        return cls(
            kind=kind,
            text=InlineText.from_value(inline_payload),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass
class Document:
    meta: dict[str, Any]
    blocks: list[Block] = field(default_factory=list)

    @property
    def paragraphs(self) -> list[str]:
        paragraphs: list[str] = []
        for block in self.blocks:
            if block.kind in {"heading", "paragraph", "label"} and block.text is not None:
                paragraphs.append(block.text.text)
            elif block.kind == "list":
                paragraphs.extend(f"- {item.text}" for item in block.items if item.text)
        return paragraphs

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": dict(self.meta),
            "blocks": [block.to_dict() for block in self.blocks],
            "paragraphs": self.paragraphs,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Document":
        return cls(
            meta=dict(value.get("meta", {})),
            blocks=[Block.from_mapping(block) for block in value.get("blocks", [])],
        )


def ensure_document(value: Document | Mapping[str, Any]) -> Document:
    if isinstance(value, Document):
        return value
    return Document.from_mapping(value)
