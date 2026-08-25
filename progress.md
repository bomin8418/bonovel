# progress.md — 项目进度日志

> 每次会话都从这里读起，每个会话结尾都更新这里的 Session Record。

## Current Verified State

- **Repository root**：`E:\03-aiproject\bo-novel`
- **Standard startup path**：`PYTHONPATH=src python -m bonovel`（或 `./init.sh`）
- **Standard verification path**：`python -m unittest discover -s tests -t .`（当前 56 项，全绿）
- **Highest priority unfinished feature**：无（核心功能已全部完成；后续可按 feature_list.json 中的 `planned` 项扩展）
- **Current blocker**：无

## Session Record

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
