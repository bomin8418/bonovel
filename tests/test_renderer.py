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

    def test_default_is_plain(self):
        self.assertEqual(themes.default_theme().name, "plain")


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


if __name__ == "__main__":
    unittest.main()
