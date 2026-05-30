from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FALLBACK_THEME_NAME = "System Default"
DEFAULT_THEME_NAME = "Strawberry Matcha"
THEME_TOKEN_NAMES = (
    "primary",
    "secondary",
    "background",
    "surface",
    "text",
    "accent",
)


@dataclass(frozen=True)
class ThemeTokens:
    primary: str
    secondary: str
    background: str
    surface: str
    text: str
    accent: str


@dataclass(frozen=True)
class Theme:
    name: str
    tokens: ThemeTokens


FALLBACK_THEME = Theme(
    name=FALLBACK_THEME_NAME,
    tokens=ThemeTokens(
        primary="#E6E6E6",
        secondary="#D8D8D8",
        background="#F6F6F6",
        surface="#FFFFFF",
        text="#303030",
        accent="#6F8F5E",
    ),
)


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_shipped_themes_path() -> Path:
    return Path(__file__).resolve().parent / "themes"


def get_user_themes_path() -> Path:
    return get_app_root() / "user_themes"


def load_themes(
    *,
    shipped_themes_path: Path | None = None,
    user_themes_path: Path | None = None,
) -> dict[str, Theme]:
    themes = {FALLBACK_THEME.name: FALLBACK_THEME}

    for theme in _load_theme_directory(shipped_themes_path or get_shipped_themes_path()):
        themes[theme.name] = theme

    for theme in _load_theme_directory(user_themes_path or get_user_themes_path()):
        themes[theme.name] = theme

    return themes


def get_theme(name: str = DEFAULT_THEME_NAME) -> Theme:
    themes = load_themes()
    return themes.get(name) or themes[FALLBACK_THEME_NAME]


def sorted_theme_names(themes: dict[str, Theme]) -> list[str]:
    return sorted(themes, key=lambda name: (name != FALLBACK_THEME_NAME, name.lower()))


def _load_theme_directory(path: Path) -> Iterable[Theme]:
    if not path.is_dir():
        return ()

    themes: list[Theme] = []
    for theme_path in sorted(path.glob("*.json")):
        theme = _load_theme_file(theme_path)
        if theme is not None:
            themes.append(theme)
    return themes


def _load_theme_file(path: Path) -> Theme | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    name = str(data.get("name") or path.stem).strip()
    if not name:
        return None

    tokens: dict[str, str] = {}
    for token_name in THEME_TOKEN_NAMES:
        value = data.get(token_name)
        if not isinstance(value, str) or not _is_hex_color(value):
            return None
        tokens[token_name] = value.upper()

    return Theme(name=name, tokens=ThemeTokens(**tokens))


def _is_hex_color(value: str) -> bool:
    if len(value) != 7 or not value.startswith("#"):
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value[1:])


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))


def _rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02X}{green:02X}{blue:02X}"


def mix(color: str, other: str, amount: float) -> str:
    red, green, blue = _hex_to_rgb(color)
    other_red, other_green, other_blue = _hex_to_rgb(other)
    return _rgb_to_hex(
        round(red + (other_red - red) * amount),
        round(green + (other_green - green) * amount),
        round(blue + (other_blue - blue) * amount),
    )


def theme_stylesheet(theme: Theme) -> str:
    tokens = theme.tokens
    primary = tokens.primary
    secondary = tokens.secondary
    background = tokens.background
    surface = tokens.surface
    text = tokens.text
    accent = tokens.accent
    white = "#FFFFFF"
    black = "#000000"

    primary_soft = mix(primary, white, 0.72)
    primary_softer = mix(primary, white, 0.84)
    primary_text = mix(primary, black, 0.34)
    primary_border = mix(primary, white, 0.45)
    secondary_soft = mix(secondary, white, 0.70)
    secondary_softer = mix(secondary, white, 0.84)
    secondary_text = mix(secondary, black, 0.48)
    secondary_border = mix(secondary, white, 0.42)
    surface_lift = mix(surface, white, 0.45)
    surface_deep = mix(surface, black, 0.04)
    text_soft = mix(text, white, 0.34)
    text_muted = mix(text, white, 0.48)
    border_soft = mix(secondary, surface, 0.55)
    accent_soft = mix(accent, white, 0.78)
    accent_text = mix(accent, black, 0.30)
    danger_bg = mix("#F2B9B0", surface, 0.62)
    danger_text = "#9D4F42"

    return f"""
            QWidget {{
                background-color: {background};
                color: {text};
                font-family: "Segoe UI";
                font-size: 14px;
            }}

            QLabel {{
                background-color: transparent;
            }}

            QPlainTextEdit {{
                background-color: {surface_lift};
                color: {text};
                border: 1px dashed {primary_border};
                border-radius: 16px;
                padding: 22px;
                selection-background-color: {primary};
                selection-color: {text};
            }}

            QPushButton, QComboBox, QToolButton, QLineEdit {{
                background-color: {surface};
                color: {text};
                border: 1px solid transparent;
                border-radius: 12px;
                padding: 11px 14px;
            }}

            QPushButton:hover, QComboBox:hover, QToolButton:hover, QLineEdit:hover {{
                background-color: {primary_softer};
                border-color: {primary};
            }}

            QPushButton:disabled, QComboBox:disabled, QToolButton:disabled, QLineEdit:disabled {{
                color: {text_muted};
                background-color: {surface_deep};
                border-color: {border_soft};
            }}

            QComboBox {{
                min-width: 150px;
                min-height: 24px;
            }}

            QComboBox#modeCombo, QComboBox#themeCombo {{
                background-color: {surface_lift};
                border-color: {secondary_border};
                padding-left: 14px;
            }}

            QLineEdit#savedNotesSearch {{
                background-color: {surface_lift};
                border-color: {secondary_border};
                selection-background-color: {primary};
                selection-color: {text};
            }}

            QLineEdit#savedNotesSearch:focus {{
                border-color: {primary};
                background-color: {primary_softer};
            }}

            QToolButton#settingsButton {{
                background-color: {secondary_soft};
                border-color: transparent;
                color: {secondary_text};
                padding: 12px 18px;
                font-weight: 600;
            }}

            QMenu {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border_soft};
                border-radius: 12px;
                padding: 10px;
            }}

            QMenu::item {{
                padding: 8px 28px 8px 12px;
                border-radius: 6px;
            }}

            QMenu::item:selected {{
                background-color: {primary_softer};
            }}

            QCheckBox {{
                spacing: 10px;
                background-color: transparent;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {secondary};
                border-radius: 5px;
                background-color: {background};
            }}

            QCheckBox::indicator:checked {{
                background-color: {secondary};
                border-color: {secondary_border};
            }}

            QFrame#topBar,
            QFrame#leftNav,
            QFrame#rightUtility,
            QFrame#bottomActions {{
                background-color: {surface};
                border: 1px solid transparent;
                border-radius: 18px;
            }}

            QFrame#mainContent {{
                background-color: {surface};
                border: 1px solid transparent;
                border-radius: 18px;
            }}

            QFrame#editorCard {{
                background-color: {surface_lift};
                border: 1px solid {primary_border};
                border-radius: 18px;
            }}

            QFrame#utilityGroup {{
                background-color: {secondary_softer};
                border: 1px solid transparent;
                border-radius: 14px;
            }}

            QLabel#appTitle {{
                color: {text};
                font-size: 18px;
                font-weight: 700;
            }}

            QLabel#sectionTitle {{
                color: {text};
                font-size: 18px;
                font-weight: 700;
                background-color: transparent;
            }}

            QLabel#panelHint {{
                color: {text_muted};
                font-size: 12px;
                background-color: transparent;
            }}

            QLabel#fieldLabel {{
                color: {text_soft};
                background-color: transparent;
            }}

            QFrame#emptyState {{
                background-color: transparent;
                border: none;
            }}

            QLabel#emptyStateHeading {{
                color: {text};
                font-size: 26px;
                font-weight: 700;
            }}

            QLabel#emptyStateText {{
                color: {text_soft};
                font-size: 15px;
            }}

            QLabel#emptyStateArt {{
                color: {accent_text};
                font-size: 15px;
                font-weight: 700;
            }}

            QLabel#emptyStateIcon {{
                background-color: {accent_soft};
                border: 1px solid {secondary_border};
                border-radius: 20px;
                padding: 18px;
            }}

            QPushButton#navButton {{
                text-align: left;
                background-color: {surface};
                border: 1px solid transparent;
                border-radius: 14px;
                padding: 13px 16px;
                color: {secondary_text};
            }}

            QPushButton#navButton:hover,
            QPushButton#navButton[active="true"] {{
                background-color: {secondary_soft};
                border-color: transparent;
                color: {text};
            }}

            QPushButton#primaryAction {{
                background-color: {primary_softer};
                color: {primary_text};
                border-color: {primary_border};
                padding: 15px 18px;
                font-size: 16px;
                font-weight: 700;
            }}

            QPushButton#primaryAction:hover {{
                background-color: {primary_soft};
                border-color: {primary};
            }}

            QPushButton#secondaryAction {{
                background-color: {secondary_softer};
                border-color: transparent;
                color: {secondary_text};
                padding: 14px 16px;
                font-weight: 600;
            }}

            QPushButton#secondaryAction:hover {{
                background-color: {secondary_soft};
                border-color: {secondary};
            }}

            QScrollArea {{
                background-color: transparent;
                border: none;
            }}

            QListWidget#savedNotesList {{
                background-color: transparent;
                border: none;
                outline: none;
            }}

            QListWidget#savedNotesList::item {{
                background-color: transparent;
                border: none;
                color: {text};
                padding: 0;
                margin: 0;
            }}

            QListWidget#savedNotesList::item:hover,
            QListWidget#savedNotesList::item:selected {{
                background-color: transparent;
                border: none;
            }}

            QFrame#savedNoteRow {{
                background-color: {surface_lift};
                border: 1px solid transparent;
                border-radius: 12px;
            }}

            QFrame#savedNoteRow:hover {{
                background-color: {secondary_soft};
                border-color: {secondary_border};
            }}

            QLabel#savedNoteTitle {{
                color: {text};
                background-color: transparent;
                font-weight: 600;
                font-size: 13px;
            }}

            QToolButton#savedNoteDeleteButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 7px;
                padding: 3px;
            }}

            QToolButton#savedNoteDeleteButton:hover {{
                background-color: {danger_bg};
                border-color: {mix("#F2B9B0", surface, 0.35)};
            }}

            QToolButton#savedNoteDeleteButton[confirming="true"] {{
                background-color: {danger_bg};
                border-color: {mix("#F2B9B0", surface, 0.35)};
            }}

            QPushButton#utilityDanger {{
                background-color: {danger_bg};
                border-color: {mix("#F2B9B0", surface, 0.35)};
                color: {danger_text};
                padding: 13px 14px;
            }}
        """
