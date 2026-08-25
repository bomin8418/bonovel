"""界面视图基类与通用绘制辅助。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from bonovel import renderer as r
from bonovel.themes import Theme


class View(ABC):
    """所有界面（书架/阅读/设置/帮助/书签）的基类。"""

    def __init__(self, app: Any, theme: Theme, columns: int, rows: int):
        self.app = app
        self.theme = theme
        self.columns = columns
        self.rows = rows

    @abstractmethod
    def render(self, screen: r.Screen) -> None:
        """把界面内容写入 Screen 缓冲。"""

    @abstractmethod
    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        """处理一个逻辑键，返回跳转的视图名或 None。"""

    def resize(self, columns: int, rows: int) -> None:
        self.columns = columns
        self.rows = rows


def style_line(content: str, style: r.Style) -> str:
    return r.apply_style(content, style)


def draw_header(
    screen: r.Screen, title: str, theme: Theme, hint: str = ""
) -> None:
    """顶部标题栏：填充背景色，右侧显示小提示。"""
    width = screen.columns
    text = " " + title
    if hint:
        text = f"{title}   ·   {hint}"
    text = f" {title} " if not hint else f" {title} · {hint} "
    if r.utils.display_width(text) < width:
        text += " " * (width - r.utils.display_width(text))
    else:
        text = text[:width]
    screen.set(
        style_line(text, r.Style(fg=theme.header_fg, bg=theme.header_bg)), row=0
    )


def draw_footer(screen: r.Screen, theme: Theme, text: str = "") -> None:
    """底部状态栏：显示快捷键提示/页码。"""
    row = screen.rows - 1
    width = screen.columns
    line = (" " + text) if text else " "
    if r.utils.display_width(line) < width:
        line += " " * (width - r.utils.display_width(line))
    screen.set(
        style_line(line, r.Style(fg=theme.status_fg, bg=theme.status_bg)), row=row
    )
