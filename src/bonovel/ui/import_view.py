"""导入界面：手动输入 .txt 文件路径并导入。"""

from __future__ import annotations

from typing import Optional

from bonovel import renderer as r
from bonovel.themes import Theme
from bonovel.ui.base import View, draw_footer, draw_header


class ImportView(View):
    """按 i 打开的路径输入框：输入 .txt 路径回车导入。"""

    def __init__(self, app, theme: Theme, columns: int, rows: int):
        super().__init__(app, theme, columns, rows)
        self.path = ""
        self.error = ""

    def render(self, screen: r.Screen) -> None:
        draw_header(
            screen,
            "导入小说",
            self.theme,
            hint="输入 .txt 路径  Enter 导入  Esc 取消",
        )
        style = r.Style(fg=self.theme.foreground, bg=self.theme.background)
        sel_style = r.Style(fg=self.theme.selection_fg, bg=self.theme.selection_bg)
        screen.set(r.apply_style(f"  路径: {self.path}_", sel_style), row=1)
        if self.error:
            screen.set(
                r.apply_style(f"  {self.error}", r.Style(fg=self.theme.accent_fg)),
                row=2,
            )
        screen.set(
            r.apply_style(
                f"  也可把 .txt 放入数据目录自动入库：{self.app.data_dir}",
                r.Style(fg=self.theme.dim_fg),
            ),
            row=3,
        )
        draw_footer(
            screen,
            self.theme,
            "支持绝对/相对路径与中文文件名；路径不存在会提示失败",
        )

    def on_key(self, key: str, text: Optional[str]) -> Optional[str]:
        if key == "backspace":
            if self.path:
                self.path = self.path[:-1]
            return None
        if key == "enter":
            return self._import()
        if key in ("esc", "ctrl-c"):
            self.app.pop_stack()
            return None
        # 可打印字符（含中文宽字符）追加到路径
        if text and ord(text) >= 0x20:
            self.path += text
        return None

    def _import(self) -> Optional[str]:
        path = self.path.strip()
        if not path:
            self.error = "路径为空，请输入 .txt 文件路径"
            return None
        before = self.app._view
        self.app._import_paths([path])
        if self.app._view is not before:
            return None  # 已自动进入阅读（open_book 清栈）
        # 未自动打开或导入失败：回书架并刷新列表
        self.app.pop_stack()
        v = self.app._view
        if v is not None and hasattr(v, "refresh"):
            v.refresh()
        self.app.force_redraw = True
        return None
