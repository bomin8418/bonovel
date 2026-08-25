"""应用主状态机与主事件循环、全局异常捕获与日志。"""

from __future__ import annotations

import logging
import sys
import time
from typing import List, Optional
from pathlib import Path

from bonovel import config, renderer as r
from bonovel import keys
from bonovel.errors import AppError, ParseError
from bonovel.library import Book, Library
from bonovel.parser import parse_files
from bonovel.themes import Theme, get_theme

logger = logging.getLogger("bonovel")


class App:
    """应用核心：持有配置、书库、主题、视图栈与主循环。"""

    def __init__(self, directory=None, files_to_import: Optional[list] = None):
        self.data_dir = config.data_dir(directory)
        cfg = config.load_config(self.data_dir)
        self.cfg = cfg
        self.library = Library(self.data_dir)
        self.library.scan_data_dir()  # 自动入库数据目录内的 .txt
        self.theme: Theme = get_theme(cfg["theme"])
        self.columns = r.terminal_size().columns
        self.rows = r.terminal_size().rows
        self.toast: str = ""
        self.force_redraw = True
        self._stack: List[object] = []
        self._running = True
        self._view: Optional[object] = None
        self.import_files = list(files_to_import or [])
        self._recent_active_book: Optional[Book] = None

    # ---------- 主题 ----
    def apply_theme(self, name: str) -> None:
        self.theme = get_theme(name)
        self.force_redraw = True

    # ---------- 视图栈 ----
    def push_stack(self, view):
        self._stack.append(self._view)
        self._view = view
        self.force_redraw = True

    def pop_stack(self):
        if self._stack:
            self._view = self._stack.pop()
        elif not isinstance(self._view, self._shelf_type()):
            # 兜底回书架
            self.open_shelf()
        self.force_redraw = True
        return self._view

    def _shelf_type(self):
        from bonovel.ui.shelf_view import ShelfView

        return ShelfView

    def quit(self) -> None:
        self._running = False

    # ---------- 打开书架/书 ----
    def open_shelf(self) -> None:
        from bonovel.ui.shelf_view import ShelfView

        self._stack.clear()
        self._view = ShelfView(self, self.theme, self.columns, self.rows)
        self._view.refresh()
        self.force_redraw = True

    def open_book(self, book: Book) -> None:
        from bonovel.ui.reader import ReaderView

        self._stack.clear()
        try:
            novel = parse_files(book.files)
        except ParseError as exc:
            self.toast = str(exc)
            self.force_redraw = True
            return
        reader = ReaderView(
            self, book.id, self.theme, self.columns, self.rows, novel, self.cfg
        )
        # 恢复进度
        prog = book.progress
        if prog and prog.total_pages > 1:
            reader.app_page = max(0, min(prog.page_index, reader.total_pages - 1))
        book.opened = time.time()
        self.library.save()
        self._recent_active_book = book
        self._view = reader
        self.force_redraw = True

    def enter_import(self) -> None:
        """处理文件导入：直接从命令行文件参数或书库现有导入。"""
        if self.import_files:
            # 启动时传入的文件
            self._import_paths(self.import_files)
            self.import_files = []
        else:
            self.toast = "请通过命令行传入 .txt 文件，或（规划中）文件选择器"
            self.force_redraw = True

    def _import_paths(self, paths: List["str | Path"]) -> None:
        try:
            book = self.library.import_files(paths)
        except (AppError, ParseError) as exc:
            self.toast = f"导入失败：{exc}"
            self.force_redraw = True
            return
        self.toast = f"已导入《{book.title}》"
        if self._recent_active_book is None:
            self.open_book(book)
        else:
            self.force_redraw = True

    # ---------- 主循环 ----
    def run(self) -> int:
        r.ensure_vt_enabled()
        # 日志落盘
        logging.basicConfig(
            filename=str(config.log_path(self.data_dir)),
            level=logging.WARNING,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        if self.columns < 20 or self.rows < 4:
            # 终端过小：非交互提示后安全退出
            r.write_out(
                sys.stdout,
                r.cursor_show()
                + f"\n[bo-novel] 终端尺寸过小（{self.columns}x{self.rows}）。"
                + "请放大终端窗口或调整字号后再试。\n",
            )
            return 2
        self.open_shelf()
        raw = keys.enter_raw()
        parser = keys.KeyParser()
        try:
            out = sys.stdout
            r.write_out(out, r.clear_screen() + r.cursor_goto(1, 1) + r.cursor_hide())
            while self._running:
                self._render(out)
                # 读取一个逻辑键
                byte = raw.read_byte()
                evt = parser.push(byte)
                while evt is None:
                    # 逃逸序列中间态：继续读（带超时保护）
                    byte = raw.read_byte()
                    evt = parser.push(byte)
                    if parser._escape_buf is not None and len(parser._escape_buf) > 8:
                        evt = parser.resolve() or (keys.UNKNOWN, None)
                key, text = evt
                self._dispatch(key, text)
            # 正常退出前保存进度
            self._save_active_progress()
        except KeyboardInterrupt:
            self._save_active_progress()
        except Exception as exc:  # noqa: BLE001
            logger.exception("应用运行发生异常")
            self._fatal(str(exc))
        finally:
            self._restore_terminal()
            r.write_out(out, r.cursor_show() + r.clear_screen())
        return 0

    def _render(self, out) -> None:
        if not self.force_redraw:
            return
        screen = r.Screen(columns=self.columns, rows=self.rows)
        view = self._view
        if view is not None:
            try:
                view.render(screen)
            except Exception:
                logger.exception("渲染界面时异常")
        # toast 显示于首行提示条下（简单覆盖最后状态行）
        if self.toast:
            row = max(self.rows - 1, 1)
            screen.set(r.apply_style("  " + self.toast, r.Style(fg=self.theme.status_bg, bg=self.theme.status_fg)), row=row)
            self.toast = ""
        r.write_out(out, screen.render())
        self.force_redraw = False

    def _dispatch(self, key: str, text: Optional[str]) -> None:
        view = self._view
        if view is None:
            return
        if key == keys.RESIZE:
            self.columns = r.terminal_size().columns
            self.rows = r.terminal_size().rows
            view.resize(self.columns, self.rows)
            self.force_redraw = True
            return
        nav = view.on_key(key, text)
        if nav == "shelf":
            self.open_shelf()
        self.force_redraw = True

    # ---------- 生命周期 ----
    def _save_active_progress(self) -> None:
        from bonovel.ui.reader import ReaderView

        v = self._view
        if isinstance(v, ReaderView) and self.cfg.get("auto_save", True):
            book = self.library.get(v.book_id)
            if book is not None:
                book.progress = v.progress()
                self.library.save()

    def _restore_terminal(self) -> None:
        try:
            keys.leave_raw()
        except Exception:
            pass

    def _fatal(self, message: str) -> None:
        try:
            r.write_out(
                sys.stdout,
                r.cursor_show()
                + "\n[bo-novel] 发生错误，已退出。日志见 "
                + str(config.log_path(self.data_dir)),
            )
        except Exception:
            pass


def run(files_to_import: Optional[list] = None, data_dir: Optional[str] = None) -> int:
    """CLI 入口的实现。"""
    app = App(directory=data_dir, files_to_import=files_to_import)
    return app.run()
