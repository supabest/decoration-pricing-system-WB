"""P1-2 · CLI 冒烟：apply --split 出分部分项报价表 + 自动备注。

用虚构快照（monkeypatch 注入），不依赖真实密钥 / 价表，不输出任何定价明细。
"""
from __future__ import annotations

import json

from openpyxl import load_workbook

import cli
import export_xlsx


def _item(code="X-1", team="虚构班组"):
    return {
        "internal_code": code, "trade_team": team,
        "item_name": "虚构子目", "spec": "", "unit": "m2",
        "unit_price": 10.0, "aux_rule_type": "FIXED",
        "aux_fixed_k": 0.0, "aux_rate_detail": None,
    }


def _snap():
    return {
        "benchmark_items": [_item()], "waste_rates": {},
        "material_prices": {}, "aux_excel_items": [],
        "generated_at": "2026-01-01T00:00:00+00:00",
    }


def _row(row_id, sheet, section, candidates):
    return {
        "row_id": row_id, "sheet": sheet, "section": section,
        "name": f"虚构清单行{row_id}", "spec": "虚构特征", "unit": "m2",
        "qty": 2.0, "candidates": candidates,
    }


def _candidates(tmp_path, rows):
    p = tmp_path / "candidates.json"
    p.write_text(json.dumps({"source": "虚构清单", "rows": rows},
                            ensure_ascii=False), encoding="utf-8")
    return p


def _cand():
    return [{"code": "X-1", "team": "虚构班组", "item_name": "虚构子目",
             "spec": "", "unit": "m2"}]


def test_apply_split_produces_group_sheets_and_remarks(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.snapshot, "load_snapshot", lambda path=None: _snap())
    cands = _candidates(tmp_path, [
        _row(1, "A分部", "地面工程", _cand()),
        _row(2, "A分部", "墙面工程", _cand()),
        _row(3, "B分部", "", []),                 # 无候选 → 自动备注
    ])
    out = tmp_path / "报价表.xlsx"

    rc = cli.main(["apply", str(cands), "-o", str(out), "--auto", "--split"])

    assert rc == 0 and out.exists()
    wb = load_workbook(out)
    assert "A分部" in wb.sheetnames and "B分部" in wb.sheetnames
    assert export_xlsx.SUMMARY_SHEET in wb.sheetnames
    # A 分部内应有章节标题行
    texts = [str(c.value or "") for row in wb["A分部"].iter_rows() for c in row]
    assert "地面工程" in texts and "墙面工程" in texts
    # 未套价行的自动备注
    headers = [c.value for c in wb["B分部"][1]]
    remark_col = headers.index("备注") + 1
    assert "无候选子目" in str(wb["B分部"].cell(row=2, column=remark_col).value)
    wb.close()


def test_apply_without_split_keeps_single_sheet(tmp_path, monkeypatch):
    """向后兼容：不传 --split 时行为与 P0 完全一致。"""
    monkeypatch.setattr(cli.snapshot, "load_snapshot", lambda path=None: _snap())
    cands = _candidates(tmp_path, [_row(1, "A分部", "地面工程", _cand())])
    out = tmp_path / "single.xlsx"

    rc = cli.main(["apply", str(cands), "-o", str(out), "--auto"])

    assert rc == 0
    wb = load_workbook(out)
    assert wb.sheetnames == ["套价结果"]
    wb.close()


def test_apply_split_help_renders(capsys):
    import pytest
    with pytest.raises(SystemExit) as exc:
        cli.main(["apply", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--split" in out and "--no-summary" in out
