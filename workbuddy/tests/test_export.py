"""T4b · 导出 —— 测试先行（往返无损）"""
from pathlib import Path

import pytest
from openpyxl import load_workbook

import export_xlsx

OUT = Path("/tmp/__test_export__.xlsx")

ROWS = [
    {"seq": 1, "name": "地面-水泥砂浆找平", "spec": "50mm 水泥砂浆", "unit": "m2", "qty": 120.5,
     "labor": 35.0, "material": 0.0, "aux": 5.0, "unit_price": 40.0, "amount": 4820.0,
     "bid": "NS-01", "remark": ""},
    {"seq": 2, "name": "墙面-乳胶漆", "spec": "满刮腻子两遍", "unit": "m2", "qty": 300.0,
     "labor": 28.0, "material": 12.0, "aux": 3.0, "unit_price": 43.0, "amount": 12900.0,
     "bid": "YQ-02", "remark": "含基层处理"},
]


@pytest.fixture
def exported():
    export_xlsx.export(ROWS, OUT, title="套价结果", sections=None)
    yield OUT
    OUT.unlink(missing_ok=True)


def test_file_created(exported):
    assert exported.exists() and exported.stat().st_size > 0


def test_header_row(exported):
    wb = load_workbook(exported)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert "项目名称" in headers
    assert "综合单价" in headers
    assert "合价" in headers
    wb.close()


def test_row_count(exported):
    wb = load_workbook(exported)
    ws = wb.active
    # 表头 + 2 数据行 + 合计行
    assert ws.max_row >= 4
    wb.close()


def test_values_roundtrip(exported):
    wb = load_workbook(exported)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(headers)}
    second = [c.value for c in ws[3]]
    assert second[idx["项目名称"]] == "墙面-乳胶漆"
    assert abs(second[idx["工程量"]] - 300.0) < 1e-6
    assert abs(second[idx["综合单价"]] - 43.0) < 1e-6
    wb.close()


def test_total_row_present(exported):
    wb = load_workbook(exported)
    ws = wb.active
    texts = [str(c.value or "") for row in ws.iter_rows() for c in row]
    assert any("合计" in t for t in texts)
    wb.close()


def test_number_format_applied(exported):
    wb = load_workbook(exported)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col = headers.index("综合单价") + 1
    assert ws.cell(row=2, column=col).number_format.startswith("0.00")
    wb.close()
