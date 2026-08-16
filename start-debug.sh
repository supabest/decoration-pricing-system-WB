#!/bin/bash
# 一键启动装修成本系统「本地调试后端」（DEBUG_PRICING 已开）
# 用法: bash start-debug.sh   （或在 Claude Code 里输入 /debug-pricing）
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
cd "$BACKEND_DIR"

if nc -z localhost 8000 2>/dev/null; then
  echo "✅ 后端已在运行 (localhost:8000)"
else
  nohup venv311/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    > /tmp/debug-backend.log 2>&1 &
  echo "🚀 后端已后台启动 (PID $!)，日志: /tmp/debug-backend.log"
fi

echo "🔍 调试日志页: http://localhost:8000/api/v1/pricing/debug-logs?format=html"
