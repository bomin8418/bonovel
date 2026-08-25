"""章节目录界面：列出章节并可跳转。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.themes import Theme
from bonovel.ui.base import View, draw_footer, draw_header


class ChaptersView(View):
    """在阅读中按 g 打开的章节目录。"""

    def __init__(self, app, return_view: View, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.return_view = return_view
        self.chapters = return_view.novel.chapters
        self.cursor = 0
        self.offset = 0

    def render(self, screen: r.Screen) -> None:
        draw_header(screen, "章节目录", self.theme, hint="↑ ↓选择  enter 跳转  q 返回")
        avail = self.rows - 2
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + avail:
            self.offset = self.cursor - avail + 1
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        sel_style = r.Style(fg=self.theme.selection_fg, bg=self.theme.selection_bg)
        row = 1
        for i in range(self.offset, min(self.offset + avail, len(self.chapters))):
            ch = self.chapters[i]
            label = f"  {i + 1:>3}. {ch.title}"
            if i == self.cursor:
                screen.set(r.apply_style(label, sel_style), row=row)
            else:
                screen.set(r.apply_style(label, style), row=row)
            row += 1
        draw_footer(screen, self.theme, f"{self.cursor + 1}/{len(self.chapters)} 章")

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        total = len(self.chapters)
        if key == "up":
            self.cursor = (self.cursor - 1) % total
        elif key == "down":
            self.cursor = (self.cursor + 1) % total
        elif key == "pageup":
            self.cursor = max(0, self.cursor - 10)
        elif key == "pagedown":
            self.cursor = min(total - 1, self.cursor + 10)
        elif key == "enter":
            self.return_view.goto_chapter(self.cursor)
            self.app.pop_stack()
            return None
        elif key in ("q", "esc", "ctrl-c"):
            self.app.pop_stack()
            return None
        return None
