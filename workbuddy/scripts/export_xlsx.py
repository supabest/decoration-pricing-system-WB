"""套价结果导出 —— openpyxl 生成报价表

列结构对齐远端 docs/tool.html 的 EXP_COLS（实测 16 列）+ 3 套预设：
    client  对甲    /  internal 对内 /  labor 劳务
WB 额外保留 1 列「套用子目」，用于编号跨班组重复时的匹配溯源。

默认（不传 preset / columns）输出全部 17 列，兼容既有调用。
"""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REMOTE_PRESETS = ("client", "internal", "labor")


def _col(key, label, width, num, src, client, internal, labor):
    return {
        "key": key, "label": label, "width": width, "num": num, "src": src,
        "presets": {"client": client, "internal": internal, "labor": labor},
    }


# 顺序、标签、列宽、预设归属逐字对齐远端 EXP_COLS
EXP_COLS = [
    _col("seq", "序号", 5, False, "seq", True, True, True),
    _col("code", "编号", 10, False, "code", True, True, True),
    _col("name", "项目名称", 28, False, "name", True, True, True),
    _col("spec", "项目特征", 44, False, "spec", False, True, True),
    _col("unit", "单位", 6, False, "unit", True, True, True),
    _col("qty", "工程量", 10, True, "qty", True, True, True),
    _col("lab", "人工单价", 10, True, "labor", False, True, True),
    _col("mat_price", "主材单价", 10, True, "mat_price", True, True, False),
    _col("mat", "主材费", 10, True, "material", True, True, False),
    _col("waste", "主材损耗率", 8, True, "waste", True, True, False),
    _col("aux", "辅材费", 10, True, "aux", False, True, False),
    _col("mgmt", "管理费", 8, True, "mgmt", False, True, False),
    _col("profit", "利润", 8, True, "profit", False, True, False),
    _col("usp", "综合单价", 12, True, "unit_price", True, True, False),
    _col("total", "合价", 14, True, "amount", True, True, True),
    _col("remark", "备注", 22, False, "remark", True, True, True),
]

EXTRA_COLS = [
    _col("bid", "套用子目", 18, False, "bid", True, True, True),
]

ALL_COLS = EXP_COLS + EXTRA_COLS
_BY_KEY = {c["key"]: c for c in ALL_COLS}

# 兼容旧代码可能引用的常量
COLUMNS = [(c["key"], c["label"], c["width"], c["num"]) for c in ALL_COLS]

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER_FILL = PatternFill("solid", fgColor="EDEDED")
NUM_FMT = "0.00"


def resolve_columns(preset=None, columns=None) -> list:
    """preset 用远端三套预设；columns 为 key 列表时精确覆盖（按给定顺序）。"""
    if columns is not None:
        return [_BY_KEY[k] for k in columns if k in _BY_KEY]
    if preset:
        if preset not in REMOTE_PRESETS:
            raise ValueError(f"未知预设 {preset}，可用: {', '.join(REMOTE_PRESETS)}")
        return [c for c in ALL_COLS if c["presets"][preset]]
    return list(ALL_COLS)


def _value(col, data: dict):
    key = col["key"]
    if key == "code" and not data.get("code"):
        # 未带清单原编号时，从套用子目里提取编号（去掉班组后缀）
        bid = data.get("bid") or ""
        return ", ".join(part.split("/")[0] for part in bid.split(", ") if part)
    return data.get(col["src"], "")


def _write_header(ws, cols) -> None:
    for i, c in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=i, value=c["label"])
        cell.font = Font(bold=True, size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
        cell.fill = HEADER_FILL
        ws.column_dimensions[get_column_letter(i)].width = c["width"]
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22


def _write_row(ws, row_no: int, data: dict, cols) -> None:
    for i, c in enumerate(cols, start=1):
        value = _value(c, data)
        if c["num"]:
            try:
                value = float(value or 0)
            except (TypeError, ValueError):
                value = 0.0
        cell = ws.cell(row=row_no, column=i, value=value)
        cell.border = BORDER
        if c["num"]:
            cell.number_format = NUM_FMT
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(vertical="center", wrap_text=(c["key"] == "spec"))


def export(rows, path, title: str = "套价结果", sections=None,
           preset=None, columns=None) -> str:
    """导出为 xlsx。

    sections: [(分区名, [行...]), ...] 时插入分区标题行
    preset:   client / internal / labor
    columns:  远端列 key 列表，精确指定要导出的列
    """
    cols = resolve_columns(preset, columns)
    if not cols:
        raise ValueError("没有可导出的列")

    wb = Workbook()
    ws = wb.active
    ws.title = (title or "套价结果")[:31]
    _write_header(ws, cols)

    r = 2
    total = 0.0
    blocks = sections if sections else [(None, rows)]
    for section_name, items in blocks:
        if section_name:
            ws.cell(row=r, column=1, value=section_name).font = Font(bold=True, size=10)
            for c in range(1, len(cols) + 1):
                ws.cell(row=r, column=c).border = BORDER
                ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor="F7F7F7")
            r += 1
        for item in items:
            _write_row(ws, r, item, cols)
            total += float(item.get("amount") or 0)
            r += 1

    amount_idx = next((i for i, c in enumerate(cols, start=1) if c["key"] == "total"), None)
    # 先设边框再合并：合并后非左上角变成 MergedCell，属性只读
    for c in range(1, len(cols) + 1):
        ws.cell(row=r, column=c).border = BORDER
    if amount_idx and amount_idx > 1:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=amount_idx - 1)
    flag = ws.cell(row=r, column=1, value="合计")
    flag.font = Font(bold=True, size=10)
    flag.alignment = Alignment(horizontal="center", vertical="center")

    if amount_idx:
        cell = ws.cell(row=r, column=amount_idx, value=round(total, 2))
        cell.font = Font(bold=True, size=10)
        cell.number_format = NUM_FMT
        cell.alignment = Alignment(horizontal="right", vertical="center")

    wb.save(str(path))
    return str(path)
