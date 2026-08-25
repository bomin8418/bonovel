# bo-novel 项目进度与交接文档

> 最后更新：2025-08-25 ｜ 维护说明：每次重大变更后更新本文件；AI 协作者优先阅读 `AGENTS.md`（协作约定）与本文件（现状交接）。

## 1. 项目概览

基于终端（TUI）的小说阅读器，Python 3.11 纯标准库实现，零第三方依赖。

- 包结构：`bonovel/`（app / parser / utils / layout / renderer / themes / keys / stats / library / config / errors / cli + `ui/` 子包）
- 入口：`python -m bonovel [小说.txt] [-d 数据目录]`；`pyproject.toml` 提供 console script `bonovel`
- 数据目录：默认 `~/.bonovel`（`library.json`、`config.json`、`bonovel.log`），可经 `-d`/`--data-dir` 或 `BONOVEL_DATA_DIR` 指定
- 测试：`python -m unittest discover -s tests`（当前 55 项，全绿）

## 2. 已完成功能（已提交 git）

| 功能 | 说明 | 提交 |
|---|---|---|
| 项目骨架 | 包结构、config、errors、CLI、pyproject.toml、README | 8a1394a |
| 导入与解析 | .txt 编码自动检测（UTF-8/GBK/GB18030/Big5、BOM）、章节检测（第X章/回/节/卷、Chapter N 等）、大文件行索引 | 8a1394a |
| 渲染层 | ANSI 渲染基元、整屏缓冲刷新、分页/滚动双模式排版、字号/行距档位、首行缩进、页码进度条 | 8a1394a |
| 主题 | 5 套内置主题：sepia / classic / dark / paper / terminal（`themes.py`） | 8a1394a |
| 键盘 | 跨平台按键归一化（Windows `msvcrt` / Unix `termios`），方向键/翻页/Ctrl 组合/resize | 8a1394a |
| 阅读核心 | 书架/阅读/章节目录/书签/设置/帮助六界面、进度记忆重启恢复、WPM 速度统计 | 8a1394a |
| 书库 | `library.json` 持久化、导入/删除/最近阅读 | 8a1394a |
| **数据目录自动扫描** | 启动时自动扫描数据目录顶层 `*.txt` 并入库，幂等；新增 `Library.scan_data_dir()`，`App.__init__` 调用 | ed77e0b |

## 3. 当前任务（已批准计划，尚未完成）

计划：「让 bo-novel 更像普通命令行工具（外观/文案伪装 + 全局可运行）」

- [ ] 子步1：`themes.py` 新增「终端命令风」主题 `plain`（白底、无彩色块、dim 强调），加入 `_THEMES`/`_ORDER` 与 `config` 合法主题集合 —— **尚未开始**
- [ ] 子步2：书架首页标题/提示文案改为命令行风格（"bonovel + type a command (...)"），交互按键不变
- [ ] 子步3：`bonovel.bat`（Windows）与 `bin/bonovel`（POSIX）全局启动脚本（免 pip install），README 补充运行方式
- [ ] 子步4：主题/配置测试、全量测试、`--version` 冒烟、`git diff` 检查

状态标记：⏳ 进行中 / ✅ 已完成 / ⬜ 未开始

## 4. 已知限制与环境事实（重要，避免重复踩坑）

1. **`pip install` 被沙箱权限拦截**：本会话中 `pip install -e .` 被判定为环境变更而被拒。`pyproject.toml` 已就位，安装需用户在目标环境手动执行：
   ```bash
   cd E:\03-aiproject\bo-novel
   python -m pip install -e .
   ```
   免安装应急：`set PYTHONPATH=%CD%`（cmd）或 `export PYTHONPATH="$PWD"`（bash）后 `python -m bonovel`。
2. **终端交互无法自动化验证**：`App.run()` 进入 raw mode 阻塞循环，自动化环境无法模拟真实按键；交互路径靠「构造 App + 直接调用视图方法」的冒烟脚本验证。
3. **测试目前 55 项**：位于 `tests/test_parser.py`、`test_renderer.py`、`test_stats.py`（含 LibraryTestCase）。
4. **`~/.bonovel` 当前无小说文件**；用户曾把小说放入数据目录期望自动出现（已由自动扫描功能解决，ed77e0b）。注意数据目录只扫顶层 `.txt`，不递归。

## 5. 常用命令

```bash
python -m unittest discover -s tests -v        # 全量测试
python -m bonovel --version                     # 版本
python -m bonovel 小说.txt                      # 导入并阅读
python -m bonovel -d /path/to/books             # 指定数据目录
python -m bonovel --help                        # CLI 帮助
```
