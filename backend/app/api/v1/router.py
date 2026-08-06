"""API v1 路由汇总"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    ai_pricing as ai_pricing_endpoint,
    export,
    knowledge,
)

api_router = APIRouter()

# ── 生产端点 ──
api_router.include_router(ai_pricing_endpoint.router, prefix="/pricing", tags=["AI套价"])
api_router.include_router(export.router, prefix="/export", tags=["导出"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])

# ── DEPRECATED: 以下端点未实现，仅保留路由占位 ──
# api_router.include_router(enterprise_price.router, prefix="/enterprise-prices", tags=["deprecated"])
# api_router.include_router(material_price.router, prefix="/material-prices", tags=["deprecated"])
# api_router.include_router(quota.router, prefix="/quotas", tags=["deprecated"])
# api_router.include_router(bill_of_quantities.router, prefix="/bill-items", tags=["deprecated"])
# api_router.include_router(ai_recommend.router, prefix="/ai/recommend", tags=["deprecated"])
# api_router.include_router(auto_match.router, prefix="/ai/match", tags=["deprecated"])
# api_router.include_router(auto_pricing.router, prefix="/ai/pricing", tags=["deprecated"])
# api_router.include_router(project.router, prefix="/projects", tags=["deprecated"])
