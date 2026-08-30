"""辅材费用清单导出服务 — 分工种·品种明细（口径B）

每个工种一个 sheet，行为辅材品种（消耗量合计 × 信息价 = 合价），
FIXED 类子目拆不出品种，归入「固定辅材费（定额包干）」行；
末尾生成「辅材汇总」sheet（工种 → 材料费/固定费/合计 + 总计）。
"""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from app.schemas.export import AuxGroup, AuxListExportRequest
from app.services.excel_export import FONT_NAME, FILL_HEADER, NUM_FMT, THIN_BORDER

HEADER_LABELS = ["序号", "辅材名称", "单位", "消耗量合计", "信息价(元)", "合价(元)", "备注"]
COL_WIDTHS = [6, 26, 8, 14, 12, 14, 16]
FIXED_LINE_NAME = "固定辅材费（定额包干）"


class AuxListExporter:
    """将 AuxListExportRequest 转换为辅材费用清单 Workbook"""

    def __init__(self, request: AuxListExportRequest):
        self.req = request
        self.wb = Workbook()
        self.wb.remove(self.wb.active)  # 按需创建工种 sheet

    def generate(self) -> BytesIO:
        for group in self.req.groups:
            if group.lines:
                self._write_trade_sheet(group)
        self._write_summary_sheet()

        buf = BytesIO()
        self.wb.save(buf)
        buf.seek(0)
        return buf

    def _title(self) -> str:
        suffix = f"（信息价月份：{self.req.price_month}）" if self.req.price_month else ""
        return suffix

    def _write_trade_sheet(self, group: AuxGroup):
        ws = self.wb.create_sheet(title=group.sheet_name)
        n_cols = len(HEADER_LABELS)

        # 标题行
        ws.cell(row=1, column=1, value=f"{group.sheet_name}辅材费用清单{self._title()}")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
        title_cell = ws.cell(row=1, column=1)
        title_cell.font = Font(name=FONT_NAME, bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        # 表头
        for c, label in enumerate(HEADER_LABELS, start=1):
            cell = ws.cell(row=2, column=c, value=label)
            cell.font = Font(name=FONT_NAME, bold=True)
            cell.fill = FILL_HEADER
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # 品种行（前端已按合价降序、固定费行置尾）
        r = 3
        seq = 0
        for line in group.lines:
            seq += 1
            ws.cell(row=r, column=1, value=seq)
            ws.cell(row=r, column=2, value=line.name)
            ws.cell(row=r, column=3, value=line.unit or ("—" if line.is_fixed else ""))
            if line.is_fixed:
                ws.cell(row=r, column=4, value="—")
                ws.cell(row=r, column=5, value="—")
            else:
                ws.cell(row=r, column=4, value=line.qty_total)
                ws.cell(row=r, column=5, value=line.price)
            ws.cell(row=r, column=6, value=line.subtotal)
            ws.cell(row=r, column=7, value="定额包干" if line.is_fixed else "")
            r += 1

        # 小计行
        ws.cell(row=r, column=2, value="辅材小计")
        ws.cell(row=r, column=6, value=group.total)

        # 样式：表头/小计加粗，数值列统一格式
        for row in ws.iter_rows(min_row=2, max_row=r, min_col=1, max_col=n_cols):
            for cell in row:
                cell.font = Font(name=FONT_NAME, bold=(cell.row in (2, r)))
                cell.border = THIN_BORDER
                if cell.column in (4, 5, 6) and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT

        for i, width in enumerate(COL_WIDTHS, start=1):
            ws.column_dimensions[chr(64 + i)].width = width

    def _write_summary_sheet(self):
        ws = self.wb.create_sheet(title="辅材汇总")
        headers = ["工种", "其中材料费", "其中固定辅材费", "辅材合计"]

        ws.cell(row=1, column=1, value=f"{self.req.project_name} 辅材汇总{self._title()}")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        title_cell = ws.cell(row=1, column=1)
        title_cell.font = Font(name=FONT_NAME, bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        for c, label in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=c, value=label)
            cell.font = Font(name=FONT_NAME, bold=True)
            cell.fill = FILL_HEADER
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")

        r = 3
        grand = [0.0, 0.0, 0.0]  # 材料费 / 固定费 / 合计
        for group in self.req.groups:
            if not group.lines:
                continue
            ws.cell(row=r, column=1, value=group.sheet_name)
            ws.cell(row=r, column=2, value=group.material_subtotal)
            ws.cell(row=r, column=3, value=group.fixed_subtotal)
            ws.cell(row=r, column=4, value=group.total)
            grand[0] += group.material_subtotal
            grand[1] += group.fixed_subtotal
            grand[2] += group.total
            r += 1

        ws.cell(row=r, column=1, value="总计")
        ws.cell(row=r, column=2, value=grand[0])
        ws.cell(row=r, column=3, value=grand[1])
        ws.cell(row=r, column=4, value=grand[2])

        for row in ws.iter_rows(min_row=2, max_row=r, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.font = Font(name=FONT_NAME, bold=(cell.row in (2, r)))
                cell.border = THIN_BORDER
                if cell.column >= 2 and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 16
        ws.column_dimensions["D"].width = 16
