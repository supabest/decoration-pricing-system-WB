"""AI 套价 API 端点"""
from fastapi import APIRouter, HTTPException
from app.schemas.ai_pricing import (
    PriceSingleRequest, PriceBatchRequest,
    PriceResponse, PriceBatchResponse,
)
from app.services.ai_pricing_service import price_single as svc_price_single

router = APIRouter(prefix="/pricing", tags=["AI套价"])


@router.post("/single", response_model=PriceResponse)
async def price_single_item(req: PriceSingleRequest):
    """单行套价：一条清单 → AI 匹配子目"""
    try:
        result = await svc_price_single(
            req.item.name,
            req.item.spec or "",
            req.item.unit or "",
            req.api_key
        )
        return PriceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=PriceBatchResponse)
async def price_batch_items(req: PriceBatchRequest):
    """批量套价：多条清单 → AI 匹配子目"""
    from app.services.ai_pricing_service import price_single as svc_price_single
    results = []
    success = 0
    failed = 0
    for item in req.items:
        try:
            r = await svc_price_single(item.name, item.spec or "", item.unit or "", req.api_key)
            results.append({"name": item.name, **r})
            if r.get("matched"):
                success += 1
            else:
                failed += 1
        except Exception as e:
            results.append({"name": item.name, "matched": [], "overall_confidence": 0, "note": str(e)[:100]})
            failed += 1
    return PriceBatchResponse(results=results, total=len(req.items), success=success, failed=failed)
