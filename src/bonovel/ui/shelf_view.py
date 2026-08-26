"""书架界面：导入、选择、删除小说与最近阅读。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.library import Book
from bonovel.themes import Theme
from bonovel.ui.base import View, draw_footer, draw_header


class ShelfView(View):
    """首页书架：列出已入库书目，支持导入/选择/删除。"""

    def __init__(self, app, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.books: list = []
        self.cursor = 0
        self.offset = 0
        self.import_path: Optional[str] = None
        self.message = ""

    def refresh(self) -> None:
        self.books = self.app.library.all()
        self.cursor = min(self.cursor, max(len(self.books) - 1, 0))
        self.offset = min(self.offset, max(len(self.books) - 1, 0))

    def render(self, screen: r.Screen) -> None:
        draw_header(
            screen,
            "bonovel",
            self.theme,
            hint="usage: i=import  enter=open  d=delete  ?=help  q=quit",
        )
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        sel_style = r.Style(fg=self.theme.selection_fg, bg=self.theme.selection_bg)
        dim_style = r.Style(fg=self.theme.dim_fg, bg=self.theme.background)
        avail = self.rows - 3  # 头 + 列表 + 尾
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + avail:
            self.offset = self.cursor - avail + 1

        row = 1
        if not self.books:
            screen.set(
                r.apply_style(
                    "  no books imported — run: python -m bonovel <file.txt>", style
                ),
                row=1,
            )
        else:
            for i in range(self.offset, min(self.offset + avail, len(self.books))):
                b = self.books[i]
                percent = int(b.progress.percent()) if b.progress else 0
                label = f"  {b.title}"
                label = r.utils.pad_to(label, min(40, self.columns - 20))
                label += f"  [{percent}%]"
                if i == self.cursor:
                    screen.set(r.apply_style(label, sel_style), row=row)
                else:
                    screen.set(r.apply_style(label, style), row=row)
                row += 1

        # 底部提示/最近
        if self.message:
            draw_footer(screen, self.theme, self.message)
        else:
            draw_footer(
                screen,
                self.theme,
                f"{len(self.books)} book(s) · BONOVEL_DATA_DIR={self.app.data_dir}",
            )
        self.message = ""

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        if key == "i":
            from bonovel.ui.import_view import ImportView

            self.app.push_stack(
                ImportView(self.app, self.theme, self.columns, self.rows)
            )
            return None
        if key in ("q", "ctrl-c"):
            self.app.quit()
            return None
        if key == "?":
            self.app.push_stack(FromHelp(self.app, self.theme, self.columns, self.rows))
            return None
        if not self.books:
            return None
        n = len(self.books)
        if key == "up":
            self.cursor = (self.cursor - 1) % n
        elif key == "down":
            self.cursor = (self.cursor + 1) % n
        elif key == "d":
            book = self.books[self.cursor]
            self.app.library.remove(book.id)
            self.refresh()
            self.message = f"已从书架移除《{book.title}》"
        elif key == "enter":
            book = self.books[self.cursor]
            self.app.open_book(book)
            return None
        return None


class FromHelp(View):
    """借用帮助视图的快捷跳转。"""

    def __init__(self, app, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        from bonovel.ui.settings_view import HelpView

        self._inner = HelpView(app, theme, columns, rows)

    def render(self, screen: r.Screen) -> None:
        self._inner.render(screen)

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        self._inner.on_key(key, text)
        if key in ("q", "esc", "ctrl-c"):
            self.app.pop_stack()
        return None
