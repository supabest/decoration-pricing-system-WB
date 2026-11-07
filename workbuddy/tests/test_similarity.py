"""S2 · 相似清单一致性校验 —— 测试先行

算法逐字对齐 backend/app/services/similarity_checker.py；一律虚构清单、虚构编号。
"""
from __future__ import annotations

import pytest

import similarity


def _item(index, name="虚构墙面乳胶漆", spec="刮腻子三遍 乳胶漆两遍",
          unit="m2", matched_ids=None, conf=100):
    return {
        "index": index, "name": name, "spec": spec, "unit": unit,
        "matched_ids": list(matched_ids or []),
        "overall_confidence": conf,
    }


# ---------- 集合运算与权重 ----------

def test_jaccard_empty_and_general():
    assert similarity.jaccard(set(), set()) == 1.0
    assert similarity.jaccard({"a"}, set()) == 0.0
    assert similarity.jaccard(set(), {"a"}) == 0.0
    assert similarity.jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)


def test_bigrams_strips_punctuation_and_digits():
    bg = similarity.bigrams("石膏板（9.5mm）")
    assert "9." not in bg and ".5" not in bg
    assert "石膏" in bg


def test_compute_similarity_identical_is_one():
    a = _item(1)
    assert similarity.compute_similarity(a, dict(a)) == 1.0


def test_unit_mismatch_costs_exactly_ten_percent():
    a = _item(1)
    b = _item(2, unit="m")
    assert similarity.compute_similarity(a, b) == pytest.approx(0.90)


def test_weights_sum_to_one():
    total = similarity.W_NAME + similarity.W_SPEC + similarity.W_ENG + similarity.W_UNIT
    assert total == pytest.approx(1.0)


def test_engineering_reuses_retrieve_parse():
    a = _item(1, name="墙面木饰面", spec="木饰面 挂贴")
    b = _item(2, name="墙面木饰面", spec="木饰面 挂贴")
    assert similarity.compute_similarity(a, b) == 1.0


# ---------- 阈值与 Union-Find ----------

def _patch_similarity(monkeypatch, matrix):
    """matrix[(i,j)] → sim，i/j 为 items 下标（0-based）。"""
    def fake(a, b):
        i, j = a["index"] - 1, b["index"] - 1
        return matrix.get((i, j), matrix.get((j, i), 0.0))
    monkeypatch.setattr(similarity, "compute_similarity", fake)


def test_threshold_boundary(monkeypatch):
    items = [_item(1), _item(2)]
    _patch_similarity(monkeypatch, {(0, 1): 0.90})
    assert len(similarity.find_similar_groups(items, 0.90)) == 1
    _patch_similarity(monkeypatch, {(0, 1): 0.8999})
    assert similarity.find_similar_groups(items, 0.90) == []


def test_union_find_transitivity(monkeypatch):
    items = [_item(1), _item(2), _item(3)]
    _patch_similarity(monkeypatch, {(0, 1): 0.95, (1, 2): 0.95, (0, 2): 0.10})
    groups = similarity.find_similar_groups(items, 0.90)
    assert len(groups) == 1 and len(groups[0]) == 3


def test_single_item_groups_are_dropped(monkeypatch):
    items = [_item(i) for i in (1, 2, 3, 4)]
    _patch_similarity(monkeypatch, {(0, 1): 0.95})
    groups = similarity.find_similar_groups(items, 0.90)
    assert len(groups) == 1 and len(groups[0]) == 2


def test_threshold_argument_is_effective(monkeypatch):
    items = [_item(1), _item(2)]
    _patch_similarity(monkeypatch, {(0, 1): 0.85})
    assert similarity.find_similar_groups(items, 0.90) == []
    assert len(similarity.find_similar_groups(items, 0.80)) == 1


# ---------- check_consistency 返回结构 ----------

def test_short_input_returns_empty_structure():
    r = similarity.check_consistency([_item(1)])
    assert set(r) == {"similar_groups", "warnings", "total_items",
                      "groups_found", "warnings_count"}
    assert r["total_items"] == 1
    assert r["similar_groups"] == [] and r["warnings"] == []
    assert r["groups_found"] == 0 and r["warnings_count"] == 0


def test_no_top_level_is_consistent_key():
    r = similarity.check_consistency([_item(1), _item(2)])
    assert "is_consistent" not in r
    assert "is_consistent" in r["similar_groups"][0]


def test_consistent_group_has_no_warnings():
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"]), _item(2, matched_ids=["YQ-02"])])
    assert r["groups_found"] == 1
    assert r["similar_groups"][0]["is_consistent"] is True
    assert r["warnings_count"] == 0


def test_different_subids_yield_medium_warning():
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"]), _item(2, matched_ids=["YQ-07"])])
    assert r["warnings_count"] == 1
    assert r["warnings"][0]["severity"] == "medium"
    assert "子目不匹配" in r["warnings"][0]["message"]


def test_unpriced_yields_high_warning_and_auto_fix():
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"]), _item(2, matched_ids=[], conf=0)])
    w = r["warnings"][0]
    assert w["severity"] == "high"
    assert 2 in w["unpriced_items"]
    assert w["auto_fix"]["from_index"] == 1
    assert w["auto_fix"]["sub_ids"] == ["YQ-02"]


def test_confidence_gap_over_20_yields_low_warning():
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"], conf=100),
        _item(2, matched_ids=["YQ-02"], conf=79)])
    assert r["warnings_count"] == 1
    assert r["warnings"][0]["severity"] == "low"


def test_summary_counts_match_lengths():
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"]), _item(2, matched_ids=["YQ-07"])])
    assert r["groups_found"] == len(r["similar_groups"])
    assert r["warnings_count"] == len(r["warnings"])


def test_offline_no_socket(monkeypatch):
    import socket

    def boom(*a, **k):
        raise AssertionError("一致性校验不应发起网络调用")
    monkeypatch.setattr(socket, "socket", boom)
    r = similarity.check_consistency([
        _item(1, matched_ids=["YQ-02"]), _item(2, matched_ids=["YQ-02"])])
    assert r["groups_found"] == 1


# ---------- build_check_items ----------

def _candidates(rows):
    return {"rows": rows}


def _row(row_id, sheet="A分部", section="地面", name="虚构墙面乳胶漆",
         spec="刮腻子三遍", unit="m2"):
    return {"row_id": row_id, "sheet": sheet, "section": section,
            "name": name, "spec": spec, "unit": unit, "qty": 1.0, "candidates": []}


def test_build_check_items_from_decisions():
    cands = _candidates([_row(1), _row(2, section="墙面")])
    decisions = {"1": {"code": "X-1", "team": "虚构班组"},
                 "2": {"subs": [{"code": "X-2"}, {"code": "X-1"}]}}
    items = similarity.build_check_items(cands, decisions)
    assert [i["index"] for i in items] == [1, 2]
    assert items[0]["matched_ids"] == ["X-1"]
    assert items[1]["matched_ids"] == ["X-1", "X-2"]
    assert all(i["overall_confidence"] == 100 for i in items)
    assert items[0]["sheet"] == "A分部" and items[1]["section"] == "墙面"


def test_build_check_items_honours_explicit_confidence():
    cands = _candidates([_row(1)])
    items = similarity.build_check_items(cands, {"1": {"code": "X-1", "confidence": 72}})
    assert items[0]["overall_confidence"] == 72


def test_default_confidence_prevents_false_unpriced():
    """远端把 overall_confidence 缺省 0 视为「未套价」，必须显式填默认值。"""
    cands = _candidates([_row(1), _row(2)])
    decisions = {"1": {"code": "YQ-02"}, "2": {"code": "YQ-02"}}
    items = similarity.build_check_items(cands, decisions)
    r = similarity.check_consistency(items)
    assert r["warnings_count"] == 0, "正常套价行不得被误判为未套价 high"


def test_no_decisions_is_all_unpriced():
    cands = _candidates([_row(1), _row(2)])
    items = similarity.build_check_items(cands, {})
    assert all(i["matched_ids"] == [] for i in items)
    r = similarity.check_consistency(items)
    assert r["warnings"][0]["severity"] == "high"
