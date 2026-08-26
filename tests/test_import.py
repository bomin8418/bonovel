"""导入流程单元测试：启动自动导入与路径输入框导入。"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from bonovel.app import App
from bonovel.themes import get_theme
from bonovel.ui.import_view import ImportView
from bonovel.ui.reader import ReaderView
from bonovel.ui.shelf_view import ShelfView


class ImportFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data_dir = Path(self.tmp) / "data"
        self.data_dir.mkdir()
        self.book = Path(self.tmp) / "小说.txt"
        self.book.write_text(
            "书名\n\n第一章 初见\n这是正文。\n第二章 重逢\n正文继续。\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_startup_cli_files_auto_import(self):
        app = App(directory=str(self.data_dir), files_to_import=[str(self.book)])
        self.assertEqual(app.import_files, [str(self.book)])
        app.enter_import()
        self.assertIsInstance(app._view, ReaderView)
        self.assertEqual(len(app.library.all()), 1)
        self.assertEqual(app.import_files, [])

    def test_import_view_typed_path_imports_and_opens(self):
        app = App(directory=str(self.data_dir))
        view = ImportView(app, get_theme("plain"), 80, 24)
        for ch in str(self.book):
            view.on_key(ch, ch)
        view.on_key("enter", "\n")
        # 未打开过书 → 自动进入阅读
        self.assertIsInstance(app._view, ReaderView)
        self.assertEqual(len(app.library.all()), 1)

    def test_import_view_backspace_edits(self):
        app = App(directory=str(self.data_dir))
        view = ImportView(app, get_theme("plain"), 80, 24)
        for ch in "abc":
            view.on_key(ch, ch)
        view.on_key("backspace", None)
        self.assertEqual(view.path, "ab")

    def test_import_view_empty_path_error(self):
        app = App(directory=str(self.data_dir))
        view = ImportView(app, get_theme("plain"), 80, 24)
        view.on_key("enter", "\n")
        self.assertEqual(view.error, "路径为空，请输入 .txt 文件路径")
        self.assertEqual(len(app.library.all()), 0)

    def test_import_view_nonexistent_path_fails(self):
        app = App(directory=str(self.data_dir))
        view = ImportView(app, get_theme("plain"), 80, 24)
        for ch in str(self.data_dir / "nope.txt"):
            view.on_key(ch, ch)
        view.on_key("enter", "\n")
        self.assertEqual(len(app.library.all()), 0)
        self.assertIn("导入失败", app.toast)
        # 回退到书架
        self.assertIsInstance(app._view, ShelfView)

    def test_import_view_esc_cancels(self):
        app = App(directory=str(self.data_dir))
        view = ImportView(app, get_theme("plain"), 80, 24)
        for ch in "abc":
            view.on_key(ch, ch)
        view.on_key("esc", None)
        self.assertIsInstance(app._view, ShelfView)


if __name__ == "__main__":
    unittest.main()
