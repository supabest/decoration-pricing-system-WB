"""P1 · 辅材费用清单导出（分工种·品种明细）

对齐远端 docs/tool.html 的 buildAuxExport() 与 backend/app/services/aux_export.py：

  · 按工种（trade_team）分组；品种行 = Σ(消耗量 × 工程量)，合价 = Σ(信息价 × 消耗量 × 工程量)
  · 固定辅材费 = Σ(fixed_k × 工程量)，以「固定辅材费（定额包干）」行置于品种行末尾
  · 品种行按合价降序、工种组按合计降序（与远端一致）
  · 未套子目（未套价 / 子目缺失 / 无工种）单独成 sheet，供人工补费，避免漏算
  · 末尾「辅材汇总」sheet：工种 → 材料费 / 固定费 / 合计；合同额给定时附「占总成本比例」

与网页应用的边界：本模块**不依赖后端 FastAPI**，在 workbuddy 会话内离线生成 xlsx。
数据一律取自本地加密快照，不联网、不写任何外部服务。
"""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import aux_rules
import retrieve

HEADER_LABELS = ["序号", "辅材名称", "单位", "消耗量合计", "信息价(元)", "合价(元)", "备注"]
COL_WIDTHS = [6, 26, 8, 14, 12, 14, 16]
FIXED_LINE_NAME = "固定辅材费（定额包干）"
SUMMARY_SHEET = "辅材汇总"
UNCLASSIFIED_SHEET = "未套子目清单"
UNCLASSIFIED_HEADERS = ["序号", "项目名称", "项目特征", "单位", "工程量", "原因", "需补辅材费(元)"]
FIXED_NOTE = "注：因基准单价大部分辅材单价为固定费用包干，没有明细，此表之辅材费用仅供预测该工种辅材总费用之用。"
UNCLASSIFIED_NOTE = "注：以下清单项未套子目，其辅材费未计入本清单各工种汇总；请在「需补辅材费」列自行评估填写，避免漏算。"

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER_FILL = PatternFill("solid", fgColor="EDEDED")
NUM_FMT = "0.00"
_INVALID_SHEET_CHARS = re.compile(r"[\\/*?:\[\]]")


def _num(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _sheet_name(name: str, used: set[str]) -> str:
    """openpyxl sheet 名：不超过 31 字符、禁含特殊字符，且不得重名。"""
    base = _INVALID_SHEET_CHARS.sub("_", str(name or "未分类")).strip()[:31] or "未分类"
    candidate, i = base, 2
    while candidate in used:
        suffix = f"_{i}"
        candidate = base[:31 - len(suffix)] + suffix
        i += 1
    used.add(candidate)
    return candidate


def build_aux_export(priced_rows: list[dict], snap: dict) -> dict:
    """聚合出辅材清单数据（纯计算，不写文件）。

    priced_rows: [{"row_id", "name", "spec", "unit", "qty",
                   "picks": [(code, team, extra), ...]}, ...]
    snap:        load_snapshot() 的结果
    """
    items = snap.get("benchmark_items") or []
    index = {retrieve.identify(i): i for i in items}
    price_lib = snap.get("material_prices") or {}

    trade_map: dict[str, dict] = {}
    unclassified: list[dict] = []
    expect_total = 0.0

    for row in priced_rows:
        qty = _num(row.get("qty"))
        picks = row.get("picks") or []
        if not picks:
            unclassified.append({
                "name": row.get("name", ""), "spec": row.get("spec", ""),
                "unit": row.get("unit", ""), "qty": qty, "reason": "未套价",
            })
            continue

        for code, team, _extra in picks:
            item = index.get((code, team))
            if not item:
                unclassified.append({
                    "name": row.get("name", ""), "spec": row.get("spec", ""),
                    "unit": row.get("unit", ""), "qty": qty, "reason": "子目缺失",
                })
                continue
            trade = str(team or "").strip()
            if not trade:
                unclassified.append({
                    "name": row.get("name", ""), "spec": row.get("spec", ""),
                    "unit": row.get("unit", ""), "qty": qty, "reason": "无工种",
                })
                continue

            # 对账基准：远端口径 = Σ 各子目辅材费（每单位清单量）× 工程量
            expect_total += aux_rules.aux_cost(item, price_lib) * qty

            detail = aux_rules.aux_detail(item, price_lib)
            fixed_k = detail["fixed_k"]
            materials = detail["materials"]
            if not fixed_k and not materials:
                continue     # 该子目无辅材配方（与远端 3444 行一致）

            g = trade_map.setdefault(trade, {"lines": {}, "fixed": 0.0})
            g["fixed"] += fixed_k * qty
            for m in materials:
                name = m["name"]
                rec = price_lib.get(name) if isinstance(price_lib, dict) else None
                unit = (rec or {}).get("unit", "") if isinstance(rec, dict) else ""
                line = g["lines"].setdefault(name, {
                    "name": name, "unit": unit, "qty_total": 0.0,
                    "price": m["price"], "subtotal": 0.0, "is_fixed": False,
                })
                line["qty_total"] += _num(m.get("consume")) * qty
                line["subtotal"] += _num(m.get("subtotal")) * qty

    groups = []
    for trade, g in trade_map.items():
        lines = sorted(g["lines"].values(), key=lambda l: -l["subtotal"])
        mat_sub = sum(l["subtotal"] for l in lines)
        if g["fixed"]:
            lines.append({
                "name": FIXED_LINE_NAME, "unit": "", "qty_total": None,
                "price": None, "subtotal": g["fixed"], "is_fixed": True,
            })
        groups.append({
            "sheet_name": trade, "lines": lines,
            "fixed_subtotal": g["fixed"], "material_subtotal": mat_sub,
            "total": mat_sub + g["fixed"],
        })
    groups.sort(key=lambda x: -x["total"])

    grand_total = sum(g["total"] for g in groups)
    return {
        "groups": groups,
        "unclassified": unclassified,
        "grand_total": grand_total,
        "expect_total": expect_total,
        "diff": expect_total - grand_total,
    }


def _style_header(ws, row_no: int, labels: list[str]) -> None:
    for c, label in enumerate(labels, start=1):
        cell = ws.cell(row=row_no, column=c, value=label)
        cell.font = Font(bold=True, size=10)
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _title(ws, text: str, n_cols: int) -> None:
    ws.cell(row=1, column=1, value=text)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    c = ws.cell(row=1, column=1)
    c.font = Font(bold=True, size=14)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28


def _note(ws, row_no: int, text: str, n_cols: int) -> None:
    ws.merge_cells(start_row=row_no, start_column=1, end_row=row_no, end_column=n_cols)
    c = ws.cell(row=row_no, column=1, value=text)
    c.font = Font(italic=True, size=10, color="808080")
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[row_no].height = 30


def _write_trade_sheet(wb, group: dict, sheet_name: str) -> None:
    ws = wb.create_sheet(title=sheet_name)
    n = len(HEADER_LABELS)
    _title(ws, f"{group['sheet_name']}辅材费用清单", n)
    _style_header(ws, 2, HEADER_LABELS)

    r = 3
    for i, line in enumerate(group["lines"], start=1):
        fixed = bool(line["is_fixed"])
        values = [
            i, line["name"],
            line["unit"] or ("—" if fixed else ""),
            "—" if fixed else round(line["qty_total"], 4),
            "—" if fixed else line["price"],
            line["subtotal"],
            "定额包干" if fixed else "",
        ]
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = BORDER
            if c in (4, 5, 6) and isinstance(v, (int, float)):
                cell.number_format = NUM_FMT
                cell.alignment = Alignment(horizontal="right", vertical="center")
        r += 1

    # 小计行（静态数值；网页版用公式，本模块离线生成故直接写值，避免 Excel 未重算显示为空）
    for c in range(1, n + 1):
        ws.cell(row=r, column=c).border = BORDER
    flag = ws.cell(row=r, column=1, value="小计")
    flag.font = Font(bold=True, size=10)
    sub = ws.cell(row=r, column=6, value=round(group["total"], 2))
    sub.font = Font(bold=True, size=10)
    sub.number_format = NUM_FMT
    sub.alignment = Alignment(horizontal="right", vertical="center")

    for i, w in enumerate(COL_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"
    _note(ws, r + 1, FIXED_NOTE, n)


def _write_summary_sheet(wb, result: dict, project_name: str,
                         contract_amount: float, target_profit_rate: float) -> None:
    ws = wb.create_sheet(title=SUMMARY_SHEET)
    cost_base = None
    if contract_amount and contract_amount > 0:
        cost_base = contract_amount * (1 - _num(target_profit_rate) / 100.0)

    headers = ["工种", "其中材料费", "其中固定辅材费", "辅材合计"]
    if cost_base:
        headers.append("占总成本比例")
    n = len(headers)
    _title(ws, f"{project_name} 辅材汇总", n)
    _style_header(ws, 2, headers)

    groups = [g for g in result["groups"] if g["lines"]]
    grand = [0.0, 0.0, 0.0]
    r = 3
    for g in groups:
        values = [g["sheet_name"], g["material_subtotal"], g["fixed_subtotal"], g["total"]]
        if cost_base:
            values.append(g["total"] / cost_base if cost_base else 0.0)
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = BORDER
            if c in (2, 3, 4):
                cell.number_format = NUM_FMT
            if c == 5:
                cell.number_format = "0.00%"
        grand[0] += g["material_subtotal"]
        grand[1] += g["fixed_subtotal"]
        grand[2] += g["total"]
        r += 1

    totals = ["总计", *grand]
    if cost_base:
        totals.append(grand[2] / cost_base if cost_base else 0.0)
    for c, v in enumerate(totals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = Font(bold=True, size=10)
        cell.border = BORDER
        if c in (2, 3, 4):
            cell.number_format = NUM_FMT
        if c == 5:
            cell.number_format = "0.00%"

    for i, w in enumerate([20, 16, 16, 16, 14][:n], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"


def _write_unclassified_sheet(wb, result: dict) -> None:
    ws = wb.create_sheet(title=UNCLASSIFIED_SHEET)
    n = len(UNCLASSIFIED_HEADERS)
    _title(ws, "未套子目清单（辅材费未计入各工种汇总）", n)
    _style_header(ws, 2, UNCLASSIFIED_HEADERS)

    r = 3
    for i, u in enumerate(result["unclassified"], start=1):
        values = [i, u["name"], u["spec"], u["unit"], u["qty"], u["reason"], None]
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = BORDER
            if c == 5 and isinstance(v, (int, float)):
                cell.number_format = NUM_FMT
            if c in (2, 3):
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        r += 1

    for i, w in enumerate([6, 28, 34, 8, 12, 12, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"
    _note(ws, r + 1, UNCLASSIFIED_NOTE, n)


def export_aux_workbook(result: dict, path, project_name: str = "套价表",
                        contract_amount: float = 0, target_profit_rate: float = 0) -> str:
    """把 build_aux_export 的结果写成多 sheet 工作簿，返回路径。"""
    wb = Workbook()
    wb.remove(wb.active)
    used: set[str] = {SUMMARY_SHEET, UNCLASSIFIED_SHEET}

    for g in result["groups"]:
        if g["lines"]:
            _write_trade_sheet(wb, g, _sheet_name(g["sheet_name"], used))
    _write_summary_sheet(wb, result, project_name, contract_amount, target_profit_rate)
    if result["unclassified"]:
        _write_unclassified_sheet(wb, result)

    wb.save(str(Path(path)))
    return str(Path(path))
