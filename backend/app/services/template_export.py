"""模板导出服务 — 用 openpyxl 在用户模板上填入数据并插入子目行"""
from __future__ import annotations

from io import BytesIO
from typing import List, Dict, Optional
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import RowDimension

from app.schemas.export import TemplateExportRequest, ExportRow, ExportSubItem


FONT_NAME = "微软雅黑"
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
NUM_FMT = '#,##0.00'


class TemplateExcelExporter:
    """在用户上传的模板上填入 BOQ 数据，支持子目行插入"""

    def __init__(self, request: TemplateExportRequest, template_bytes: bytes):
        self.req = request
        self.wb = load_workbook(BytesIO(template_bytes))
        self.ws = self.wb.active
        self.hdr_row = request.header_row  # 0-based header row index

        # Build reverse mapping: field_key → template column index (0-based)
        self.field_to_col: Dict[str, int] = {}
        for col_idx, field_key in request.column_mapping.items():
            self.field_to_col[field_key] = int(col_idx)

        # Track row info for outline grouping
        self.row_levels: Dict[int, int] = {}  # {1-based row: outline_level}
        self.sub_rows: set = set()            # 1-based row indices of sub-item rows

    def generate(self) -> BytesIO:
        """生成并返回 BytesIO 缓冲区"""
        self._fill_data()
        self._apply_styles()
        self._set_row_heights()
        self._set_outline()
        buf = BytesIO()
        self.wb.save(buf)
        buf.seek(0)
        return buf

    # ── 数据填入 ────────────────────────────────────────────

    def _fill_data(self):
        """遍历 BOQ 数据，在模板中填入数据、插入子目行"""
        if not self.field_to_col:
            raise ValueError("未匹配到任何数据列，请检查模板表头是否符合规范，或手动映射列。")
        if not self.req.groups:
            raise ValueError("无清单数据，请先导入 BOQ 并套价。")

        out_row = self.hdr_row + 2  # 1-based: header+1 = first data row
        folding = self.req.group_folding

        seq = 0
        for group in self.req.groups:
            for section in group.sections:
                for row in section.rows:
                    seq += 1
                    # 写入父行
                    self._write_data_row(out_row, row, seq)
                    if folding:
                        self.row_levels[out_row] = 2  # 父行 level 2
                    out_row += 1

                    # 子目行：在父行下方插入
                    if self.req.show_subs and row.subs:
                        n = len(row.subs)
                        self.ws.insert_rows(out_row, n)
                        # 复制父行样式到新插入的子目行
                        self._copy_row_style(out_row - 1, out_row, n)
                        for sub in row.subs:
                            self._write_sub_row(out_row, sub, row)
                            if folding:
                                self.row_levels[out_row] = 3  # 子目 level 3
                                self.sub_rows.add(out_row)
                            out_row += 1

        # 合计行
        self._write_summary_row(out_row)

    def _write_data_row(self, r: int, row: ExportRow, seq: int):
        """写入父行数据到模板第 r 行"""
        mgmt_rate = self.req.mgmt_rate / 100
        profit_rate = self.req.profit_rate / 100
        labor = row.labor_price or 0

        for field_key, col_idx in self.field_to_col.items():
            c = col_idx + 1  # openpyxl 1-based column
            cell = self.ws.cell(row=r, column=c)

            if field_key == "seq":
                cell.value = seq
            elif field_key == "code":
                cell.value = ""
            elif field_key == "name":
                cell.value = row.name or ""
            elif field_key == "spec":
                cell.value = row.spec or ""
            elif field_key == "unit":
                cell.value = row.unit or ""
            elif field_key == "qty":
                cell.value = row.qty or 0
            elif field_key == "lab":
                cell.value = labor
            elif field_key == "mat_name":
                cell.value = row.mat_name or ""
            elif field_key == "mat_price":
                cell.value = row.mat_price or 0
            elif field_key == "mat":
                # 主材费 = 主材单价 × (1 + 损耗率/100)
                mp = row.mat_price or 0
                wr = row.waste_rate or 0
                cell.value = mp * (1 + wr / 100)
            elif field_key == "waste":
                cell.value = row.waste_rate or 0
            elif field_key == "aux":
                cell.value = row.aux_cost or 0
            elif field_key == "mgmt":
                cell.value = labor * mgmt_rate
            elif field_key == "profit":
                cell.value = labor * profit_rate
            elif field_key == "usp":
                mat_cost = (row.mat_price or 0) * (1 + (row.waste_rate or 0) / 100)
                cell.value = labor + mat_cost + (row.aux_cost or 0) + labor * mgmt_rate + labor * profit_rate
            elif field_key == "total":
                usp = labor + (row.mat_price or 0) * (1 + (row.waste_rate or 0) / 100) + (row.aux_cost or 0) + labor * mgmt_rate + labor * profit_rate
                cell.value = usp * (row.qty or 0)
            elif field_key == "remark":
                cell.value = row.remark or ""

            # 数字格式
            if isinstance(cell.value, float):
                cell.number_format = NUM_FMT

    def _write_sub_row(self, r: int, sub: ExportSubItem, parent: ExportRow):
        """写入子目行数据到模板第 r 行"""
        ep = sub.unit_price or 0
        sub_qty = (parent.qty or 0) * (sub.conv or 1.0) * (sub.coef or 1.0)
        mgmt_rate = self.req.mgmt_rate / 100
        profit_rate = self.req.profit_rate / 100

        for field_key, col_idx in self.field_to_col.items():
            c = col_idx + 1
            cell = self.ws.cell(row=r, column=c)

            if field_key == "seq":
                cell.value = ""
            elif field_key == "code":
                cell.value = str(sub.bid or "")
            elif field_key == "name":
                cell.value = f"  └ {sub.name or ''}"
            elif field_key == "spec":
                cell.value = sub.spec or ""
            elif field_key == "unit":
                cell.value = sub.unit or ""
            elif field_key == "qty":
                cell.value = sub_qty
            elif field_key == "lab":
                cell.value = ep
            elif field_key == "mat":
                cell.value = 0
            elif field_key == "waste":
                cell.value = parent.waste_rate or 0
            elif field_key == "aux":
                cell.value = 0
            elif field_key == "mgmt":
                cell.value = ep * mgmt_rate
            elif field_key == "profit":
                cell.value = ep * profit_rate
            elif field_key == "usp":
                cell.value = ep  # 子目 USP 不加管理费/利润
            elif field_key == "total":
                cell.value = ep * sub_qty
            elif field_key == "remark":
                cell.value = ""

            if isinstance(cell.value, float):
                cell.number_format = NUM_FMT

    def _write_summary_row(self, r: int):
        """在模板末尾写入合计行"""
        for field_key, col_idx in self.field_to_col.items():
            c = col_idx + 1
            cell = self.ws.cell(row=r, column=c)

            if field_key == "name":
                cell.value = "合计"
            elif field_key == "total":
                col_letter = get_column_letter(c)
                # SUM: header+2 to r-1 (all data rows)
                first = self.hdr_row + 2
                last = r - 1
                if last >= first:
                    cell.value = f"=SUM({col_letter}{first}:{col_letter}{last})"
                    cell.number_format = NUM_FMT

            # 合计行加粗 + 顶边框
            cell.font = Font(name=FONT_NAME, bold=True, size=10)
            cell.border = Border(
                top=Side(style="thin"),
                bottom=Side(style="thin"),
                left=Side(style="thin"),
                right=Side(style="thin"),
            )

    # ── 格式套用（与方式一配置导出保持一致）──────────────

    def _apply_styles(self):
        """为数据区域单元格应用统一格式：字体、对齐、边框、自动换行"""
        max_data_row = self.ws.max_row
        max_col = len(self.field_to_col)
        if max_col == 0:
            return

        # 列属性：从 field_to_col 推断各列的对齐方式
        center_keys = {"seq", "code", "unit"}
        num_keys = {"qty", "lab", "mat", "waste", "aux", "mgmt", "profit", "usp", "total"}

        for r in range(self.hdr_row + 2, max_data_row + 1):
            for c in range(1, max_col + 1):
                cell = self.ws.cell(row=r, column=c)

                # 找出该列对应的 field_key
                field_key = None
                for fk, ci in self.field_to_col.items():
                    if ci + 1 == c:
                        field_key = fk
                        break

                align_h = "left"
                if field_key in center_keys:
                    align_h = "center"
                elif field_key in num_keys:
                    align_h = "right"

                cell.alignment = Alignment(
                    vertical="center",
                    horizontal=align_h,
                    wrap_text=True,
                    shrink_to_fit=False,
                )
                cell.font = Font(name=FONT_NAME, size=10)
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )

                # 数字格式
                if field_key in num_keys and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT

        # 表头行样式（保留原字体大小，补齐对齐和边框）
        hdr_row_1based = self.hdr_row + 1
        for c in range(1, max_col + 1):
            cell = self.ws.cell(row=hdr_row_1based, column=c)
            current_align = cell.alignment
            cell.alignment = Alignment(
                vertical="center",
                horizontal="center",
                wrap_text=True,
            )
            if not cell.font or not cell.font.bold:
                cell.font = Font(name=FONT_NAME, bold=True, size=cell.font.size if cell.font and cell.font.size else 10)
            cell.border = Border(
                left=Side(style="thin"), right=Side(style="thin"),
                top=Side(style="thin"), bottom=Side(style="thin"),
            )

    def _set_row_heights(self):
        """根据内容自动估算行高"""
        max_data_row = self.ws.max_row
        max_col = len(self.field_to_col)
        if max_col == 0:
            return

        # 估算列宽（从模板读取，无则默认 10）
        col_widths = {}
        for c in range(1, max_col + 1):
            letter = get_column_letter(c)
            dim = self.ws.column_dimensions.get(letter)
            col_widths[c] = dim.width if dim and dim.width else 10

        for r in range(self.hdr_row + 2, max_data_row + 1):
            max_lines = 1
            for c in range(1, max_col + 1):
                cell = self.ws.cell(row=r, column=c)
                val = cell.value
                if isinstance(val, str) and val.startswith("="):
                    txt = "12345.67"
                else:
                    txt = str(val or "")
                if not txt:
                    continue
                cw = col_widths.get(c, 10)
                cpl = max(1, int(cw * 0.6))
                lines = (len(txt) + cpl - 1) // cpl
                if lines > max_lines:
                    max_lines = lines
            height = max(20, min(300, max_lines * 18))
            self.ws.row_dimensions[r].height = height

    def _set_outline(self):
        """设置分组折叠：summaryBelow=false，子目行初始折叠、level=3"""
        if not self.req.group_folding:
            return

        from openpyxl.worksheet.properties import Outline
        self.ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)

        for r, level in self.row_levels.items():
            self.ws.row_dimensions[r].outlineLevel = level
        for r in self.sub_rows:
            self.ws.row_dimensions[r].hidden = True

    def _copy_row_style(self, src_row: int, start_row: int, count: int):
        """将源行的样式（字体/对齐/边框/列宽）复制到插入行"""
        for c in range(1, self.ws.max_column + 1):
            src_cell = self.ws.cell(row=src_row, column=c)
            for offset in range(count):
                target = self.ws.cell(row=start_row + offset, column=c)
                if src_cell.font:
                    target.font = Font(
                        name=src_cell.font.name or FONT_NAME,
                        size=src_cell.font.size or 10,
                        bold=src_cell.font.bold or False,
                    )
                if src_cell.alignment:
                    target.alignment = Alignment(
                        vertical=src_cell.alignment.vertical or "center",
                        horizontal=src_cell.alignment.horizontal or "left",
                        wrap_text=True,
                    )
                if src_cell.border:
                    target.border = Border(
                        left=Side(style=src_cell.border.left.style or "thin"),
                        right=Side(style=src_cell.border.right.style or "thin"),
                        top=Side(style=src_cell.border.top.style or "thin"),
                        bottom=Side(style=src_cell.border.bottom.style or "thin"),
                    )
