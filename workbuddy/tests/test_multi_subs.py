"""P0-2 · 一行多子目组合

对齐远端：
  rowUnitPrice   = Σ effPrice(sub)                 [人工]
  rowMatCost     = Σ matPrice×(1+损耗)×coef×conv  [主材]
  computeAuxForRow = Σ computeAuxForSub(sub)       [辅材，不乘系数]
  syncRowMat     —— 行级主材价只是暂存区，子目级参数优先
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

import cli
import snapshot

CAND = Path("/tmp/__dp_cand_multi__.json")
DEC = Path("/tmp/__dp_dec_multi__.json")
OVR = Path("/tmp/__dp_ovr_multi__.json")
OUT = Path("/tmp/__dp_out_multi__.xlsx")


def _two_picks():
    items = snapshot.load_snapshot()["benchmark_items"]
    seen, out = set(), []
    for it in items:
        key = (it["internal_code"], it["trade_team"])
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
        if len(out) == 2:
            break
    return out


@pytest.fixture
def prepared():
    picks = _two_picks()
    CAND.write_text(json.dumps({
        "source": "synthetic", "generated_at": "test",
        "rows": [{
            "row_id": 1, "sheet": "T", "section": "S",
            "name": "合成测试行", "spec": "", "unit": "m2", "qty": 3.0,
            "candidates": [{"code": c, "team": t, "item_name": "合成子目",
                            "spec": "", "unit": "m2"} for c, t in picks],
        }],
    }, ensure_ascii=False), encoding="utf-8")
    for p in (DEC, OVR, OUT):
        p.unlink(missing_ok=True)
    yield picks
    for p in (CAND, DEC, OVR, OUT):
        p.unlink(missing_ok=True)


def _run(decision, extra_args=None):
    DEC.write_text(json.dumps({"1": decision}, ensure_ascii=False), encoding="utf-8")
    args = ["apply", str(CAND), "-o", str(OUT), "--decisions", str(DEC)]
    if extra_args:
        args += extra_args
    cli.main(args)
    wb = load_workbook(OUT)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    row = {h: ws.cell(row=2, column=i + 1).value for i, h in enumerate(headers)}
    wb.close()
    return row


def _sub_sum(picks, field, scale=1.0):
    """直接从快照读各子目贡献求和（仅用于测试内部对账，不输出定价）。"""
    idx = {(i["internal_code"], i["trade_team"]): i
           for i in snapshot.load_snapshot()["benchmark_items"]}
    return sum(float(idx[p][field]) * scale for p in picks)


def test_two_subs_labor_equals_sum(prepared):
    picks = prepared
    d = {"subs": [{"code": c, "team": t} for c, t in picks]}
    r = _run(d)
    assert float(r["人工单价"]) == pytest.approx(_sub_sum(picks, "unit_price"))


def test_two_subs_material_equals_sum(prepared):
    picks = prepared
    d = {"subs": [{"code": c, "team": t, "mat_price": 100.0, "waste_rate": 0}
                  for c, t in picks]}
    r = _run(d)
    assert float(r["主材费"]) == pytest.approx(200.0)


def test_two_subs_aux_equals_sum(prepared):
    picks = prepared
    d = {"subs": [{"code": c, "team": t} for c, t in picks]}
    r = _run(d)
    idx = {(i["internal_code"], i["trade_team"]): i
           for i in snapshot.load_snapshot()["benchmark_items"]}
    expected = sum(cli._aux_cost(idx[p]) for p in picks)
    assert float(r["辅材费"]) == pytest.approx(expected)


def test_bid_lists_all_subs(prepared):
    picks = prepared
    d = {"subs": [{"code": c, "team": t} for c, t in picks]}
    r = _run(d)
    for c, t in picks:
        assert c in r["套用子目"]
        assert t in r["套用子目"]


def test_sub_level_param_beats_row_override(prepared):
    """远端口径：行级主材价是暂存区，子目级显式参数优先。"""
    picks = prepared
    d = {"subs": [{"code": c, "team": t, "mat_price": 50.0, "waste_rate": 0}
                  for c, t in picks]}
    OVR.write_text(json.dumps({"1": {"mat_price": 100.0, "waste_rate": 0}}), encoding="utf-8")
    r = _run(d, ["--overrides", str(OVR)])
    assert float(r["主材费"]) == pytest.approx(100.0)


def test_invalid_sub_is_skipped_without_breaking_row(prepared):
    picks = prepared
    d = {"subs": [
        {"code": picks[0][0], "team": picks[0][1], "mat_price": 100.0, "waste_rate": 0},
        {"code": "NO-SUCH-CODE", "team": "不存在班组"},
    ]}
    r = _run(d)
    assert float(r["主材费"]) == pytest.approx(100.0)
    assert "NO-SUCH-CODE" not in (r["套用子目"] or "")
