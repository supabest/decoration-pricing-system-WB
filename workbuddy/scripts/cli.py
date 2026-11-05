"""统一入口

    python cli.py prepare <清单.xlsx> -o candidates.json      # 生成候选（不含价格）
    python cli.py apply candidates.json -o 结果.xlsx [--decisions d.json] [--auto]
    python cli.py stats                                       # 快照统计

保密设计：prepare 产出的候选只含编号/名称/规格/单位，不含任何价格字段；
价格只在 apply 阶段从本地解密快照里读取，不进入模型上下文。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import aux_rules
import export_xlsx
import ingest
import price
import retrieve
import snapshot

TOP_N = 40


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _aux_cost(item, price_lib=None) -> float:
    """单子目辅材费；price_lib 缺省时从快照取信息价（带缓存）。"""
    if price_lib is None:
        price_lib = _default_price_lib()
    return aux_rules.aux_cost(item, price_lib)


@lru_cache(maxsize=1)
def _default_price_lib() -> dict:
    return snapshot.load_snapshot().get("material_prices") or {}


def cmd_prepare(args) -> int:
    rows = ingest.parse_boq(args.boq)
    items = snapshot.load_snapshot()["benchmark_items"]
    out = {"source": str(args.boq), "generated_at": _now(), "rows": []}
    for i, r in enumerate(rows, start=1):
        cands = retrieve.build_candidates(r["name"], r["spec"], r["unit"], items)[:TOP_N]
        out["rows"].append({
            "row_id": i,
            "sheet": r["sheet"],
            "section": r["section"],
            "name": r["name"],
            "spec": r["spec"],
            "unit": r["unit"],
            "qty": r["qty"],
            "candidates": [{
                "code": c["internal_code"],
                "team": c["trade_team"],
                "item_name": c["item_name"],
                "spec": c.get("spec", ""),
                "unit": c["unit"],
            } for c in cands],
        })
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[prepare] {len(out['rows'])} 行 → {args.out}")
    return 0


def _num(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _picks(row, decision, auto):
    """行 → [(编号, 班组, 子目自带参数), ...]。

    decisions 支持两种写法：
      单子目：{"code": "NS-017", "team": "泥水班组"}
      多子目：{"subs": [{"code": ..., "team": ..., "coef": 1.0}, ...]}
    无决策时 --auto 取候选第一名。
    """
    if decision and decision.get("subs"):
        return [(s.get("code", ""), s.get("team", ""), s)
                for s in decision["subs"] if s.get("code")]
    if decision and decision.get("code"):
        return [(decision["code"], decision.get("team", ""), {})]
    if auto and row["candidates"]:
        top = row["candidates"][0]
        return [(top["code"], top["team"], {})]
    return []


def _build_subs(picks, override, waste_rates, index, price_lib):
    """对齐远端 rowUnitPrice / rowMatCost / computeAuxForRow 口径。

    人工 = Σ(子目单价 × coef × conv)      [effPrice，globalCoef 默认 1]
    主材 = Σ(主材价 × (1+损耗率/100) × coef × conv)
    辅材 = Σ 各子目辅材费（不乘 coef/conv）
    """
    subs, aux_total, hit = [], 0.0, []
    for code, team, extra in picks:
        item = index.get((code, team))
        if not item:
            continue

        def param(name, default):
            # 远端口径：行级参数只是暂存区，子目级显式值优先
            if name in extra:
                return extra[name]
            if name in override:
                return override[name]
            return default

        subs.append({
            "unit_price": _num(item.get("unit_price")),
            "coef": _num(param("coef", 1.0), 1.0),
            "conv": _num(param("conv", 1.0), 1.0),
            "mat_price": _num(param("mat_price", 0.0)),
            "waste_rate": _num(param("waste_rate", waste_rates.get(code, 0))),
        })
        aux_total += _aux_cost(item, price_lib)
        hit.append((code, team))
    return subs, aux_total, hit


def cmd_apply(args) -> int:
    data = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8")) if args.decisions else {}
    overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8")) if args.overrides else {}

    snap = snapshot.load_snapshot()
    index = {retrieve.identify(i): i for i in snap["benchmark_items"]}
    waste_rates = snap.get("waste_rates") or {}
    price_lib = snap.get("material_prices") or {}

    out_rows = []
    matched = 0
    for row in data["rows"]:
        rid = str(row["row_id"])
        d = decisions.get(rid)
        picks = _picks(row, d, args.auto)
        subs, aux_cost, hit = _build_subs(picks, overrides.get(rid, {}),
                                          waste_rates, index, price_lib)
        if hit:
            matched += 1

        base = {"subs": subs, "aux_cost": aux_cost, "qty": row["qty"]}
        b = price.breakdown(base)
        # 主材单价 = Σ(净料价 × coef × conv)，与远端 effRowMatPrice 同基；
        # 等效损耗率由「主材费 ÷ 主材单价 − 1」反推并取整，避免长小数写进 Excel
        mat_base = sum(s["mat_price"] * s["coef"] * s["conv"] for s in subs)
        eff_waste = round((b["material"] / mat_base - 1) * 100, 2) if mat_base else 0.0
        out_rows.append({
            "seq": row["row_id"],
            "name": row["name"],
            "spec": row["spec"],
            "unit": row["unit"],
            "qty": row["qty"],
            "labor": b["labor"],
            "mat_price": mat_base,
            "material": b["material"],
            "waste": eff_waste,
            "aux": b["aux"],
            "mgmt": 0.0,       # 内部口径不含管理费
            "profit": 0.0,     # 内部口径不含利润
            "unit_price": b["unit_price"],
            "amount": b["amount"],
            "bid": ", ".join(f"{c}/{t}" for c, t in hit),
            "remark": (d or {}).get("remark", "") if hit else "未匹配",
        })

    columns = args.columns.split(",") if args.columns else None
    export_xlsx.export(out_rows, args.out, title="套价结果",
                       preset=args.preset, columns=columns)
    total = sum(r["amount"] for r in out_rows)
    print(f"[apply] {len(out_rows)} 行，已匹配 {matched}，合计 {total:.2f} → {args.out}")
    return 0


def cmd_stats(args) -> int:
    data = snapshot.load_snapshot()
    s = snapshot.stats(data)
    for k, v in s.items():
        print(f"{k}: {v}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="decoration-pricing")
    sp = p.add_subparsers(dest="cmd", required=True)

    pp = sp.add_parser("prepare", help="BOQ → 候选清单（不含价格）")
    pp.add_argument("boq")
    pp.add_argument("-o", "--out", required=True)
    pp.set_defaults(func=cmd_prepare)

    pa = sp.add_parser("apply", help="候选 + 决策 → 计价 → Excel")
    pa.add_argument("candidates")
    pa.add_argument("-o", "--out", required=True)
    pa.add_argument("--decisions", help="行号→子目 的判定结果 JSON")
    pa.add_argument("--overrides", help="行号→计价参数（mat_price/waste_rate/coef/conv）JSON")
    pa.add_argument("--preset", choices=list(export_xlsx.REMOTE_PRESETS),
                    help="导出列预设：client 对甲 / internal 对内 / labor 劳务")
    pa.add_argument("--columns", help="精确指定导出列 key，逗号分隔（优先级高于 --preset）")
    pa.add_argument("--auto", action="store_true", help="无决策时取候选第一名（基线模式）")
    pa.set_defaults(func=cmd_apply)

    ps = sp.add_parser("stats", help="快照统计（不含定价）")
    ps.set_defaults(func=cmd_stats)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
