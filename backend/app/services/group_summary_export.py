"""ZS02-T02 集团汇总表导出服务（对甲报价）

口径（集团计价办法 2024 版 · 与前端 docs/tool.html:buildGroupSummary / groupSubPrice 逐式同源）：
  单价  H = A人工 + Σ(Bi主材单价 × Ci消耗量) + D辅材 + E机械 + (A+E)×mgmt + (A+E)×profit
  一 · 分部分项工程费 = Σ 非 D 类子目合价（H × coef × conv × qty），按「专业·分部」归集小计
  二 · 措施项目费     = Σ D 类合价 + 绿安费；绿安费 = ∑(分部分项 人工+机械) × green
  三 · 其他项目费     = 预算包干费 ∑(分部分项 人工+机械) × baogan + Σ手工费用 + 精装修配合费
                        （coordFee × 装修面积；coordFee=None 未配置 → 不计取，备注留痕）；暂列金额固定 0
  四 · 税金           = (一+二+三) × tax      五 · 总造价 = 一+二+三+四    单方 = 五 ÷ 装修面积

★ 费率一律来自 request.rates（缺省即 T01 种子），本文件逻辑分支内不出现任何费率字面量。
★ 待询价判据：mats[].price is None（甲供未限价）；mats==[] 与 price=0 都是合法常态，不算待询价。
  端点层已前置拦截（绝不带待询价出表），服务层同时把 pending 子目排除在各部分之外，避免绕过口径。

Excel 样式/公式列惯例参照 app/services/excel_export.py（分组折叠 + 合计行 SUM 只覆盖父行、
不打进组头行），汇总合计行写成 Excel 公式（口径同方式一），供甲方在 Excel 内复核。
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import Outline

from app.schemas.group_export import GroupSummaryItem, GroupSummaryRequest

# ── 样式常量（沿用 excel_export.py）────────────────────────────────────
FONT_NAME = "微软雅黑"
THIN_BORDER = Border(left=Side(style="thin"), right=Side(style="thin"),
                     top=Side(style="thin"), bottom=Side(style="thin"))
FILL_HEADER = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
FILL_GROUP = PatternFill(start_color="EEF3F8", end_color="EEF3F8", fill_type="solid")
FILL_SUMMARY = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
NUM_FMT = '#,##0.00'

SHEET_ITEMS = "清单明细"
SHEET_SUMMARY = "单位工程计价汇总表"

DISCIPLINE_MEASURES = "D"          # ZS02-D = 单价措施项目：只进第二部分，不进第一部分/绿安·包干基数
COORD_UNSET_REMARK = "参数未配置（未计取）"

# sheet1 列定义：ZS02 单价组成 A~H 全分解（F/G/H/合价 写为 Excel 公式列）
ITEM_COLUMNS: List[Dict[str, Any]] = [
    {"key": "seq", "label": "序号", "width": 5, "num": True},
    {"key": "code", "label": "子目编码", "width": 13},
    {"key": "discipline", "label": "专业", "width": 6},
    {"key": "section_name", "label": "分部", "width": 14},
    {"key": "name", "label": "项目名称", "width": 20},
    {"key": "spec", "label": "项目特征", "width": 24},
    {"key": "unit", "label": "单位", "width": 7},
    {"key": "work_type", "label": "工种", "width": 8},
    {"key": "coef", "label": "含量系数", "width": 9, "num": True},
    {"key": "conv", "label": "换算系数", "width": 9, "num": True},
    {"key": "qty", "label": "工程量", "width": 9, "num": True},
    {"key": "lab", "label": "A 人工", "width": 11, "num": True},
    {"key": "mat", "label": "B 主材费", "width": 12, "num": True},
    {"key": "aux", "label": "D 辅材", "width": 10, "num": True},
    {"key": "mech", "label": "E 机械", "width": 10, "num": True},
    {"key": "mgmt", "label": "F 管理费", "width": 11, "num": True},
    {"key": "profit", "label": "G 利润", "width": 11, "num": True},
    {"key": "h", "label": "H 综合单价", "width": 13, "num": True},
    {"key": "amount", "label": "合价", "width": 13, "num": True},
    {"key": "remark", "label": "备注", "width": 20},
]

# sheet1 右对齐列：数字列（序号除外，与组头/合计的文字标签同列）
ITEM_RIGHT_COLS = tuple(i + 1 for i, col in enumerate(ITEM_COLUMNS)
                        if col.get("num") and col["key"] != "seq")


def _pct(v: Optional[float]) -> str:
    """费率显示：0.17 → 17%（同前端 groupRateLabel；None/坏值 → —）"""
    if v is None:
        return "—"
    try:
        return f"{round(float(v) * 10000) / 100:g}%"
    except (TypeError, ValueError):
        return "—"


def _money(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:,.2f}"


def _num(v: float) -> str:
    """写进公式的数值字面量：0.17 → '0.17'、100 → '100'（不出现 100.0）。

    F7：固定 6 位小数 + 尾零裁剪，弃用 `:g`——`:g` 对大数切科学计数（1234567 → 1.23457e+06）
    且 6 位有效数字会舍入大金额，Excel 公式都无法解析/失真。"""
    s = f"{float(v):.6f}".rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


class GroupSummaryExporter:
    """把 GroupSummaryRequest 重算为 T02 四部分汇总，并生成双 sheet xlsx"""

    def __init__(self, request: GroupSummaryRequest):
        self.req = request

    # ── 重算 ────────────────────────────────────────────────────────

    @staticmethod
    def pending_codes(req: GroupSummaryRequest) -> List[str]:
        """待询价子目编码（去重、保持首次出现顺序）；端点据此 400 拦截导出。"""
        codes: List[str] = []
        for item in req.items:
            if any(m.price is None for m in item.mats):
                if item.code not in codes:
                    codes.append(item.code)
        return codes

    def sub_price(self, item: GroupSummaryItem) -> Dict[str, Any]:
        """单条集团子目重算：H 及其 A~G 分量（公式同 groupSubPrice / import_group_benchmark.recalc_h）。"""
        R = self.req.rates
        lab, aux, mech = item.lab, item.aux, item.mech
        mat = 0.0
        pending_names: List[str] = []
        for m in item.mats:
            if m.price is None:                 # 甲供未限价：不计假值，只登记待询价
                pending_names.append(m.name or "主材")
                continue
            mat += m.price * m.consumption      # 消耗量口径（源表已含损耗，不再乘损耗率）
        lm = lab + mech                         # 管理费/利润基数只认「人工+机械」
        mgmt = lm * R.mgmt
        profit = lm * R.profit
        return {
            "code": item.code, "discipline": item.discipline, "section_name": item.section_name,
            "name": item.name, "spec": item.spec, "unit": item.unit, "work_type": item.work_type,
            "qty": item.qty, "coef": item.coef, "conv": item.conv,
            "lab": lab, "mat": mat, "aux": aux, "mech": mech,
            "mgmt": mgmt, "profit": profit,
            "h": lab + mat + aux + mech + mgmt + profit,
            "pending": bool(pending_names), "pending_names": pending_names,
        }

    def compute(self) -> Dict[str, Any]:
        """T02 四部分汇总 + 分部小计 + 明细行（前端面板与 Excel 共用同一份结果）"""
        R = self.req.rates
        area = max(0.0, self.req.fitout_area or 0.0)   # 负面积钳 0，避免配合费倒扣
        part1 = d_measures = base = 0.0
        unpriced = 0   # 计数单位为子目级（F1 后前端 buildGroupSummary 同为子目级，两端镜像）；端点前置 400 拦截
        sections: Dict[str, Dict[str, Any]] = {}
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for item in self.req.items:
            p = self.sub_price(item)
            # coef/conv 为 0 时按前端 parseFloat()||1.0 同口径当 1.0，不让金额整体消失
            k = (item.coef or 1.0) * (item.conv or 1.0)
            amount = p["h"] * k * (item.qty or 0.0)
            p.update({"amount": amount, "group": f"{item.discipline}·{item.section_name}"})
            groups.setdefault(p["group"], []).append(p)
            if p["pending"]:                        # 待询价：不进任何部分，仅计数
                unpriced += 1
                p["counted"] = False
                continue
            p["counted"] = True
            if item.discipline == DISCIPLINE_MEASURES:   # D 类合价只进 part2
                d_measures += amount
                continue
            part1 += amount
            base += (p["lab"] + p["mech"]) * k * (item.qty or 0.0)
            sec = sections.setdefault(p["group"], {"name": p["group"], "amount": 0.0})
            sec["amount"] += amount

        green = base * R.green
        # 对甲补录手工行：后端重算 amount=qty×usp（前端值不被信任），measure→二、other→三，不入绿安/包干基数
        manual_measure_total = sum((ln.qty or 0.0) * (ln.usp or 0.0) for ln in self.req.manual_measures)
        manual_other_total = sum((ln.qty or 0.0) * (ln.usp or 0.0) for ln in self.req.manual_others)
        part2 = d_measures + manual_measure_total + green
        baogan = base * R.baogan
        coord_configured = R.coordFee is not None
        coord_amount = (R.coordFee or 0.0) * area if coord_configured else 0.0
        mf = self.req.manual_fees
        manual_total = (max(0.0, mf.overtime_fee) + max(0.0, mf.contract_change_fee)
                        + max(0.0, mf.inflation_fee))
        part3 = baogan + manual_total + coord_amount + manual_other_total
        part4 = (part1 + part2 + part3) * R.tax
        total = part1 + part2 + part3 + part4
        return {
            "project_name": self.req.project_name, "area": area,
            "part1": part1, "part2": part2, "part3": part3, "part4": part4,
            "total": total, "per_sqm": (total / area if area > 0 else None),
            "labor_mech_base": base, "green": green, "d_measures": d_measures,
            "manual_measure_total": manual_measure_total, "manual_other_total": manual_other_total,
            "manual_measure_lines": self.req.manual_measures, "manual_other_lines": self.req.manual_others,
            "baogan": baogan, "coord_amount": coord_amount,
            "coord_configured": coord_configured,
            "manual_total": manual_total,
            "manual_fees": {"赶工措施费": max(0.0, mf.overtime_fee),
                            "合同变更费用": max(0.0, mf.contract_change_fee),
                            "装修类型涨幅费用": max(0.0, mf.inflation_fee)},
            "sections": list(sections.values()), "groups": list(groups.items()),
            "unpriced": unpriced,
        }

    def summary_rows(self) -> List[Dict[str, Any]]:
        """T02 核心六行（勾稽口径）：label 供断言取数，remark 留痕所用费率"""
        c = self.compute()
        R = self.req.rates
        return [
            {"label": "分部分项", "amount": c["part1"],
             "remark": f"一 · Σ已套价合价（不含 {DISCIPLINE_MEASURES} 类措施）；"
                       f"管理费 {_pct(R.mgmt)}/利润 {_pct(R.profit)}，基数=人工+机械"},
            {"label": "措施项目", "amount": c["part2"],
             "remark": f"二 · D类措施 {_money(c['d_measures'])} + 手工补录 {_money(c['manual_measure_total'])} + 绿安费 {_money(c['green'])}"
                       f"（基数 {_money(c['labor_mech_base'])} × {_pct(R.green)}）"},
            {"label": "其他项目", "amount": c["part3"],
             "remark": f"三 · 预算包干 {_money(c['baogan'])} + 手工费用 {_money(c['manual_total'])} + 手工补录行 {_money(c['manual_other_total'])}"
                       f" + 精装修配合费 {_money(c['coord_amount'])}；暂列金额集团规定不予计取"},
            {"label": "税金", "amount": c["part4"], "remark": f"四 · (一+二+三) × {_pct(R.tax)}"},
            {"label": "总造价", "amount": c["total"], "remark": "五 · 一+二+三+四"},
            {"label": "单方造价", "amount": c["per_sqm"] or 0.0,
             "remark": (f"五 ÷ 装修面积 {_num(c['area'])} m²" if c["per_sqm"] is not None
                        else "装修面积未填写，不计算单方造价")},
        ]

    # ── Excel ───────────────────────────────────────────────────────

    def generate(self) -> BytesIO:
        """生成双 sheet xlsx（sheet1 清单明细 A~H 分解、sheet2 单位工程计价汇总表）"""
        c = self.compute()
        wb = Workbook()
        wb.remove(wb.active)
        self._write_items_sheet(wb, c)
        self._write_summary_sheet(wb, c)
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    @staticmethod
    def _safe_text(val: Any) -> Any:
        """F7 Excel 公式注入护栏：文本单元格值以 =/+/-/@ 开头则前置 ' 转义（只针对文字列，
        公式列 mgmt/profit/h/amount 不经此函数）。"""
        if isinstance(val, str) and val[:1] in ('=', '+', '-', '@'):
            return "'" + val
        return val

    # sheet1：清单明细（一条子目一行，组头行按「专业·分部」分组折叠）

    def _write_items_sheet(self, wb: Workbook, c: Dict[str, Any]):
        ws = wb.create_sheet(title=SHEET_ITEMS)
        col_letters = {col["key"]: get_column_letter(i + 1) for i, col in enumerate(ITEM_COLUMNS)}
        ncol = len(ITEM_COLUMNS)
        self._put_title(ws, 1, f"{c['project_name']}  清单明细（ZS02 单价组成 A~H 分解）", ncol)
        for i, col in enumerate(ITEM_COLUMNS):
            ws.cell(row=2, column=i + 1, value=col["label"])
        self._style_row(ws, 2, ncol, "header")
        ws.freeze_panes = "A3"

        r = 3
        seq = 0
        data_rows: List[int] = []
        for gname, entries in c["groups"]:
            ws.cell(row=r, column=1, value=f"【{gname}】")
            self._style_row(ws, r, ncol, "group")
            ws.row_dimensions[r].outlineLevel = 1
            r += 1
            for it in entries:
                seq += 1
                self._write_item_row(ws, r, seq, it, col_letters)
                if it["counted"]:               # 待询价行不进合计 SUM 区间（不拼假值）
                    data_rows.append(r)
                ws.row_dimensions[r].outlineLevel = 2
                self._style_row(ws, r, ncol, "data", ITEM_RIGHT_COLS)
                r += 1
        self._write_items_total(ws, r, col_letters, c, data_rows)
        # 分组折叠：汇总行在明细上方（同 excel_export._set_outline）
        ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)
        self._set_widths(ws, ITEM_COLUMNS)

    def _write_item_row(self, ws, r: int, seq: int, it: Dict[str, Any], letters: Dict[str, str]):
        R = self.req.rates
        values = {
            "seq": seq, "code": it["code"], "discipline": it["discipline"],
            "section_name": it["section_name"], "name": it["name"], "spec": it["spec"],
            "unit": it["unit"], "work_type": it["work_type"],
            "coef": it["coef"], "conv": it["conv"], "qty": it["qty"],
            "lab": it["lab"], "mat": round(it["mat"], 4), "aux": it["aux"], "mech": it["mech"],
            "remark": "",
        }
        # lm_l = A 人工列字母、mech_l = E 机械列字母（命名避开「h」：h 在本表里是 H 综合单价列/键）
        lm_l, mech_l = letters["lab"], letters["mech"]
        values["mgmt"] = f"=({lm_l}{r}+{mech_l}{r})*{_num(R.mgmt)}"
        values["profit"] = f"=({lm_l}{r}+{mech_l}{r})*{_num(R.profit)}"
        values["h"] = f"={lm_l}{r}+{letters['mat']}{r}+{letters['aux']}{r}+{mech_l}{r}" \
                      f"+{letters['mgmt']}{r}+{letters['profit']}{r}"
        values["amount"] = f"={letters['h']}{r}*{letters['coef']}{r}*{letters['conv']}{r}" \
                           f"*{letters['qty']}{r}"
        if it["pending"]:
            # 待询价：H/合价不拼假值（与前端 rowGroupAgg「pending → unit:null」同口径），也不进合计；
            # A/B/D/E/F/G 仍照实展示（已知分量，供判断还差哪几条价）
            values["h"] = values["amount"] = "待询价"
            values["remark"] = "甲供待询价：" + "、".join(it["pending_names"]) + "（不计入汇总）"
        for i, col in enumerate(ITEM_COLUMNS):
            val = values.get(col["key"], "")
            if col["key"] in ("name", "spec", "section_name"):   # F7：用户可控文本列防公式注入
                val = self._safe_text(val)
            cell = ws.cell(row=r, column=i + 1, value=val)
            if col.get("num") and isinstance(val, (int, float)):
                cell.number_format = NUM_FMT

    def _write_items_total(self, ws, r: int, letters: Dict[str, str],
                           c: Dict[str, Any], data_rows: List[int]):
        """合计行：合价列写 SUM 公式，只覆盖已套价明细行（不打进组头行，口径同方式一）"""
        ws.cell(row=r, column=1, value="合计")
        if data_rows:
            formula = f"=SUM({self._sum_ranges(data_rows, letters['amount'])})"
            ws.cell(row=r, column=self._col_of("amount"), value=formula).number_format = NUM_FMT
            remark = (f"含 {DISCIPLINE_MEASURES} 类措施 {_money(c['d_measures'])}（汇总表列第二部分）"
                      + (f"；{c['unpriced']} 条待询价未计入" if c["unpriced"] else ""))
            ws.cell(row=r, column=self._col_of("remark"), value=remark)
        self._style_row(ws, r, len(ITEM_COLUMNS), "summary", ITEM_RIGHT_COLS)

    @staticmethod
    def _col_of(key: str) -> int:
        """ITEM_COLUMNS key → 1-based Excel 列号"""
        return next(i + 1 for i, col in enumerate(ITEM_COLUMNS) if col["key"] == key)

    @staticmethod
    def _sum_ranges(rows: List[int], letter: str) -> str:
        """不连续行号 → 连续区间串（同 excel_export._build_ranges 惯例）：3,4,6 → 'L3:L4,L6'"""
        ranges: List[Tuple[int, int]] = []
        start = end = rows[0]
        for idx in rows[1:]:
            if idx == end + 1:
                end = idx
            else:
                ranges.append((start, end))
                start = end = idx
        ranges.append((start, end))
        return ",".join(f"{letter}{s}" if s == e else f"{letter}{s}:{letter}{e}" for s, e in ranges)

    # sheet2：单位工程计价汇总表（T02 行结构 + 备注列留痕费率）

    def _write_summary_sheet(self, wb: Workbook, c: Dict[str, Any]):
        ws = wb.create_sheet(title=SHEET_SUMMARY)
        R = self.req.rates
        ncol = 4
        self._put_title(ws, 1, f"{c['project_name']}  单位工程计价汇总表（ZS02-T02）", ncol)
        for i, label in enumerate(["编号", "名称", "金额（元）", "备注"]):
            ws.cell(row=2, column=i + 1, value=label)
        self._style_row(ws, 2, ncol, "header")
        ws.freeze_panes = "A3"          # 同 sheet1 惯例：标题行 + 表头行常驻
        m = get_column_letter(3)

        r = 3

        # 逐行写入（父行金额在子行写完后回填 SUM 公式）
        def put(row: int, no: str, name: str, amount, remark: str, kind: str = "data"):
            ws.cell(row=row, column=1, value=no)
            ws.cell(row=row, column=2, value=name)
            cell = ws.cell(row=row, column=3, value=amount)
            if isinstance(amount, (int, float)):
                cell.number_format = NUM_FMT
            ws.cell(row=row, column=4, value=remark)
            self._style_row(ws, row, ncol, kind)
            if kind == "sub":
                # 明细行下沉一级：配合 summaryBelow=False，折叠时隐藏子行、保留 一/二/三 父行
                ws.row_dimensions[row].outlineLevel = 1
            return row

        # 一 · 分部分项工程费（子行 = 专业·分部小计）
        r1 = put(r, "一", "分部分项工程费", None,
                 f"Σ已套价合价（不含 {DISCIPLINE_MEASURES} 类措施）；管理费 {_pct(R.mgmt)}/"
                 f"利润 {_pct(R.profit)}，基数=人工+机械", "part")
        r += 1
        sec_first = r
        for sec in c["sections"]:
            put(r, "", sec["name"], round(sec["amount"], 4), "", "sub")
            r += 1
        if c["sections"]:
            ws.cell(row=r1, column=3,
                    value=f"=SUM({m}{sec_first}:{m}{r - 1})").number_format = NUM_FMT
        else:
            ws.cell(row=r1, column=3, value=round(c["part1"], 4)).number_format = NUM_FMT

        # 二 · 措施项目费
        r2 = put(r, "二", "措施项目费", None,
                 f"D类措施 {_money(c['d_measures'])} + 手工补录 {_money(c['manual_measure_total'])} + 绿安费 {_money(c['green'])}", "part")
        r += 1
        ch_first = r
        put(r, "（一）", "绿安费", round(c["green"], 4),
            f"∑(分部分项 人工+机械) {_money(c['labor_mech_base'])} × {_pct(R.green)}", "sub")
        r += 1
        put(r, "", "单价措施项目费", round(c["d_measures"], 4),
            f"Σ 已套 ZS02-{DISCIPLINE_MEASURES} 类条目合价", "sub")
        r += 1
        for ln in c["manual_measure_lines"]:
            put(r, "", ln.name or "措施补录行", round((ln.qty or 0.0) * (ln.usp or 0.0), 4),
                f"手工补录：{_num(ln.qty)} × {_num(ln.usp)} 元" + (f"（{ln.remark}）" if ln.remark else ""), "sub")
            r += 1
        ws.cell(row=r2, column=3, value=f"=SUM({m}{ch_first}:{m}{r - 1})").number_format = NUM_FMT

        # 三 · 其他项目费
        r3 = put(r, "三", "其他项目费", None,
                 f"预算包干 {_money(c['baogan'])} + 手工费用 {_money(c['manual_total'])}"
                 f" + 精装修配合费 {_money(c['coord_amount'])}；暂列金额集团规定不予计取", "part")
        r += 1
        o3 = r
        put(r, "", "暂列金额", 0, "集团规定不予计取（固定 0）", "sub")
        r += 1
        put(r, "", "精装修管理及配合费", round(c["coord_amount"], 4),
            (f"{_num(R.coordFee)} 元/m² × 装修面积 {_num(c['area'])} m²" if c["coord_configured"]
             else COORD_UNSET_REMARK), "sub")
        r += 1
        put(r, "", "预算包干费", round(c["baogan"], 4),
            f"∑(分部分项 人工+机械) {_money(c['labor_mech_base'])} × {_pct(R.baogan)}", "sub")
        r += 1
        for name, amount in c["manual_fees"].items():
            put(r, "", name, round(amount, 4), "手工金额（项目表单录入）", "sub")
            r += 1
        for ln in c["manual_other_lines"]:
            put(r, "", ln.name or "其他补录行", round((ln.qty or 0.0) * (ln.usp or 0.0), 4),
                f"手工补录行：{_num(ln.qty)} × {_num(ln.usp)} 元" + (f"（{ln.remark}）" if ln.remark else ""), "sub")
            r += 1
        ws.cell(row=r3, column=3, value=f"=SUM({m}{o3}:{m}{r - 1})").number_format = NUM_FMT

        # 四 · 税金      五 · 总造价      单方造价
        r4 = put(r, "四", "税金", f"=({m}{r1}+{m}{r2}+{m}{r3})*{_num(R.tax)}",
                 f"(一+二+三) × {_pct(R.tax)}", "part")
        r += 1
        r5 = put(r, "五", "总造价",
                 f"={m}{r1}+{m}{r2}+{m}{r3}+{m}{r4}", "一+二+三+四", "total")
        r += 1
        if c["per_sqm"] is not None:
            put(r, "", "单方造价", f"={m}{r5}/{_num(c['area'])}",
                f"五 ÷ 装修面积 {_num(c['area'])} m²", "total")
        else:
            put(r, "", "单方造价", None, "装修面积未填写，不计算单方造价", "total")
        r += 1
        put(r, "说明", "费率参数（group_pricing_rules）", None,
            f"管理 {_pct(R.mgmt)} / 利润 {_pct(R.profit)} / 绿安 {_pct(R.green)} / "
            f"包干 {_pct(R.baogan)} / 税金 {_pct(R.tax)} / "
            f"精装修配合费 {(_num(R.coordFee) + ' 元/m²') if c['coord_configured'] else '未配置'}"
            + (f"；{c['unpriced']} 条待询价未计入本表" if c["unpriced"] else ""), "note")
        for i, w in enumerate([8, 26, 16, 56], start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        # 汇总行在上、明细行在下
        ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)

    # ── 样式小工具 ──────────────────────────────────────────────────

    @staticmethod
    def _put_title(ws, row: int, text: str, ncol: int):
        # F7：标题以 project_name 开头——同样过注入转义（正常中文名不受影响）
        ws.cell(row=row, column=1, value=GroupSummaryExporter._safe_text(text))
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncol)
        GroupSummaryExporter._style_row(ws, row, ncol, "title")

    @staticmethod
    def _style_row(ws, row: int, ncol: int, kind: str,
                   right_cols: Tuple[int, ...] = (3,)):
        """标题/表头/组头/父行/合计（加粗）/数据行；边框与填充沿用 excel_export 惯例

        right_cols：需要右对齐的金额/数字列号（sheet1 传数字列，sheet2 默认金额列 C）。
        """
        bold = kind in ("title", "header", "group", "part", "total", "summary")
        size = 14 if kind == "title" else 10
        fill = {"header": FILL_HEADER, "group": FILL_GROUP,
                "part": FILL_SUMMARY, "total": FILL_SUMMARY,
                "summary": FILL_SUMMARY}.get(kind)
        for c in range(1, ncol + 1):
            cell = ws.cell(row=row, column=c)
            cell.font = Font(name=FONT_NAME, bold=bold, size=size)
            if kind in ("title", "header"):
                h_align = "center"
            elif c in right_cols and kind != "note":
                h_align = "right"
            else:
                h_align = "left"
            cell.alignment = Alignment(vertical="center", horizontal=h_align, wrap_text=True)
            cell.border = THIN_BORDER
            if fill:
                cell.fill = fill

    @staticmethod
    def _set_widths(ws, columns: List[Dict[str, Any]]):
        for i, col in enumerate(columns):
            ws.column_dimensions[get_column_letter(i + 1)].width = col["width"]
