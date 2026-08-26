"""主题模型：内置配色主题表与查找。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

Color = "tuple[int, int, int]"


@dataclass
class Theme:
    """一整套配色：界面各元素的前景/背景色。"""

    name: str
    title: str
    background: Color
    foreground: Color
    header_fg: Color
    header_bg: Color
    selection_fg: Color
    selection_bg: Color
    dim_fg: Color
    accent_fg: Color
    status_fg: Color
    status_bg: Color


_THEMES: Dict[str, Theme] = {
    "sepia": Theme(
        name="sepia", title="护眼 · 暖黄",
        background=(250, 244, 232), foreground=(80, 68, 50),
        header_fg=(250, 244, 232), header_bg=(139, 119, 92),
        selection_fg=(255, 255, 255), selection_bg=(176, 142, 88),
        dim_fg=(150, 138, 118), accent_fg=(166, 94, 46),
        status_fg=(80, 68, 50), status_bg=(232, 220, 198),
    ),
    "classic": Theme(
        name="classic", title="经典 · 白底黑字",
        background=(255, 255, 255), foreground=(20, 20, 20),
        header_fg=(255, 255, 255), header_bg=(60, 60, 60),
        selection_fg=(255, 255, 255), selection_bg=(52, 120, 246),
        dim_fg=(120, 120, 120), accent_fg=(0, 90, 160),
        status_fg=(40, 40, 40), status_bg=(230, 230, 230),
    ),
    "dark": Theme(
        name="dark", title="暗色 · 夜间",
        background=(24, 26, 32), foreground=(210, 215, 220),
        header_fg=(24, 26, 32), header_bg=(150, 160, 172),
        selection_fg=(0, 0, 0), selection_bg=(120, 200, 120),
        dim_fg=(110, 116, 124), accent_fg=(120, 200, 120),
        status_fg=(210, 215, 220), status_bg=(44, 48, 56),
    ),
    "paper": Theme(
        name="paper", title="纸张 · 米白",
        background=(247, 241, 227), foreground=(51, 45, 36),
        header_fg=(247, 241, 227), header_bg=(120, 108, 90),
        selection_fg=(255, 255, 255), selection_bg=(150, 130, 90),
        dim_fg=(150, 140, 125), accent_fg=(150, 90, 40),
        status_fg=(51, 45, 36), status_bg=(230, 222, 204),
    ),
    "terminal": Theme(
        name="terminal", title="终端 · 绿字",
        background=(12, 18, 14), foreground=(120, 210, 130),
        header_fg=(12, 18, 14), header_bg=(60, 130, 70),
        selection_fg=(12, 18, 14), selection_bg=(120, 210, 130),
        dim_fg=(70, 120, 80), accent_fg=(180, 240, 190),
        status_fg=(120, 210, 130), status_bg=(22, 34, 26),
    ),
    "plain": Theme(
        name="plain", title="命令行 · 单色",
        background=(255, 255, 255), foreground=(30, 30, 30),
        header_fg=(255, 255, 255), header_bg=(70, 70, 70),
        selection_fg=(255, 255, 255), selection_bg=(90, 90, 90),
        dim_fg=(140, 140, 140), accent_fg=(60, 60, 60),
        status_fg=(30, 30, 30), status_bg=(232, 232, 232),
    ),
    "plain-dark": Theme(
        name="plain-dark", title="命令行 · 单色暗",
        background=(24, 24, 26), foreground=(205, 205, 205),
        header_fg=(24, 24, 26), header_bg=(120, 120, 124),
        selection_fg=(24, 24, 26), selection_bg=(155, 155, 158),
        dim_fg=(110, 110, 114), accent_fg=(180, 180, 184),
        status_fg=(205, 205, 205), status_bg=(40, 40, 44),
    ),
}

_ORDER = ["sepia", "classic", "dark", "paper", "terminal", "plain", "plain-dark"]


def theme_names() -> list:
    return list(_ORDER)


def get_theme(name: str) -> Theme:
    return _THEMES[name]


def default_theme() -> Theme:
    return _THEMES["plain-dark"]


def describe_themes() -> str:
    return "，".join(f"{k}({t.title})" for k, t in _THEMES.items())


def is_valid(name: str) -> bool:
    return name in _THEMES
