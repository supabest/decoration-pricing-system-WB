"""Excel 导出服务 — 使用 openpyxl 生成标准成本分析 Excel"""
from __future__ import annotations

from io import BytesIO
from typing import List, Dict, Optional, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import RowDimension

from app.schemas.export import ExportRequest, ExportColumn, ExportRow, ExportSubItem


# ── 样式常量 ──────────────────────────────────────────────

FONT_NAME = "微软雅黑"

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

FILL_HEADER = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
FILL_SUMMARY = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")

NUM_FMT = '#,##0.00'


class ExcelExporter:
    """将 ExportRequest 转换为 openpyxl Workbook"""

    def __init__(self, request: ExportRequest):
        self.req = request
        self.cols = request.columns
        self.col_keys = [c.key for c in self.cols]
        self.col_idx = {k: i for i, k in enumerate(self.col_keys)}  # key → 0-based index
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "套价清单"

        # 行追踪
        self.current_row = 0  # 0-based
        self.data_row_indices: List[int] = []  # 0-based 所有数据行索引（含子目行，用于公式）
        self.main_row_indices: List[int] = []  # 0-based 仅父行索引（不含子目，用于合计行 SUM）
        self.row_meta: List[dict] = []  # 每行元信息 {level, is_data, is_hidden, cells}

    def generate(self) -> BytesIO:
        """生成 Excel 并返回 BytesIO 缓冲区"""
        self._write_header_row()
        self._write_data_rows()
        self._write_summary_row()
        self._apply_formulas()
        self._apply_styles()
        self._set_column_widths()
        self._set_row_heights()
        self._set_outline()

        buf = BytesIO()
        self.wb.save(buf)
        buf.seek(0)
        return buf

    # ── 行写入 ────────────────────────────────────────────

    def _next_row(self) -> int:
        """获取下一个 Excel 行号（1-based）并推进游标"""
        self.current_row += 1
        return self.current_row

    def _write_title_row(self):
        r = self._next_row()  # row 1
        title = f"{self.req.project_name}  套价表"
        self.ws.cell(row=r, column=1, value=title)
        # 合并单元格
        if len(self.cols) > 1:
            self.ws.merge_cells(start_row=r, start_column=1,
                                end_row=r, end_column=len(self.cols))
        self.row_meta.append({"level": 0, "is_data": False, "is_hidden": False,
                              "type": "title"})

    def _write_header_row(self):
        r = self._next_row()  # row 2
        for i, col in enumerate(self.cols):
            self.ws.cell(row=r, column=i + 1, value=col.label)
        self.row_meta.append({"level": 0, "is_data": False, "is_hidden": False,
                              "type": "header"})

    def _write_data_rows(self):
        seq = 0
        for group in self.req.groups:
            # 分组标题行
            self._write_group_header(group.sheet_name)

            for section in group.sections:
                # 分部标题行
                self._write_section_header(section.name)

                for row in section.rows:
                    seq += 1
                    # 清单项数据行
                    self._write_data_row(row, seq)

                    # 子目明细行
                    if self.req.show_subs and row.subs:
                        for sub in row.subs:
                            self._write_sub_item_row(sub, row)

    def _write_group_header(self, sheet_name: str):
        r = self._next_row()
        self.ws.cell(row=r, column=1, value=f"【{sheet_name}】")
        self.row_meta.append({"level": 0, "is_data": False, "is_hidden": False,
                              "type": "group"})

    def _write_section_header(self, section_name: str):
        r = self._next_row()
        self.ws.cell(row=r, column=1, value=section_name)
        level = 1 if self.req.group_folding else 0
        self.row_meta.append({"level": level, "is_data": False, "is_hidden": False,
                              "type": "section"})

    def _write_data_row(self, row: ExportRow, seq: int):
        r = self._next_row()
        level = 2 if self.req.group_folding else 0

        for i, col in enumerate(self.cols):
            val = self._get_cell_value(col.key, row, seq)
            cell = self.ws.cell(row=r, column=i + 1, value=val)
            if col.num and isinstance(val, (int, float)):
                cell.number_format = NUM_FMT

        self.data_row_indices.append(self.current_row - 1)  # 0-based
        self.main_row_indices.append(self.current_row - 1)  # 0-based，仅父行用于 SUM
        self.row_meta.append({"level": level, "is_data": True, "is_hidden": False,
                              "type": "data", "row": row})

    def _write_sub_item_row(self, sub: ExportSubItem, parent_row: ExportRow):
        r = self._next_row()
        level = 3 if self.req.group_folding else 0
        sub_qty = (parent_row.qty or 0) * (sub.conv or 1.0) * (sub.coef or 1.0)
        mgmt_rate = self.req.mgmt_rate / 100
        profit_rate = self.req.profit_rate / 100

        for i, col in enumerate(self.cols):
            val = self._get_sub_cell_value(col.key, sub, sub_qty, parent_row, mgmt_rate, profit_rate)
            cell = self.ws.cell(row=r, column=i + 1, value=val)
            if col.num and isinstance(val, (int, float)):
                cell.number_format = NUM_FMT

        self.data_row_indices.append(self.current_row - 1)  # 0-based
        self.row_meta.append({"level": level, "is_data": True, "is_hidden": True,
                              "type": "sub", "sub": sub})

    def _write_summary_row(self):
        # 使用 main_row_indices（仅父行）避免子目行双倍计数
        sum_indices = self.main_row_indices if self.main_row_indices else self.data_row_indices
        if not sum_indices:
            return

        r = self._next_row()

        # 将不连续的父行索引按顺序合并为连续区间，生成紧凑的 SUM 公式
        # 例: [3,4,9] → "=SUM(F4:F5,F10)" 而非 "=SUM(F4:F10)"（后者会包含中间的子目行）
        sorted_idx = sorted(sum_indices)

        def _build_ranges():
            """将索引列表转为连续区间列表，每个区间为 (start_1based, end_1based)"""
            ranges = []
            start = sorted_idx[0]
            end = sorted_idx[0]
            for idx in sorted_idx[1:]:
                if idx == end + 1:
                    end = idx
                else:
                    ranges.append((start + 1, end + 1))
                    start = end = idx
            ranges.append((start + 1, end + 1))
            return ranges

        ranges = _build_ranges()
        # 如果只有一个连续区间且覆盖全部（无子目行打断），直接用连续 range
        use_continuous = len(ranges) == 1

        for i, col in enumerate(self.cols):
            cell = self.ws.cell(row=r, column=i + 1)
            if i == 0:
                cell.value = "合计"
            elif col.key in ("qty", "lab", "mat", "aux", "total"):
                col_letter = get_column_letter(i + 1)
                if use_continuous:
                    cell.value = f"=SUM({col_letter}{ranges[0][0]}:{col_letter}{ranges[0][1]})"
                else:
                    # 多区间：=SUM(F4:F5,F10:F10)
                    parts = [f"{col_letter}{s}:{col_letter}{e}" if s != e else f"{col_letter}{s}"
                             for s, e in ranges]
                    cell.value = f"=SUM({','.join(parts)})"
                cell.number_format = NUM_FMT

        self.row_meta.append({"level": 0, "is_data": False, "is_hidden": False,
                              "type": "summary"})

    # ── 单元格值获取 ──────────────────────────────────────

    def _get_cell_value(self, key: str, row: ExportRow, seq: int):
        mgmt_rate = self.req.mgmt_rate / 100
        profit_rate = self.req.profit_rate / 100
        labor = row.labor_price or 0

        if key == "seq":
            return seq
        elif key == "code":
            return ""  # 编号只在子目行显示
        elif key == "name":
            return row.name or ""
        elif key == "spec":
            return row.spec or ""
        elif key == "unit":
            return row.unit or ""
        elif key == "qty":
            return row.qty or 0
        elif key == "lab":
            return labor
        elif key == "mat":
            return row.mat_price or 0
        elif key == "waste":
            return row.waste_rate or 0
        elif key == "aux":
            return row.aux_cost or 0
        elif key == "mgmt":
            return labor * mgmt_rate
        elif key == "profit":
            return labor * profit_rate
        elif key == "usp":
            mat_cost = (row.mat_price or 0) * (1 + (row.waste_rate or 0) / 100)
            return labor + mat_cost + (row.aux_cost or 0) + labor * mgmt_rate + labor * profit_rate
        elif key == "total":
            usp = labor + (row.mat_price or 0) * (1 + (row.waste_rate or 0) / 100) + (row.aux_cost or 0) + labor * mgmt_rate + labor * profit_rate
            return usp * (row.qty or 0)
        elif key == "remark":
            return row.remark or ""
        return ""

    def _get_sub_cell_value(self, key: str, sub: ExportSubItem, sub_qty: float,
                            parent: ExportRow, mgmt_rate: float, profit_rate: float):
        ep = sub.unit_price or 0

        if key == "seq":
            return ""
        elif key == "code":
            return str(sub.bid or "")
        elif key == "name":
            return f"  └ {sub.name or ''}"
        elif key == "spec":
            return sub.spec or ""
        elif key == "unit":
            return sub.unit or ""
        elif key == "qty":
            return sub_qty
        elif key == "lab":
            return ep
        elif key == "mat":
            return 0
        elif key == "waste":
            return parent.waste_rate or 0
        elif key == "aux":
            return 0
        elif key == "mgmt":
            return ep * mgmt_rate
        elif key == "profit":
            return ep * profit_rate
        elif key == "usp":
            return ep
        elif key == "total":
            return ep * sub_qty
        elif key == "remark":
            return ""
        return ""

    # ── Excel 公式 ────────────────────────────────────────

    def _apply_formulas(self):
        """将数据行的计算列替换为 Excel 公式"""
        lab_col = self._col_letter("lab")
        mat_col = self._col_letter("mat")
        waste_col = self._col_letter("waste")
        aux_col = self._col_letter("aux")
        mgmt_col = self._col_letter("mgmt")
        profit_col = self._col_letter("profit")
        usp_col = self._col_letter("usp")
        total_col = self._col_letter("total")
        qty_col = self._col_letter("qty")

        mgmt_rate = self.req.mgmt_rate / 100
        profit_rate = self.req.profit_rate / 100

        for idx in self.data_row_indices:
            R = idx + 1  # Excel 1-based row number
            row_meta = self.row_meta[idx] if idx < len(self.row_meta) else {}
            is_sub = row_meta.get("type") == "sub"

            # 管理费 = 人工单价 × 管理费率
            if mgmt_col and lab_col:
                cell = self.ws.cell(row=R, column=self.col_idx["mgmt"] + 1)
                cell.value = f"={lab_col}{R}*{mgmt_rate}"

            # 利润 = 人工单价 × 利润率
            if profit_col and lab_col:
                cell = self.ws.cell(row=R, column=self.col_idx["profit"] + 1)
                cell.value = f"={lab_col}{R}*{profit_rate}"

            # 综合单价：
            # - 子目行：保留值 = unit_price（不含管理费/利润加成）
            # - 父行：公式 = 人工 + 主材×(1+损耗率/100) + 辅材 + 管理费 + 利润
            if usp_col and not is_sub:
                parts = []
                if lab_col:
                    parts.append(f"{lab_col}{R}")
                if mat_col and waste_col:
                    parts.append(f"{mat_col}{R}*(1+{waste_col}{R}/100)")
                elif mat_col:
                    parts.append(f"{mat_col}{R}")
                if aux_col:
                    parts.append(f"{aux_col}{R}")
                if mgmt_col:
                    parts.append(f"{mgmt_col}{R}")
                if profit_col:
                    parts.append(f"{profit_col}{R}")
                if parts:
                    cell = self.ws.cell(row=R, column=self.col_idx["usp"] + 1)
                    cell.value = f"={'+'.join(parts)}"

            # 合价 = 综合单价 × 工程量
            if total_col and usp_col and qty_col:
                cell = self.ws.cell(row=R, column=self.col_idx["total"] + 1)
                cell.value = f"={usp_col}{R}*{qty_col}{R}"

    def _col_letter(self, key: str) -> Optional[str]:
        """获取列 key 对应的 Excel 列字母，不存在返回 None"""
        if key not in self.col_idx:
            return None
        return get_column_letter(self.col_idx[key] + 1)

    # ── 样式应用 ──────────────────────────────────────────

    def _apply_styles(self):
        """为所有单元格应用样式"""
        max_row = self.current_row
        max_col = len(self.cols)

        for r in range(1, max_row + 1):
            meta = self.row_meta[r - 1] if r <= len(self.row_meta) else {}
            row_type = meta.get("type", "")

            for c in range(1, max_col + 1):
                cell = self.ws.cell(row=r, column=c)
                col_key = self.cols[c - 1].key if c <= len(self.cols) else ""
                col_def = self.cols[c - 1] if c <= len(self.cols) else None

                # 字体
                if row_type == "title":
                    font = Font(name=FONT_NAME, bold=True, size=14)
                elif row_type == "header":
                    font = Font(name=FONT_NAME, bold=True, size=10)
                elif row_type == "summary":
                    font = Font(name=FONT_NAME, bold=True, size=10)
                else:
                    font = Font(name=FONT_NAME, size=10)

                # 对齐
                if row_type in ("title", "header"):
                    h_align = "center"
                elif col_def and col_def.num:
                    h_align = "right"
                elif col_key in ("seq", "unit"):
                    h_align = "center"
                else:
                    h_align = "left"

                alignment = Alignment(
                    vertical="center",
                    horizontal=h_align,
                    wrap_text=True,
                    shrink_to_fit=False,
                )

                # 填充
                fill = None
                if row_type == "header":
                    fill = FILL_HEADER
                elif row_type == "summary":
                    fill = FILL_SUMMARY

                cell.font = font
                cell.alignment = alignment
                cell.border = THIN_BORDER
                if fill:
                    cell.fill = fill

    # ── 列宽 ──────────────────────────────────────────────

    def _set_column_widths(self):
        for i, col in enumerate(self.cols):
            letter = get_column_letter(i + 1)
            width = col.width
            # 特殊列加宽
            if col.key == "spec":
                width = max(width, 55 if self.req.show_subs else 48)
            elif col.key == "name":
                width = max(width, 40 if self.req.show_subs else 32)
            elif col.key == "remark":
                width = max(width, 28)
            # 数字列不超过 14
            if col.num:
                width = min(width, 14)
            self.ws.column_dimensions[letter].width = width

    # ── 行高 ──────────────────────────────────────────────

    def _set_row_heights(self):
        for i, meta in enumerate(self.row_meta):
            r = i + 1  # 1-based
            row_type = meta.get("type", "")

            if row_type == "title":
                self.ws.row_dimensions[r].height = 30
            elif row_type == "header":
                self.ws.row_dimensions[r].height = 22
            elif row_type == "group":
                self.ws.row_dimensions[r].height = 20
            elif meta.get("is_data") or row_type == "section":
                # 根据内容估算行高
                max_lines = 1
                for c_idx, col in enumerate(self.cols):
                    cell = self.ws.cell(row=r, column=c_idx + 1)
                    val = cell.value
                    # 公式单元格按数字显示值估算
                    if isinstance(val, str) and val.startswith("="):
                        txt = "12345.67"  # 假设显示为数字
                    else:
                        txt = str(val or "")
                    if not txt:
                        continue
                    cw = col.width or 10
                    # Excel列宽单位基于默认字体，中文字符约为2倍宽
                    # 保守估算：每单位列宽约可容纳0.6个中文字符
                    cpl = max(1, int(cw * 0.6))
                    lines = (len(txt) + cpl - 1) // cpl
                    if lines > max_lines:
                        max_lines = lines
                # 10pt字体约18pt行高，留2pt间距
                height = max(20, min(300, max_lines * 18))
                self.ws.row_dimensions[r].height = height

    # ── 折叠/大纲 ─────────────────────────────────────────

    def _set_outline(self):
        if not self.req.group_folding:
            return

        self.ws.sheet_properties.outlinePr = None  # 使用默认
        # summaryBelow = False → 汇总行在明细上方
        self.ws.sheet_properties.outlinePr = self.ws.sheet_properties.outlinePr or type(
            self.ws.sheet_properties.outlinePr
        )(summaryBelow=False, summaryRight=True) if self.ws.sheet_properties.outlinePr else None

        # 手动设置 outlinePr
        from openpyxl.worksheet.properties import Outline
        self.ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)

        for i, meta in enumerate(self.row_meta):
            r = i + 1  # 1-based
            level = meta.get("level", 0)
            if level > 0:
                self.ws.row_dimensions[r].outlineLevel = level
            if meta.get("is_hidden"):
                self.ws.row_dimensions[r].hidden = True
