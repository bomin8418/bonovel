"""阅读排版器：分页与滚动两种模式，结合字号/行距档位。

核心职责：
  * 分页模式：把连续的文本行按“首行缩进 + 段间距 + 终端宽度/可用行数”
    切分为一页页，供 Kinde 式整屏翻页。
  * 滚动模式：维护一个可见行窗口，按 scroll_step 逐行滚动。
文本行的来源是 Novell.line_text() 的行索引，此处只做纯排版计算，
不直接持有文件字节。
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from bonovel import utils

# 中文小说首行缩进
INDENT = "\u3000\u3000"  # 两个全角空格

# 字号档位影响：可用行数密度（等效行高）
_FONT_SIZE_ROWS = {0: float("inf"), 1: 1.0, 2: 1.4}
# 行距档位影响：行距 + 段间距
_LINE_SPACING = {0: 0.0, 1: 1.0, 2: 2.0}
# 段间距基元（空行数）
PARAGRAPH_GAP = 1


@lru_cache(maxsize=8192)
def _char_width(ch: str) -> int:
    """字符显示宽度（缓存结果，避免逐字符 unicodedata 开销）。"""
    return 2 if utils.display_width(ch) > 1 else 1


class Page:
    """一页的内容：起始/结束逻辑行与可渲染行列表。"""

    __slots__ = ("start_line", "end_line", "rows", "page_no", "total_pages")

    def __init__(
        self,
        start_line: int,
        end_line: int,
        rows: List[str],
        page_no: int = 0,
        total_pages: int = 1,
    ):
        self.start_line = start_line
        self.end_line = end_line
        self.rows = rows
        self.page_no = page_no
        self.total_pages = total_pages

    def __repr__(self) -> str:  # pragma: no cover - 仅调试
        return (
            f"Page(start={self.start_line}, end={self.end_line}, "
            f"rows={len(self.rows)}, no={self.page_no}/{self.total_pages})"
        )


def _usable_width(columns: int) -> int:
    """去除左右留白后可用于正文的宽度。"""
    margin = 2
    return max(columns - margin * 2, 20)


def _lines_per_screen(rows: int, font_size: int, line_spacing: int) -> int:
    """估算可用作正文的行数：扣除头部 + 页脚 + 行距消耗。

    返回整屏大致可容纳的普通正文行数（分页时逐行校验）。
    """
    header_rows = 1
    footer_rows = 1
    available = rows - header_rows - footer_rows - 1  # 保守留一行余量
    if font_size not in _FONT_SIZE_ROWS:
        font_size = 1
    eff = available if _FONT_SIZE_ROWS[font_size] == float("inf") else available
    if font_size == 2:
        eff = int(available * 0.7)  # 大字号仅显示约七成行
    elif font_size == 0:
        eff = available + 2
    gap = _LINE_SPACING.get(line_spacing, 1.0)
    return max(eff - int(gap), 4)


class NovelLayouter:
    """基于行索引的分页器（Kindle 式翻页）。

    把逻辑行列表逐行包装成页，每页高度 <= 可用行数，遇到段落跳转、
    标题等自动分段。
    """

    def __init__(
        self,
        total_lines: int,
        lines_func,
        columns: int = 80,
        rows: int = 24,
        font_size: int = 1,
        line_spacing: int = 1,
        indent: bool = True,
    ):
        self.lines_func = lines_func
        self.width = _usable_width(columns)
        self.rows = rows
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.indent = indent
        self.total_lines = total_lines
        # 折行结果缓存：以所用宽度为键；宽度不变时 reflow 只重排不复折
        self._rows: List[List[str]] = []
        self._rows_width: int = -1
        self._pages: List[Page] = []
        self._build_pages()

    def _count_lines(self) -> int:
        return self.total_lines

    def _wrap(self, text: str, width: int) -> List[str]:
        """将单段文本按终端宽度折行；中文按字符，宽度统计考虑全角。"""
        if width <= 0:
            return [text]
        lines: List[str] = []
        cur: List[str] = []
        cur_w = 0
        for ch in text:
            w = 1 if ch.isascii() else _char_width(ch)
            if cur_w + w > width:
                lines.append("".join(cur))
                cur = [ch]
                cur_w = w
            else:
                cur.append(ch)
                cur_w += w
        if cur:
            lines.append("".join(cur))
        if not lines:
            lines = [""]
        return lines

    def _wrap_line(self, i: int) -> List[str]:
        """第 i 行的折行结果（不含缩进前缀）；空行返回空列表。"""
        text = self.lines_func_line(i).strip()
        if not text:
            return []
        if self.indent:
            return self._wrap(text, self.width - len(INDENT))
        return self._wrap(text, self.width)

    def reflow(
        self,
        columns: int,
        rows: int,
        font_size: int,
        line_spacing: int,
    ) -> None:
        """按新参数重排；参数未变直接返回，宽度未变时复用折行缓存。"""
        new_width = _usable_width(columns)
        if (
            new_width == self.width
            and rows == self.rows
            and font_size == self.font_size
            and line_spacing == self.line_spacing
        ):
            return
        if new_width != self.width:
            self.width = new_width
            self._rows = []
            self._rows_width = -1
        self.rows = rows
        self.font_size = font_size
        self.line_spacing = line_spacing
        self._build_pages()

    def _build_pages(self) -> None:
        """按行索引把连续文本切成多页（折行结果按宽度缓存复用）。"""
        if not self._rows or self._rows_width != self.width:
            self._rows = [self._wrap_line(i) for i in range(self.total_lines)]
            self._rows_width = self.width
        rows_cache = self._rows
        max_rows = _lines_per_screen(self.rows, self.font_size, self.line_spacing)
        pages: List[Page] = []
        current_rows: List[str] = []
        current_line_start = 0
        total = self.total_lines
        first_row_of_page = True

        line_index = 0
        while line_index < total:
            wrapped = rows_cache[line_index]
            count = len(wrapped) if wrapped else 1  # 空行占一行
            if current_rows and len(current_rows) + count > max_rows:
                pages.append(
                    self._make_page(current_line_start, line_index - 1, current_rows)
                )
                current_line_start = line_index
                current_rows = []
                first_row_of_page = True
            if wrapped:
                # 每页第一行不缩进（章节起始/正文开头）
                prefix = INDENT if (self.indent and not first_row_of_page) else ""
                current_rows.extend(prefix + w for w in wrapped)
            else:
                # 空行表示段落分隔：仅当已在本页有内容时追加
                if current_rows:
                    current_rows.append("")
            first_row_of_page = False
            line_index += 1

        if current_rows:
            pages.append(self._make_page(current_line_start, total - 1, current_rows))

        self._pages = pages if pages else [Page(0, 0, [])]

    def lines_func_line(self, i: int) -> str:
        """从行索引取第 i 行文本。"""
        return self.lines_func(i)

    def _make_page(self, start: int, end: int, rows: List[str]) -> Page:
        return Page(start_line=start, end_line=end, rows=rows)

    def page_count(self) -> int:
        return len(self._pages)

    def page_at(self, index: int) -> Page:
        if index < 0:
            index = 0
        if index >= len(self._pages):
            index = len(self._pages) - 1
        return self._pages[index]


class ScrollWindow:
    """滚动模式：维护可见行窗口（对行索引的视图，不缓存大文本）。"""

    def __init__(self, total_lines: int, step: int = 3):
        self.total_lines = total_lines
        self.step = max(step, 1)
        self.top = 0

    def scroll_down(self) -> int:
        old = self.top
        self.top = min(self.top + self.step, max(self.total_lines - 1, 0))
        return self.top - old

    def scroll_up(self) -> int:
        old = self.top
        self.top = max(self.top - self.step, 0)
        return self.top - old

    def page_down(self, height: int) -> None:
        self.top = min(self.top + height, max(self.total_lines - 1, 0))

    def page_up(self, height: int) -> None:
        self.top = max(self.top - height, 0)

    def go_to_line(self, line: int, height: int) -> None:
        self.top = max(0, min(line, max(self.total_lines - 1, 0)))


def visible_lines(window: ScrollWindow, count: int) -> List[int]:
    """滚动窗口可见的逻辑行号列表。"""
    return list(range(window.top, min(window.top + count, window.total_lines)))
