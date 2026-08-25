"""配置管理：默认值、读取、校验与原子保存。

数据目录（书库 / 配置 / 日志）定位策略（优先级由高到低）：
  1. 命令行 --data-dir 显式指定
  2. 环境变量 BONOVEL_DATA_DIR
  3. 平台默认目录（经 pathlib.Path.home() 派生，跨平台安全）
配置以 JSON 存储在 <data_dir>/config.json，含直接编辑的注释性说明由
内置 set 界面维护，本模块保证对外始终返回完整默认合并后的结果。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from bonovel.errors import ConfigError

CONFIG_FILENAME = "config.json"
LIBRARY_FILENAME = "library.json"
LOG_FILENAME = "bonovel.log"

# 默认配置。新增配置项时必须同时提供合理默认值与类型。
DEFAULTS: Dict[str, Any] = {
    # --- 阅读外观 ---
    "theme": "sepia",       # 内置主题名，见 themes.py
    "font_size": 1,          # 0=小 1=标准 2=大（影响页面密度，非真实变宽字体）
    "line_spacing": 1,       # 0=紧凑 1=标准 2=宽松
    # --- 阅读行为 ---
    "reading_mode": "page",  # "page" | "scroll"
    "scroll_step": 3,        # 滚动模式每次按键步进行数
    "auto_save": True,       # 退出/换书时自动保存阅读进度
    # --- 界面 ---
    "show_progress_bar": True,
    "show_footer_hint": True,
    # --- 状态 ---
    # last_read 为 {"title": str, "files": [str...], "position": {...}} 或 null
    "last_read": None,
}

# 允许的枚举值范围
_MODE_VALUES = ("page", "scroll")
_FONT_SIZES = (0, 1, 2)
_LINE_SPACINGS = (0, 1, 2)


def default_config() -> Dict[str, Any]:
    """返回默认配置的深拷贝，避免外部修改污染默认值。"""
    import copy

    return copy.deepcopy(DEFAULTS)


def data_dir(override: str | Path | None = None) -> Path:
    """解析最终的运行数据目录，必要时创建。"""
    env = os.environ.get("BONOVEL_DATA_DIR")
    if override:
        base = Path(override)
    elif env:
        base = Path(env)
    else:
        home = Path.home()
        base = home / ".bonovel"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:  # pragma: no cover - 难以在测试中稳定复现
        raise ConfigError(f"无法创建数据目录 {base}：{exc}") from exc
    return base


def config_path(directory: str | Path | None = None) -> Path:
    return data_dir(directory) / CONFIG_FILENAME


def library_path(directory: str | Path | None = None) -> Path:
    return data_dir(directory) / LIBRARY_FILENAME


def log_path(directory: str | Path | None = None) -> Path:
    return data_dir(directory) / LOG_FILENAME


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """把 override 中的键合并进 base 的浅拷贝（仅处理顶层标量键）。"""
    merged = dict(base)
    for key, value in override.items():
        if key in merged:
            merged[key] = value
    return merged


def _validate(cfg: Dict[str, Any]) -> None:
    if cfg["theme"] not in ("classic", "sepia", "dark", "paper", "terminal"):
        raise ConfigError(f"无效主题：{cfg['theme']!r}")
    if cfg["font_size"] not in _FONT_SIZES:
        raise ConfigError(f"无效字号：{cfg['font_size']!r}")
    if cfg["line_spacing"] not in _LINE_SPACINGS:
        raise ConfigError(f"无效行距：{cfg['line_spacing']!r}")
    if cfg["reading_mode"] not in _MODE_VALUES:
        raise ConfigError(f"无效阅读模式：{cfg['reading_mode']!r}")
    if isinstance(cfg["scroll_step"], bool) or not isinstance(cfg["scroll_step"], int):
        raise ConfigError("无效滚动步进：必须为整数")
    if cfg["scroll_step"] < 1 or cfg["scroll_step"] > 20:
        raise ConfigError("无效滚动步进：必须在 1~20 之间")


def load_config(directory: str | Path | None = None) -> Dict[str, Any]:
    """加载配置并与默认值合并，保证返回结构完整且已校验。"""
    cfg = default_config()
    path = config_path(directory)
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"配置文件无法读取 {path}：{exc}") from exc
        if isinstance(raw, dict):
            cfg = _merge(cfg, raw)
    _validate(cfg)
    return cfg


def save_config(cfg: Dict[str, Any], directory: str | Path | None = None) -> None:
    """原子保存配置（写临时文件再替换），避免中断造成损坏。

    允许传入部分配置：未提供的字段自动保留默认值后一并持久化。
    """
    full = _merge(default_config(), cfg)
    _validate(full)
    path = config_path(directory)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=".config-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(full, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except BaseException:
            # 出错时清理临时文件
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as exc:  # pragma: no cover
        raise ConfigError(f"无法保存配置 {path}：{exc}") from exc
