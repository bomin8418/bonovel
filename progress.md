# progress.md — 项目进度日志

> 每次会话都从这里读起，每个会话结尾都更新这里的 Session Record。

## Current Verified State

- **Repository root**：`E:\03-aiproject\bo-novel`
- **Standard startup path**：`python run.py`（或 `./init.sh`）
- **Standard verification path**：`python run.py --test`（等价 `python -m unittest discover -s tests -t .`；当前 62 项，全绿）
- **Highest priority unfinished feature**：无（核心功能已全部完成；后续可按 feature_list.json 中的 `planned` 项扩展）
- **Current blocker**：无

## Session Record

### 会话：统一启动/测试入口（run.py + 脚本瘦身）— 已完成

- **Goal**：简化启动与测试流程，全平台一条命令搞定
- **Completed**：新增根目录 `run.py` 统一启动器（`python run.py` 启动、`python run.py --test` 跑测试，透传其余 CLI 参数）；`init.sh`/`bonovel.bat`/`bin/bonovel` 全部瘦身委托 run.py；README/AGENTS.md 标准路径同步为 `python run.py` / `python run.py --test`
- **Verification run**：`python run.py --test` → 62 项 OK；`python run.py --version` → bo-novel 0.1.0；旧命令 `python -m unittest discover -s tests -t .` 回归仍绿
- **Evidence recorded**：run.py 实跑输出见上；README/AGENTS.md/脚本已读确证
- **Commits**：待提交
- **Known risks**：无
- **Next best action**：无

### 会话：修复 keys.py 缺少 List 类型导入 — 已完成

- **Goal**：验证并修复 `src/bonovel/keys.py` 使用 `List[int]` 但未导入 `List` 的问题
- **Verification**：确认 L220 `self._pending: List[int] = []` 存在且 `typing` 仅导入了 `Optional, Tuple`；实测 `_make_raw_input()` 正常实例化，**无运行时错误**（`from __future__ import annotations` 使注解惰性化，且函数体内局部变量注解本就不求值），问题属于静态分析级缺陷（mypy/pyright 会报 `List` 未定义）。
- **Fixed**：第 10 行改为 `from typing import List, Optional, Tuple`
- **Verification run**：`python -m unittest discover -s tests -t .` → 62 项 OK；`py_compile src/bonovel/keys.py` OK
- **Commits**：待提交
- **Next best action**：无

### 会话：修复 Windows 翻页/方向键失效 — 已完成

- **Goal**：修复 Windows 下翻页功能无法使用（方向键、PgUp/PgDn、Home/End 不响应）
- **Root cause**：`keys._WinInput.read_byte()` 将 msvcrt 扩展键（`\xe0`/`\x00` 前缀 + 扫描码）原样传给 `KeyParser`，`\xe0` 被当作宽字符、`\x00` 被当作 RESIZE，方向键/翻页键永不转成逻辑键。
- **Completed**：新增 `_WIN_EXT_KEY_SEQ` 扫描码→ANSI 序列表与 `_win_ext_key_sequence()`；`_WinInput` 缓冲并逐字节吐出转义序列，未知扩展键回退为扫描码字符；保留代理对逻辑。`\x00` 不再泄漏为误触发 RESIZE。
- **Verification run**：`python -m unittest discover -s tests -t .` → 62 项 OK（新增 6 项 WinExtKeyTestCase）；模拟 msvcrt 冒烟输出 down/up/pagedown/left/right/ctrl-c。
- **Evidence recorded**：见 tests/test_renderer.py::WinExtKeyTestCase；smoke 脚本实测 `_WinInput` 翻译正确。
- **Commits**：待提交
- **Known risks**：F1–F4 翻译为 `\x1bOP` 等，解析器未定义 F 键（返回 unknown），不影响阅读功能。
- **Next best action**：无

### 会话：终端命令风改造（theme/plain + 首页伪装 + 全局脚本）— 已完成

- **Goal**：新增 plain（命令行·单色）主题、书架首页伪装成命令行工具、免 pip 全局启动脚本
- **Completed**：plain 主题（themes.py + config 校验联动）、书架首页命令行风文案、`bonovel.bat` / `bin/bonovel` 全局脚本、README 更新
- **Verification run**：`python -m unittest discover -s tests` → 56 项 OK
- **Evidence recorded**：提交 `19a4425`；README/themes.py/shelf_view.py 已读确证
- **Commits**：`19a4425`、`ae19136`、`ed77e0b`、`8a1394a`
- **Known risks**：POSIX 脚本需绕开 Windows `python3` 占位别名（已用解释器探测处理）
- **Next best action**：无

### 会话：按模板指南重构目录（src 布局 + harness 文件）— 进行中

- **Goal**：按 walkinglabs 模板建立 AGENTS.md/init.sh/progress.md/feature_list.json，代码迁入 src/
- **Completed**：`git mv bonovel src/bonovel`；pyproject/启动脚本/tests 注入 src；init.sh 与 feature_list.json 已建
- **Verification run**：待最终 `./init.sh` 冒烟与提交
- **Evidence recorded**：56 项测试在 src 布局下 `python -m unittest discover -s tests -t .` 全绿
- **Commits**：待提交
- **Known risks**：`pip install` 在沙箱被拦截（已用 init.sh/PYTHONPATH 回退）
- **Next best action**：完成 AGENTS.md 重写、README/.gitignore 更新、小说数据迁移，最终提交
