"""BOQ 工程量清单读取

处理三类真实世界的坑：
1. 多级表头 —— 以「项目名称」所在行为表头行，只按精确列名定位，不依赖 used range
2. 纵向合并 —— 一条清单项占 2 个物理行，非左上角一律折叠为空，避免重复计数
3. 合并区残留值 —— 文件底层可能仍保存旧值（如合并的单价列），折叠后一并屏蔽
"""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import load_workbook

from retrieve import normalize_unit

HEADER_TOKENS = {"序号", "项目名称", "项目特征", "计量单位", "工程量", "综合单价",
                 "备注", "数量小计", "合价", "金额"}
MAX_SCAN_COL = 40
MAX_SCAN_ROW = 12

SECTION_RE = re.compile(r'^[（(]?\s*[一二三四五六七八九十百]+\s*[）)]?\s*[、.．]?\s*')
_FIELD_ALIASES = {
    "seq": ("序号", "编号"),
    "name": ("项目名称", "名称", "清单名称", "项目"),
    "spec": ("项目特征", "项目特征描述", "特征描述", "规格型号"),
    "unit": ("计量单位", "单位"),
    "qty": ("工程量", "数量", "清单工程量"),
    "unit_price": ("综合单价", "单价"),
    "remark": ("备注",),
}


def _text(v) -> str:
    if v is None:
        return ""
    return str(v).replace("\r", "").strip()


def _norm(v) -> str:
    """表头归一化：去换行与所有空白（真实文件里常见「计量\\n单位」这种折行写法）"""
    return re.sub(r"\s+", "", _text(v))


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _merge_shadow(ws) -> set[tuple[int, int]]:
    """合并区内非左上角的坐标集合 —— 这些格子一律视为空。"""
    shadow: set[tuple[int, int]] = set()
    for rng in ws.merged_cells.ranges:
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                if (r, c) != (rng.min_row, rng.min_col):
                    shadow.add((r, c))
    return shadow


def _read(ws, shadow, row: int, col: int):
    if col is None or (row, col) in shadow:
        return None
    return ws.cell(row=row, column=col).value


def detect_header_row(ws) -> int | None:
    limit = min(MAX_SCAN_ROW, ws.max_row or 1)
    width = min(MAX_SCAN_COL, ws.max_column or 1)
    for r in range(1, limit + 1):
        for c in range(1, width + 1):
            if _norm(ws.cell(row=r, column=c).value) == "项目名称":
                return r
    return None


def detect_columns(ws, header_row: int) -> dict:
    width = min(MAX_SCAN_COL, ws.max_column or 1)
    cols: dict[str, int] = {}
    for c in range(1, width + 1):
        v = _norm(ws.cell(row=header_row, column=c).value)
        if not v:
            continue
        for field, aliases in _FIELD_ALIASES.items():
            if field in cols:
                continue
            if v in aliases:
                cols[field] = c
                break
    return cols


def _clean_section(raw: str) -> str:
    return SECTION_RE.sub("", _text(raw)).strip()


def parse_sheet(ws) -> list[dict]:
    header_row = detect_header_row(ws)
    if header_row is None:
        return []
    cols = detect_columns(ws, header_row)
    if "name" not in cols:
        return []

    shadow = _merge_shadow(ws)
    out: list[dict] = []
    section = ""

    for r in range(header_row + 1, (ws.max_row or 0) + 1):
        name = _text(_read(ws, shadow, r, cols.get("name")))
        spec = _text(_read(ws, shadow, r, cols.get("spec")))
        unit = _text(_read(ws, shadow, r, cols.get("unit")))
        seq = _text(_read(ws, shadow, r, cols.get("seq")))
        qty = _num(_read(ws, shadow, r, cols.get("qty")))

        if not name:
            continue
        if name in HEADER_TOKENS or spec in HEADER_TOKENS:
            continue

        # 章节行：有序号、无特征、无单位
        if seq and not spec and not unit:
            section = _clean_section(name)
            continue

        # 单位工程标题行：仅名称
        if not spec and not unit and qty is None:
            continue

        out.append({
            "sheet": ws.title,
            "section": section,
            "name": name,
            "spec": spec,
            "unit": normalize_unit(unit),
            "qty": qty if qty is not None else 0.0,
            "source_row": r,
        })
    return out


def parse_boq(path) -> list[dict]:
    wb = load_workbook(filename=str(path), data_only=True)
    rows: list[dict] = []
    for ws in wb.worksheets:
        rows.extend(parse_sheet(ws))
    wb.close()
    return rows
