"""bo-novel 异常体系。

所有向终端用户可直接展示的、可由上层友好处理的可预期错误，
都派生自 AppError；未预期的运行时故障仍由系统异常承载并写入日志。
"""

from __future__ import annotations


class AppError(Exception):
    """应用可预期的错误基类，message 面向终端用户可直接展示。"""


class ConfigError(AppError):
    """配置读取/写入失败。"""


class ParseError(AppError):
    """小说文本解析失败（如编码无法识别、文件结构异常）。"""


class UnsupportedEncoding(ParseError):
    """无法以已知编码解码文件。"""


class CorruptFile(ParseError):
    """文件已损坏或不是有效的文本小说。"""


class TerminalTooSmall(AppError):
    """终端尺寸过小，无法正常渲染界面。"""


class LibraryError(AppError):
    """书库管理（导入/删除/记录元数据）失败。"""


class UserCancelled(AppError):
    """用户在交互流程中主动取消。"""
