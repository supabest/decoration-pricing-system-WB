"""辅材费计算 —— 与 docs/tool.html getAuxDetailForSub / computeAuxForSub 逐项对齐

    辅材(单子目) = aux_fixed_k + Σ(材料信息价 × 消耗量)
      · RATE  : aux_rate_detail = {type:RATE,  materialName, consume}
      · GROUP : aux_rate_detail = {type:GROUP, items:[{name, consume}, ...]}
      · FIXED : 只有 aux_fixed_k
    辅材(行)   = Σ 各子目，不乘 coef / conv

注意：aux_fixed_k 是**无条件叠加**的，RATE/GROUP 规则同样带；
     分支依据是 aux_rate_detail.type，不是 aux_rule_type 标签。
     信息价查不到时按 0 计（远端 getMaterialPrice 行为）。
"""
from __future__ import annotations


def _num(v, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _price(lib, name) -> float:
    if not name:
        return 0.0
    rec = (lib or {}).get(name)
    if isinstance(rec, dict):
        return _num(rec.get("price"))
    return _num(rec) if rec is not None else 0.0


def aux_detail(item, price_lib=None) -> dict:
    """返回 {fixed_k, materials:[{name, consume, price, subtotal}]}，便于辅材清单导出（P1）。"""
    if not isinstance(item, dict):
        return {"fixed_k": 0.0, "materials": []}
    fixed_k = _num(item.get("aux_fixed_k"))
    materials = []
    rd = item.get("aux_rate_detail")
    if isinstance(rd, dict):
        kind = (rd.get("type") or "").upper()
        if kind == "RATE":
            name = rd.get("materialName") or ""
            consume = _num(rd.get("consume"))
            p = _price(price_lib, name)
            materials.append({"name": name, "consume": consume,
                              "price": p, "subtotal": p * consume})
        elif kind == "GROUP":
            for m in rd.get("items") or []:
                if not isinstance(m, dict):
                    continue
                name = m.get("name") or ""
                consume = _num(m.get("consume"))
                p = _price(price_lib, name)
                materials.append({"name": name, "consume": consume,
                                  "price": p, "subtotal": p * consume})
    return {"fixed_k": fixed_k, "materials": materials}


def aux_cost(item, price_lib=None) -> float:
    d = aux_detail(item, price_lib)
    return d["fixed_k"] + sum(m["subtotal"] for m in d["materials"])
