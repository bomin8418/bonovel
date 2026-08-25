"""ANSI 转义序列渲染基元与终端能力封装（纯标准库）。

Windows 10+ 的 conhost/Windows Terminal 默认支持 VT 序列，脚本启动时
通过 ctypes 调用 EnableVirtualTerminalProcessing 开启 STDOUT/STDERR 的
VT 处理（在 config 初始化阶段调用 ensure_vt_enabled）。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, TextIO

from bonovel import utils

ANSICOL = "\x1b["
_RESET = ANSICOL + "0m"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def ensure_vt_enabled() -> bool:
    """确保当前控制台支持 ANSI/VT 序列（Windows 专用，其余平台直接放行）。"""
    if not is_windows():
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        for handle_id in (-11, -12):  # STD_OUTPUT_HANDLE / STD_ERROR_HANDLE
            handle = kernel32.GetStdHandle(wintypes.DWORD(handle_id))
            if handle == wintypes.HANDLE(-1).value or handle is None:
                continue
            mode = wintypes.DWORD()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                continue
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return True
    except (ImportError, OSError, AttributeError):  # pragma: no cover
        return False


@dataclass
class TermSize:
    """终端宽高（列、行）。"""

    columns: int = 80
    rows: int = 24


def terminal_size(stream: Optional[TextIO] = None) -> TermSize:
    """获取当前终端尺寸；不可用时返回保守默认并尽可能优雅降级。"""
    stream = stream or sys.stdout
    try:
        size = os.get_terminal_size(stream.fileno())
        return TermSize(columns=size.columns, rows=size.lines)
    except (OSError, ValueError, AttributeError):
        cols = os.environ.get("COLUMNS")
        rows = os.environ.get("LINES")
        return TermSize(
            columns=int(cols) if cols and cols.isdigit() else 80,
            rows=int(rows) if rows and rows.isdigit() else 24,
        )


def _sgr(attrs: List[str]) -> str:
    return f"{ANSICOL}{';'.join(attrs)}m"


def sgr_reset() -> str:
    return _RESET


def sgr_fg(rgb: "tuple[int, int, int]") -> str:
    r, g, b = rgb
    return f"{ANSICOL}38;2;{r};{g};{b}m"


def sgr_bg(rgb: "tuple[int, int, int]") -> str:
    r, g, b = rgb
    return f"{ANSICOL}48;2;{r};{g};{b}m"


def sgr_bold() -> str:
    return _sgr(["1"])


def sgr_dim() -> str:
    return _sgr(["2"])


def cursor_goto(row: int, col: int) -> str:
    """1 基坐标定位光标。"""
    return f"{ANSICOL}{row};{col}H"


def cursor_save() -> str:
    return f"{ANSICOL}s"


def cursor_restore() -> str:
    return f"{ANSICOL}u"


def cursor_hide() -> str:
    return f"{ANSICOL}?25l"


def cursor_show() -> str:
    return f"{ANSICOL}?25h"


def clear_screen() -> str:
    return ANSICOL + "2J"


def clear_line() -> str:
    return ANSICOL + "2K"


def erase_lines_above() -> str:
    return ANSICOL + "K" * 1  # 占位：实际需配合光标定位


@dataclass
class Style:
    """一段文本的样式描述（前景/背景/加粗/暗淡），用于排版层组合。"""

    fg: "Optional[tuple[int, int, int]]" = None
    bg: "Optional[tuple[int, int, int]]" = None
    bold: bool = False
    dim: bool = False


def apply_style(text: str, style: "Style") -> str:
    """给文本包裹 SGR 前缀与重置后缀。无样式则原样返回。"""
    if not style or (not style.fg and not style.bg and not style.bold and not style.dim):
        return text
    attrs: List[str] = []
    if style.fg:
        attrs.append(f"38;2;{style.fg[0]};{style.fg[1]};{style.fg[2]}")
    if style.bg:
        attrs.append(f"48;2;{style.bg[0]};{style.bg[1]};{style.bg[2]}")
    if style.bold:
        attrs.append("1")
    if style.dim:
        attrs.append("2")
    return f"{ANSICOL}{';'.join(attrs)}m{text}{_RESET}"


class Screen:
    """整屏离屏缓冲 + 一次性刷新的简易渲染控制器。

    用法：draw 阶段将各行（含样式）写入 buffer，最后 flush() 定位到缓冲区
    顶部整块写出，避免逐行滚动造成闪烁。
    """

    def __init__(self, columns: int = 80, rows: int = 24):
        self.columns = columns
        self.rows = rows
        self._lines: List[str] = []
        self._dirty = False

    def set(self, line: str, row: int = 0) -> None:
        """写入第 row 行（0 基、相对缓冲顶部）的内容（可含样式码）。"""
        while len(self._lines) <= row:
            self._lines.append("")
        self._lines[row] = line
        self._dirty = True

    def clear(self) -> None:
        self._lines = []
        self._dirty = True

    def render(self) -> str:
        """把缓冲区渲染为 ANSI 输出串（从已知坐标开始整块覆盖）。"""
        if not self._dirty:
            return ""
        out = [cursor_hide(), cursor_goto(1, 1)]
        for i in range(self.rows):
            line = self._lines[i] if i < len(self._lines) else ""
            width = _plain_width(line)
            if width < self.columns:
                line += " " * (self.columns - width)
            out.append(line)
            out.append(ANSICOL + "0m")
            if i < self.rows - 1:
                out.append("\r\n")
        out.append(cursor_show())
        self._dirty = False
        return "".join(out)


def _plain_width(line: str) -> int:
    """计算剥离 ANSI 序列后的显示宽度（考虑全角字符占 2 列）。"""
    import re

    plain = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", line)
    return utils.display_width(plain)


def write_out(stream: Optional[TextIO], text: str) -> None:
    (stream or sys.stdout).write(text)
    try:
        (stream or sys.stdout).flush()
    except (ValueError, OSError):
        pass
