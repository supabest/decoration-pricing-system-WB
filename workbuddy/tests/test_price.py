"""T3 · 计价引擎 —— 测试先行

内部口径（不含管理费/利润）：
    人工 = Σ(子目单价 × coef × conv)
    主材 = Σ(子目主材价 × (1 + 损耗率/100) × coef × conv)
    辅材 = 行辅材费
    综合单价 = 人工 + 主材 + 辅材

17% 管理费 / 12% 利润只属集团 296 条对甲口径，不在本模块。
"""
import pytest

import price

EPS = 1e-6


def sub(unit_price=0.0, coef=1.0, conv=1.0, mat_price=0.0, waste_rate=0.0):
    return {"unit_price": unit_price, "coef": coef, "conv": conv,
            "mat_price": mat_price, "waste_rate": waste_rate}


def row(subs=None, aux_cost=0.0, qty=1.0):
    return {"subs": subs or [], "aux_cost": aux_cost, "qty": qty}


# ---------- 人工 ----------

def test_labor_single_sub():
    assert abs(price.labor_price([sub(unit_price=100)]) - 100) < EPS


def test_labor_applies_coef_and_conv():
    # 200 × 1.5 × 0.8 = 240
    assert abs(price.labor_price([sub(unit_price=200, coef=1.5, conv=0.8)]) - 240) < EPS


def test_labor_sums_subs():
    assert abs(price.labor_price([sub(unit_price=100), sub(unit_price=50, coef=2, conv=0.5)]) - 150) < EPS


# ---------- 主材 ----------

def test_material_applies_waste_rate():
    # 200 × (1 + 10/100) = 220
    assert abs(price.material_cost([sub(mat_price=200, waste_rate=10)]) - 220) < EPS


def test_material_applies_coef_and_conv():
    # 100 × 1.1 × 2 × 0.5 = 110
    assert abs(price.material_cost([sub(mat_price=100, waste_rate=10, coef=2, conv=0.5)]) - 110) < EPS


def test_material_zero_when_no_price():
    assert price.material_cost([sub(mat_price=0)]) == 0


# ---------- 综合单价 ----------

def test_unit_price_full_composition():
    # 人工 100 + 主材 220 + 辅材 5 = 325
    r = row([sub(unit_price=100, mat_price=200, waste_rate=10)], aux_cost=5)
    assert abs(price.unit_price(r) - 325) < EPS


def test_unit_price_no_subs():
    assert abs(price.unit_price(row([], aux_cost=10)) - 10) < EPS


def test_unit_price_has_no_mgmt_or_profit():
    """内部口径不得混入管理费/利润：同样输入，结果必须等于 人工+主材+辅材。"""
    r = row([sub(unit_price=1000, mat_price=500, waste_rate=5)], aux_cost=20)
    assert abs(price.unit_price(r) - (1000 + 525 + 20)) < EPS


# ---------- 合价 ----------

def test_row_amount():
    r = row([sub(unit_price=100, mat_price=100)], aux_cost=0, qty=12.5)
    assert abs(price.row_amount(r) - 200 * 12.5) < EPS


# ---------- 汇总 ----------

def test_summarize_sums_rows():
    rows = [row([sub(unit_price=100)], qty=2), row([sub(unit_price=50)], qty=4)]
    total = price.summarize(rows)
    assert abs(total["amount"] - (200 + 200)) < EPS
    assert total["rows"] == 2
    assert abs(total["qty"] - 6) < EPS


# ---------- 缺字段容错 ----------

@pytest.mark.parametrize("bad", [
    {}, {"subs": None}, {"subs": [{}]}, {"subs": [{"unit_price": None}]},
])
def test_missing_fields_treated_as_zero(bad):
    assert price.unit_price(bad) == 0
