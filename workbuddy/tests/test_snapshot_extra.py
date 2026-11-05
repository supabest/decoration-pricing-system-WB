"""P0-0 扩加密快照：材料信息价数据集

RED 阶段期望：现有 load_snapshot() 没有 material_prices 键。
"""
from __future__ import annotations

import snapshot


def test_snapshot_has_material_prices():
    data = snapshot.load_snapshot()
    assert "material_prices" in data, "快照必须包含 material_prices 数据集"
    assert isinstance(data["material_prices"], dict)
    assert len(data["material_prices"]) >= 20, "信息价种子至少 20 种"


def test_material_price_record_shape():
    data = snapshot.load_snapshot()
    lib = data["material_prices"]
    assert lib, "信息价库不能为空"
    # 只校验结构与类型，绝不把价格写进断言或输出
    name, rec = next(iter(lib.items()))
    assert isinstance(name, str) and name
    assert isinstance(rec, dict)
    assert {"price", "unit", "effective_month"} <= set(rec)
    assert isinstance(rec["price"], (int, float))


def test_snapshot_has_aux_excel_items():
    """辅材清单项（P1 导出用），本期一并入快照。"""
    data = snapshot.load_snapshot()
    assert "aux_excel_items" in data
    assert isinstance(data["aux_excel_items"], list)
    assert len(data["aux_excel_items"]) > 0


def test_stats_reports_new_datasets():
    data = snapshot.load_snapshot()
    s = snapshot.stats(data)
    assert "material_prices" in s
    assert "aux_excel_items" in s
    assert s["material_prices"] == len(data["material_prices"])
    assert s["aux_excel_items"] == len(data["aux_excel_items"])


def test_empty_has_new_keys():
    e = snapshot.empty()
    assert e["material_prices"] == {}
    assert e["aux_excel_items"] == []


def test_legacy_snapshot_is_backward_compatible():
    """旧格式密文（无新键）解密后应自动补空结构，不抛异常。"""
    import json
    from pathlib import Path

    legacy = {
        "benchmark_items": [{"internal_code": "X-1", "unit_price": 1.0}],
        "waste_rates": {},
        "generated_at": "2026-01-01",
    }
    blob = snapshot.seal_json(legacy)
    p = Path("/tmp/dp-legacy-snapshot.enc")
    p.write_text(blob, encoding="utf-8")
    data = snapshot.load_snapshot(p)
    assert data["material_prices"] == {}
    assert data["aux_excel_items"] == []
    assert len(data["benchmark_items"]) == 1
