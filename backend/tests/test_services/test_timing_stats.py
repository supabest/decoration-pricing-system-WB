"""套价耗时统计（elapsed_ms）回归

背景：问「几百条清单要多久」曾只能靠猜——每次套价的真实耗时没有落库。
现在 price_single 计时壳把耗时经 schedule_timing 旁路写入 ai_pricing_logs.elapsed_ms，
/timing-stats 用 summarize_elapsed 出聚合值。本用例钉住三件事：
  1. 聚合口径（avg/p50/p95/max）与脏值容错；
  2. 计时行只写清单三列 + 耗时，绝不带 prompt/候选等正文；
  3. 无事件循环时 schedule_timing 不得抛（同步脚本直调 price_single 的路径）。
"""
import asyncio

from app.services.pricing_debug_logger import (
    schedule_timing, summarize_elapsed, timing_row,
)


def test_summarize_empty():
    assert summarize_elapsed([]) == {
        "count": 0, "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "max_ms": 0, "total_s": 0,
    }


def test_summarize_percentiles_and_total():
    vals = [1000] * 19 + [10000]  # 20 条：一条 10s，其余 1s
    s = summarize_elapsed(vals)
    assert s["count"] == 20
    assert s["avg_ms"] == 1450
    assert s["p50_ms"] == 1000
    assert s["p95_ms"] == 1000  # 与 percentile_disc 同口径：累计到 95% 处仍是 1s
    assert s["max_ms"] == 10000
    assert s["total_s"] == 29.0


def test_summarize_tolerates_postgrest_dirty_values():
    """PostgREST 可能回字符串/None；负数与不可解析值直接丢弃，不参与均值。"""
    s = summarize_elapsed([None, "1200", 800.0, "abc", -5])
    assert s["count"] == 2
    assert s["avg_ms"] == 1000
    assert s["max_ms"] == 1200


def test_timing_row_only_carries_listing_and_elapsed():
    row = timing_row("x" * 300, "y" * 3000, "z" * 30, 1234.6)
    assert set(row) == {"item_name", "item_spec", "item_unit", "elapsed_ms"}
    assert len(row["item_name"]) == 200
    assert len(row["item_spec"]) == 2000
    assert len(row["item_unit"]) == 20
    assert row["elapsed_ms"] == 1235
    assert timing_row("a", "", "", -1)["elapsed_ms"] == 0


def test_schedule_timing_without_event_loop_is_noop():
    """同步上下文（无运行中 loop）只跳过，不抛——计时是旁路，不能影响套价主流程。"""
    schedule_timing("清单", "", "m2", 100)


def test_schedule_timing_fires_task_in_loop(monkeypatch):
    """有 loop 时真的挂上异步写库（用桩替掉插入，测试不打网络）。"""
    from app.services import pricing_debug_logger as mod

    called = []

    async def fake_insert(row):
        called.append(row)

    monkeypatch.setattr(mod, "_insert_timing", fake_insert)

    async def main():
        mod._bg_tasks.clear()
        mod.schedule_timing("清单", "", "m2", 100)
        for _ in range(5):
            await asyncio.sleep(0)
        assert called and called[0]["elapsed_ms"] == 100

    asyncio.run(main())


def test_price_single_wrapper_records_timing(monkeypatch):
    """计时壳必须无条件落一行：把 _price_single 换成 0ms 的桩，断言 elapsed_ms 写进去了
    （钉住「壳还在、且仍走 schedule_timing」——重构把 price_single 合并回实现会静默丢数据）。"""
    from app.services import ai_pricing_service as svc
    from app.services import pricing_debug_logger as mod

    rows = []

    async def fake_insert(row):
        rows.append(row)

    async def fake_impl(name, spec, unit, api_key, model=None, debug_log=None, mode='internal'):
        return {"matched": [], "overall_confidence": 0, "note": "stub"}

    monkeypatch.setattr(mod, "_insert_timing", fake_insert)
    monkeypatch.setattr(svc, "_price_single", fake_impl)

    async def main():
        res = await svc.price_single("墙面乳胶漆", "两遍", "m2", "k")
        for _ in range(5):
            await asyncio.sleep(0)
        return res

    assert asyncio.run(main())["note"] == "stub"
    assert len(rows) == 1
    assert rows[0]["item_name"] == "墙面乳胶漆"
    assert rows[0]["item_unit"] == "m2"
    assert rows[0]["elapsed_ms"] >= 0
