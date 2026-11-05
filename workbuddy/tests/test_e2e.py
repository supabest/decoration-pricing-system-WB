"""T5 · 端到端 —— 测试先行

两段式：
  prepare  BOQ → 候选清单（不含任何价格字段）
  apply    候选 + 决策 → 计价 → Excel
"""
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

import cli

SAMPLE = Path("/Users/alick/Downloads/23aF工程量清单简.xlsx")
CAND = Path("/tmp/__e2e_candidates__.json")
OUT = Path("/tmp/__e2e_result__.xlsx")
needs_sample = pytest.mark.skipif(not SAMPLE.exists(), reason="样本文件不存在")


@pytest.fixture
def prepared():
    for p in (CAND, OUT):
        p.unlink(missing_ok=True)
    cli.main(["prepare", str(SAMPLE), "-o", str(CAND)])
    yield CAND
    for p in (CAND, OUT):
        p.unlink(missing_ok=True)


@needs_sample
def test_prepare_row_count(prepared):
    data = json.loads(prepared.read_text(encoding="utf-8"))
    assert len(data["rows"]) == 10


@needs_sample
def test_prepare_every_row_has_candidates(prepared):
    data = json.loads(prepared.read_text(encoding="utf-8"))
    for row in data["rows"]:
        assert row["candidates"], f"第 {row['row_id']} 行无候选"
        assert len(row["candidates"]) <= 40


@needs_sample
def test_candidates_carry_no_price(prepared):
    """保密红线：候选清单不得携带任何价格字段。"""
    text = prepared.read_text(encoding="utf-8")
    data = json.loads(text)
    for row in data["rows"]:
        for c in row["candidates"]:
            assert "unit_price" not in c
            assert "price" not in c
            assert set(c) <= {"code", "team", "item_name", "spec", "unit"}


@needs_sample
def test_apply_auto_exports(prepared):
    cli.main(["apply", str(CAND), "-o", str(OUT), "--auto"])
    assert OUT.exists()
    wb = load_workbook(OUT)
    ws = wb.active
    assert ws.max_row >= 12
    wb.close()


@needs_sample
def test_apply_result_has_prices(prepared):
    cli.main(["apply", str(CAND), "-o", str(OUT), "--auto"])
    wb = load_workbook(OUT)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    up = headers.index("综合单价") + 1
    values = [ws.cell(row=r, column=up).value for r in range(2, 12)]
    assert any(float(v or 0) > 0 for v in values), "所有综合单价为 0，计价未生效"
    wb.close()


@needs_sample
def test_decisions_override_auto(prepared):
    """显式决策优先于自动 top1。"""
    data = json.loads(prepared.read_text(encoding="utf-8"))
    first = data["rows"][0]
    top = first["candidates"][0]
    decisions = {str(first["row_id"]): {"code": top["code"], "team": top["team"], "confidence": 99}}
    dpath = Path("/tmp/__e2e_decisions__.json")
    dpath.write_text(json.dumps(decisions, ensure_ascii=False), encoding="utf-8")
    try:
        cli.main(["apply", str(CAND), "-o", str(OUT), "--decisions", str(dpath)])
        wb = load_workbook(OUT)
        ws = wb.active
        headers = [c.value for c in ws[1]]
        bid_col = headers.index("套用子目") + 1
        # 编号跨班组重复，导出必须带班组消歧
        assert ws.cell(row=2, column=bid_col).value == f'{top["code"]}/{top["team"]}'
        wb.close()
    finally:
        dpath.unlink(missing_ok=True)
