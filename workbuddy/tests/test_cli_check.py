"""S2 · CLI 冒烟：kb 提示块 / check 一致性报告 / prepare --knowledge-out

沿用 test_cli_apply_split.py 风格：虚构清单 + tmp_path + cli.main([...])。
任何输出都不含定价明细。
"""
from __future__ import annotations

import json
import re

import pytest

import cli

PRICING_RE = re.compile(
    r"¥\s*\d|\d+\.\d+\s*/\s*m|综合单价|unit_price|\bprice\b"
)


def _row(row_id, sheet="A分部", section="地面",
         name="虚构墙面乳胶漆", spec="刮腻子三遍 乳胶漆两遍"):
    return {"row_id": row_id, "sheet": sheet, "section": section,
            "name": name, "spec": spec, "unit": "m2", "qty": 1.0,
            "candidates": []}


def _candidates(tmp_path, rows, name="candidates.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"source": "虚构清单", "rows": rows}, ensure_ascii=False),
                 encoding="utf-8")
    return p


def _decisions(tmp_path, data, name="decisions.json"):
    p = tmp_path / name
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


# ---------- kb ----------

def test_cli_kb_prints_sanitized_block_to_stdout(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["kb"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "## 当前知识库（必须遵守）" in out
    assert "【技巧】" in out and "【同义词】" in out and "【规则】" in out
    assert not PRICING_RE.search(out)
    assert list(tmp_path.iterdir()) == [], "kb 默认不得落盘"


def test_cli_kb_out_writes_file(tmp_path):
    out = tmp_path / "kb_prompt.txt"
    rc = cli.main(["kb", "-o", str(out)])
    assert rc == 0 and out.exists()
    text = out.read_text(encoding="utf-8")
    assert "【规则】" in text and not PRICING_RE.search(text)


def test_cli_kb_custom_source(tmp_path):
    src = tmp_path / "custom.json"
    src.write_text(json.dumps({
        "tips": [{"keyword": "虚构技巧", "content": "虚构内容", "team": ""}],
        "synonyms": [], "rules": [],
    }, ensure_ascii=False), encoding="utf-8")
    rc = cli.main(["kb", "--kb", str(src)])
    assert rc == 0


def test_cli_kb_help_renders(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["kb", "--help"])
    assert exc.value.code == 0
    assert "--kb-out" in capsys.readouterr().out


# ---------- check --help ----------

def test_cli_check_help_renders(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["check", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for flag in ("--decisions", "--group-by", "--threshold", "--default-confidence"):
        assert flag in out


# ---------- check ----------

def test_cli_check_produces_report(tmp_path):
    cands = _candidates(tmp_path, [_row(1), _row(2)])
    dec = _decisions(tmp_path, {"1": {"code": "YQ-02"}, "2": {"code": "YQ-07"}})
    out = tmp_path / "consistency.json"
    rc = cli.main(["check", str(cands), "--decisions", str(dec), "-o", str(out)])
    assert rc == 0 and out.exists()
    text = out.read_text(encoding="utf-8")
    report = json.loads(text)
    assert set(report) == {"similar_groups", "warnings", "total_items",
                           "groups_found", "warnings_count"}
    assert report["total_items"] == 2
    assert report["warnings_count"] == 1
    assert report["warnings"][0]["severity"] == "medium"
    assert not PRICING_RE.search(text), "报告不得含任何定价明细"


def test_cli_check_consistent_rows_have_no_warnings(tmp_path):
    cands = _candidates(tmp_path, [_row(1), _row(2)])
    dec = _decisions(tmp_path, {"1": {"code": "YQ-02"}, "2": {"code": "YQ-02"}})
    out = tmp_path / "report.json"
    cli.main(["check", str(cands), "--decisions", str(dec), "-o", str(out)])
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["warnings_count"] == 0


def test_cli_check_no_decisions_all_unpriced(tmp_path):
    cands = _candidates(tmp_path, [_row(1), _row(2)])
    out = tmp_path / "report.json"
    rc = cli.main(["check", str(cands), "-o", str(out)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["warnings_count"] == 1
    assert report["warnings"][0]["severity"] == "high"


def test_cli_check_group_by_section_keeps_domains_separate(tmp_path):
    cands = _candidates(tmp_path, [_row(1, section="地面"), _row(2, section="墙面")])
    dec = _decisions(tmp_path, {"1": {"code": "YQ-02"}, "2": {"code": "YQ-07"}})
    out = tmp_path / "report.json"
    cli.main(["check", str(cands), "--decisions", str(dec),
              "-o", str(out), "--group-by", "section"])
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_items"] == 2
    assert report["groups_found"] == 0, "跨域不应连边"


def test_cli_check_threshold_is_effective(tmp_path, monkeypatch):
    cands = _candidates(tmp_path, [_row(1), _row(2)])
    monkeypatch.setattr(cli.similarity, "compute_similarity", lambda a, b: 0.85)
    out = tmp_path / "report.json"
    cli.main(["check", str(cands), "-o", str(out)])
    assert json.loads(out.read_text(encoding="utf-8"))["groups_found"] == 0
    cli.main(["check", str(cands), "-o", str(out), "--threshold", "0.8"])
    assert json.loads(out.read_text(encoding="utf-8"))["groups_found"] == 1


def test_cli_check_auto_fix_is_advisory_only(tmp_path):
    """报告里保留 auto_fix 建议，但 check 绝不改写 candidates / decisions。"""
    cands = _candidates(tmp_path, [_row(1), _row(2)])
    dec = _decisions(tmp_path, {"1": {"code": "YQ-02"}})
    before_c, before_d = cands.read_text(encoding="utf-8"), dec.read_text(encoding="utf-8")
    out = tmp_path / "report.json"
    cli.main(["check", str(cands), "--decisions", str(dec), "-o", str(out)])
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["warnings"][0]["auto_fix"]["sub_ids"] == ["YQ-02"]
    assert cands.read_text(encoding="utf-8") == before_c
    assert dec.read_text(encoding="utf-8") == before_d


# ---------- prepare --knowledge-out ----------

def test_prepare_knowledge_out_does_not_change_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "_now", lambda: "2026-01-01T00:00:00+00:00")
    monkeypatch.setattr(cli.ingest, "parse_boq", lambda path: [{
        "sheet": "A分部", "section": "地面", "name": "虚构墙面乳胶漆",
        "spec": "刮腻子三遍", "unit": "m2", "qty": 1.0}])
    monkeypatch.setattr(cli.snapshot, "load_snapshot", lambda path=None: {
        "benchmark_items": [], "waste_rates": {}, "material_prices": {},
        "aux_excel_items": [], "generated_at": "2026-01-01T00:00:00+00:00"})

    plain = tmp_path / "plain.json"
    with_kb = tmp_path / "with_kb.json"
    kb_out = tmp_path / "kb.txt"
    assert cli.main(["prepare", "虚构清单.xlsx", "-o", str(plain)]) == 0
    assert cli.main(["prepare", "虚构清单.xlsx", "-o", str(with_kb),
                     "--knowledge-out", str(kb_out)]) == 0
    assert plain.read_text(encoding="utf-8") == with_kb.read_text(encoding="utf-8")
    assert kb_out.exists() and "【规则】" in kb_out.read_text(encoding="utf-8")
