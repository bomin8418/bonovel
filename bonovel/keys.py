"""跨平台键盘输入层：把原始字节/键码归一化为逻辑按键事件。

Windows 使用 msvcrt，Unix 使用 termios/tty。均为 Python 标准库。
逻辑键解析（KeyParser）是纯函数式的字节状态机，可脱离终端单测。
"""

from __future__ import annotations

import sys
from typing import Optional, Tuple

# 逻辑按键常量
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
ENTER = "enter"
BACKSPACE = "backspace"
TAB = "tab"
ESC = "escape"
PAGE_UP = "pageup"
PAGE_DOWN = "pagedown"
HOME = "home"
END = "end"
DELETE = "delete"
CTRL_LEFT = "ctrl-left"
CTRL_RIGHT = "ctrl-right"
CTRL_UP = "ctrl-up"
CTRL_DOWN = "ctrl-down"
RESIZE = "resize"
CTRL_C = "ctrl-c"
CTRL_Z = "ctrl-z"
UNKNOWN = "unknown"

CHARS_ENTER = ("\r", "\n")
CHARS_BACKSPACE = ("\x08", "\x7f")
CHARS_TAB = ("\t",)

# 逃逸序列映射：形态 ESC [ 序号 最终符，或 ESC O 最终符
_ESCAPE_SEQUENCES = {
    # 经典 ANSI
    "[A": UP, "[B": DOWN, "[C": RIGHT, "[D": LEFT,
    "[H": HOME, "[F": END,
    "[1~": HOME, "[4~": END, "[3~": DELETE,
    "[5~": PAGE_UP, "[6~": PAGE_DOWN,
    # Ctrl + 方向键（CSI 参数）
    "[1;5A": CTRL_UP, "[1;5B": CTRL_DOWN,
    "[1;5C": CTRL_RIGHT, "[1;5D": CTRL_LEFT,
    # 应用光标键模式（ESC O ...）
    "OA": UP, "OB": DOWN, "OC": RIGHT, "OD": LEFT,
    "OH": HOME, "OF": END,
}

# 判定 CSI 控制序列：ESC [ 参数 ; 参数 最终字母
_CSI_FINAL = "ABCDHF"


def is_windows() -> bool:
    return sys.platform.startswith("win")


class KeyParser:
    """字节流状态机：把普通键与 ESQ 序列归一化为逻辑键。

    用法：对每个读到的字节调用 push(byte)。当累积到可判定的完整逻辑键时
    返回 (logic_key, text)；若处于逃逸序列中间态且尚不完整则返回 None
    （调用方需继续喂字节），此时可用 resolve() 强制结算（如遇超时）。
    """

    def __init__(self):
        self._escape_buf: Optional[str] = None
        self._escape_mode = False  # 当前字节是否处于逃逸序列中

    def _start_esc(self):
        self._escape_buf = ""

    def _finish_escape(self) -> Tuple[str, Optional[str]]:
        buf = self._escape_buf or ""
        self._escape_buf = None
        if not buf:
            return (ESC, None)
        key = self._lookup(buf)
        return (key, None)

    def _lookup(self, buf: str) -> str:
        if buf in _ESCAPE_SEQUENCES:
            return _ESCAPE_SEQUENCES[buf]
        return UNKNOWN

    def push(self, byte: int) -> Optional[Tuple[str, Optional[str]]]:
        ch = chr(byte & 0xFF)

        # ---- 处于逃逸序列中 ----
        if self._escape_buf is not None:
            self._escape_buf += ch
            buf = self._escape_buf
            # CSI 形：ESC [ ... 终符（字典键含前导 '['，如 "[A"）
            if buf.startswith("["):
                if buf in _ESCAPE_SEQUENCES:
                    return self._finish_escape()
                # 数字参数可能未结束；若以终符字母结尾则尝试结算
                if len(buf) > 1 and buf[-1] in _CSI_FINAL:
                    if buf in _ESCAPE_SEQUENCES:
                        return self._finish_escape()
                    self._escape_buf = None
                    return (UNKNOWN, None)
                return None  # 还需更多字节
            if buf.startswith("O"):
                if buf in _ESCAPE_SEQUENCES:
                    return self._finish_escape()
                if len(buf) == 2:
                    return None
                self._escape_buf = None
                return (UNKNOWN, None)
            # 裸 ESC 后接了非预期字符
            self._escape_buf = None
            return (UNKNOWN, None)

        # ---- 普通键 ----
        if ch == "\x1b":
            self._escape_buf = ""
            return None  # 开始累积逃逸序列
        if ch in CHARS_ENTER:
            return (ENTER, "\n")
        if ch in CHARS_BACKSPACE:
            return (BACKSPACE, None)
        if ch in CHARS_TAB:
            return (TAB, "\t")
        if ch == "\x03":
            return (CTRL_C, None)
        if ch == "\x1a":
            return (CTRL_Z, None)
        if byte == 0:
            return (RESIZE, None)
        if "\x01" <= ch <= "\x1a":
            letter = chr(ord("A") + ord(ch) - ord("\x01"))
            return ("ctrl-" + letter.lower(), None)
        if 0x20 <= byte <= 0x7E:
            return (chr(byte), chr(byte))  # 可打印 ASCII
        if byte >= 0x80:
            return (ch, ch)  # 宽字符（中文文本）
        return (UNKNOWN, None)

    def resolve(self) -> Optional[Tuple[str, Optional[str]]]:
        """结算未完成的逃逸序列（如超时、无更多字节）。"""
        if self._escape_buf is not None:
            self._escape_buf = None
            return (ESC, None)
        return None


def iter_keys(parser: KeyParser, bytes_iter) -> "list[Tuple[str, str]]":
    """把一串字节喂入解析器，返回所有已可判定的逻辑键（不含中间态）。

    主要用于测试与批量消费输入。
    """
    keys: list = []
    for b in bytes_iter:
        evt = parser.push(b)
        if evt is not None and evt[0] != UNKNOWN:
            keys.append(evt)
    return keys


def reads_keys(parser: KeyParser, byte_sequence) -> "list[Tuple[str, str]]":
    """便捷测试助手：给定字节序列返回逻辑键列表。"""
    keys: list = []
    for b in byte_sequence:
        evt = parser.push(b)
        if evt is not None:
            keys.append(evt)
    return keys


def str_to_bytes(s: str) -> "list[int]":
    """测试助手：把含常规字符与 \\x1b 标记的序列转为字节列表。"""
    return [ord(c) for c in s]


class RawInput:
    """底层阻塞读取一个原始字节；由平台专用实现子类化。"""

    def read_byte(self) -> int:
        raise NotImplementedError


def _make_raw_input() -> RawInput:
    if is_windows():
        import msvcrt

        class _WinInput(RawInput):
            def __init__(self):
                self._msvcrt = msvcrt

            def read_byte(self) -> int:
                # 读宽字符；若为代理对，追加读下半部分
                ch = self._msvcrt.getwch()
                code = ord(ch)
                if 0xD800 <= code <= 0xDBFF:  # 高代理
                    lo = ord(self._msvcrt.getwch())
                    return code  # 简化：仅传高代理，键层按宽字符处理
                return code

            def kbhit(self) -> bool:
                try:
                    return bool(self._msvcrt.kbhit())
                except Exception:  # pragma: no cover
                    return False

        return _WinInput()
    else:  # pragma: no cover - Unix 路径由测试环境模拟
        import os
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()

        class _UnixInput(RawInput):
            def __enter__(self):
                self._old = termios.tcgetattr(fd)
                tty.setraw(fd)
                return self

            def __exit__(self, *exc):
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old)
                return False

            def read_byte(self) -> int:
                return os.read(fd, 1)[0]

            def kbhit(self) -> bool:
                try:
                    return bool(select.select([fd], [], [], 0)[0])
                except Exception:
                    return False

        ctx = _UnixInput()
        ctx.__enter__()
        return ctx


_ACTIVE_CTX: Optional[RawInput] = None


def enter_raw() -> RawInput:
    """进入原始模式并返回输入实例。"""
    global _ACTIVE_CTX
    if _ACTIVE_CTX is None:
        _ACTIVE_CTX = _make_raw_input()
    return _ACTIVE_CTX


def leave_raw() -> None:  # pragma: no cover
    global _ACTIVE_CTX
    _ACTIVE_CTX = None
