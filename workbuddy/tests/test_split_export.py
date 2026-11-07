"""P1-2 · 拆表导出：按分部（源 sheet）分 sheet，sheet 内按章节插标题行。

口径对齐 backend/app/services/excel_export.py 的 _generate_split()：
每个 group 一个 sheet，内部按 section 分区，末尾可选汇总 sheet。
用虚构数值，不引用任何真实定价。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

import export_xlsx

OUT = Path("/tmp/__test_split_export__.xlsx")


def _row(seq, sheet, section, amount):
    return {
        "seq": seq, "sheet": sheet, "section": section,
        "name": f"虚构清单行{seq}", "spec": "虚构特征", "unit": "m2", "qty": 1.0,
        "labor": 10.0, "mat_price": 0.0, "material": 0.0, "waste": 0.0,
        "aux": 0.0, "mgmt": 0.0, "profit": 0.0,
        "unit_price": 10.0, "amount": amount,
        "bid": "X-1/虚构班组", "remark": "",
    }


ROWS = [
    _row(1, "A分部", "地面工程", 100.0),
    _row(2, "A分部", "地面工程", 200.0),
    _row(3, "A分部", "墙面工程", 50.0),
    _row(4, "B分部", "", 400.0),
]


@pytest.fixture
def exported():
    export_xlsx.export_split(ROWS, OUT, include_summary=True)
    yield OUT
    OUT.unlink(missing_ok=True)


def _texts(ws):
    return [str(c.value or "") for row in ws.iter_rows() for c in row]


def test_one_sheet_per_group(exported):
    wb = load_workbook(exported)
    assert "A分部" in wb.sheetnames
    assert "B分部" in wb.sheetnames
    wb.close()


def test_section_header_rows(exported):
    wb = load_workbook(exported)
    texts = _texts(wb["A分部"])
    assert "地面工程" in texts and "墙面工程" in texts
    wb.close()


def test_each_sheet_has_own_header_and_total(exported):
    wb = load_workbook(exported)
    for name, expected in (("A分部", 350.0), ("B分部", 400.0)):
        ws = wb[name]
        headers = [c.value for c in ws[1]]
        assert "项目名称" in headers and "合价" in headers
        col = headers.index("合价") + 1
        totals = [ws.cell(row=r, column=col).value
                  for r in range(2, ws.max_row + 1)
                  if ws.cell(row=r, column=1).value == "合计"]
        assert totals and totals[-1] == pytest.approx(expected)
    wb.close()


def test_summary_sheet_totals(exported):
    wb = load_workbook(exported)
    assert export_xlsx.SUMMARY_SHEET in wb.sheetnames
    ws = wb[export_xlsx.SUMMARY_SHEET]
    texts = _texts(ws)
    assert "A分部" in texts and "B分部" in texts
    assert any("总计" in t for t in texts)
    wb.close()


def test_no_summary_when_disabled(tmp_path):
    out = tmp_path / "no_summary.xlsx"
    export_xlsx.export_split(ROWS, out, include_summary=False)
    wb = load_workbook(out)
    assert export_xlsx.SUMMARY_SHEET not in wb.sheetnames
    wb.close()


def test_sheet_names_sanitized_and_unique(tmp_path):
    """源工作表名含非法字符 / 超长 / 重名时，仍生成合法且不重复的 sheet 名。"""
    rows = [
        _row(1, "A/B", "", 1.0),
        _row(2, "A:B", "", 2.0),                  # 清洗后同为 A_B → 需去重
        _row(3, "很长的分部名称" * 8, "", 3.0),   # 超过 31 字符
    ]
    out = tmp_path / "sanitized.xlsx"
    export_xlsx.export_split(rows, out, include_summary=False)
    wb = load_workbook(out)
    assert len(wb.sheetnames) == 3
    for name in wb.sheetnames:
        assert len(name) <= 31
        assert not any(ch in name for ch in "[]:*?/\\")
    wb.close()


def test_single_group_still_works(tmp_path):
    out = tmp_path / "single.xlsx"
    export_xlsx.export_split([_row(1, "唯一分部", "", 7.0)], out,
                             include_summary=False)
    wb = load_workbook(out)
    assert wb.sheetnames == ["唯一分部"]
    wb.close()
