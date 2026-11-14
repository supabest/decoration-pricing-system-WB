"""P1 · CLI 冒烟：candidates → aux 子命令 → 多 sheet 辅材费用清单

用虚构数值，不引用、不输出任何真实定价，也不依赖真实密钥/快照
（load_snapshot 以 monkeypatch 注入内存虚构快照）。
"""
from __future__ import annotations

import json

import pytest
from openpyxl import load_workbook

import cli
import export_aux


def _item(code, team, fixed_k=2.0):
    return {
        "internal_code": code, "trade_team": team,
        "item_name": "虚构子目" + code, "spec": "", "unit": "m2",
        "unit_price": 10.0, "aux_rule_type": "FIXED",
        "aux_fixed_k": fixed_k, "aux_rate_detail": None,
    }


def _snap(items=None):
    return {
        "benchmark_items": items if items is not None else [_item("X-1", "泥水班组")],
        "waste_rates": {}, "material_prices": {}, "aux_excel_items": [],
        "generated_at": "2026-01-01T00:00:00+00:00",
    }


def _write_candidates(path, rows):
    path.write_text(
        json.dumps({"source": "虚构清单", "rows": rows}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _row(row_id, qty, candidates):
    return {
        "row_id": row_id, "sheet": "虚构", "section": "虚构",
        "name": f"虚构清单行{row_id}", "spec": "虚构特征", "unit": "m2",
        "qty": qty, "candidates": candidates,
    }


def test_cli_aux_exports_workbook(tmp_path, monkeypatch):
    """--auto 取候选第一名 → 分工种 sheet + 辅材汇总 + 未套子目清单。"""
    monkeypatch.setattr(cli.datasource, "load_snapshot", lambda path=None: _snap())
    cands = _write_candidates(tmp_path / "candidates.json", [
        _row(1, 3, [{"code": "X-1", "team": "泥水班组", "item_name": "虚构子目",
                     "spec": "", "unit": "m2"}]),
        _row(2, 5, []),                      # 未套价 → 未套子目清单
    ])
    out = tmp_path / "aux.xlsx"

    rc = cli.main(["aux", str(cands), "-o", str(out), "--auto"])

    assert rc == 0
    assert out.exists()
    wb = load_workbook(out)
    assert "泥水班组" in wb.sheetnames
    assert export_aux.SUMMARY_SHEET in wb.sheetnames
    assert export_aux.UNCLASSIFIED_SHEET in wb.sheetnames
    # 固定辅材费 2.0 × 工程量 3 = 6.0
    assert wb[export_aux.SUMMARY_SHEET]["D3"].value == pytest.approx(6.0)
    assert wb[export_aux.UNCLASSIFIED_SHEET]["B3"].value == "虚构清单行2"
    assert wb[export_aux.UNCLASSIFIED_SHEET]["F3"].value == "未套价"
    wb.close()


def test_cli_aux_help_renders_all_options(capsys):
    """--help 能完整渲染（help 文本里的 % 需转义，否则 argparse 格式化报错）。"""
    with pytest.raises(SystemExit) as exc:
        cli.main(["aux", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for opt in ("--decisions", "--auto", "--project-name",
                "--contract-amount", "--target-profit-rate"):
        assert opt in out


def test_cli_aux_empty_candidates_returns_nonzero(tmp_path, monkeypatch, capsys):
    """空清单不产生空工作簿，明确返回非零并给出提示。"""
    monkeypatch.setattr(cli.datasource, "load_snapshot", lambda path=None: _snap([]))
    cands = _write_candidates(tmp_path / "empty.json", [])
    out = tmp_path / "aux.xlsx"

    rc = cli.main(["aux", str(cands), "-o", str(out)])

    assert rc == 1
    assert not out.exists()
    assert "无可导出的辅材数据" in capsys.readouterr().out
