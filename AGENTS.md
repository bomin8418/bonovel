# AGENTS.md — 代理操作手册

> 这是代理（Codex / Claude Code / 其他 agent）每次会话开始时的第一个读入文件。
> 它定义：开始写代码前要做什么、如何工作、如何收尾。

## 项目是什么

bo-novel 是一个**终端小说阅读器**（TUI），Python 3.11 纯标准库、零第三方依赖，跨 Windows/macOS/Linux。
核心能力：.txt 导入与自动编码识别、分页/滚动阅读、章节目录、书签、进度记忆、主题、阅读速度统计。

## 启动流程（Startup Workflow）

每次会话开始，**先读、再写**，顺序如下：

1. 读 `progress.md` ——了解「当前已验证状态」与上个会话的「Next best action」。
2. 读 `feature_list.json` ——了解每个功能的状态与验证方式。
3. 读本文件剩余部分（工作规则、definition of done）。
4. 用 `standard verification path` 跑一次基线验证，确认绿色后再动手。

**标准路径**（见 progress.md）：

- 启动：`python run.py`（或 `./init.sh`）
- 验证：`python run.py --test`（等价 `python -m unittest discover -s tests -t .`）

## 目录结构

```
bo-novel/
├── AGENTS.md              # 本手册
├── run.py                 # 统一启动器：启动 + 测试（python run.py / --test）
├── init.sh                # 验证 + 启动
├── feature_list.json      # 功能清单（状态 + 验证 + 证据）
├── progress.md            # 每次会话的进度记录
├── src/                   # 生产代码 src/bonovel/
├── tests/                 # unittest 测试（留在根目录）
├── README.md / pyproject.toml / bonovel.bat / bin/bonovel   # 文档与入口脚本
└── .gitignore
```

## 架构要点

- 主循环 `src/bonovel/app.py` → `App`：持有 cfg/library/theme/视图栈，用 `keys.KeyParser` 读键分发到 View.on_key()。
- View 基类 `src/bonovel/ui/base.py`：render(screen) 写 `renderer.Screen` 缓冲；on_key() 返回/跳转。
- 渲染 `renderer.py`：手写 ANSI；`ensure_vt_enabled()` 开 Windows VT。
- 主题 `themes.py`：`Theme` + 内置集合；新增主题需同步 `config._validate`（已改为从 theme_names() 派生）。
- 解析 `parser.py`：行偏移索引 + 按需 line_text()；编码 `utils.py`（BOM→UTF-8→gbk→gb18030→big5）。
- 书库 `library.py`：library.json 持久化 + `scan_data_dir()` 启动自动入库数据目录顶层 .txt。
- 速度/进度 `stats.py`：ReadingStats(WPM) / ProgressMemory。

## 工作规则（Working Rules）

1. **一次只做一个功能**：`feature_list.json` 中同时只能有一个 `in_progress`，做完并验证、写 evidence 后才算通过。
2. **改动前跑基线**：标准验证命令要绿，否则先修 baseline 再做别的。
3. **凡声称完成必须有证据**：做了验证却无命令/输出记录，不算 done。
4. **提交前验证**：改完跑 `python run.py --test` 全绿；`git status` 确认改动范围干净。
5. **跨平台**：msvcrt/termios/ctypes 在平台分支内延迟 import，不在顶层 import；路径用 pathlib.Path。
6. **改动收尾更新文档**：更新 progress.md 的 Session Record、feature_list.json 的 status/evidence。

## Definition of Done（最重要）

一个功能/改动「完成」必须同时满足：

1. 标准启动路径能跑（`./init.sh` 或等价命令）。
2. 标准验证路径全绿（`python run.py --test`）。
3. `feature_list.json` 里该项 status 更新为 `passing` 且 evidence 有实跑命令/输出。
4. `progress.md` 更新了 Current Verified State 与 Session Record。
5. 无半成品：`git status` 干净（或改动已提交），下一会话无需手工修补即可继续。
6. 提交信息写清「做了什么 + 验证了什么」。

## 键位约定（阅读界面）

`↓/→/Space/PgDn` 下一、`↑/←/PgUp` 上一、`Home/End` 首末、`p` 分页/滚动、`g` 章节目录、`@` 加书签、`b` 书签列表、`c` 设置、`?` 帮助、`q/Esc` 返回、`Ctrl-C` 退出。

## 已知环境限制

- `pip install -e .` 在本会话沙箱被权限拦截；用 `./init.sh` 或 `python run.py` 回退。
- `python3` 在 Windows 是占位别名；脚本探测真实可用解释器。
- 终端交互无法自动化验证，用「构造 App + 直接调用视图」的冒烟脚本替代。
