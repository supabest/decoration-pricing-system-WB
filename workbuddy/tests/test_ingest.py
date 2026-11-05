"""T4 · BOQ 读取 —— 测试先行

样本含两个陷阱：
1. 一条清单项纵向合并占 2 个物理行（第 2 行读出来是空）
2. 合并区非左上角仍残留值（P11 = 500），不折叠会多出一条假记录

注意：两个 sheet 名都含「精装修」（ZS02-A-精装修工程 / ZS02-B- 精装修水电），
过滤必须用前缀，不能按关键字包含。
"""
from pathlib import Path

import pytest

import ingest

SAMPLE = Path("/Users/alick/Downloads/23aF工程量清单简.xlsx")
needs_sample = pytest.mark.skipif(not SAMPLE.exists(), reason="样本文件不存在")


def rows():
    return ingest.parse_boq(SAMPLE)


def sheet_a():
    return [r for r in rows() if r["sheet"].startswith("ZS02-A")]


def sheet_b():
    return [r for r in rows() if r["sheet"].startswith("ZS02-B")]


@needs_sample
def test_sheet_count():
    assert len({r["sheet"] for r in rows()}) == 2


@needs_sample
def test_item_counts():
    assert len(sheet_a()) == 6, f"精装修应 6 条，实际 {len(sheet_a())}"
    assert len(sheet_b()) == 4, f"水电应 4 条，实际 {len(sheet_b())}"


@needs_sample
def test_no_phantom_row_from_merged_residue():
    """P11 残留值不得产生第 7 条记录。"""
    assert len(sheet_a()) == 6


@needs_sample
def test_required_fields_present():
    for r in rows():
        for f in ("sheet", "section", "name", "spec", "unit", "qty", "source_row"):
            assert f in r, f"缺字段 {f}"
        assert r["name"].strip()


@needs_sample
def test_sections_parsed():
    assert {r["section"] for r in sheet_a()} == {"楼地面工程", "天棚工程", "墙面工程"}
    assert {r["section"] for r in sheet_b()} == {"给排水工程", "电气工程"}


@needs_sample
def test_quantity_maps_to_total_column():
    assert abs(sheet_a()[0]["qty"] - 1.04) < 1e-6


@needs_sample
def test_units_normalized():
    units = {r["unit"] for r in rows()}
    assert "㎡" not in units and "m²" not in units
    assert "" not in units, "存在单位为空的行 —— 表头可能折行（如「计量\\n单位」）导致列未识别"
    assert units <= {"m2", "m", "m3", "个", "组", "套"}


@needs_sample
def test_no_header_rows_leaked():
    names = {r["name"] for r in rows()}
    for token in ("项目名称", "序号", "项目特征", "计量单位", "工程量"):
        assert token not in names


@needs_sample
def test_source_rows_are_unique():
    keys = [(r["sheet"], r["source_row"]) for r in rows()]
    assert len(keys) == len(set(keys))
