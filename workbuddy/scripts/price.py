"""内部套价计价引擎 —— 与 docs/tool.html compUnitPrice() 逐项对齐

    人工     = Σ(子目单价 × coef × conv)
    主材     = Σ(子目主材价 × (1 + 损耗率/100) × coef × conv)
    辅材     = 行辅材费
    综合单价 = 人工 + 主材 + 辅材

注意：管理费与利润**不在内部口径内**。原前端公式里的
mgmt = 人工 × 管理费率、profit = 人工 × 利润率 只用于集团 296 条对甲报价（二期）。
"""
from __future__ import annotations


def _f(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def labor_price(subs) -> float:
    total = 0.0
    for s in subs or []:
        total += _f(s.get("unit_price")) * _f(s.get("coef"), 1.0) * _f(s.get("conv"), 1.0)
    return total


def material_cost(subs) -> float:
    total = 0.0
    for s in subs or []:
        mat = _f(s.get("mat_price"))
        if not mat:
            continue
        total += (mat * (1 + _f(s.get("waste_rate")) / 100)
                  * _f(s.get("coef"), 1.0) * _f(s.get("conv"), 1.0))
    return total


def unit_price(row) -> float:
    """行综合单价 = 人工 + 主材 + 辅材"""
    subs = (row or {}).get("subs") or []
    return labor_price(subs) + material_cost(subs) + _f((row or {}).get("aux_cost"))


def row_amount(row) -> float:
    return unit_price(row) * _f((row or {}).get("qty"))


def summarize(rows) -> dict:
    amount = 0.0
    qty = 0.0
    count = 0
    for r in rows or []:
        amount += row_amount(r)
        qty += _f(r.get("qty"))
        count += 1
    return {"rows": count, "qty": qty, "amount": amount}


def breakdown(row) -> dict:
    """拆出人工/主材/辅材三项，供报价单分列展示与对账。"""
    subs = (row or {}).get("subs") or []
    return {
        "labor": labor_price(subs),
        "material": material_cost(subs),
        "aux": _f((row or {}).get("aux_cost")),
        "unit_price": unit_price(row),
        "amount": row_amount(row),
    }
