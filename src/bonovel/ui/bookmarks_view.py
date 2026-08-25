"""书签列表界面：查看、跳转、删除书签。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.library import Book
from bonovel.themes import Theme
from bonovel.ui.base import View, draw_footer, draw_header


class BookmarksView(View):
    """在阅读中按 b 打开的书签管理。"""

    def __init__(self, app, return_view: View, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.return_view = return_view
        self.book: Optional[Book] = app.library.get(return_view.book_id)
        self.cursor = 0
        self.offset = 0
        self.bookmarks = list(self.book.bookmarks) if self.book else []

    def render(self, screen: r.Screen) -> None:
        draw_header(
            screen, "书签", self.theme, hint="↑ ↓选择  d 删除  enter 跳转  q 返回"
        )
        avail = self.rows - 2
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + avail:
            self.offset = self.cursor - avail + 1
        base_style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        sel_style = r.Style(fg=self.theme.selection_fg, bg=self.theme.selection_bg)
        if not self.bookmarks:
            screen.set(
                r.apply_style("  暂无书签。按 @ 可在阅读中添加书签。", base_style),
                row=1,
            )
        else:
            row = 1
            for i in range(self.offset, min(self.offset + avail, len(self.bookmarks))):
                bm = self.bookmarks[i]
                label = f"  {i + 1:>2}. 第{bm.page + 1}页"
                if bm.note:
                    label += f"  · {bm.note}"
                if i == self.cursor:
                    screen.set(r.apply_style(label, sel_style), row=row)
                else:
                    screen.set(r.apply_style(label, base_style), row=row)
                row += 1
        draw_footer(screen, self.theme, f"{len(self.bookmarks)} 条书签")

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        if not self.bookmarks:
            if key in ("q", "esc", "ctrl-c"):
                self.app.pop_stack()
            return None
        n = len(self.bookmarks)
        if key == "up":
            self.cursor = (self.cursor - 1) % n
        elif key == "down":
            self.cursor = (self.cursor + 1) % n
        elif key == "d":
            del self.bookmarks[self.cursor]
            self.cursor = min(self.cursor, len(self.bookmarks) - 1)
            self._persist()
        elif key == "enter":
            self.return_view.jump_page(self.bookmarks[self.cursor].page)
            self.app.pop_stack()
        elif key in ("q", "esc", "ctrl-c"):
            self.app.pop_stack()
        return None

    def _persist(self) -> None:
        if self.book is not None:
            self.book.bookmarks = self.bookmarks
            self.app.library.save()
