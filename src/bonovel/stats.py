"""阅读速度统计（WPM）与自动进度保存。

阅读速度：按“页查看时长”与页内字数估算当前速度，并累计会话平均速度。
进度：切换页面/退出界面时记录最后位置，由上层调用 save 持久化到 library.json。
"""

from __future__ import annotations

import time
from typing import Optional


class ReadingStats:
    """跟踪阅读速度：每页停留时长 + 页字数 → 当前 WPM 与累计平均。"""

    def __init__(self):
        self._char_total = 0
        self._time_total = 0.0
        self._last_char = 0
        self._last_time: Optional[float] = None
        self.current_impact: float = 0.0

    def record_page(self, chars: int) -> None:
        """进入一页：记录该页字数与进入时刻。"""
        now = time.monotonic()
        # 若刚从上一页而来且记录过，累计停留时长
        if self._last_time is not None:
            dt = now - self._last_time
            if dt > 0:
                self._time_total += dt
        self._char_total += chars
        self._last_char = chars
        self._last_time = now

    def leave(self) -> None:
        """离开当前页：结算停留时长。"""
        if self._last_time is not None:
            dt = time.monotonic() - self._last_time
            if dt > 0:
                self._time_total += dt
            self._last_time = None

    def _measurement(self) -> float:
        """返回当前页的速度（字符/分钟）。"""
        if self._last_time is None:
            return 0.0
        dt = time.monotonic() - self._last_time
        if dt <= 0:
            return 0.0
        return self._last_char * 60.0 / dt

    @property
    def current_wpm(self) -> float:
        """当前速度（以 汉字/分钟 计，约合 WPM）。"""
        return self._measurement() / 300.0

    @property
    def average_wpm(self) -> float:
        """会话平均速度。"""
        if self._time_total <= 0:
            return 0.0
        return self._char_total * 60.0 / self._time_total / 300.0


class ProgressMemory:
    """单部小说的书籍进度记忆：最后一个阅读位置与总进度。"""

    def __init__(self, page_index: int = 0, total_pages: int = 1, line: int = 0):
        self.page_index = page_index
        self.total_pages = max(total_pages, 1)
        self.line = line

    def percent(self) -> float:
        if self.total_pages <= 1:
            return 0.0
        return self.page_index / (self.total_pages - 1) * 100.0

    def to_dict(self) -> dict:
        return {
            "page_index": self.page_index,
            "total_pages": self.total_pages,
            "line": self.line,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "ProgressMemory":
        if not data:
            return cls()
        try:
            return cls(
                page_index=int(data.get("page_index", 0)),
                total_pages=max(int(data.get("total_pages", 1)), 1),
                line=int(data.get("line", 0)),
            )
        except (TypeError, ValueError):  # pragma: no cover - 容错
            return cls()
