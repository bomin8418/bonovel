# vscode-bonovel — bo-novel 终端阅读器插件

在 VSCode 集成终端中用 **bo-novel** 打开当前 `.txt` 小说（复用 bo-novel 自身的终端界面，零重实现）。

## 前置要求

- 已全局安装 bo-novel（任选其一）：
  - pip wheel 安装：`bonovel` 命令可用（`bonovel --version`）
  - 独立可执行文件：把 `bonovel.exe`（Windows）或 `bonovel`（POSIX）所在目录加入 PATH
- 参考项目根目录 `install_global.bat` / `install_global.sh`。

## 安装

VSCode → 扩展面板 → 右上角 `...` → **从 VSIX 安装**，选择 `dist/bonovel-0.1.0.vsix`。

## 用法

1. 打开/选中一个 `.txt` 小说文件。
2. 触发方式任选：
   - 命令面板（`Ctrl+Shift+P`）→ `bo-novel: 在终端打开当前小说`
   - 编辑器右键菜单（仅 `.txt` 显示）
   - 资源管理器右键菜单（仅 `.txt` 显示）
3. 自动新建名为 `bo-novel` 的集成终端并运行：
   `bonovel "<小说路径>" [-d <数据目录>]`

## 配置

| 设置 | 默认 | 说明 |
| --- | --- | --- |
| `bonovel.command` | `bonovel` | 全局命令名，或可执行文件完整路径。留默认值时插件会自动探测 `%LOCALAPPDATA%\bonovel\bonovel.exe`、`<系统盘>\Python311\Scripts\bonovel.exe` 等已知位置 |
| `bonovel.dataDir` | `""` | 可选，传给 `-d` 的用户数据目录（留空不传） |

## 常见问题：找不到 `bonovel` 命令

集成终端继承的是 **VSCode 进程**的环境。如果在安装/改 PATH 之后才打开 VSCode，终端仍可能找不到 `bonovel`。解决办法（任选）：

1. **完全重启 VSCode**，让集成终端继承最新的 PATH。
2. 或把 `bonovel.command` 设为完整路径，例如 `C:\python311\Scripts\bonovel.exe`（插件会直接用绝对路径，不依赖 PATH）。

