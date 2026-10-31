"""AI 套价全过程调试日志"""
import asyncio, json, httpx, traceback
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core.config import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rest_auth() -> dict:
    """调试日志的 Supabase 认证头：优先 service_role、未配回退 anon。

    ai_pricing_logs 含用户清单内容，2026-10-18 起 RLS 锁读
    （data/migrations/ai_pricing_logs_rls_migration.sql）：匿名只剩 INSERT，
    读取必须走 service_role（Render 已配）。本机未配该键时回退 anon——
    写入不受影响；读取会因 RLS 返回空，要在本机看日志请在 backend/.env 补
    SUPABASE_SERVICE_ROLE_KEY（可选）。
    """
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    return {"apikey": key, "Authorization": f"Bearer {key}"}


# ── 套价耗时统计（elapsed_ms） ──
# 与 DEBUG_PRICING 无关：调试日志记的是「这次怎么匹配的」，耗时记的是「花了多久」。
# 前者默认关（正文含用户清单内容），后者每次套价都要有，否则问了「几百条要跑多久」
# 仍然只能靠猜。行里只填清单三列 + elapsed_ms，不落 prompt/候选/AI 原文。
def timing_row(name: str, spec: str, unit: str, elapsed_ms: float) -> dict:
    return {
        "item_name": (name or "")[:200],
        "item_spec": (spec or "")[:2000],
        "item_unit": (unit or "")[:20],
        "elapsed_ms": max(0, int(round(elapsed_ms))),
    }


async def _insert_timing(row: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/ai_pricing_logs",
                headers={
                    **_rest_auth(),
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=[row],
            )
    except Exception as e:
        # 计时是旁路，写失败不能影响套价
        print(f"[TIMING] 保存失败: {e}")


_bg_tasks: set = set()


def schedule_timing(name: str, spec: str, unit: str, elapsed_ms: float):
    """计时落库不阻塞响应：Supabase 往返几十到几百 ms，同步等待就等于每行多付一次
    RTT，而这正是用户感知的那段时间。任务引用留在模块级 set，避免被 GC 回收。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # 无运行中事件循环：计时是旁路，丢掉即可
    task = loop.create_task(_insert_timing(timing_row(name, spec, unit, elapsed_ms)))
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)


def summarize_elapsed(values: list) -> dict:
    """把一串耗时（ms）规约成可直接看的统计量；只出聚合值、不出清单名——
    ai_pricing_logs 的 RLS 锁读就是因为行里有用户清单内容，聚合值才能安全外露。"""
    vals = []
    for v in values:
        try:
            n = int(float(v))
        except (TypeError, ValueError):
            continue
        if n >= 0:
            vals.append(n)
    if not vals:
        return {"count": 0, "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "max_ms": 0, "total_s": 0}
    vals.sort()

    def pct(p: float) -> int:
        # 与 Postgres percentile_disc 同口径：取「累计占比首次达到 p」的实测值
        # （min/max 插值会给出库里不存在的耗时，看 P95 时容易误判单条最慢的成因）
        k = p * len(vals)
        idx = int(k) - 1 if k == int(k) else int(k)
        return vals[max(0, min(len(vals) - 1, idx))]

    return {
        "count": len(vals),
        "avg_ms": int(round(sum(vals) / len(vals))),
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "max_ms": vals[-1],
        "total_s": round(sum(vals) / 1000, 1),
    }


async def fetch_recent_timings(hours: int = 24, limit: int = 5000) -> list:
    """读近 N 小时的 elapsed_ms。读取需 service_role（RLS 锁读），本机未配该键时返回
    空列表——与 /pricing/debug-logs 同一既定行为，不是故障。"""
    since = (datetime.now(timezone.utc) - timedelta(hours=max(1, hours))).isoformat()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/ai_pricing_logs"
                f"?select=elapsed_ms&elapsed_ms=not.is.null&created_at=gte.{since}"
                f"&order=created_at.desc&limit={max(1, min(limit, 20000))}",
                headers=_rest_auth(),
            )
            if r.status_code == 200:
                return [row.get("elapsed_ms") for row in r.json()]
    except Exception as e:
        print(f"[TIMING] 查询失败: {e}")
    return []


class PricingDebugLog:
    """单条清单的调试日志收集器"""

    def __init__(self, name: str, spec: str, unit: str, api_key: str = ""):
        self.name = name
        self.spec = spec
        self.unit = unit
        self.api_key = api_key
        self.steps = {}
        self._collect("input", {
            "name": name,
            "spec": spec,
            "unit": unit,
            "api_key_prefix": (api_key[:8] + "***") if api_key else "(empty)",
        })

    def _collect(self, step: str, data: dict):
        self.steps[step] = {
            "ts": _now_iso(),
            "data": data,
        }

    def log_route(self, teams: list[str]):
        self._collect("route", {"teams": teams, "count": len(teams)})

    def log_candidates(self, candidates: list[dict], total: int):
        self._collect("candidates", {
            "total": total,
            "top10": [
                {
                    # 对内行用 internal_code/item_name/trade_team，集团（ZS02）行用 code/name/
                    # discipline；两者只会出现其一，故回退取值而不是写死一套字段名。
                    "code": c.get("internal_code") or c.get("code", ""),
                    "name": c.get("item_name") or c.get("name", ""),
                    "team": c.get("trade_team") or c.get("discipline", ""),
                    "unit": c.get("unit", ""),
                }
                for c in (candidates[:10] if isinstance(candidates, list) else [])
            ],
        })

    def log_engineering(self, eng: dict):
        self._collect("engineering", eng)

    def log_prompt(self, system_prompt: str, user_prompt: str):
        self._collect("prompt", {
            "system_length": len(system_prompt),
            "system_preview": system_prompt[:500],
            "user_length": len(user_prompt),
            "user_preview": user_prompt[:500],
        })

    def log_response(self, raw: str, parsed: Optional[dict]):
        self._collect("response", {
            "raw_length": len(raw),
            "raw_preview": raw[:500],
            "parsed": parsed,
        })

    def log_final(self, result: dict):
        self._collect("final", result)

    def log_error(self, error: str):
        self._collect("error", {"message": error, "traceback": traceback.format_exc()[-500:]})

    def to_db_row(self) -> dict:
        def raw_data(step_name):
            return self.steps.get(step_name, {}).get("data", {})
        return {
            "item_name": self.name[:200],
            "item_spec": (self.spec or "")[:2000],
            "item_unit": (self.unit or "")[:20],
            "input_json": raw_data("input"),
            "route_json": raw_data("route"),
            "candidate_json": raw_data("candidates"),
            "engineering_json": raw_data("engineering"),
            "prompt_text": {"system": raw_data("prompt"), "user": raw_data("prompt")},
            "response_json": raw_data("response"),
            "final_result": raw_data("final"),
            "error_message": raw_data("error"),
        }


async def save_debug_log(log: PricingDebugLog):
    """异步保存调试日志到 Supabase，失败不影响主流程"""
    if not settings.DEBUG_PRICING:
        return
    try:
        row = log.to_db_row()
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/ai_pricing_logs",
                headers={
                    **_rest_auth(),
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=[row],
            )
    except Exception as e:
        # 日志写入失败不能影响套价
        print(f"[DEBUG_LOG] 保存失败: {e}")


async def get_recent_logs(limit: int = 20) -> list[dict]:
    """查询最近的调试日志"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/ai_pricing_logs"
                f"?select=*&order=created_at.desc&limit={limit}",
                headers=_rest_auth(),
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        print(f"[DEBUG_LOG] 查询失败: {e}")
    return []
