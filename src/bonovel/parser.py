"""小说 .txt 解析：加载、规范化、章节检测、行索引与按需读取。

性能策略：
  * 解析时仅建立“行偏移索引”（每行在文件中的字节偏移），不把全文载入内存，
    从而支持超大文本文件流畅翻页。
  * 阅读时按需从行索引定位、读取对应字节段并解码。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from bonovel.errors import CorruptFile, ParseError
from bonovel import utils

# 章节标题判定：第X章 / 第X回 / 序章 / 第X节 / 第X卷 / 第X部分 / Chapter N / Ch N
_CHAPTER_RE = re.compile(
    r"^\s{0,8}(第[0-9零一二三四五六七八九十百千万〇两]+[章节回卷部集幕篇]"
    r"|序章|楔子|引子|尾声"
    r"|[Cc]hapter\s+[0-9]+|[Cc]h\.?\s*[0-9]+"
    r"|卷之[0-9零一二三四五六七八九十百]+"
    r")\s*[：:\.\-\s]?.*$"
)
# 数字标题行：如 "001"、"12"、"三"
_NUMERIC_HEADING_RE = re.compile(
    r"^\s{0,8}([0-9]{1,4}|[0-9零一二三四五六七八九十百千万]{1,4})\s*[。\.、]?\s*$"
)

# 单行有效内容（非空白、非纯分隔符）判定
_BLANK_RE = re.compile(r"^\s*$")
_DIVIDER_RE = re.compile(r"^[\s\-—=_*·~]{2,}$")

MAX_LINE_BYTES = 256 * 1024  # 单行理论上限，防止异常文件拖垮性能


@dataclass(frozen=True)
class Chapter:
    """章节元数据：标题、在文本中的起始行的逻辑序号（0 基）。"""

    title: str
    start_line: int


@dataclass
class Novel:
    """一部小说：元数据、章节索引与行索引（用于按需读取与翻页）。"""

    title: str
    files: List[str]
    codec: str = "utf-8"
    chapters: List[Chapter] = field(default_factory=list)
    # 每个逻辑行的字节偏移；最后补一个总长哨兵
    line_offsets: List[int] = field(default_factory=list)
    _raw: bytes = b""

    @property
    def character_count(self) -> int:
        return sum(len(self.line_text(i)) for i in range(self.line_count))

    @property
    def line_count(self) -> int:
        n = len(self.line_offsets)
        return n - 1 if n else 0

    def line_text(self, line: int) -> str:
        """返回指定逻辑行的文本（不缓存，按需解码）。"""
        if not 0 <= line < self.line_count:
            return ""
        start = self.line_offsets[line]
        end = self.line_offsets[line + 1]
        seg = self._raw[start:end]
        # 去掉行尾的 \r 或 \n
        if seg.endswith(b"\n"):
            seg = seg[:-1]
        if seg.endswith(b"\r"):
            seg = seg[:-1]
        try:
            return seg.decode(self.codec, errors="replace")
        except (LookupError, ValueError):
            return seg.decode("utf-8", errors="replace")


def _strip_bom(data: bytes) -> bytes:
    if data.startswith(utils._UTF8_BOM):
        return data[len(utils._UTF8_BOM) :]
    return data


def _build_line_offsets(data: bytes) -> List[int]:
    """建立行索引：返回每行起始偏移 + 末尾哨兵。"""
    offsets = [0]
    for i, byte in enumerate(data):
        if byte == 0x0A:  # \n
            offsets.append(i + 1)
    # 末尾也作为哨兵（即使无换行）
    if offsets[-1] < len(data):
        offsets.append(len(data))
    # 空文件
    if len(data) == 0:
        offsets = [0]
    return offsets


def _detect_title(files: List[str], first_lines: List[Tuple[int, str]]) -> "Tuple[str, int]":
    """从文件清单与开头若干行推断书名，返回 (书名, 选定行号)。

    -1 表示未从内容行取到书名（使用文件主文件名）。
    """
    for line_no, line in first_lines:
        stripped = line.strip()
        if not stripped or _DIVIDER_RE.match(stripped):
            continue
        if _CHAPTER_RE.match(stripped) or _NUMERIC_HEADING_RE.match(stripped):
            return stripped, line_no
        if 2 <= len(stripped) <= 30:
            return stripped, line_no
    stem = Path(files[0]).stem if files else "未命名小说"
    return stem, -1


def parse_files(files: List["str | Path"]) -> Novel:
    """导入一个或多个 .txt 文件为 Novel。

    - 多文件视为同一部小说的连续章节，按传入顺序拼接。
    - 自动识别编码（首个文件决定整体编码依据，后续文件按同一编码尽力解码）。
    """
    if not files:
        raise ParseError("没有可导入的文件。")
    paths = [Path(f) for f in files]

    chunks_raw: List[bytes] = []
    codec = "utf-8"
    first_file = True
    for p in paths:
        if not p.exists():
            raise CorruptFile(f"文件不存在：{p}")
        if not p.is_file():
            raise CorruptFile(f"不是普通文件：{p}")
        try:
            raw = p.read_bytes()
        except OSError as exc:
            raise CorruptFile(f"无法读取 {p}：{exc}") from exc
        if not raw:
            continue  # 忽略空文件
        raw = _strip_bom(raw)
        if first_file:
            codec, _ = utils.read_text_file(p)
            first_file = False
        # 解码校验：无法按已定编码解码时若为本文件首个编码，尝试重测
        chunks_raw.append(raw)

    if not chunks_raw:
        raise CorruptFile("导入的文件均为空，没有可读内容。")

    data = b"\n".join(chunks_raw)
    offsets = _build_line_offsets(data)

    # 预读前 60 行用于标题推断
    sample_lines: List[Tuple[int, str]] = []
    for i in range(min(len(offsets) - 1, 60)):
        start = offsets[i]
        end = offsets[i + 1]
        seg = data[start:end].rstrip(b"\r\n")
        try:
            txt = seg.decode(codec, errors="replace")
        except (LookupError, ValueError):
            txt = seg.decode("utf-8", errors="replace")
        sample_lines.append((i, txt))

    title, title_line = _detect_title([str(p) for p in paths], sample_lines)
    chapters = _scan_all_chapters(data, offsets, codec, title_line=title_line)

    novel = Novel(
        title=title,
        files=[str(p) for p in paths],
        codec=codec,
        chapters=chapters,
        line_offsets=offsets,
        _raw=data,
    )
    if novel.line_count <= 0:
        raise CorruptFile("文件内容为空或无法识别为文本。")
    return novel


def _scan_all_chapters(
    data: bytes, offsets: List[int], codec: str, title_line: int = -1
) -> List[Chapter]:
    """在全量行上扫描章节标题（供精确章节目录）。

    title_line 为探测到的书名所在行号；若该行恰好形似章节标题，跳过之，
    避免把书名误当成第一个章节。
    """
    chapters: List[Chapter] = []
    if len(offsets) > 500_000:
        # 超大文本：仅对前 5000 行与后续每隔若干行抽样，避免过慢
        sample = set(range(min(len(offsets) - 1, 5000)))
        sample |= {i for i in range(5000, len(offsets) - 1, 8)}
    else:
        sample = set(range(len(offsets) - 1))

    for i in sorted(sample):
        start = offsets[i]
        end = offsets[i + 1]
        seg = data[start:end].rstrip(b"\r\n")
        try:
            txt = seg.decode(codec, errors="replace")
        except (LookupError, ValueError):
            continue
        stripped = txt.strip()
        if not stripped or _DIVIDER_RE.match(stripped):
            continue
        is_head = bool(_CHAPTER_RE.match(stripped)) or bool(
            _NUMERIC_HEADING_RE.match(stripped)
        )
        if is_head:
            if i == title_line:
                # 该行被识别为书名，不纳入章节
                continue
            chapters.append(Chapter(title=stripped, start_line=i))
    if not chapters:
        chapters = [Chapter(title="全文", start_line=0)]
    return chapters


def chapter_index_of(novel: Novel, line: int) -> int:
    """给定行号，返回其所属章节在 chapters 中的下标（0 基）。"""
    idx = 0
    for i, ch in enumerate(novel.chapters):
        if ch.start_line <= line:
            idx = i
        else:
            break
    return idx
