#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# 双副本同步守卫：docs/ ↔ frontend/public/ 四个文件必须逐字节一致
#
# 为什么：Cloudflare Pages 只部署 frontend/public/。任一副本落单会让线上
#   · ai_knowledge_base.json 缺失 → admin 未登录时知识库面板读到旧规则集
#   · tool/m/admin.html 不一致 → 电脑端/手机端/管理端行为分叉且难排查
#
# 不再纳管 benchmark_data.json / waste_rates.json：价表已退出公网，线上兜底改走
#   登录态的 GET /api/v1/benchmark/snapshot（密文快照在后端解密），docs 下这两份
#   明文只留本机开发用，已进 .gitignore。
#
# 用法：scripts/check_dual_copy.sh
#   全一致 exit 0；有差异逐个列出并 exit 1
# ══════════════════════════════════════════════════════════════════
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILES=(tool.html m.html admin.html ai_knowledge_base.json)

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
echo "双副本 ${#FILES[@]}/${#FILES[@]} 一致"
