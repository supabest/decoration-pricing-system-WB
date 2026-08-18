"""AI 套价 API 端点"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
from app.core.auth import require_auth, optional_auth
from app.schemas.ai_pricing import (
    PriceSingleRequest, PriceBatchRequest,
    PriceResponse, PriceBatchResponse,
)
from app.schemas.similarity import (
    ConsistencyCheckRequest, ConsistencyCheckResponse,
)
from app.core.config import settings
from app.services.ai_pricing_service import price_single as svc_price_single
from app.services.similarity_checker import check_consistency

router = APIRouter(tags=["AI套价"])


@router.post("/single", response_model=PriceResponse)
async def price_single_item(req: PriceSingleRequest):
    """单行套价：一条清单 → AI 匹配子目"""
    try:
        result = await svc_price_single(
            req.item.name,
            req.item.spec or "",
            req.item.unit or "",
            req.api_key,
            model=req.model
        )
        return PriceResponse(**result)
    except Exception as e:
        logger.error(f"price_single error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch", response_model=PriceBatchResponse)
async def price_batch_items(req: PriceBatchRequest):
    """批量套价：多条清单 → AI 匹配子目"""
    from app.services.ai_pricing_service import price_single as svc_price_single
    results = []
    success = 0
    failed = 0
    for item in req.items:
        try:
            r = await svc_price_single(item.name, item.spec or "", item.unit or "", req.api_key, model=req.model)
            results.append({"name": item.name, **r})
            if r.get("matched"):
                success += 1
            else:
                failed += 1
        except Exception as e:
            results.append({"name": item.name, "matched": [], "overall_confidence": 0, "note": str(e)[:100]})
            failed += 1
    return PriceBatchResponse(results=results, total=len(req.items), success=success, failed=failed)


@router.post("/check-consistency", response_model=ConsistencyCheckResponse)
async def check_pricing_consistency(req: ConsistencyCheckRequest):
    """相似清单一致性校验：检测套价结果中高度相似但结果不同的清单"""
    try:
        items_dicts = [item.model_dump() for item in req.items]
        result = check_consistency(items_dicts)
        return ConsistencyCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/report-failure")
async def report_pricing_failure(item: dict):
    """上报套价失败条目 → Supabase pricing_failures 表 (累加计数)"""
    import httpx
    try:
        name = (item.get("name") or "")[:200]
        spec = (item.get("spec") or "")[:2000]
        unit = (item.get("unit") or "")[:20]
        if not name:
            return {"ok": False, "reason": "empty name"}

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/rpc/report_pricing_failure",
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
                    "Content-Type": "application/json",
                },
                json={"p_name": name, "p_spec": spec, "p_unit": unit},
            )
            return {"ok": r.status_code in (200, 201, 204)}
    except Exception as e:
        logger.error(f"report_failure error: {e}")
        return {"ok": False}


@router.get("/failure-stats")
async def get_failure_stats(limit: int = 50):
    """查询套价失败统计排行"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/pricing_failures"
                f"?select=*&order=fail_count.desc&limit={limit}",
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
                },
            )
            if r.status_code == 200:
                data = r.json()
                return {"items": data, "total": len(data)}
    except Exception as e:
        logger.error(f"failure_stats error: {e}")
    return {"items": [], "total": 0}


@router.get("/debug-logs")
async def get_debug_logs(limit: int = 20, format: str = "json",
                          user: dict = Depends(require_auth)):
    """查询最近的 AI 套价调试日志 (需登录)"""
    from app.services.pricing_debug_logger import get_recent_logs
    try:
        logs = await get_recent_logs(limit)
        if format == "html":
            return _render_logs_html(logs)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


def _render_logs_html(logs: list[dict]) -> HTMLResponse:
    import json as _json

    def _dv(val):
        """安全取值，兼容 dict 和 str"""
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                return _json.loads(val)
            except Exception:
                return val
        return val or {}

    def _ds(val):
        """安全显示"""
        if isinstance(val, (dict, list)):
            return _json.dumps(val, ensure_ascii=False, indent=2)
        return str(val)

    items_html = ""
    for log in logs:
        fn = _dv(log.get("final_result"))
        matched = fn.get("matched", []) if isinstance(fn, dict) else []
        conf = fn.get("overall_confidence", 0) if isinstance(fn, dict) else 0
        status = "✅" if matched else "❌"
        cands = _dv(log.get("candidate_json"))
        resp = _dv(log.get("response_json"))
        eng = _dv(log.get("engineering_json"))
        prompt = _dv(log.get("prompt_text"))
        route = _dv(log.get("route_json"))

        # 候选 top5
        top5 = (cands.get("top10", []) if isinstance(cands, dict) else [])[:5]
        cand_rows = "".join(
            f'<li>{c.get("code","")} {c.get("name","")} ({c.get("team","")})</li>'
            for c in top5 if isinstance(c, dict)
        )

        # AI parsed
        parsed = resp.get("parsed", {}) if isinstance(resp, dict) else {}

        # Prompt preview
        sys_preview = ""
        if isinstance(prompt, dict):
            s = prompt.get("system", {})
            if isinstance(s, dict):
                sys_preview = f"system: {s.get('system_length',0)} chars, user: {s.get('user_length',0)} chars<br>"
                sys_preview += f"<pre>{s.get('system_preview','')[:800]}</pre>"

        items_html += f"""
        <details style="margin:8px 0;border:1px solid #ddd;border-radius:8px;padding:12px;background:#fff">
          <summary style="cursor:pointer;font-size:14px;font-weight:600">
            {status} [{conf}%] {log.get("item_name","?")} ({log.get("item_unit","")})
            <span style="color:#888;font-size:11px;margin-left:8px">{str(log.get("created_at",""))[:19]}</span>
          </summary>
          <div style="margin-top:10px;font-size:12px">
            <p><b>特征:</b> {str(log.get("item_spec",""))[:200]}</p>
            <p><b>班组路由:</b> <code>{_ds(route)}</code></p>
            <p><b>候选 (top5):</b></p><ul>{cand_rows}</ul>
            <p><b>工程理解:</b> <code>{_ds(eng)}</code></p>
            <p><b>AI 返回:</b></p>
            <pre style="background:#f5f5f5;padding:8px;border-radius:4px;overflow-x:auto;max-height:200px">{_ds(parsed)}</pre>
            <p><b>最终结果:</b> <code>{_ds(fn)}</code></p>
            <details><summary>📝 Prompt 摘要</summary>{sys_preview}</details>
          </div>
        </details>"""
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>AI套价调试日志</title>
<style>body{{font-family:-apple-system,sans-serif;max-width:1000px;margin:20px auto;padding:0 20px;background:#f8f9fa}}h1{{font-size:20px}}code{{background:#eee;padding:1px 4px;border-radius:3px;font-size:11px}}</style></head>
<body><h1>🔍 AI 套价调试日志 ({len(logs)} 条)</h1>{items_html}</body></html>"""
    return HTMLResponse(content=html)
