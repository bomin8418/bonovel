"""文本编码检测与显示宽度等通用工具（纯标准库）。"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Tuple

from bonovel.errors import UnsupportedEncoding

# 常见编码的 BOM
_UTF8_BOM = b"\xef\xbb\xbf"
_UTF16_LE_BOM = b"\xff\xfe"
_UTF16_BE_BOM = b"\xfe\xff"
_UTF32_LE_BOM = b"\xff\xfe\x00\x00"
_UTF32_BE_BOM = b"\x00\x00\xfe\xff"

# 允许的候选编码（解码回退顺序）。gbk 优先：纯 GBK 字节可被 gbk 精确定位，
# 超出 gbk 范围的字符（如部分 CJK 扩展）方回落至其超集 gb18030。
_FALLBACK_ENCODINGS = ("gbk", "gb18030", "big5")

# 乱码/控制性判定阈值：允许的宽窄字符比例下限
_MIN_VALID_RATIO = 0.7
# 采样字节上限，避免超大数据文件全量解码
_MAX_SAMPLE = 2 * 1024 * 1024


def _has_utf8_bom(data: bytes) -> bool:
    return data.startswith(_UTF8_BOM)


def _is_strictly_valid_utf8(data: bytes) -> bool:
    """严格校验整段数据能否无损解码为 UTF-8。"""
    try:
        data.decode("utf-8", errors="strict")
        return True
    except UnicodeDecodeError:
        return False


def _looks_like_garbage(text: str) -> bool:
    """粗判解码结果是否乱码——检查常见替换符与控制字符占比。

    Windows-1252 类单字节误解码会产生大量 U+FFFD；GBK 误读为 UTF-8 会有
    较高控制字符密度。此处仅做取舍辅助，不作为唯一依据。
    """
    if not text:
        return False
    bad = sum(1 for ch in text if ch == "\ufffd")
    controls = sum(
        1
        for ch in text
        if unicodedata.category(ch).startswith("C")
        and ch not in ("\n", "\r", "\t", "\x00")
    )
    suspicious = bad + controls * 3
    return suspicious / len(text) > 0.02


def detect_encoding(data: bytes) -> Tuple[str, str]:
    """检测字节流的文本编码，返回 (codec_name, decoded_text)。

    判定顺序：
      1. 4/2/3 字节 BOM 精确定位（UTF-8/UTF-16/UTF-32）
      2. 无 BOM：UTF-8 严格解码通过且不似乱码 → utf-8
      3. 回退顺序尝试 gb18030（涵盖 GBK）/big5，返回解码最自然者
    全部失败则抛 UnsupportedEncoding。
    """
    if not data:
        return "utf-8", ""

    # --- BOM 精确判定 ---
    if data.startswith(_UTF32_LE_BOM) or data.startswith(_UTF32_BE_BOM):
        enc = "utf-32" if data.startswith(_UTF32_BE_BOM) else "utf-32-le"
        text = _decode_strict(data, enc)
        return "utf-32", text
    if data.startswith(_UTF16_LE_BOM):
        return "utf-16-le", _decode_strict(data, "utf-16-le")
    if data.startswith(_UTF16_BE_BOM):
        return "utf-16-be", _decode_strict(data, "utf-16-be")
    if data.startswith(_UTF8_BOM):
        text = _decode_strict(data[len(_UTF8_BOM) :], "utf-8")
        return "utf-8", text

    # --- 无 BOM：尝试 UTF-8 ---
    sample = data[:_MAX_SAMPLE]
    if _is_strictly_valid_utf8(sample):
        text = _decode_strict(data, "utf-8")
        if not _looks_like_garbage(text):
            return "utf-8", text

    # --- 回退：中文多字节编码 ---
    for enc in _FALLBACK_ENCODINGS:
        try:
            text = data.decode(enc, errors="strict")
        except UnicodeDecodeError:
            continue
        if not _looks_like_garbage(text):
            return enc, text

    raise UnsupportedEncoding(
        "无法识别文件编码：既非标准 UTF-8，也非常见中文编码（GBK/GB18030/Big5）。"
    )


def _decode_strict(data: bytes, enc: str) -> str:
    try:
        return data.decode(enc, errors="strict")
    except UnicodeDecodeError as exc:
        raise UnsupportedEncoding(f"按 {enc} 解码失败：{exc}") from exc


def read_text_file(path: "str | Path") -> Tuple[str, str]:
    """读入文本文件并自动识别编码，返回 (codec, text)。

    交由导入层调用；异常统一转为 UnsupportedEncoding 以便上层友好处理。
    """
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise UnsupportedEncoding(f"无法读取文件 {path}：{exc}") from exc
    codec, text = detect_encoding(raw)
    return codec, text


def display_width(text: str) -> int:
    """计算字符串在终端的显示宽度：全角(CJK等)按 2 列，其余按 1 列。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad_to(text: str, width: int, align: str = "left") -> str:
    """按终端显示宽度在右侧/中间填充空格，保证对齐。"""
    w = display_width(text)
    if w >= width:
        return text
    pad = " " * (width - w)
    if align == "right":
        return pad + text
    if align == "center":
        left = (width - w) // 2
        return " " * left + text + " " * (width - w - left)
    return text + pad
