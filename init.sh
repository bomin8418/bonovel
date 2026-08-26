#!/usr/bin/env sh
# init.sh — 启动脚本：安装依赖 + 验证 + 打印启动命令（一步到位）。
# 用法：./init.sh            # 安装 + 验证 + 打印启动命令
#       RUN_START_COMMAND=1 ./init.sh   # 验证后直接启动

# --- 三个可配置变量（按项目实际情况修改） ---
INSTALL_CMD='echo "bo-novel 零第三方依赖，跳过安装"'   # 依赖安装命令（本项无依赖）
VERIFY_CMD='python run.py --test'                      # 基础验证命令
START_CMD='python run.py'                              # 启动命令

set -e

echo "[init.sh] 当前目录: $(pwd)"

echo "[init.sh] 安装依赖..."
eval "$INSTALL_CMD"

echo "[init.sh] 运行验证..."
eval "$VERIFY_CMD"

echo "[init.sh] 验证通过。启动命令:"
echo "    $START_CMD"

if [ "${RUN_START_COMMAND:-0}" = "1" ]; then
  echo "[init.sh] 正在启动..."
  exec sh -c "$START_CMD"
fi
