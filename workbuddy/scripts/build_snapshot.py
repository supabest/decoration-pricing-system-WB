"""重建加密快照 —— 把辅材信息价与辅材清单项并入同一密文

用法（在技能根目录）：
    .venv/bin/python scripts/build_snapshot.py

数据来源（均只读，不改动原项目）：
    - 基准价/损耗率：仓库 backend/app/data/benchmark_snapshot.enc（或当前技能副本）
    - 辅材信息价：仓库 data/seeds/seed_material_prices.sql
    - 辅材清单项：仓库 data/seeds/aux_excel_items.json

仓库根目录默认按本文件位置向上两级推导（workbuddy/ 位于仓库根下）；
也可用环境变量 DECORATION_PRICING_REPO 显式覆盖，便于在技能安装目录运行。

密文写回 data/benchmark_snapshot.enc；密钥来自 .env，绝不写进产物。
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import snapshot

REPO = Path(
    os.environ.get("DECORATION_PRICING_REPO")
    or Path(__file__).resolve().parents[2]
).expanduser()
REPO_SNAPSHOT = REPO / "backend" / "app" / "data" / "benchmark_snapshot.enc"
SEED_SQL = REPO / "data" / "seeds" / "seed_material_prices.sql"
SEED_AUX = REPO / "data" / "seeds" / "aux_excel_items.json"

INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+public\.material_prices\s*"
    r"\(name,\s*unit,\s*price,\s*effective_month,\s*source\)\s*VALUES\s*"
    r"\('([^']*)',\s*'([^']*)',\s*([\d.]+),\s*'([^']*)',\s*'([^']*)'\)",
    re.IGNORECASE,
)


def parse_material_prices(sql_text: str) -> dict:
    """按 name 取最新生效月的价格，等价于远端 loadMaterialPrices() 的取数口径。"""
    latest: dict = {}
    for name, unit, price, month, source in INSERT_RE.findall(sql_text):
        rec = {
            "price": float(price),
            "unit": unit,
            "effective_month": month,
            "source": source,
        }
        old = latest.get(name)
        if old is None or month > old["effective_month"]:
            latest[name] = rec
    return latest


def base_payload() -> dict:
    src = REPO_SNAPSHOT if REPO_SNAPSHOT.exists() else snapshot.DEFAULT_SNAPSHOT
    data = snapshot.load_snapshot(src)
    if not data.get("benchmark_items"):
        raise RuntimeError(f"基础快照不可用或无权限解密: {src}")
    return data


def build() -> dict:
    payload = base_payload()
    payload["material_prices"] = parse_material_prices(SEED_SQL.read_text(encoding="utf-8"))
    payload["aux_excel_items"] = json.loads(SEED_AUX.read_text(encoding="utf-8"))
    payload["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return payload


def main() -> int:
    payload = build()
    blob = snapshot.seal_json(payload)
    out = snapshot.DEFAULT_SNAPSHOT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    s = snapshot.stats(payload)
    print(f"[build_snapshot] 写入 {out} ({len(blob)} 字符)")
    for k, v in s.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
