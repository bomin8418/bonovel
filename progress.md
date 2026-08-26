# progress.md — 项目进度日志

> 每次会话都从这里读起，每个会话结尾都更新这里的 Session Record。

## Current Verified State

- **Repository root**：`E:\03-aiproject\bo-novel`
- **Standard startup path**：`python run.py`（或 `./init.sh`）
- **Standard verification path**：`python run.py --test`（等价 `python -m unittest discover -s tests -t .`；当前 75 项，全绿）
- **Highest priority unfinished feature**：无（核心功能已全部完成；后续可按 feature_list.json 中的 `planned` 项扩展）
- **Current blocker**：无

## Session Record

### 会话：打包全局安装包（wheel + exe）+ VSCode 终端启动器插件 — 已完成

- **Goal**：产出可全局安装的安装包与 VSCode 插件
- **Completed**：
  - pip wheel：`C:\Python311\python.exe -m pip wheel . -w dist --no-deps` → `dist/bo_novel-0.1.0-py3-none-any.whl`；全局安装到 `C:\Python311\Scripts\bonovel.exe`
  - PyInstaller exe：`pyinstaller --onefile --console --name bonovel --paths src --collect-submodules bonovel packaging/pyinstaller_entry.py` → `dist/bonovel.exe`（warn 文件无缺失 bonovel.ui.* 模块）
  - `install_global.bat`（wheel/exe 双模式，PowerShell 改用户级 PATH，纯 ASCII 防编码问题）与 `install_global.sh`（POSIX pip --user）
  - VSCode 插件 `extensions/vscode-bonovel/`（命令 bonovel.open、右键菜单仅 .txt、配置 command/dataDir）；vsce 打包 → `dist/bonovel-0.1.0.vsix`
- **Verification run**：`bonovel --version`（wheel 与 exe 两路径）→ bo-novel 0.1.0；install_global.bat 两模式实跑并把命令目录加入用户 PATH；.vsix 打包成功（3.54KB）；`python run.py --test` 全绿
- **Evidence recorded**：见 dist/ 产物、install_global.bat/.sh、extensions/vscode-bonovel/
- **Commits**：待提交
- **Known risks**：exe 仅本平台可构建；.bat 必须保持 ASCII（cmd 用 ANSI 码页读 .bat）
- **Next best action**：无

### 会话：分页缩进改为「段首缩进 · 续行顶格」— 已完成

- **Goal**：修复正文"第一行顶格、之后全部缩进"的不一致观感
- **Root cause**：`_build_pages` 按"每页首行不缩进、其余全缩进"处理（first_row_of_page 特例），页内段落首行与续行无法区分，每翻一页首行顶格显得突兀
- **Completed**：`layout.py` 去掉 `first_row_of_page`，改为每个逻辑行（段落）仅首行加 `INDENT`，续行顶格；页面在逻辑行间断开故页首恒为段落首行，全篇一致；滚动模式本就统一缩进不受影响
- **Verification run**：`python run.py --test` → 82 项 OK（新增 2 项段首缩进测试）；冒烟：60 字段落折 4 行（首行 INDENT + 3 行 flush）、两段各自首行缩进
- **Evidence recorded**：见 tests/test_renderer.py::LayoutPageTestCase；冒烟输出见上
- **Commits**：待提交
- **Known risks**：章标题行（书内文本行）也按段落首行缩进处理；超大段落超一屏时仍有既有分页溢出问题（非本次范围）
- **Next best action**：无

### 会话：迁移旧默认主题 plain → plain-dark（自动升级）— 已完成

- **Goal**：修复暗色模式下已保存 config.json（theme:plain 白底）仍然刺眼的问题
- **Root cause**：上一轮仅改新默认值，本机 `~/.bonovel/config.json` 仍存着旧默认 `plain`（白底），加载时不会自动变暗
- **Completed**：`config` 新增内部字段 `theme_source`（auto/manual，auto=未手动改过）；`load_config` 中若 theme 为旧默认 plain 且 source 为 auto 则迁移为 plain-dark（仅内存、幂等）；`settings_view` 切主题时置 source=manual 标记手动选择不受迁移影响；`_validate` 校验 source 取值
- **Verification run**：`python run.py --test` → 80 项 OK（新增 2 项迁移测试 + 更新 test_stats 手动 plain 用例）；冒烟：本机旧配置 load 后 theme=plain-dark，手动 plain 保留
- **Evidence recorded**：见 tests/test_config.py 迁移两项 + tests/test_stats.py
- **Commits**：待提交
- **Known risks**：历史未手动选过的 plain 配置一律迁移（无法区分旧自动写入与早期手动选择）；此后用户切换主题即打上 manual 标记，不再误迁移
- **Next best action**：无

### 会话：修复大写按键（C/P/G/B/Q 等）无响应 — 已完成

- **Goal**：修复按提示大写 `C` 打开设置无反应（及 P/G/B/Q/I/D 同理）
- **Root cause**：页脚/帮助提示用大写字母，但各视图 `on_key` 只匹配小写；`Shift+C` 经 KeyParser 得到 `('C','C')`，无分支命中而静默失效
- **Completed**：`App._dispatch` 开头对 `key` 统一 `lower()` 归一化（text 保留原样），一处覆盖所有视图；特殊键/控制键本就小写不受影响；ImportView 用 text 追加路径不受影响
- **Verification run**：`python run.py --test` → 78 项 OK（新增 tests/test_app.py::AppDispatchTestCase 3 项）；冒烟：大写 C→SettingsView、大写 P→模式切换为 scroll
- **Evidence recorded**：见 tests/test_app.py；冒烟输出见上
- **Commits**：待提交
- **Known risks**：无
- **Next best action**：无

### 会话：默认主题改为暗色单色（plain-dark）— 已完成

- **Goal**：修复暗色编辑器终端下默认主题白底刺眼的问题
- **Completed**：新增 `plain-dark`（命令行·单色暗，全灰阶暗底）主题并设为默认（themes.py + config.DEFAULTS）；`plain`（白底）保留供亮色环境；测试断言同步（test_default_is_plain_dark / config 默认值）
- **Verification run**：`python run.py --test` → 75 项 OK
- **Evidence recorded**：default_theme() 返回 plain-dark；theme_names() 含 plain-dark；字段完整
- **Commits**：待提交
- **Known risks**：已有 config.json 存了旧主题的用户不自动生效（需在设置改主题或删 config.json），符合"仅改默认值"约定
- **Next best action**：无

### 会话：修复退格键空路径无效操作 — 已完成

- **Goal**：验证并修复 `ImportView.on_key` 退格键在 `self.path` 为空时执行 `self.path[:-1]` 的无效操作
- **Verification**：确认 `ui/import_view.py` L50 存在该写法；空字符串 `""[:-1]` 得 `""`，不报错、无副作用（纯无效操作），问题属实但零影响
- **Fixed**：L50 加守卫 `if self.path: self.path = self.path[:-1]`
- **Verification run**：`python -m unittest discover -s tests -t .` → 75 项 OK
- **Commits**：待提交
- **Next best action**：无

### 会话：交互导入（路径输入框）+ 启动自动导入 + 宽字符输入修复 — 已完成

- **Goal**：修复书架按 `i` 导入失败（原实现仅在命令行传参后按 i 才有效，无交互导入手段）
- **Completed**：
  - 新增 `ui/import_view.py`：按 `i` 打开路径输入框，输入 .txt 路径（含中文文件名）回车导入，Esc/Backspace 支持，失败/取消回书架刷新
  - 启动自动导入：`python run.py 小说.txt` 启动即导入并进入阅读，不再需要手动按 i（app.run 先 enter_import 再 open_shelf）
  - `keys.KeyParser` 宽字符修复：`byte>0xFF` 直接返回整码（Windows msvcrt 中文输入）；Unix 下 `>=0x80` 累积 UTF-8 多字节再解码，解决此前中文输入截断/乱码
- **Verification run**：`python run.py --test` → 75 项 OK（新增 3 项宽字符键解析 + 6 项 ImportFlowTestCase）；冒烟：书架→i→输入路径→回车→进入 ReaderView；Windows 模拟中文路径输入码点正确
- **Evidence recorded**：见 tests/test_renderer.py::KeyParserTestCase 与 tests/test_import.py
- **Commits**：待提交
- **Known risks**：Unix 下非 UTF-8 字节输入可能被当作无效 UTF-8 丢弃；路径含空格需手动输入（未做补齐）
- **Next best action**：无

### 会话：优化视图切换/重排延迟（排版折行缓存 + 复用 layouter）— 已完成

- **Goal**：修复进入帮助/设置/章节目录后退出偶发明显卡顿（用户重复按键导致双重跳转）
- **Root cause**：退出设置强制 `resize()→_reflow()` 全量重建所有页（`_build_pages` 逐行解码 + 折行两次 + 逐字符 `unicodedata` 宽度计算）。实测 50k 行重建约 7.9s。
- **Completed**：`layout.py` 新增 `_char_width` 缓存、`_wrap` 列表累积 + ASCII 快径、`_build_pages` 每行只折行一次并按宽度缓存 `_rows`；新增 `reflow()`（参数未变直接返回、宽度未变只重排不复折）。`reader.py` 的 `_reflow()` 改为首次创建、之后复用 layouter。
- **Verification run**：`python run.py --test` → 66 项 OK（新增 4 项 LayoutReflowTestCase）；50k 行基准：首次构建 7.9→1.7s、无变化 reflow ~0s、字号/行数 reflow 0.07-0.11s；ReaderView 冒烟同尺寸 resize ~0s。
- **Evidence recorded**：见 tests/test_renderer.py::LayoutReflowTestCase；基准/冒烟输出见上。
- **Commits**：待提交
- **Known risks**：宽度变化（终端 resize）仍会全量重折行（50k 行约 1.9s），属可接受偶发。
- **Next best action**：无

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
