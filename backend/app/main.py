"""装修工程AI套价系统 — FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.core.config import settings
from app.core.middleware import RequestLogMiddleware
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：检查数据库连接、加载缓存预热等
    yield
    # 关闭时：清理资源


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="装修工程 AI 智能套价系统 API",
    lifespan=lifespan,
)


# 捕获 Pydantic 验证错误，返回详细信息
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://[a-z0-9]+\.decoration-pricing-system\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLogMiddleware)

# 路由注册
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """生产健康检查 — 验证 Supabase 连接"""
    db_status = "disconnected"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/benchmark_items?select=id&limit=1",
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
                },
            )
            db_status = "connected" if r.status_code == 200 else "error"
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "version": settings.APP_VERSION,
    }
