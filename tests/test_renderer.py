"""渲染/主题/排版/键盘输入层单元测试。"""

from __future__ import annotations

import unittest

from bonovel import keys, renderer, themes
from bonovel.layout import (
    ScrollWindow,
    NovelLayouter,
    visible_lines,
)
from bonovel.themes import get_theme, theme_names


class RendererTestCase(unittest.TestCase):
    def test_sgr_fg_bg(self):
        self.assertEqual(renderer.sgr_fg((1, 2, 3)), "\x1b[38;2;1;2;3m")
        self.assertEqual(renderer.sgr_bg((9, 8, 7)), "\x1b[48;2;9;8;7m")

    def test_apply_style_empty(self):
        self.assertEqual(renderer.apply_style("abc", renderer.Style()), "abc")

    def test_apply_style_color(self):
        out = renderer.apply_style("hi", renderer.Style(fg=(10, 20, 30)))
        self.assertIn("hi", out)
        self.assertTrue(out.startswith("\x1b[38;2;"))

    def test_cursor_sequences(self):
        self.assertIn("\x1b[", renderer.cursor_hide())
        self.assertIn("\x1b[", renderer.cursor_show())
        self.assertEqual(renderer.cursor_goto(3, 5), "\x1b[3;5H")

    def test_screen_render_bounds(self):
        scr = renderer.Screen(columns=5, rows=3)
        scr.set("ab")
        out = scr.render()
        self.assertIn("\x1b[1;1H", out)
        # 第二行应含空白补齐
        self.assertIn("\x1b[0m\r\n", out)

    def test_plain_width_strips_ansi(self):
        text = renderer.sgr_fg((1, 2, 3)) + "中x" + renderer.sgr_reset()
        self.assertEqual(renderer._plain_width(text), 3)


class ThemesTestCase(unittest.TestCase):
    def test_all_themes_have_required_fields(self):
        for name in theme_names():
            t = get_theme(name)
            self.assertTrue(t.background)
            self.assertTrue(t.foreground)
            self.assertTrue(t.header_fg)
            self.assertTrue(t.selection_bg)

    def test_default_is_plain_dark(self):
        self.assertEqual(themes.default_theme().name, "plain-dark")


class LayoutPageTestCase(unittest.TestCase):
    def lines_func(self, i):
        return self._lines[i]

    def test_basic_pagination_partitions_all_lines(self):
        self._lines = [f"第{i}行内容 " for i in range(40)]
        lay = NovelLayouter(
            len(self._lines),
            lambda i: self.lines_func(i),
            columns=40,
            rows=12,
            font_size=1,
            line_spacing=1,
        )
        self.assertGreaterEqual(lay.page_count(), 1)

    def test_pagination_covers_all_lines(self):
        self._lines = [f"测试段落内容第{i}行" for i in range(30)]
        lay = NovelLayouter(
            len(self._lines),
            lambda i: self.lines_func(i),
            columns=40,
            rows=10,
            font_size=1,
            line_spacing=1,
        )
        total = lay.page_count()
        first = lay.page_at(0)
        last = lay.page_at(total - 1)
        # 覆盖应从 0 行开始，到至少 29 行
        self.assertEqual(first.start_line, 0)
        self.assertGreaterEqual(last.end_line, 28)

    def test_wrap_respects_width(self):
        self._lines = ["一二三四五六七八九十" * 10]
        width = 20
        lay = NovelLayouter(
            len(self._lines),
            lambda i: self.lines_func(i),
            columns=width,
            rows=24,
            font_size=1,
            line_spacing=1,
        )
        p = lay.page_at(0)
        for row in p.rows:
            # 含缩进也不超过可用宽度太多
            self.assertLessEqual(len(row), width + 1)


class LayoutReflowTestCase(unittest.TestCase):
    """reflow 复用折行缓存：参数未变跳过、宽度未变只重排。"""

    def _lines(self, n):
        return [f"这是第{i}行用于重排测试的正文内容文本段落。" for i in range(n)]

    def _make(self, n=200, columns=80, rows=24):
        lines = self._lines(n)
        return NovelLayouter(
            len(lines),
            lambda i: lines[i],
            columns=columns,
            rows=rows,
            font_size=1,
            line_spacing=1,
        )

    def test_reflow_same_params_keeps_pages(self):
        lay = self._make()
        before = lay.page_count()
        first_before = lay.page_at(0)
        lay.reflow(80, 24, 1, 1)  # 参数未变：应直接返回
        self.assertEqual(lay.page_count(), before)
        self.assertEqual(lay.page_at(0).start_line, first_before.start_line)

    def test_reflow_font_change_repartitions(self):
        lay = self._make(rows=24)
        pc_normal = lay.page_count()
        lay.reflow(80, 24, 2, 1)  # 大字号 → 更多页
        self.assertGreater(lay.page_count(), pc_normal)
        self.assertEqual(lay.page_at(lay.page_count() - 1).end_line, 199)

    def test_reflow_rows_change_covers_all(self):
        lay = self._make(n=300, rows=30)
        lay.reflow(80, 12, 1, 1)  # 更少行 → 页数变多
        last = lay.page_at(lay.page_count() - 1)
        self.assertEqual(last.end_line, 299)
        # 覆盖 0..299 全部行
        seen = set()
        for i in range(lay.page_count()):
            p = lay.page_at(i)
            seen.add(p.start_line)
            seen.add(p.end_line)
        self.assertIn(0, seen)
        self.assertIn(299, seen)

    def test_reflow_width_change_rebuilds(self):
        lay = self._make(n=150, columns=80)
        lay.reflow(30, 24, 1, 1)  # 变窄 → 每行折成多行 → 页数变多
        self.assertGreater(lay.page_count(), self._make(n=150, columns=80).page_count())
        last = lay.page_at(lay.page_count() - 1)
        self.assertEqual(last.end_line, 149)


class ScrollWindowTestCase(unittest.TestCase):
    def test_scroll_limits(self):
        w = ScrollWindow(10, step=3)
        w.scroll_down()
        self.assertEqual(w.top, 3)
        w.scroll_up()
        self.assertEqual(w.top, 0)
        w.scroll_down()
        w.scroll_down()
        w.scroll_down()  # 应钳制到末尾
        self.assertEqual(w.top, 9)

    def test_visible_lines(self):
        w = ScrollWindow(10)
        self.assertEqual(visible_lines(w, 3), [0, 1, 2])


class KeyParserTestCase(unittest.TestCase):
    @staticmethod
    def _stob(s: str):
        return [ord(c) for c in s]

    def test_arrow_keys(self):
        p = keys.KeyParser()
        # ESC [ A = up
        keys_list = keys.reads_keys(p, self._stob("\x1b[A"))
        self.assertEqual(keys_list[0][0], "up")

    def test_plain_char(self):
        p = keys.KeyParser()
        self.assertEqual(keys.reads_keys(p, [ord("a")]), [("a", "a")])

    def test_enter(self):
        p = keys.KeyParser()
        self.assertEqual(p.push(ord("\n")), (keys.ENTER, "\n"))

    def test_ctrl_c(self):
        p = keys.KeyParser()
        self.assertEqual(p.push(0x03), (keys.CTRL_C, None))

    def test_page_down_sequence(self):
        p = keys.KeyParser()
        res = keys.reads_keys(p, self._stob("\x1b[6~"))
        self.assertEqual(res[0][0], "pagedown")

    def test_ctrl_left_sequence(self):
        p = keys.KeyParser()
        res = keys.reads_keys(p, self._stob("\x1b[1;5D"))
        self.assertEqual(res[0][0], "ctrl-left")

    def test_escape_alone(self):
        p = keys.KeyParser()
        self.assertIsNone(p.push(0x1B))
        self.assertEqual(p.resolve(), (keys.ESC, None))

    def test_wide_char_windows_byte(self):
        # Windows msvcrt 直接返回码点 >0xFF：中=0x4E2D
        p = keys.KeyParser()
        self.assertEqual(p.push(0x4E2D), ("中", "中"))

    def test_utf8_multibyte_input(self):
        # Unix 原始模式：中 = 0xE4 0xB8 0xAD 逐字节累积
        p = keys.KeyParser()
        res = keys.reads_keys(p, [0xE4, 0xB8, 0xAD])
        self.assertEqual(res, [("中", "中")])

    def test_utf8_ascii_mix(self):
        p = keys.KeyParser()
        res = keys.reads_keys(p, [ord("a"), 0xE4, 0xB8, 0xAD, ord("b")])
        self.assertEqual([k for k, _ in res], ["a", "中", "b"])


class WinExtKeyTestCase(unittest.TestCase):
    """Windows msvcrt 扩展键（\xe0/\x00 前缀 + 扫描码）→ 逻辑键翻译。"""

    def test_scan_code_mapping(self):
        self.assertEqual(keys._win_ext_key_sequence("H"), "\x1b[A")
        self.assertEqual(keys._win_ext_key_sequence("P"), "\x1b[B")
        self.assertEqual(keys._win_ext_key_sequence("K"), "\x1b[D")
        self.assertEqual(keys._win_ext_key_sequence("M"), "\x1b[C")
        self.assertEqual(keys._win_ext_key_sequence("I"), "\x1b[5~")
        self.assertEqual(keys._win_ext_key_sequence("Q"), "\x1b[6~")
        self.assertEqual(keys._win_ext_key_sequence("G"), "\x1b[1~")
        self.assertEqual(keys._win_ext_key_sequence("O"), "\x1b[4~")
        self.assertIsNone(keys._win_ext_key_sequence("z"))

    def _feed(self, seq: str):
        p = keys.KeyParser()
        res = keys.reads_keys(p, [ord(c) for c in seq])
        return res[0][0]

    def test_arrow_down_via_e0_scan(self):
        # '\xe0' + 'P' = 下方向键，翻译为 \x1b[B 后解析为 down
        self.assertEqual(self._feed(keys._win_ext_key_sequence("P")), "down")

    def test_page_up_down_via_e0_scan(self):
        self.assertEqual(self._feed(keys._win_ext_key_sequence("I")), "pageup")
        self.assertEqual(self._feed(keys._win_ext_key_sequence("Q")), "pagedown")

    def test_home_end_via_e0_scan(self):
        self.assertEqual(self._feed(keys._win_ext_key_sequence("G")), "home")
        self.assertEqual(self._feed(keys._win_ext_key_sequence("O")), "end")

    def test_left_right_via_e0_scan(self):
        self.assertEqual(self._feed(keys._win_ext_key_sequence("K")), "left")
        self.assertEqual(self._feed(keys._win_ext_key_sequence("M")), "right")

    def test_f1_via_null_scan(self):
        # '\x00' + ';' = F1；翻译后为 \x1bOP，解析器未定义 F 键 → unknown
        self.assertEqual(keys._win_ext_key_sequence(";"), "\x1bOP")
        self.assertEqual(self._feed("\x1bOP"), "unknown")


if __name__ == "__main__":
    unittest.main()
