"""核心功能测试：stats 阅读速度、进度记忆、书库导入与配置联动。"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from bonovel import config
from bonovel.library import Library
from bonovel.stats import ProgressMemory, ReadingStats
from bonovel.themes import theme_names


class ReadingStatsTestCase(unittest.TestCase):
    def test_progress_percent_bounds(self):
        p = ProgressMemory(page_index=0, total_pages=1)
        self.assertEqual(p.percent(), 0.0)
        p2 = ProgressMemory(page_index=5, total_pages=11)
        self.assertAlmostEqual(p2.percent(), 50.0)

    def test_progress_roundtrip(self):
        p = ProgressMemory(page_index=3, total_pages=10, line=7)
        clone = ProgressMemory.from_dict(p.to_dict())
        self.assertEqual(clone.page_index, 3)
        self.assertEqual(clone.total_pages, 10)
        self.assertEqual(clone.line, 7)

    def test_from_dict_none(self):
        p = ProgressMemory.from_dict(None)
        self.assertEqual(p.page_index, 0)

    def test_wpm_zero_when_no_time(self):
        s = ReadingStats()
        self.assertEqual(s.current_wpm, 0.0)
        self.assertEqual(s.average_wpm, 0.0)


class ThemeNamesTestCase(unittest.TestCase):
    def test_theme_names_valid(self):
        from bonovel.themes import is_valid

        for n in theme_names():
            self.assertTrue(is_valid(n))
        self.assertFalse(is_valid("nope"))

    def test_plain_theme_available_and_config_accepts(self):
        from bonovel.themes import get_theme

        # plain 主题必须已登记且字段完整
        self.assertIn("plain", theme_names())
        t = get_theme("plain")
        self.assertTrue(t.background and t.foreground and t.header_fg)

        # config 校验应接受 plain（写临时 config.json 再 load）
        import json

        tmp = tempfile.mkdtemp()
        try:
            p = Path(tmp) / "config.json"
            p.write_text(json.dumps({"theme": "plain"}), encoding="utf-8")
            from bonovel import config as cfg_mod

            loaded = cfg_mod.load_config(tmp)
            self.assertEqual(loaded["theme"], "plain")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class LibraryTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib = Library(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name, text, enc="utf-8"):
        p = Path(self.tmp) / name
        p.write_text(text, encoding=enc)
        return p

    def test_import_and_reload(self):
        p = self._write("novel.txt", "我的书\n第一章 一\n正文A\n第二章 二\n正文B\n")
        book = self.lib.import_files([p])
        self.assertEqual(book.title, "我的书")
        # 重新加载同一目录应能还原书库
        lib2 = Library(self.tmp)
        self.assertIn(book.id, lib2.books)

    def test_progress_save_reload(self):
        p = self._write("p.txt", "书\n第一章\n内容\n")
        book = self.lib.import_files([p])
        book.progress = ProgressMemory(page_index=2, total_pages=8)
        self.lib.save()
        lib2 = Library(self.tmp)
        reloaded = lib2.get(book.id)
        self.assertEqual(reloaded.progress.page_index, 2)

    def test_remove_book(self):
        p = self._write("r.txt", "标题\n第一章\n内容\n")
        book = self.lib.import_files([p])
        self.lib.remove(book.id)
        self.assertIsNone(self.lib.get(book.id))

    def test_bookmarks_persist(self):
        from bonovel.library import Bookmark

        p = self._write("bm.txt", "标题\n第一章\n内容\n")
        book = self.lib.import_files([p])
        book.bookmarks.append(Bookmark(page=4, note="好段"))
        self.lib.save()
        lib2 = Library(self.tmp)
        rb = lib2.get(book.id)
        self.assertEqual(len(rb.bookmarks), 1)
        self.assertEqual(rb.bookmarks[0].page, 4)

    def test_scan_data_dir_auto_imports(self):
        # 把 txt 直接放进数据目录
        p = self._write("放入的.txt", "扫描小说\n第一章\n正文内容\n")
        added = self.lib.scan_data_dir()
        self.assertEqual(added, 1)
        self.assertEqual(len(self.lib.books), 1)
        book = next(iter(self.lib.books.values()))
        self.assertEqual(book.title, "扫描小说")

    def test_scan_data_dir_is_idempotent(self):
        self._write("a.txt", "甲书\n第一章\n内容\n")
        self._write("b.txt", "乙书\n第一章\n内容\n")
        added1 = self.lib.scan_data_dir()
        self.assertEqual(added1, 2)
        # 已入库后重复扫描不再新增
        added2 = self.lib.scan_data_dir()
        self.assertEqual(added2, 0)
        self.assertEqual(len(self.lib.books), 2)


if __name__ == "__main__":
    unittest.main()
