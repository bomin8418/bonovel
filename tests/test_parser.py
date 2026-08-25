"""文件导入与解析层单元测试：编码检测、章节解析、大文件策略。"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from bonovel.errors import UnsupportedEncoding
from bonovel.parser import Chapter, Novel, chapter_index_of, parse_files
from bonovel import utils


class EncodingDetectionTestCase(unittest.TestCase):
    def test_utf8_no_bom(self):
        data = "第一章 测试\n你好世界。".encode("utf-8")
        codec, text = utils.detect_encoding(data)
        self.assertEqual(codec, "utf-8")
        self.assertIn("你好世界", text)

    def test_utf8_with_bom(self):
        text = "第一章 带BOM\n内容"
        data = b"\xef\xbb\xbf" + text.encode("utf-8")
        codec, decoded = utils.detect_encoding(data)
        self.assertEqual(codec, "utf-8")
        self.assertFalse(decoded.startswith("\ufeff"))

    def test_gbk(self):
        data = "第一章 测试\n中文GBK内容".encode("gbk")
        codec, text = utils.detect_encoding(data)
        # gb18030 是 gbk 的超集，纯 GBK 字节同样可被 gb18030 解码
        self.assertIn(codec, ("gbk", "gb18030"))
        self.assertIn("中文GBK内容", text)

    def test_gb18030(self):
        data = "分卷\r\n第三章\r\n简体＋正體".encode("gb18030")
        codec, text = utils.detect_encoding(data)
        self.assertIn(codec, ("gbk", "gb18030"))
        self.assertIn("简体", text)

    def test_utf16le_bom(self):
        data = b"\xff\xfe" + "第一章 测试".encode("utf-16-le")
        codec, text = utils.detect_encoding(data)
        self.assertEqual(codec, "utf-16-le")
        self.assertIn("第一章", text)

    def test_random_binary_rejected(self):
        data = bytes(range(256)) * 4  # 伪随机二进制，任意中文编码都难以无错解码
        with self.assertRaises(UnsupportedEncoding):
            utils.detect_encoding(data)

    def test_empty(self):
        codec, text = utils.detect_encoding(b"")
        self.assertEqual(text, "")

    def test_display_width(self):
        self.assertEqual(utils.display_width("abc"), 3)
        self.assertEqual(utils.display_width("中文"), 4)
        self.assertEqual(utils.display_width("中a"), 3)

    def test_read_text_file(self):
        tmp = tempfile.mkdtemp()
        try:
            p = Path(tmp) / "book.txt"
            p.write_text("第一章 内容", encoding="gbk")
            codec, text = utils.read_text_file(p)
            self.assertEqual(codec, "gbk")
            self.assertEqual(text, "第一章 内容")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name, text, encoding="utf-8"):
        p = Path(self.tmp) / name
        p.write_text(text, encoding=encoding)
        return p

    def test_basic_utf8_parse(self):
        p = self._write(
            "book.txt",
            "我的小说\n\n第一章 初见\n这是正文第一行。\n第二章 重逢\n第二段内容。\n",
        )
        novel = parse_files([p])
        self.assertEqual(novel.title, "我的小说")
        self.assertGreaterEqual(len(novel.chapters), 2)
        self.assertEqual(novel.line_count, 6)

    def test_gbk_parse(self):
        p = self._write(
            "book2.txt",
            "书名\n\n第一章 第一章\n正文内容A。\n第二章 第二章\n正文B。\n",
            encoding="gbk",
        )
        novel = parse_files([p])
        self.assertEqual(novel.codec, "gbk")
        self.assertEqual(novel.line_text(3), "正文内容A。")

    def test_chapter_detection_variants(self):
        lines = [
            "正文前言",
            "第一章 开始",
            "第二章 继续",
            "第三回 回顾",
            "序章 篇首",
            "第10章 数字",
            "Chapter 5 引用",
            "尾声 终章",
        ]
        p = self._write("c.txt", "\n".join(lines) + "\n", encoding="utf-8")
        novel = parse_files([p])
        titles = [c.title for c in novel.chapters]
        # 首个标题行（第一章）会被当作书名跳过
        self.assertIn("第二章 继续", titles)
        self.assertIn("第三回 回顾", titles)
        self.assertIn("序章 篇首", titles)

    def test_empty_file_raises(self):
        p = self._write("empty.txt", "")
        with self.assertRaises(Exception):
            parse_files([p])

    def test_multi_file_merge(self):
        p1 = self._write("a.txt", "书名\n\n第一章 甲\n内容甲。\n", encoding="utf-8")
        p2 = self._write("b.txt", "\n第二章 乙\n内容乙。\n", encoding="utf-8")
        novel = parse_files([p1, p2])
        self.assertIn("第二章 乙", [c.title for c in novel.chapters])

    def test_chapter_index_of(self):
        p = self._write(
            "idx.txt",
            "书名\n第一章 一\n内容1\n第二章 二\n内容2\n",
            encoding="utf-8",
        )
        novel = parse_files([p])
        # line 3 (内容1) 属于第一章所在章节下标
        self.assertIsInstance(chapter_index_of(novel, 3), int)


if __name__ == "__main__":
    unittest.main()
