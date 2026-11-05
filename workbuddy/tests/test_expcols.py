"""P0-4 · 导出列对齐远端 EXP_COLS + 3 套预设

远端实际 16 列（已数过源码）；WB 额外保留 1 列「套用子目」用于匹配溯源。
预设列集合按远端 preset:{client,internal,labor} 定义。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

import export_xlsx

OUT = Path("/tmp/__dp_out_expcols__.xlsx")

ROWS = [{
    "seq": 1, "code": "NS-017", "name": "合成测试行", "spec": "虚构特征",
    "unit": "m2", "qty": 2.0, "labor": 10.0, "mat_price": 100.0,
    "material": 105.0, "waste": 5.0, "aux": 2.0, "mgmt": 0.0,
    "profit": 0.0, "unit_price": 117.0, "amount": 234.0,
    "bid": "NS-017/泥水班组", "remark": "",
}]


@pytest.fixture
def wbfile():
    OUT.unlink(missing_ok=True)
    yield OUT
    OUT.unlink(missing_ok=True)


def _headers(path):
    wb = load_workbook(path)
    h = [c.value for c in wb[wb.sheetnames[0]][1]]
    wb.close()
    return h


def test_expcols_count_and_keys():
    keys = [c["key"] for c in export_xlsx.EXP_COLS]
    assert len(keys) == 16
    assert keys == ["seq", "code", "name", "spec", "unit", "qty", "lab",
                    "mat_price", "mat", "waste", "aux", "mgmt", "profit",
                    "usp", "total", "remark"]


def test_every_col_has_label_width_num_and_presets():
    for c in export_xlsx.EXP_COLS:
        assert c["label"] and c["width"] > 0
        assert isinstance(c["num"], bool)
        assert {"client", "internal", "labor"} <= set(c["presets"])


def test_default_export_has_all_remote_columns(wbfile):
    export_xlsx.export(ROWS, wbfile, title="测试")
    h = _headers(wbfile)
    for c in export_xlsx.EXP_COLS:
        assert c["label"] in h


def test_preset_client(wbfile):
    export_xlsx.export(ROWS, wbfile, preset="client")
    h = _headers(wbfile)
    remote = {c["label"] for c in export_xlsx.EXP_COLS if c["presets"]["client"]}
    assert remote <= set(h)
    excluded = {c["label"] for c in export_xlsx.EXP_COLS if not c["presets"]["client"]}
    assert not (excluded & set(h)), f"对甲预设不该含: {excluded & set(h)}"


def test_preset_labor(wbfile):
    export_xlsx.export(ROWS, wbfile, preset="labor")
    h = _headers(wbfile)
    remote = {c["label"] for c in export_xlsx.EXP_COLS if c["presets"]["labor"]}
    assert remote <= set(h)
    excluded = {c["label"] for c in export_xlsx.EXP_COLS if not c["presets"]["labor"]}
    assert not (excluded & set(h))


def test_preset_internal_has_every_remote_column(wbfile):
    export_xlsx.export(ROWS, wbfile, preset="internal")
    h = _headers(wbfile)
    for c in export_xlsx.EXP_COLS:
        assert c["label"] in h


def test_custom_columns(wbfile):
    export_xlsx.export(ROWS, wbfile, columns=["name", "total"])
    h = _headers(wbfile)
    assert "项目名称" in h and "合价" in h
    assert "人工单价" not in h


def test_numeric_columns_formatted(wbfile):
    export_xlsx.export(ROWS, wbfile)
    wb = load_workbook(wbfile)
    ws = wb.active
    h = [c.value for c in ws[1]]
    for c in export_xlsx.EXP_COLS:
        if c["num"]:
            col = h.index(c["label"]) + 1
            assert ws.cell(row=2, column=col).number_format.startswith("0.00")
    wb.close()


def test_total_row_still_on_amount_column(wbfile):
    export_xlsx.export(ROWS, wbfile)
    wb = load_workbook(wbfile)
    ws = wb.active
    h = [c.value for c in ws[1]]
    amt = h.index("合价") + 1
    last = ws.max_row
    assert ws.cell(row=last, column=amt).value == pytest.approx(234.0)
    wb.close()


def test_bid_extension_column_present(wbfile):
    """WB 扩展列保留编号+班组，编号跨班组重复时必须可溯源。"""
    export_xlsx.export(ROWS, wbfile, preset="client")
    assert "套用子目" in _headers(wbfile)
