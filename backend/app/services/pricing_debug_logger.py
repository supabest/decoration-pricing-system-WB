"""AI 套价全过程调试日志"""
import json, httpx, traceback
from datetime import datetime, timezone
from typing import Optional
from app.core.config import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
                    "code": c.get("internal_code", ""),
                    "name": c.get("item_name", ""),
                    "team": c.get("trade_team", ""),
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
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
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
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
                },
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        print(f"[DEBUG_LOG] 查询失败: {e}")
    return []
