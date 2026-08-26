#!/usr/bin/env sh
# install_global.sh — 全局安装 bo-novel（POSIX：macOS / Linux）
# 用法：./install_global.sh [wheel|exe]
#   wheel（默认）：pip install --user（从源码构建安装），命令为 bonovel
#   exe          ：把当前平台已构建的 dist/bonovel 复制到 ~/.local/bin
set -e

MODE="${1:-wheel}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

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
else
  # 探测可用的 python3/python（绕开 Windows 的 python3 占位别名）
  for PY in python3 python; do
    if command -v "$PY" >/dev/null 2>&1 && "$PY" -c "import sys" >/dev/null 2>&1; then
      "$PY" -m pip install --user "$ROOT"
      echo "[install] 已通过 pip --user 安装：bonovel"
      break
    fi
  done
fi
echo "[install] 验证：bonovel --version"
