"""设置界面：字号/行距/主题切换即时预览与快捷键表。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.themes import Theme, theme_names
from bonovel.ui.base import View, draw_footer, draw_header


class SettingsView(View):
    """按 c 打开的阅读设置。修改即时生效并回写配置。"""

    FONT_LABELS = ("小", "标准", "大")
    SPACING_LABELS = ("紧凑", "标准", "宽松")
    MODE_LABELS = ("分页 Page", "滚动 Scroll")

    def __init__(self, app, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.cfg = app.cfg
        self.rows_tpl = [
            ("theme", "主题"),
            ("font_size", "字号"),
            ("line_spacing", "行距"),
            ("reading_mode", "阅读模式"),
            ("scroll_step", "滚动步进"),
            ("auto_save", "自动保存进度"),
        ]
        self.cursor = 0

    def render(self, screen: r.Screen) -> None:
        draw_header(screen, "阅读设置", self.theme, hint="↑ ↓选择  鼠标/键修改  q 返回")
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        sel_style = r.Style(fg=self.theme.selection_fg, bg=self.theme.selection_bg)
        row = 1
        for i, (key, label) in enumerate(self.rows_tpl):
            value = self._value_str(key)
            line = f"  {label} : {value}"
            if i == self.cursor:
                screen.set(r.apply_style(line, sel_style), row=row)
            else:
                screen.set(r.apply_style(line, style), row=row)
            row += 1
        draw_footer(screen, self.theme, "修改即时生效，自动保存到配置")

    def _value_str(self, key: str) -> str:
        v = self.cfg.get(key)
        if key == "theme":
            return f"{v}（{self._theme_title(v)}）"
        if key == "font_size":
            return self.FONT_LABELS[int(v)] if v is not None else ""
        if key == "line_spacing":
            return self.SPACING_LABELS[int(v)] if v is not None else ""
        if key == "reading_mode":
            return self.MODE_LABELS[0] if v == "page" else self.MODE_LABELS[1]
        if key == "scroll_step":
            return str(v)
        if key == "auto_save":
            return "开" if v else "关"
        return str(v)

    def _theme_title(self, name: str) -> str:
        from bonovel.themes import get_theme

        try:
            return get_theme(name).title
        except KeyError:
            return name

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        cfg = self.cfg
        if key == "up":
            self.cursor = (self.cursor - 1) % len(self.rows_tpl)
        elif key == "down":
            self.cursor = (self.cursor + 1) % len(self.rows_tpl)
        elif key in ("left", "right"):
            self._cycle(self.rows_tpl[self.cursor][0], -1 if key == "left" else 1)
        elif key in ("enter", " "):
            self._cycle(self.rows_tpl[self.cursor][0], 1)
        elif key in ("q", "esc", "ctrl-c"):
            self._apply_return()
            return None
        return None

    def _cycle(self, key: str, delta: int) -> None:
        if key == "theme":
            names = theme_names()
            idx = names.index(self.cfg["theme"]) if self.cfg["theme"] in names else 0
            self.cfg["theme"] = names[(idx + delta) % len(names)]
            self.app.apply_theme(self.cfg["theme"])
        elif key == "font_size":
            self.cfg["font_size"] = (int(self.cfg["font_size"]) + delta) % 3
        elif key == "line_spacing":
            self.cfg["line_spacing"] = (int(self.cfg["line_spacing"]) + delta) % 3
        elif key == "reading_mode":
            self.cfg["reading_mode"] = "scroll" if self.cfg["reading_mode"] == "page" else "page"
        elif key == "scroll_step":
            self.cfg["scroll_step"] = max(1, min(self.cfg["scroll_step"] + delta, 20))
        elif key == "auto_save":
            self.cfg["auto_save"] = not self.cfg["auto_save"]

    def _apply_return(self) -> None:
        from bonovel import config

        config.save_config(self.cfg, self.app.data_dir)
        self.app.cfg = self.cfg
        # 返回上一视图（通常是阅读），并按新模式重排排版
        restored = self.app.pop_stack()
        if restored is not None and hasattr(restored, "resize"):
            restored.resize(self.columns, self.rows)


class HelpView(View):
    """按 ? 打开的全量快捷键说明。"""

    def __init__(self, app, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.lines = [
            ("阅读", "Space/↓", "下一页 / 下一行"),
            ("阅读", "↑", "上一行 / 上一页"),
            ("阅读", "←/→", "前/后翻页"),
            ("阅读", "Home/End", "跳到首/末页"),
            ("阅读", "P", "切换 分页/滚动 模式"),
            ("阅读", "G", "打开章节目录"),
            ("阅读", "@", "在当前页添加书签"),
            ("阅读", "B", "打开书签列表"),
            ("阅读", "C", "打开设置"),
            ("阅读", "N", "翻到下一章"),
            ("阅读", "← 上一章", "(在目录中)"),
            ("全局", "?", "本帮助"),
            ("全局", "Q / Esc", "返回上级"),
            ("全局", "Ctrl-C", "退出/返回"),
        ]
        self.offset = 0

    def render(self, screen: r.Screen) -> None:
        draw_header(screen, "帮助 / 快捷键", self.theme)
        avail = self.rows - 2
        row = 1
        base = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        for grp, keys, desc in self.lines[self.offset : self.offset + avail]:
            label = f"  {grp:<4} {keys:<10} {desc}"
            screen.set(r.apply_style(label, base), row=row)
            row += 1
        draw_footer(screen, self.theme, "↑ ↓ 滚动   q 返回")

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        if key in ("up", "pageup"):
            self.offset = max(0, self.offset - 1)
        elif key in ("down", "pagedown"):
            self.offset += 1
        elif key in ("q", "esc", "ctrl-c"):
            self.app.pop_stack()
        return None
