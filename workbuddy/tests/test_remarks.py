"""P1-2 · 备注自动生成：分级口径对齐远端 buildSplitExport() 的 reason。

纯函数测试，用虚构数据，不依赖密钥 / 快照，不含任何定价明细。
"""
from __future__ import annotations

import remarks


def test_explicit_remark_is_preserved_verbatim():
    """模型或人工写的备注优先，不被自动规则覆盖。"""
    d = {"code": "X-1", "team": "虚构班组", "remark": "含基层处理，需现场复核"}
    assert remarks.build_remark(decision=d, picks=[("X-1", "虚构班组", {})],
                                hit=[("X-1", "虚构班组")]) == "含基层处理，需现场复核"


def test_no_candidate_is_unpriced_with_reason():
    """候选召回为空 → 说明不是漏判，而是无可用子目。"""
    assert "无候选子目" in remarks.build_remark(
        decision=None, picks=[], hit=[], has_candidates=False)


def test_candidates_without_decision_is_unpriced():
    """有候选但未判定 → 明确标为待判定，与「无候选」区分开。"""
    r = remarks.build_remark(decision=None, picks=[], hit=[], has_candidates=True)
    assert "待判定" in r and "无候选" not in r


def test_missing_subitem_when_picks_not_found():
    """决策给了编号但快照里查不到 → 对齐远端 reason「子目缺失」。"""
    r = remarks.build_remark(decision={"code": "X-9", "team": "虚构班组"},
                             picks=[("X-9", "虚构班组", {})], hit=[])
    assert "子目缺失" in r


def test_partial_missing_counted():
    """多子目只命中一部分 → 给出 n/m，提示人工复核。"""
    r = remarks.build_remark(
        decision={"subs": [{"code": "X-1"}, {"code": "X-9"}]},
        picks=[("X-1", "虚构班组", {}), ("X-9", "虚构班组", {})],
        hit=[("X-1", "虚构班组")])
    assert "部分子目缺失" in r and "1/2" in r


def test_low_confidence_flagged():
    """confidence < 60 视为待复核（与 SKILL.md 判定要点一致）。"""
    d = {"code": "X-1", "team": "虚构班组", "confidence": 42}
    r = remarks.build_remark(decision=d, picks=[("X-1", "虚构班组", {})],
                             hit=[("X-1", "虚构班组")])
    assert "低置信度" in r and "42" in r


def test_clean_row_has_empty_remark():
    d = {"code": "X-1", "team": "虚构班组", "confidence": 88}
    assert remarks.build_remark(decision=d, picks=[("X-1", "虚构班组", {})],
                                hit=[("X-1", "虚构班组")]) == ""


def test_explicit_remark_beats_low_confidence():
    """显式备注优先于置信度提示，避免重复堆叠。"""
    d = {"code": "X-1", "team": "虚构班组", "confidence": 30, "remark": "人工已确认"}
    assert remarks.build_remark(decision=d, picks=[("X-1", "虚构班组", {})],
                                hit=[("X-1", "虚构班组")]) == "人工已确认"
