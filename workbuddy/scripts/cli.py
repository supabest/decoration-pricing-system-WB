"""统一入口

    python cli.py prepare <清单.xlsx> -o candidates.json      # 生成候选（不含价格）
    python cli.py apply candidates.json -o 结果.xlsx [--decisions d.json] [--auto]
    python cli.py apply candidates.json -o 结果.xlsx --split   # 按分部分 sheet
    python cli.py aux   candidates.json -o 辅材清单.xlsx [--decisions d.json] [--auto]
    python cli.py kb    [-o work/kb_prompt.txt]                # 脱敏知识库提示块
    python cli.py check candidates.json --decisions d.json -o consistency.json
    python cli.py stats                                       # 快照统计

保密设计：prepare 产出的候选只含编号/名称/规格/单位，不含任何价格字段；
价格只在 apply / aux 阶段从统一数据源读取，不进入模型上下文。
数据源由 WB_PRICING_SOURCE 选择：supabase = 项目公共授权直连云端价表（多人协作默认），
snapshot = 本地加密快照（离线兜底）。云端失败不会静默回退旧价。
kb 默认只打印到 stdout（不落盘），提示块已剔除源库中的定价金额；
check 只产出一致性 JSON 报告，不自动补全、不上报、不写任何价格。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import aux_rules
import datasource
import export_aux
import export_xlsx
import ingest
import knowledge
import price
import remarks
import retrieve
import similarity
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
    return datasource.load_snapshot().get("material_prices") or {}


def cmd_prepare(args) -> int:
    rows = ingest.parse_boq(args.boq)
    items = datasource.load_snapshot()["benchmark_items"]
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

    # 可选：额外写出脱敏知识库提示块。不传时 candidates.json 结构与 P0 完全一致。
    if getattr(args, "knowledge_out", None):
        kb = knowledge.load_knowledge()
        Path(args.knowledge_out).write_text(
            knowledge.build_prompt_block(kb), encoding="utf-8")
        print(f"[prepare] 知识库提示块（{kb['total']} 条，脱敏 {kb['sanitized_count']} 条）"
              f" → {args.knowledge_out}")
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

    snap = datasource.load_snapshot()
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
            "sheet": row.get("sheet") or "未分类",
            "section": row.get("section") or "",
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
            "remark": remarks.build_remark(
                decision=d, picks=picks, hit=hit,
                has_candidates=bool(row.get("candidates")),
            ),
        })

    columns = args.columns.split(",") if args.columns else None
    if args.split:
        export_xlsx.export_split(out_rows, args.out, preset=args.preset,
                                 columns=columns,
                                 include_summary=not args.no_summary)
    else:
        export_xlsx.export(out_rows, args.out, title="套价结果",
                           preset=args.preset, columns=columns)
    total = sum(r["amount"] for r in out_rows)
    groups = len({r["sheet"] for r in out_rows}) if args.split else 1
    print(f"[apply] {len(out_rows)} 行，已匹配 {matched}，{groups} 个分部，"
          f"合计 {total:.2f} → {args.out}")
    return 0


def cmd_stats(args) -> int:
    data = datasource.load_snapshot()
    s = snapshot.stats(data)
    for k, v in s.items():
        print(f"{k}: {v}")
    return 0


def cmd_aux(args) -> int:
    """候选 + 决策 → 分工种辅材费用清单（P1）。

    与 apply 共用 candidates / decisions / --auto，但只走辅材配方引擎：
    不计算人工、主材与综合单价，也不把任何价格写进中间 JSON。
    远端口径见 docs/tool.html 的 buildAuxExport() 与 backend/app/services/aux_export.py。
    """
    data = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    decisions = (json.loads(Path(args.decisions).read_text(encoding="utf-8"))
                 if args.decisions else {})
    snap = datasource.load_snapshot()

    priced_rows = []
    for row in data["rows"]:
        d = decisions.get(str(row["row_id"]))
        priced_rows.append({
            "row_id": row["row_id"],
            "name": row.get("name", ""),
            "spec": row.get("spec", ""),
            "unit": row.get("unit", ""),
            "qty": row.get("qty", 0),
            "picks": _picks(row, d, args.auto),
        })

    result = export_aux.build_aux_export(priced_rows, snap)
    if not result["groups"] and not result["unclassified"]:
        print("[aux] 无可导出的辅材数据（清单为空，或子目均无辅材配方）")
        return 1

    # 对账：明细合计 vs Σ(每单位清单量辅材费 × 工程量)，与远端 expectTotal 同口径
    if abs(result["diff"]) > 0.01:
        print(f"[aux] ⚠ 对账差额 {result['diff']:.2f} 元，请核查辅材配方与信息价")

    export_aux.export_aux_workbook(
        result, args.out,
        project_name=args.project_name,
        contract_amount=args.contract_amount,
        target_profit_rate=args.target_profit_rate,
    )
    print(f"[aux] {len(result['groups'])} 个工种，{len(result['unclassified'])} 行未套子目，"
          f"辅材合计 {result['grand_total']:.2f} → {args.out}")
    return 0


def cmd_kb(args) -> int:
    """输出脱敏知识库提示块，供模型判子目时读入。

    默认只打印到 stdout（零落盘、零误提交）；-o 才写文件。
    源 JSON 里 7 条含价规则已改写，且 assert_no_pricing 会拦截新增含价条目。
    """
    kb = knowledge.load_knowledge(args.kb)
    block = knowledge.build_prompt_block(kb)
    if args.kb_out:
        Path(args.kb_out).write_text(block, encoding="utf-8")
        print(f"[kb] {kb['total']} 条规则（脱敏 {kb['sanitized_count']} 条）→ {args.kb_out}")
    else:
        print(block)
    return 0


def cmd_check(args) -> int:
    """候选 + 决策 → 相似清单一致性 JSON 报告（只校验，不补全、不上报）。"""
    data = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    decisions = (json.loads(Path(args.decisions).read_text(encoding="utf-8"))
                 if args.decisions else {})
    items = similarity.build_check_items(data, decisions, args.default_confidence)
    if args.group_by:
        report = similarity.check_consistency_by_domain(items, args.group_by,
                                                        args.threshold)
    else:
        report = similarity.check_consistency(items, args.threshold)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    print(f"[check] {report['total_items']} 行，{report['groups_found']} 个相似组，"
          f"{report['warnings_count']} 条警告 → {args.out}")
    return 0


def cmd_probe(args) -> int:
    """云端连通性体检：只输出表是否存在、行数、字段名，绝不输出价格。"""
    try:
        rows = datasource.probe()
    except datasource.SourceError as exc:
        print(f"[probe] 连接失败：{exc}")
        return 1
    pf = datasource.preflight()
    print(f"[probe] 数据源={pf['source']} | 通道={pf['channel']} | "
          f"身份={pf['identity']} | apikey={'有' if pf['anon_key'] else '无'}")
    print(f"{'表':<26}{'状态':<12}{'行数':>8}  字段(前 8)")
    for r in rows:
        print(f"{r['table']:<26}{r.get('status', ''):<12}"
              f"{str(r.get('count', '?')):>8}  {','.join(r.get('fields', [])[:8])}")
    missing = [r["table"] for r in rows if r["status"] == "missing"]
    empty = [r["table"] for r in rows if r["status"] == "empty"]
    errors = [r["table"] for r in rows if r["status"] not in ("ok", "empty", "missing")]
    if missing:
        print(f"[probe] ⚠ 缺表 {len(missing)} 张：{', '.join(missing)}"
              " → 先执行 sql/wb_supabase_setup.sql 建表")
    if empty:
        print(f"[probe] ⚠ 0 行可读 {len(empty)} 张：{', '.join(empty)}"
              " → 检查是否带 authenticated 身份，或先跑 sync-seeds 补库")
    if errors:
        print(f"[probe] ⚠ 连接异常 {len(errors)} 张：{', '.join(errors)}"
              " → 检查 REST 地址与授权注入")
    if not (missing or empty or errors):
        print("[probe] 云端价表全部可读")
        return 0
    # 退出码区分卡点，便于自动化按阶段 1 步骤定位
    return 2 if missing else (3 if empty else 4)


def cmd_preflight(args) -> int:
    """阶段 1 验收：只回报配置「有无」，绝不回显任何凭据值。"""
    pf = datasource.preflight()
    print(f"数据源          : {pf['source']}"
          f"{'（非云端主路径，需 WB_PRICING_SOURCE=supabase）' if pf['source'] != 'supabase' else ''}")
    print(f"REST 地址       : {'已配置' if pf['url_configured'] else '未配置'}"
          f" | 通道={pf['channel']}")
    print(f"apikey          : {'已配置' if pf['anon_key'] else '未配置'}")
    print(f"authenticated   : {pf['identity']}")
    print(f"补库管理员令牌  : {'已配置' if pf['sync_token'] else '未配置（仅 sync-seeds 需要）'}")
    print(f"离线兜底        : {'开启' if pf['fallback'] else '关闭（推荐）'}")
    issues = []
    if pf["source"] != "supabase":
        issues.append("数据源未切到 supabase")
    if not pf["url_configured"]:
        issues.append("缺 WB_SUPABASE_URL")
    if not pf["anon_key"]:
        issues.append("缺 apikey")
    if pf["identity"] == "none":
        issues.append("缺 authenticated 身份（JWT 或专用账号邮箱/密码）")
    if issues:
        print(f"[preflight] 未就绪：{'；'.join(issues)}")
        return 2
    print("[preflight] 就绪：可以跑 probe 验收")
    return 0


def cmd_sync_seeds(args) -> int:
    """一次性把云端缺失的损耗率 / 辅材数据补进 Supabase（需管理员令牌）。"""
    try:
        result = datasource.sync_seeds(dry_run=args.dry_run)
    except datasource.SourceError as exc:
        print(f"[sync-seeds] 失败：{exc}")
        return 1
    for table, info in result.items():
        print(f"[sync-seeds] {table}: {info['rows']} 行 / {info['batches']} 批"
              f" → {info['status']}")
    if args.dry_run:
        print("[sync-seeds] 预演模式：未联网、未写入任何数据")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="decoration-pricing")
    sp = p.add_subparsers(dest="cmd", required=True)

    pp = sp.add_parser("prepare", help="BOQ → 候选清单（不含价格）")
    pp.add_argument("boq")
    pp.add_argument("-o", "--out", required=True)
    pp.add_argument("--knowledge-out",
                    help="额外写出脱敏知识库提示块（不传则候选结构不变）")
    pp.set_defaults(func=cmd_prepare)

    pk = sp.add_parser("kb", help="输出脱敏知识库提示块（默认 stdout，不落盘）")
    pk.add_argument("--kb", help="源知识库 JSON 路径（默认仓库 docs/ai_knowledge_base.json）")
    pk.add_argument("-o", "--kb-out", help="写出提示块到指定路径（默认只打印到 stdout）")
    pk.set_defaults(func=cmd_kb)

    pc = sp.add_parser("check", help="相似清单一致性校验 → JSON 报告（只校验）")
    pc.add_argument("candidates")
    pc.add_argument("-o", "--out", required=True)
    pc.add_argument("--decisions", help="行号→子目 判定结果 JSON（不传则全部视为未套价）")
    pc.add_argument("--group-by", choices=["sheet", "section"],
                    help="按源工作表/章节收窄比较域")
    pc.add_argument("--threshold", type=float, default=0.90,
                    help="相似度阈值，默认 0.90")
    pc.add_argument("--default-confidence", type=int, default=100,
                    help="decisions 无 confidence 字段时的默认置信度，默认 100")
    pc.set_defaults(func=cmd_check)

    pa = sp.add_parser("apply", help="候选 + 决策 → 计价 → Excel")
    pa.add_argument("candidates")
    pa.add_argument("-o", "--out", required=True)
    pa.add_argument("--decisions", help="行号→子目 的判定结果 JSON")
    pa.add_argument("--overrides", help="行号→计价参数（mat_price/waste_rate/coef/conv）JSON")
    pa.add_argument("--preset", choices=list(export_xlsx.REMOTE_PRESETS),
                    help="导出列预设：client 对甲 / internal 对内 / labor 劳务")
    pa.add_argument("--columns", help="精确指定导出列 key，逗号分隔（优先级高于 --preset）")
    pa.add_argument("--auto", action="store_true", help="无决策时取候选第一名（基线模式）")
    pa.add_argument("--split", action="store_true",
                    help="按分部（源工作表）分 sheet，内部按章节插标题行")
    pa.add_argument("--no-summary", action="store_true",
                    help="--split 时不生成末尾「汇总」sheet")
    pa.set_defaults(func=cmd_apply)

    px = sp.add_parser("aux", help="候选 + 决策 → 分工种辅材费用清单（P1）")
    px.add_argument("candidates")
    px.add_argument("-o", "--out", required=True)
    px.add_argument("--decisions", help="行号→子目 的判定结果 JSON（与 apply 共用）")
    px.add_argument("--auto", action="store_true", help="无决策时取候选第一名（基线模式）")
    px.add_argument("--project-name", default="套价表", help="汇总 sheet 的项目名称")
    px.add_argument("--contract-amount", type=float, default=0.0,
                    help="合同额（>0 时汇总表追加「占总成本比例」列）")
    px.add_argument("--target-profit-rate", type=float, default=0.0,
                    help="目标利润率(%%)，与合同额共同推算成本基数")
    px.set_defaults(func=cmd_aux)

    ps = sp.add_parser("stats", help="数据源统计（不含定价）")
    ps.set_defaults(func=cmd_stats)

    pf = sp.add_parser("preflight", help="阶段1 验收：检查云端取数环境是否就绪（只报有无，不回显值）")
    pf.set_defaults(func=cmd_preflight)

    pb = sp.add_parser("probe", help="Supabase 云端连通性体检（只读，不输出价格）")
    pb.set_defaults(func=cmd_probe)

    py = sp.add_parser("sync-seeds", help="一次性补齐云端缺失的损耗率/辅材表（需管理员令牌）")
    py.add_argument("--dry-run", action="store_true",
                    help="只预演行数与批次数：不联网、不需要令牌、不写任何数据")
    py.set_defaults(func=cmd_sync_seeds)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
