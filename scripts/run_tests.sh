#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# 一键全量回归：双副本守卫 + 5 套 JS 沙箱 + 后端 pytest
#
# 用法：scripts/run_tests.sh
#   任一项失败即整体 exit 1，末尾汇总失败项；全绿输出汇总行。
#
# 说明：
#   · JS 沙箱（docs/superpowers/tests/*.js）node 直跑，失败时自会 exit 1
#   · pytest 解释器按 venv311 → venv → python3 探测，要求能 import
#     fastapi/openpyxl/pytest（缺依赖报失败而不是静默跳过）
# ══════════════════════════════════════════════════════════════════
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=()
js_ok=0

# ── 1. 双副本同步守卫 ──
echo "── 双副本同步"
if "$ROOT/scripts/check_dual_copy.sh" >"$TMP/dual.log" 2>&1; then
  echo "✅ 双副本 6/6 一致"
else
  echo "❌ 双副本不一致："
  sed 's/^/   /' "$TMP/dual.log"
  fail+=("双副本")
fi

# ── 2. JS 沙箱回归 ──
echo
echo "── JS 沙箱（docs/superpowers/tests/*.js）"
if command -v node >/dev/null 2>&1; then
  for f in "$ROOT"/docs/superpowers/tests/*.js; do
    name="$(basename "$f")"
    if out="$(node "$f" 2>&1)"; then
      echo "✅ $name — $(echo "$out" | grep -E '结果|通过 [0-9]+ /|两端一致' | tail -1 | sed 's/^ *//')"
      js_ok=$((js_ok + 1))
    else
      echo "❌ $name"
      echo "$out" | tail -15 | sed 's/^/   /'
      fail+=("JS:$name")
    fi
  done
else
  echo "❌ 未找到 node（JS 沙箱无法运行）"
  fail+=("node")
fi

# ── 3. 后端 pytest ──
echo
echo "── 后端 pytest"
PY=""
for cand in "$ROOT/backend/venv311/bin/python" "$ROOT/backend/venv/bin/python" "$(command -v python3)"; do
  if [ -n "$cand" ] && [ -x "$cand" ] && "$cand" -c "import fastapi, openpyxl, pytest" >/dev/null 2>&1; then
    PY="$cand"
    break
  fi
done
if [ -n "$PY" ]; then
  if out="$(cd "$ROOT/backend" && "$PY" -m pytest tests -q 2>&1)"; then
    echo "✅ pytest — $(echo "$out" | grep -E 'passed|failed' | tail -1 | sed 's/^ *//')  [$PY]"
  else
    echo "❌ pytest"
    echo "$out" | tail -25 | sed 's/^/   /'
    fail+=("pytest")
  fi
else
  echo "❌ 未找到含 fastapi/openpyxl/pytest 的 python（backend/venv311 / venv / python3 均不可用）"
  fail+=("pytest 未执行")
fi

# ── 汇总 ──
echo
if [ "${#fail[@]}" -eq 0 ]; then
  echo "════ 全量回归通过：双副本 6/6 + JS ${js_ok} 套 + pytest ════"
  exit 0
fi
echo "════ 失败 ${#fail[@]} 项：${fail[*]} ════"
exit 1
