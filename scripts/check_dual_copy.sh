#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# 双副本同步守卫：docs/ ↔ frontend/public/ 六个文件必须逐字节一致
#
# 为什么：Cloudflare Pages 只部署 frontend/public/。任一副本落单会让线上
#   · benchmark_data.json 缺失 → 离线兜底退化为 4 条内置数据
#   · ai_knowledge_base.json 缺失 → admin 未登录时知识库面板读到旧规则集
#   · tool/m/admin.html 不一致 → 电脑端/手机端/管理端行为分叉且难排查
#
# 用法：scripts/check_dual_copy.sh
#   全一致 exit 0；有差异逐个列出并 exit 1
# ══════════════════════════════════════════════════════════════════
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILES=(tool.html m.html admin.html benchmark_data.json waste_rates.json ai_knowledge_base.json)

fail=0
for f in "${FILES[@]}"; do
  a="$ROOT/docs/$f"
  b="$ROOT/frontend/public/$f"
  if [ ! -f "$a" ] || [ ! -f "$b" ]; then
    echo "❌ $f — 缺文件（docs 或 frontend/public）"
    fail=1
    continue
  fi
  if diff -q "$a" "$b" >/dev/null 2>&1; then
    echo "✅ $f"
  else
    echo "❌ $f — 双副本不一致"
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo
  echo "修复：cp docs/<file> frontend/public/<file>（或反向），改完重跑本脚本"
  exit 1
fi

echo
echo "双副本 6/6 一致"
