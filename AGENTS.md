# AGENTS.md — 项目约定（供 AI 协作者 / 开发者）

本文件描述 bo-novel 的工程约定、命令、架构与变更规范。接手本项目或继续开发时请先读此文件。

## 项目是什么

bo-novel 是一个**终端小说阅读器**，使用 **Python 纯标准库**（零第三方运行依赖）编写。
面向 Windows / macOS / Linux 跨平台。核心能力：.txt 导入与自动编码识别、分页/滚动阅读、
章节目录、书签、进度记忆、自定义主题、阅读速度统计。

## 常用命令（都在项目根目录执行）

```bash
# 运行（任意目录需先保证可导入；见下方“运行与安装”）
python -m bonovel --version                 # 版本
python -m bonovel --help                    # 参数说明
python -m bonovel 你的小说.txt               # 启动并导入

# 测试
python -m unittest discover -s tests -v     # 全量单元测试（当前 55 项）
python -m unittest tests.test_stats -v      # 单模块测试

# 语法检查
python -m py_compile bonovel/*.py bonovel/ui/*.py

# 暂存/查看改动
git add -A && git status --short
git diff --cached --stat
```

## 运行与安装

- **项目目录直跑**：`cd` 进根目录后 `python -m bonovel` 可用。
- **任意目录运行**：需要把项目加入 `PYTHONPATH`（`set PYTHONPATH=%CD%` / `export PYTHONPATH="$PWD"`），
  或 `python -m pip install -e .`（注：本会话中 `pip install` 在沙箱内被权限层拦截，需用户手动执行）。
- `pyproject.toml` 已声明 console script `bonovel = bonovel.cli:main`（全局安装后可用）。
- **数据目录**：书库/配置/日志存放处。默认 `~/.bonovel`；可用 `-d DIR` 或环境变量 `BONOVEL_DATA_DIR` 覆盖。
  放在数据目录 **顶层** 的 `.txt` 会在启动时被 `Library.scan_data_dir()` 自动扫描入库。

## 目录结构

```
bonovel/                # 主包
  __init__.py __main__.py cli.py app.py     # 入口与主循环
  config.py errors.py utils.py              # 配置、异常、通用工具（编码检测/显示宽度）
  parser.py layout.py renderer.py themes.py keys.py stats.py library.py
  ui/                                      # 界面视图子包
    base.py shelf_view.py reader.py settings_view.py
    chapters_view.py bookmarks_view.py
tests/                  # unittest 测试（config/parser/renderer/stats）
pyproject.toml README.md AGENTS.md PROGRESS.md
```

## 架构要点

- **主循环** `app.py` → `App`：持有 `cfg`(配置) / `library`(书库) / `theme` / 视图栈，
  用 `keys.KeyParser` 读键并分发到当前 View 的 `on_key()`。退出恢复终端。
- **View 基类** `ui/base.py`：`render(screen)` 把内容写入 `renderer.Screen` 缓冲；`on_key()` 返回/跳转。
- **渲染** `renderer.py`：手写 ANSI（SGR 24bit 色、光标、整屏 `Screen` 无闪烁刷新）；`ensure_vt_enabled()` Windows 开启 VT。
- **主题** `themes.py`：`Theme` 数据类 + 内置集合；新增主题需同步更新 `config._validate` 的合法集合。
- **解析** `parser.py`：行偏移索引 + 按需 `line_text()`，支持超大文件；章节正则见 `_CHAPTER_RE`。
- **编码** `utils.py`：BOM → UTF-8 严格校验 → gbk/gb18030/big5 回退 → 乱码比例判定。
- **书库** `library.py`：`Library` 持久化 `library.json`；`scan_data_dir()` 自动入库数据目录顶层 .txt。
- **速度/进度** `stats.py`：`ReadingStats`(WPM) / `ProgressMemory`(进度百分比、序列化)。

## 键位约定（阅读界面）

`↓/→/Space/PgDn` 下一、`↑/←/PgUp` 上一、`Home/End` 首末、`p` 切换分页/滚动、
`g` 章节目录、`@` 加书签、`b` 书签列表、`c` 设置、`?` 帮助、`q/Esc` 返回、`Ctrl-C` 退出。

## 变更规范

- **提交前**：跑 `python -m unittest discover -s tests` 全绿；`git diff --cached --stat` 确认改动范围干净。
- **新增配置项**：改 `config.py` 的 `DEFAULTS` 且同步 `_validate`；必要时更新 `config_path/load/save` 测试。
- **新增主题**：`themes.py` 加 `Theme` 并加入 `_ORDER`；`config._validate` 的主题集合必须同步。
- **改动后验证**：全量测试 + 针对改动的单元测试 + 端到端冒烟（数据目录放 .txt → 启动自动入库）。
- 跨平台注意：`msvcrt`(Win) / `termios`(Unix) / `ctypes`(Win VT) 都在平台分支内**延迟 import**，
  不要在模块顶层直接 import 平台专属库；路径一律用 `pathlib.Path`。
