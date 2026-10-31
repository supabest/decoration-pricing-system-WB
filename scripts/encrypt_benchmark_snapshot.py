#!/usr/bin/env python3
"""生成/校验基准价加密快照 backend/app/data/benchmark_snapshot.enc

用法（用 backend 的 venv，脚本要 import app.services.benchmark_snapshot）：

  python scripts/encrypt_benchmark_snapshot.py --gen-key     # 生成一把密钥
  python scripts/encrypt_benchmark_snapshot.py               # 加密 docs/ 下两份 JSON → .enc
  python scripts/encrypt_benchmark_snapshot.py --verify      # 用当前密钥解密，只报条数

密钥来源优先级：--key > 环境变量 BENCHMARK_SNAPSHOT_KEY > backend/.env。
.enc 要提交进仓库（它不含明文），密钥要配到 Render 环境变量和本机 backend/.env。
"""
import argparse, os, re, secrets, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

SRC_ITEMS = os.path.join(ROOT, "docs", "benchmark_data.json")
SRC_WASTE = os.path.join(ROOT, "docs", "waste_rates.json")


def read_key_from_env_file() -> str:
    p = os.path.join(ROOT, "backend", ".env")
    try:
        with open(p) as f:
            m = re.search(r"^BENCHMARK_SNAPSHOT_KEY=(.+)$", f.read(), re.M)
        return m.group(1).strip() if m else ""
    except FileNotFoundError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="生成基准价加密快照")
    ap.add_argument("--key", default="", help="快照密钥（hex64 或 base64）")
    ap.add_argument("--gen-key", action="store_true", help="生成一把新密钥后退出")
    ap.add_argument("--verify", action="store_true", help="解密现有快照并报告条数")
    args = ap.parse_args()

    if args.gen_key:
        print("BENCHMARK_SNAPSHOT_KEY=" + secrets.token_hex(32))
        print("# 配到 Render 环境变量与本机 backend/.env，不要提交")
        return 0

    key = args.key or os.environ.get("BENCHMARK_SNAPSHOT_KEY", "") or read_key_from_env_file()
    if not key:
        print("❌ 未找到密钥：--key / 环境变量 BENCHMARK_SNAPSHOT_KEY / backend/.env 三者其一")
        return 1

    from app.core.config import settings
    from app.services.benchmark_snapshot import SNAPSHOT_PATH, seal_json, unseal_text

    settings.BENCHMARK_SNAPSHOT_KEY = key

    if args.verify:
        try:
            with open(SNAPSHOT_PATH) as f:
                snap = unseal_text(f.read())
        except FileNotFoundError:
            print(f"❌ 快照不存在：{SNAPSHOT_PATH}")
            return 1
        except Exception as e:
            print(f"❌ 解密失败（密钥不匹配或文件损坏）：{type(e).__name__}: {e}")
            return 1
        print(f"✅ 可解密：{len(snap.get('benchmark_items') or [])} 条基准价，"
              f"{len(snap.get('waste_rates') or {})} 条损耗率，生成于 {snap.get('generated_at', '未知')}")
        return 0

    import json
    from datetime import datetime, timezone

    for src in (SRC_ITEMS, SRC_WASTE):
        if not os.path.exists(src):
            print(f"❌ 源文件不存在：{src}")
            return 1
    with open(SRC_ITEMS) as f:
        items = json.load(f)
    with open(SRC_WASTE) as f:
        waste = json.load(f)

    payload = {
        "benchmark_items": items,
        "waste_rates": waste,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    blob = seal_json(payload)

    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(SNAPSHOT_PATH, "w") as f:
        f.write(blob)
    print(f"✅ 已加密 {len(items)} 条基准价 + {len(waste)} 条损耗率")
    print(f"   → {SNAPSHOT_PATH}（{len(blob)} 字节密文，可提交）")
    print("   下一步：把 BENCHMARK_SNAPSHOT_KEY 配到 Render 环境变量，否则线上解不开")
    return 0


if __name__ == "__main__":
    sys.exit(main())
