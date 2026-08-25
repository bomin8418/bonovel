"""阅读界面：分页/滚动切换、翻页、章节跳转、书签、进度记忆、速度统计。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.errors import UserCancelled
from bonovel.layout import NovelLayouter, ScrollWindow, visible_lines
from bonovel.parser import Novel, chapter_index_of
from bonovel.stats import ProgressMemory, ReadingStats
from bonovel.themes import Theme
from bonovel.ui.base import View, draw_footer, draw_header

# 页脚信息开关（由 config 控制，这里读取）
_PAGE_KBD_HINT = "← →翻页 ↑↓滚动  P模式切换  章:目录  @书签  C设置  ?帮助  q退回"


class ReaderView(View):
    """阅读一部长篇小说的界面。"""

    def __init__(
        self,
        app,
        book_id: str,
        theme: Theme,
        columns: int,
        rows: int,
        novel: Novel,
        config_dict: dict,
    ):
        super().__init__(app, theme, columns, rows)
        self.book_id = book_id
        self.novel = novel
        self.cfg = config_dict
        self.mode = self.cfg.get("reading_mode", "page")
        self.stats = ReadingStats()
        self._app_page = 0
        self._reflow()

    # ---------- 布局 ----
    def _reflow(self) -> None:
        usable_rows = self.rows - 2  # 顶部 1 + 底部 1
        self.layouter = NovelLayouter(
            self.novel.line_count,
            self.novel.line_text,
            columns=self.columns,
            rows=self.rows,
            font_size=self.cfg.get("font_size", 1),
            line_spacing=self.cfg.get("line_spacing", 1),
            indent=True,
        )
        self.total_pages = max(self.layouter.page_count(), 1)
        self._app_page = max(0, min(self._app_page, self.total_pages - 1))
        self.scroll = ScrollWindow(self.novel.line_count, self.cfg.get("scroll_step", 3))

    def resize(self, columns: int, rows: int) -> None:
        self.columns = columns
        self.rows = rows
        self._reflow()

    # ---------- 页导航 ----
    def next_page(self) -> None:
        if self.page_index < self.total_pages - 1:
            self.app_page = self.page_index + 1
            self.stats.record_page(self._page_chars())
        else:
            self.stats.leave()

    def prev_page(self) -> None:
        if self.page_index > 0:
            self.app_page = self.page_index - 1
            self.stats.record_page(self._page_chars())

    def goto_chapter(self, index: int) -> None:
        chapters = self.novel.chapters
        if not chapters:
            return
        index = max(0, min(index, len(chapters) - 1))
        line = chapters[index].start_line
        # 转换为最近的页
        self._goto_starting_from(line)

    def _goto_starting_from(self, line: int) -> None:
        # 从某行开始重新分页，找到含该行的页
        self.app_page = 0
        for i in range(self.total_pages):
            p = self.layouter.page_at(i)
            if p.start_line <= line <= p.end_line:
                self.app_page = i
                break
        self.stats.record_page(self._page_chars())

    def jump_page(self, index: int) -> None:
        self.app_page = max(0, min(index, self.total_pages - 1))
        self.stats.record_page(self._page_chars())

    def _page_chars(self) -> int:
        p = self.layouter.page_at(self.page_index)
        return sum(len(row) for row in p.rows)

    # ---------- 滚动 ----
    def scroll_by(self, delta: int) -> None:
        old = self.scroll.top
        if delta < 0:
            self.scroll.scroll_up()
        else:
            self.scroll.scroll_down()
        if self.scroll.top != old:
            self.stats.record_page(self._page_chars())

    # ---------- app 状态交互 ----
    @property
    def app_page(self) -> int:
        return self._app_page

    @app_page.setter
    def app_page(self, value: int) -> None:
        self._app_page = value

    @property
    def page_index(self) -> int:
        """当前页索引——以 _app_page 为唯一来源。"""
        return self._app_page

    def progress(self) -> ProgressMemory:
        return ProgressMemory(
            page_index=self.page_index, total_pages=self.total_pages, line=0
        )

    # ---------- 渲染 ----
    def render(self, screen: r.Screen) -> None:
        theme = self.theme
        draw_header(
            screen,
            self.novel.title,
            theme,
            hint=f"{self.mode} 模式",
        )
        content_top = 1
        content_avail = self.rows - 2
        if self.mode == "page":
            self._render_page(screen, content_top, content_avail)
        else:
            self._render_scroll(screen, content_top, content_avail)
        self._render_footer(screen)

    def _render_page(self, screen: r.Screen, top: int, avail: int) -> None:
        p = self.layouter.page_at(self.page_index)
        chapter = self._current_chapter_title()
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        row = top
        if chapter:
            screen.set(
                r.apply_style(f"  {chapter}", r.Style(fg=self.theme.accent_fg)),
                row=top,
            )
            row += 1
        for text_row in p.rows[: max(avail - 1, 0)]:
            screen.set(r.apply_style(text_row, style), row=row)
            row += 1

    def _render_scroll(self, screen: r.Screen, top: int, avail: int) -> None:
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        row = top
        for lineno in visible_lines(self.scroll, avail):
            if lineno >= self.novel.line_count:
                break
            text = self.novel.line_text(lineno)
            if not text.strip():
                screen.set("", row=row)
                row += 1
                continue
            screen.set(r.apply_style("\u3000\u3000" + text, style), row=row)
            row += 1
            if row >= top + avail:
                break

    def _render_footer(self, screen: r.Screen) -> None:
        cfg = self.cfg
        if self.mode == "page":
            percent = int(self.page_index / max(self.total_pages - 1, 1) * 100)
            wpm = self.stats.current_wpm
            text = f"第 {self.page_index + 1}/{self.total_pages} 页（{percent}%）  WPM≈{wpm:.0f}"
        else:
            text = f"行 {self.scroll.top + 1}/{max(self.novel.line_count,1)}"
        draw_footer(screen, self.theme, text)

    def _current_chapter_title(self) -> str:
        if self.mode != "page":
            return ""
        line = self.layouter.page_at(self.page_index).start_line
        idx = chapter_index_of(self.novel, line)
        if 0 <= idx < len(self.novel.chapters):
            return self.novel.chapters[idx].title
        return ""

    # ---------- 键盘 ----
    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        if key in ("down", "right", " ", "pagedown"):
            if self.mode == "page":
                self.next_page()
            else:
                self.scroll_by(1)
            return None
        if key in ("up", "left", "pageup"):
            if self.mode == "page":
                self.prev_page()
            else:
                self.scroll_by(-1)
            return None
        if key == "home":
            self.jump_page(0)
            return None
        if key == "end":
            self.jump_page(self.total_pages - 1)
            return None
        if key == "p":
            self.mode = "page" if self.mode == "scroll" else "scroll"
            self.app.force_redraw = True
            return None
        if key == "g":
            from bonovel.ui.chapters_view import ChaptersView

            self.app.push_stack(
                ChaptersView(self.app, self, self.theme, self.columns, self.rows)
            )
            return None
        if key == "b":
            from bonovel.ui.bookmarks_view import BookmarksView

            self.app.push_stack(
                BookmarksView(self.app, self, self.theme, self.columns, self.rows)
            )
            return None
        if key == "@":
            self._add_bookmark()
            return None
        if key == "c":
            from bonovel.ui.settings_view import SettingsView

            self.app.push_stack(
                SettingsView(self.app, self.theme, self.columns, self.rows)
            )
            return None
        if key == "?":
            from bonovel.ui.settings_view import HelpView

            self.app.push_stack(
                HelpView(self.app, self.theme, self.columns, self.rows)
            )
            return None
        if key in ("q", "ctrl-c"):
            return "shelf"
        return None

    def _add_bookmark(self) -> None:
        book = self.app.library.get(self.book_id)
        if book is None:
            return
        from bonovel.library import Bookmark

        book.bookmarks.append(Bookmark(page=self.page_index))
        self.app.library.save()
        self.app.toast = f"已添加书签 @第{self.page_index + 1}页"
