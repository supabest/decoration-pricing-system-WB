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
        # 公式模式：记录每个工种 sheet 的小计行/固定费行，供「辅材汇总」sheet 写跨表引用
        self._sheet_refs = {}   # sheet_name -> {"sub_row": int, "fixed_row": int|None}

    def _q(self, sheet_name: str) -> str:
        """公式里的 sheet 名引用（包裹单引号，防特殊字符）"""
        return "'" + str(sheet_name).replace("'", "''") + "'"

    def generate(self) -> BytesIO:
        for group in self.req.groups:
            if group.lines:
                self._write_trade_sheet(group)
        self._write_summary_sheet()
        if self.req.unclassified:
            self._write_unclassified_sheet()

        buf = BytesIO()
        self.wb.save(buf)
        buf.seek(0)
        return buf

    def _write_trade_sheet(self, group: AuxGroup):
        ws = self.wb.create_sheet(title=group.sheet_name)
        n_cols = len(HEADER_LABELS)

        # 标题行
        ws.cell(row=1, column=1, value=f"{group.sheet_name}辅材费用清单")
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
        use_formula = bool(getattr(self.req, "use_formula", True))
        r = 3
        seq = 0
        fixed_row = None
        for line in group.lines:
            seq += 1
            ws.cell(row=r, column=1, value=seq)
            ws.cell(row=r, column=2, value=line.name)
            ws.cell(row=r, column=3, value=line.unit or ("—" if line.is_fixed else ""))
            if line.is_fixed:
                ws.cell(row=r, column=4, value="—")
                ws.cell(row=r, column=5, value="—")
                fixed_row = r
            else:
                ws.cell(row=r, column=4, value=line.qty_total)
                ws.cell(row=r, column=5, value=line.price)
            # 合价：公式模式 = 消耗量合计×信息价（固定费行为静态数值）
            if use_formula and not line.is_fixed:
                fcell = ws.cell(row=r, column=6, value=f"=D{r}*E{r}")
                fcell.number_format = NUM_FMT
            else:
                fcell = ws.cell(row=r, column=6, value=line.subtotal)
                fcell.number_format = NUM_FMT
            ws.cell(row=r, column=7, value="定额包干" if line.is_fixed else "")
            r += 1
        last_line_row = r - 1

        # 小计行：公式模式 = SUM(品种行合价)，否则静态数值
        sub_row = r
        sub_cell = ws.cell(row=r, column=6,
                           value=f"=SUM(F3:F{last_line_row})" if use_formula else group.total)
        sub_cell.number_format = NUM_FMT
        self._sheet_refs[group.sheet_name] = {"sub_row": sub_row, "fixed_row": fixed_row}

        # 样式：表头/小计加粗，数值列统一格式
        for row in ws.iter_rows(min_row=2, max_row=r, min_col=1, max_col=n_cols):
            for cell in row:
                cell.font = Font(name=FONT_NAME, bold=(cell.row in (2, r)))
                cell.border = THIN_BORDER
                if cell.column in (4, 5, 6) and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT

        for i, width in enumerate(COL_WIDTHS, start=1):
            ws.column_dimensions[chr(64 + i)].width = width

        # 表格下方的口径说明：固定费用包干辅材拆不出品种明细，合计仅供预测总费用
        note_row = r + 1
        ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=n_cols)
        note = ws.cell(
            row=note_row, column=1,
            value="注：因基准单价大部分辅材单价为固定费用包干，没有明细，此表之辅材费用仅供预测该工种辅材总费用之用。",
        )
        note.font = Font(name=FONT_NAME, italic=True, size=10, color="808080")
        note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.row_dimensions[note_row].height = 30

    def _write_unclassified_sheet(self):
        """未套子目清单：列出辅材费未计入汇总的清单项，供用户人工补充、避免漏算"""
        ws = self.wb.create_sheet(title="⚠️未套子目清单")
        headers = ["序号", "项目名称", "项目特征", "单位", "工程量", "原因", "需补辅材费(元)"]
        n_cols = len(headers)

        ws.cell(row=1, column=1, value="未套子目清单（辅材费未计入各工种汇总）")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
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
        for i, u in enumerate(self.req.unclassified, start=1):
            ws.cell(row=r, column=1, value=i)
            ws.cell(row=r, column=2, value=u.name)
            ws.cell(row=r, column=3, value=u.spec)
            ws.cell(row=r, column=4, value=u.unit)
            ws.cell(row=r, column=5, value=u.qty)
            ws.cell(row=r, column=6, value=u.reason)
            # 第7列留空，供用户人工填写需补充的辅材费
            r += 1

        for row in ws.iter_rows(min_row=2, max_row=r - 1, min_col=1, max_col=n_cols):
            for cell in row:
                cell.font = Font(name=FONT_NAME, bold=(cell.row == 2))
                cell.border = THIN_BORDER
                if cell.column == 5 and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT
                # 项目名称/项目特征列自动换行，长文字全部显示（行高不锁定 → Excel 自动适配）
                if cell.column in (2, 3) and cell.row > 2:
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

        for i, width in enumerate([6, 28, 34, 8, 12, 12, 16], start=1):
            ws.column_dimensions[chr(64 + i)].width = width

        # 表格下方的填写说明
        note_row = r + 1
        ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=n_cols)
        note = ws.cell(
            row=note_row, column=1,
            value="注：以下清单项未套子目，其辅材费未计入本清单各工种汇总；请在「需补辅材费」列自行评估填写，避免漏算。",
        )
        note.font = Font(name=FONT_NAME, italic=True, size=10, color="808080")
        note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.row_dimensions[note_row].height = 30

    def _write_summary_sheet(self):
        ws = self.wb.create_sheet(title="辅材汇总")
        # 占总成本比例：总成本 = 对甲合同金额 × (1 - 目标利润率/100)；合同金额未填(<=0)时整列不输出
        cost_base = None
        if self.req.contract_amount and self.req.contract_amount > 0:
            cost_base = self.req.contract_amount * (1 - (self.req.target_profit_rate or 0) / 100.0)
        headers = ["工种", "其中材料费", "其中固定辅材费", "辅材合计"]
        if cost_base:
            headers.append("占总成本比例")

        ws.cell(row=1, column=1, value=f"{self.req.project_name} 辅材汇总")
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
        first_data_row = r
        grand = [0.0, 0.0, 0.0]  # 材料费 / 固定费 / 合计
        use_formula = bool(getattr(self.req, "use_formula", True))
        for group in self.req.groups:
            if not group.lines:
                continue
            ws.cell(row=r, column=1, value=group.sheet_name)
            refs = self._sheet_refs.get(group.sheet_name) if use_formula else None
            if refs:
                s = self._q(group.sheet_name)
                sub, fixed = refs["sub_row"], refs.get("fixed_row")
                mat_cell = ws.cell(row=r, column=2,
                                   value=(f"={s}!F{sub}-{s}!F{fixed}" if fixed else f"={s}!F{sub}"))
                mat_cell.number_format = NUM_FMT
                if fixed:
                    fix_cell = ws.cell(row=r, column=3, value=f"={s}!F{fixed}")
                    fix_cell.number_format = NUM_FMT
                else:
                    ws.cell(row=r, column=3, value=0).number_format = NUM_FMT
                tot_cell = ws.cell(row=r, column=4, value=f"={s}!F{sub}")
                tot_cell.number_format = NUM_FMT
            else:
                ws.cell(row=r, column=2, value=group.material_subtotal).number_format = NUM_FMT
                ws.cell(row=r, column=3, value=group.fixed_subtotal).number_format = NUM_FMT
                ws.cell(row=r, column=4, value=group.total).number_format = NUM_FMT
            if cost_base:
                ratio = ws.cell(row=r, column=5,
                                value=(f"=D{r}/{cost_base}" if (use_formula and refs) else group.total / cost_base))
                ratio.number_format = '0.00%'
            grand[0] += group.material_subtotal
            grand[1] += group.fixed_subtotal
            grand[2] += group.total
            r += 1
        last_data_row = r - 1

        ws.cell(row=r, column=1, value="总计")
        if use_formula and last_data_row >= first_data_row:
            for col, letter in ((2, "B"), (3, "C"), (4, "D")):
                c = ws.cell(row=r, column=col, value=f"=SUM({letter}{first_data_row}:{letter}{last_data_row})")
                c.number_format = NUM_FMT
        else:
            ws.cell(row=r, column=2, value=grand[0]).number_format = NUM_FMT
            ws.cell(row=r, column=3, value=grand[1]).number_format = NUM_FMT
            ws.cell(row=r, column=4, value=grand[2]).number_format = NUM_FMT
        if cost_base:
            ratio = ws.cell(row=r, column=5, value=grand[2] / cost_base if not use_formula else f"=D{r}/{cost_base}")
            ratio.number_format = '0.00%'

        for row in ws.iter_rows(min_row=2, max_row=r, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.font = Font(name=FONT_NAME, bold=(cell.row in (2, r)))
                cell.border = THIN_BORDER
                if cell.column >= 2 and cell.column < 5 and isinstance(cell.value, (int, float)):
                    cell.number_format = NUM_FMT

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 16
        ws.column_dimensions["D"].width = 16
        if cost_base:
            ws.column_dimensions["E"].width = 14
