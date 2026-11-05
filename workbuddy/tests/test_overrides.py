"""P0-1 · --overrides 主材价 / 损耗率 / 系数 / 换算

RED 阶段期望：apply 不支持 --overrides。
测试一律用合成清单 + 虚构数值，不引用、不断言任何真实定价。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from openpyxl import load_workbook

import cli
import snapshot

CAND = Path("/tmp/__dp_cand_overrides__.json")
DEC = Path("/tmp/__dp_dec_overrides__.json")
OVR = Path("/tmp/__dp_overrides__.json")
OUT = Path("/tmp/__dp_out_overrides__.xlsx")


def _pick():
    """从快照取一个真实 (编号, 班组) 作锚点，但不读取/输出其价格。"""
    it = snapshot.load_snapshot()["benchmark_items"][0]
    return it["internal_code"], it["trade_team"]


@pytest.fixture
def prepared():
    code, team = _pick()
    CAND.write_text(json.dumps({
        "source": "synthetic", "generated_at": "test",
        "rows": [{
            "row_id": 1, "sheet": "T", "section": "S",
            "name": "合成测试行", "spec": "", "unit": "m2", "qty": 2.0,
            "candidates": [{"code": code, "team": team,
                            "item_name": "合成子目", "spec": "", "unit": "m2"}],
        }],
    }, ensure_ascii=False), encoding="utf-8")
    DEC.write_text(json.dumps({
        "1": {"code": code, "team": team, "confidence": 95}
    }, ensure_ascii=False), encoding="utf-8")
    for p in (OVR, OUT):
        p.unlink(missing_ok=True)
    yield code
    for p in (CAND, DEC, OVR, OUT):
        p.unlink(missing_ok=True)


def _run(extra=None):
    args = ["apply", str(CAND), "-o", str(OUT), "--decisions", str(DEC)]
    if extra:
        args += extra
    cli.main(args)
    wb = load_workbook(OUT)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    row = {h: ws.cell(row=2, column=i + 1).value for i, h in enumerate(headers)}
    wb.close()
    return row


def test_overrides_accepts_mat_price_and_waste(prepared):
    OVR.write_text(json.dumps({"1": {"mat_price": 100.0, "waste_rate": 5.0}}), encoding="utf-8")
    r = _run(["--overrides", str(OVR)])
    assert float(r["主材费"]) == pytest.approx(105.0)
    assert float(r["合价"]) == pytest.approx(float(r["综合单价"]) * 2.0)


def test_unit_price_equals_three_components(prepared):
    OVR.write_text(json.dumps({"1": {"mat_price": 100.0, "waste_rate": 5.0}}), encoding="utf-8")
    r = _run(["--overrides", str(OVR)])
    total = float(r["人工单价"]) + float(r["主材费"]) + float(r["辅材费"])
    assert float(r["综合单价"]) == pytest.approx(total)


def test_default_waste_rate_comes_from_snapshot(prepared):
    code = prepared
    w = float(snapshot.load_snapshot()["waste_rates"].get(code, 0))
    OVR.write_text(json.dumps({"1": {"mat_price": 100.0}}), encoding="utf-8")
    r = _run(["--overrides", str(OVR)])
    assert float(r["主材费"]) == pytest.approx(100.0 * (1 + w / 100))


def test_coef_and_conv_scale_both_labor_and_material(prepared):
    OVR.write_text(json.dumps({"1": {
        "mat_price": 100.0, "waste_rate": 0, "coef": 2.0, "conv": 0.5,
    }}), encoding="utf-8")
    r = _run(["--overrides", str(OVR)])
    assert float(r["主材费"]) == pytest.approx(100.0 * 2.0 * 0.5)


def test_without_overrides_behaves_as_before(prepared):
    r = _run()
    assert float(r["主材费"]) == 0.0
    assert float(r["综合单价"]) > 0


def test_unknown_override_row_is_ignored(prepared):
    OVR.write_text(json.dumps({"999": {"mat_price": 100.0}}), encoding="utf-8")
    r = _run(["--overrides", str(OVR)])
    assert float(r["主材费"]) == 0.0
