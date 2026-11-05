"""P0-3 · 辅材规则 FIXED / RATE / GROUP 完整实现

对齐远端 docs/tool.html：
  getAuxDetailForSub → fixedK(无条件) + 配方材料行(RATE 单材料 / GROUP 多材料)
  computeAuxForSub   → fixedK + Σ(材料价 × 消耗量)
  computeAuxForRow   → Σ 各子目，不乘 coef/conv

测试一律用虚构数值，不引用、不输出任何真实定价。
"""
from __future__ import annotations

import pytest

import cli
import snapshot
from aux_rules import aux_cost


def test_fixed_rule_returns_fixed_k():
    item = {"aux_rule_type": "FIXED", "aux_fixed_k": 4.79, "aux_rate_detail": None}
    assert aux_cost(item, {}) == pytest.approx(4.79)


def test_rate_rule_adds_fixed_k_and_material():
    item = {
        "aux_rule_type": "RATE", "aux_fixed_k": 0.45,
        "aux_rate_detail": {"type": "RATE", "materialName": "虚构材料A",
                            "consume": 0.0355, "unit": "m3"},
    }
    lib = {"虚构材料A": {"price": 10.0, "unit": "m3"}}
    assert aux_cost(item, lib) == pytest.approx(0.45 + 10.0 * 0.0355)


def test_group_rule_sums_all_materials():
    item = {
        "aux_rule_type": "GROUP", "aux_fixed_k": 1.0,
        "aux_rate_detail": {"type": "GROUP", "items": [
            {"name": "虚构材料A", "consume": 2.0},
            {"name": "虚构材料B", "consume": 0.5},
        ]},
    }
    lib = {"虚构材料A": {"price": 3.0}, "虚构材料B": {"price": 8.0}}
    assert aux_cost(item, lib) == pytest.approx(1.0 + 3.0 * 2.0 + 8.0 * 0.5)


def test_unknown_material_price_counts_as_zero():
    """远端 getMaterialPrice 查不到返回 0，不报错。"""
    item = {"aux_rule_type": "RATE", "aux_fixed_k": 2.0,
            "aux_rate_detail": {"type": "RATE", "materialName": "查无此料",
                                "consume": 99.0}}
    assert aux_cost(item, {}) == pytest.approx(2.0)


def test_no_rate_detail_means_fixed_k_only():
    item = {"aux_rule_type": "FIXED", "aux_fixed_k": 7.5}
    assert aux_cost(item, {}) == pytest.approx(7.5)


def test_rate_detail_type_drives_calc_not_rule_type_label():
    """远端按 auxRateDetail.type 分支，rule_type 只是展示标签。"""
    item = {"aux_rule_type": "FIXED", "aux_fixed_k": 0.0,
            "aux_rate_detail": {"type": "RATE", "materialName": "虚构材料A",
                                "consume": 2.0}}
    assert aux_cost(item, {"虚构材料A": {"price": 5.0}}) == pytest.approx(10.0)


def test_missing_and_malformed_inputs_degrade_to_zero():
    assert aux_cost(None, {}) == 0.0
    assert aux_cost({}, {}) == 0.0
    assert aux_cost({"aux_fixed_k": "bad"}, {}) == 0.0
    assert aux_cost({"aux_rate_detail": "not-a-dict"}, {}) == 0.0


def test_cli_uses_real_rate_detail_from_snapshot():
    """集成：挑一条真实 RATE 子目，新算法结果必须 >= 旧的「只取 fixed_k」。"""
    items = snapshot.load_snapshot()["benchmark_items"]
    rate_items = [i for i in items
                  if isinstance(i.get("aux_rate_detail"), dict)
                  and i["aux_rate_detail"].get("type") == "RATE"]
    assert rate_items, "快照里应有 RATE 规则子目"
    lib = snapshot.load_snapshot()["material_prices"]
    it = rate_items[0]
    fixed_only = float(it.get("aux_fixed_k") or 0)
    assert cli._aux_cost(it, lib) >= fixed_only
