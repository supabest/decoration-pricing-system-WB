"""P1 · 辅材清单导出（分工种 + 未套子目清单 + 占比）

对齐远端 docs/tool.html buildAuxExport() 与 backend/app/services/aux_export.py：
  · 按工种分组；材料行 = Σ(消耗量 × 工程量)，合价 = Σ(信息价 × 消耗量 × 工程量)
  · 固定辅材费 = Σ(fixed_k × 工程量)，作为「定额包干」行置于品种行末尾
  · 品种行按合价降序，工种组按合计降序
  · 未套子目（未套价 / 子目缺失 / 无工种）单列，供人工补费
  · 汇总 sheet：工种 → 材料费 / 固定费 / 合计（合同额给定时附「占总成本比例」）

测试一律用虚构数值，不引用、不输出任何真实定价。
"""
from __future__ import annotations

import pytest
from openpyxl import load_workbook

import export_aux


def make_snap(items, price_lib=None):
    return {
        "benchmark_items": items,
        "waste_rates": {},
        "material_prices": price_lib or {},
        "aux_excel_items": [],
        "generated_at": "2026-01-01T00:00:00+00:00",
    }


def make_item(code, team, fixed_k=0.0, rate_detail=None):
    return {
        "internal_code": code,
        "trade_team": team,
        "item_name": "虚构子目" + code,
        "spec": "",
        "unit": "m2",
        "work_type": "",
        "unit_price": 10.0,
        "aux_rule_type": (rate_detail or {}).get("type", "FIXED"),
        "aux_fixed_k": fixed_k,
        "aux_rate_detail": rate_detail,
    }


def priced(row_id, qty, picks, name="虚构清单行"):
    return {
        "row_id": row_id, "name": name, "spec": "虚构特征",
        "unit": "m2", "qty": qty, "picks": picks,
    }


# ---------- 分组与聚合 ----------

def test_unmatched_row_is_listed_as_unclassified():
    result = export_aux.build_aux_export([priced(1, 5, [])], make_snap([]))
    assert result["groups"] == []
    assert len(result["unclassified"]) == 1
    assert result["unclassified"][0]["reason"] == "未套价"
    assert result["unclassified"][0]["qty"] == 5
    assert result["grand_total"] == 0


def test_rate_material_scales_by_quantity():
    rd = {"type": "RATE", "materialName": "虚构材料A", "consume": 2.0, "unit": "kg"}
    snap = make_snap(
        [make_item("X-1", "泥水班组", rate_detail=rd)],
        {"虚构材料A": {"price": 3.0, "unit": "kg", "effective_month": "2026-01"}},
    )
    result = export_aux.build_aux_export([priced(1, 10, [("X-1", "泥水班组", {})])], snap)
    assert len(result["groups"]) == 1
    g = result["groups"][0]
    assert g["sheet_name"] == "泥水班组"
    line = next(l for l in g["lines"] if not l["is_fixed"])
    assert line["name"] == "虚构材料A"
    assert line["unit"] == "kg"                      # 从信息价库带出，对齐远端 (priceLib[name]||{}).unit
    assert line["qty_total"] == pytest.approx(20.0)  # 2.0 × 10
    assert line["subtotal"] == pytest.approx(60.0)   # 3.0 × 2.0 × 10
    assert g["material_subtotal"] == pytest.approx(60.0)


def test_group_material_sums_all_items():
    rd = {"type": "GROUP", "items": [
        {"name": "虚构材料A", "consume": 2.0},
        {"name": "虚构材料B", "consume": 0.5},
    ]}
    snap = make_snap(
        [make_item("X-2", "木工班组", rate_detail=rd)],
        {"虚构材料A": {"price": 3.0, "unit": "kg"},
         "虚构材料B": {"price": 8.0, "unit": "m"}},
    )
    result = export_aux.build_aux_export([priced(1, 1, [("X-2", "木工班组", {})])], snap)
    g = result["groups"][0]
    assert g["material_subtotal"] == pytest.approx(3.0 * 2.0 + 8.0 * 0.5)


def test_fixed_k_becomes_package_line_and_scales():
    snap = make_snap([make_item("X-3", "油漆班组", fixed_k=4.5)])
    result = export_aux.build_aux_export([priced(1, 3, [("X-3", "油漆班组", {})])], snap)
    g = result["groups"][0]
    assert g["fixed_subtotal"] == pytest.approx(13.5)   # 4.5 × 3
    assert g["lines"][-1]["is_fixed"] is True
    assert g["lines"][-1]["name"] == export_aux.FIXED_LINE_NAME
    assert g["lines"][-1]["subtotal"] == pytest.approx(13.5)
    assert g["total"] == pytest.approx(13.5)


def test_lines_sorted_by_subtotal_desc_and_fixed_last():
    rd = {"type": "GROUP", "items": [
        {"name": "虚构材料A", "consume": 1.0},
        {"name": "虚构材料B", "consume": 1.0},
    ]}
    snap = make_snap(
        [make_item("X-4", "泥水班组", fixed_k=1.0, rate_detail=rd)],
        {"虚构材料A": {"price": 2.0, "unit": "kg"},
         "虚构材料B": {"price": 9.0, "unit": "kg"}},
    )
    g = export_aux.build_aux_export([priced(1, 1, [("X-4", "泥水班组", {})])], snap)["groups"][0]
    names = [l["name"] for l in g["lines"]]
    assert names[0] == "虚构材料B"          # 合价高者在前
    assert names[-1] == export_aux.FIXED_LINE_NAME
    assert g["total"] == pytest.approx(2.0 + 9.0 + 1.0)


def test_groups_split_by_trade_and_sorted_by_total():
    snap = make_snap([
        make_item("A", "泥水班组", fixed_k=10.0),
        make_item("B", "木工班组", fixed_k=30.0),
    ])
    rows = [priced(1, 1, [("A", "泥水班组", {})]),
            priced(2, 1, [("B", "木工班组", {})])]
    groups = export_aux.build_aux_export(rows, snap)["groups"]
    assert [g["sheet_name"] for g in groups] == ["木工班组", "泥水班组"]
    assert groups[0]["total"] == pytest.approx(30.0)


def test_missing_item_and_missing_trade_are_unclassified():
    snap = make_snap([make_item("A", "", fixed_k=1.0)])
    rows = [priced(1, 1, [("GHOST", "泥水班组", {})]),
            priced(2, 1, [("A", "", {})])]
    result = export_aux.build_aux_export(rows, snap)
    reasons = sorted(u["reason"] for u in result["unclassified"])
    assert reasons == ["子目缺失", "无工种"]
    assert result["groups"] == []


def test_item_without_aux_recipe_is_skipped():
    snap = make_snap([make_item("A", "泥水班组", fixed_k=0.0, rate_detail=None)])
    result = export_aux.build_aux_export([priced(1, 1, [("A", "泥水班组", {})])], snap)
    assert result["groups"] == [] and result["unclassified"] == []


def test_multi_subs_accumulate_into_same_trade():
    snap = make_snap([
        make_item("A", "泥水班组", fixed_k=2.0),
        make_item("B", "泥水班组", fixed_k=3.0),
    ])
    rows = [priced(1, 2, [("A", "泥水班组", {}), ("B", "泥水班组", {})])]
    g = export_aux.build_aux_export(rows, snap)["groups"][0]
    assert g["fixed_subtotal"] == pytest.approx(10.0)  # (2+3) × 2


def test_reconciliation_matches_per_unit_aux_times_qty():
    """对账：明细合计 = Σ(每单位清单量辅材费 × 工程量)，与远端 expectTotal 同口径。"""
    rd = {"type": "RATE", "materialName": "虚构材料A", "consume": 0.5, "unit": "kg"}
    snap = make_snap(
        [make_item("A", "泥水班组", fixed_k=1.0, rate_detail=rd)],
        {"虚构材料A": {"price": 4.0, "unit": "kg"}},
    )
    rows = [priced(1, 6, [("A", "泥水班组", {})])]
    result = export_aux.build_aux_export(rows, snap)
    from aux_rules import aux_cost
    per_unit = aux_cost(snap["benchmark_items"][0], snap["material_prices"])
    assert result["expect_total"] == pytest.approx(per_unit * 6)
    assert result["grand_total"] == pytest.approx(result["expect_total"])
    assert result["diff"] == pytest.approx(0.0)


def test_dirty_inputs_degrade_to_zero():
    snap = make_snap([make_item("A", "泥水班组", fixed_k="bad")])
    result = export_aux.build_aux_export([priced(1, "oops", [("A", "泥水班组", {})])], snap)
    assert result["grand_total"] == 0.0


# ---------- 导出工作簿 ----------

def _export(result, path, **kw):
    return export_aux.export_aux_workbook(result, path, **kw)


def test_workbook_has_trade_sheet_and_summary(tmp_path):
    snap = make_snap([make_item("A", "泥水班组", fixed_k=2.0)])
    result = export_aux.build_aux_export([priced(1, 3, [("A", "泥水班组", {})])], snap)
    path = tmp_path / "aux.xlsx"
    _export(result, path, project_name="虚构项目")
    wb = load_workbook(path)
    assert "泥水班组" in wb.sheetnames
    assert "辅材汇总" in wb.sheetnames
    ws = wb["泥水班组"]
    assert [c.value for c in ws[2]] == export_aux.HEADER_LABELS
    assert wb["辅材汇总"]["A3"].value == "泥水班组"
    assert wb["辅材汇总"]["D3"].value == pytest.approx(6.0)


def test_workbook_summary_totals_and_ratio(tmp_path):
    snap = make_snap([
        make_item("A", "泥水班组", fixed_k=2.0),
        make_item("B", "木工班组", fixed_k=3.0),
    ])
    rows = [priced(1, 1, [("A", "泥水班组", {})]),
            priced(2, 1, [("B", "木工班组", {})])]
    result = export_aux.build_aux_export(rows, snap)
    path = tmp_path / "aux.xlsx"
    _export(result, path, contract_amount=100.0, target_profit_rate=20.0)
    wb = load_workbook(path)
    ws = wb["辅材汇总"]
    assert ws["E2"].value == "占总成本比例"
    assert ws["D5"].value == pytest.approx(5.0)      # 总计 = 2 + 3
    assert ws["E5"].value == pytest.approx(5.0 / 80.0)  # cost_base = 100 × (1-20%)


def test_workbook_omits_ratio_column_without_contract_amount(tmp_path):
    snap = make_snap([make_item("A", "泥水班组", fixed_k=2.0)])
    result = export_aux.build_aux_export([priced(1, 1, [("A", "泥水班组", {})])], snap)
    path = tmp_path / "aux.xlsx"
    _export(result, path)
    wb = load_workbook(path)
    assert wb["辅材汇总"]["E2"].value is None


def test_workbook_has_unclassified_sheet(tmp_path):
    result = export_aux.build_aux_export([priced(1, 5, [])], make_snap([]))
    path = tmp_path / "aux.xlsx"
    _export(result, path)
    wb = load_workbook(path)
    assert export_aux.UNCLASSIFIED_SHEET in wb.sheetnames
    ws = wb[export_aux.UNCLASSIFIED_SHEET]
    assert [c.value for c in ws[2]] == export_aux.UNCLASSIFIED_HEADERS
    assert ws["B3"].value == "虚构清单行"
    assert ws["E3"].value == 5
    assert ws["F3"].value == "未套价"
    assert ws["G3"].value is None       # 留给人工填写


def test_workbook_valid_with_no_groups(tmp_path):
    result = export_aux.build_aux_export([], make_snap([]))
    path = tmp_path / "aux.xlsx"
    _export(result, path)
    wb = load_workbook(path)
    assert "辅材汇总" in wb.sheetnames
    assert export_aux.UNCLASSIFIED_SHEET not in wb.sheetnames


def test_sheet_name_is_sanitized(tmp_path):
    snap = make_snap([make_item("A", "泥水/班组", fixed_k=1.0)])
    result = export_aux.build_aux_export([priced(1, 1, [("A", "泥水/班组", {})])], snap)
    path = tmp_path / "aux.xlsx"
    _export(result, path)
    wb = load_workbook(path)
    assert all("/" not in n for n in wb.sheetnames)
