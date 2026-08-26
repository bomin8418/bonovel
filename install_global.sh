#!/usr/bin/env sh
# install_global.sh — 全局安装 bo-novel（macOS / Linux；Windows 下自动委托 install_global.bat）
# 用法：./install_global.sh [wheel|exe]
#   wheel（默认）：优先 pip install --user；无带 pip 的 Python 时回退为免 pip 启动器
#   exe          ：把当前平台已构建的 dist/bonovel 复制到 ~/.local/bin
set -e

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

# --- Windows（Git Bash / MSYS / MinGW / Cygwin）：委托 install_global.bat ---
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if command -v cygpath >/dev/null 2>&1; then
      BAT="$(cygpath -w "$ROOT/install_global.bat")"
    else
      BAT="$ROOT/install_global.bat"
    fi
    echo "[install] 检测到 Windows 环境，委托：cmd //c \"$BAT\" $*"
    exec cmd //c "$BAT" "$@"
    ;;
esac

MODE="${1:-wheel}"

if [ "$MODE" = "exe" ]; then
  mkdir -p "$HOME/.local/bin"
  if [ ! -f "$ROOT/dist/bonovel" ]; then
    echo "[install] 未找到 dist/bonovel，请先在本平台运行 PyInstaller 构建。"
    exit 1
  fi
  cp "$ROOT/dist/bonovel" "$HOME/.local/bin/bonovel"
  chmod +x "$HOME/.local/bin/bonovel"
  echo "[install] 已安装到 $HOME/.local/bin/bonovel"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) echo "[install] 提示：请把 ~/.local/bin 加入 PATH 后重开终端。" ;;
  esac
  echo "[install] 验证：bonovel --version"
  exit 0
fi

# --- wheel 模式 ---
# 探测带 pip 的 python3/python；都不可用则回退为免 pip 启动器（bin/bonovel）
PIP_PY=""
for PY in python3 python; do
  if command -v "$PY" >/dev/null 2>&1 && "$PY" -m pip --version >/dev/null 2>&1; then
    PIP_PY="$PY"
    break
  fi
done
if [ -n "$PIP_PY" ]; then
  "$PIP_PY" -m pip install --user "$ROOT"
  echo "[install] 已通过 pip --user 安装：bonovel"
  echo "[install] 验证：bonovel --version"
  exit 0
fi

# 免 pip 回退：把 bin/bonovel 启动器复制到 ~/.local/bin
mkdir -p "$HOME/.local/bin"
cp "$ROOT/bin/bonovel" "$HOME/.local/bin/bonovel"
chmod +x "$HOME/.local/bin/bonovel"
echo "[install] 未找到带 pip 的 Python，已回退为免 pip 启动器：$HOME/.local/bin/bonovel"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "[install] 提示：请把 ~/.local/bin 加入 PATH 后重开终端。" ;;
esac
echo "[install] 验证：$HOME/.local/bin/bonovel --version"
