"""Supabase JWT 认证模块

验证前端传来的 Supabase JWT token，提取用户信息供端点使用。
未认证用户返回 401，端点可通过 Depends(require_auth) 强制认证。
"""
import logging
from typing import Optional
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError, ExpiredSignatureError
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# JWKS 缓存
_jwks: Optional[dict] = None


async def _get_jwks() -> dict:
    """获取 Supabase JWKS，缓存一份"""
    global _jwks
    if _jwks:
        return _jwks
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            )
            _jwks = r.json() if r.status_code == 200 else {"keys": []}
    except Exception:
        _jwks = {"keys": []}
    return _jwks


async def verify_supabase_jwt(token: str) -> dict:
    """验证 Supabase JWT token，返回 decoded payload

    验证步骤:
    1. 从 JWKS 获取公钥
    2. 验证 JWT 签名、过期、issuer
    3. 返回 decoded payload {sub, email, role, ...}
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    jwks = await _get_jwks()

    try:
        # 不验证 audience (Supabase JWKS 默认不设 aud)
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256", "ES256"],
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            options={"verify_aud": False},
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI 依赖：强制 JWT 认证

    用法:
        @router.post("/protected")
        async def endpoint(user: dict = Depends(require_auth)):
            return {"user_id": user["sub"]}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split("Bearer ")[-1].strip()
    payload = await verify_supabase_jwt(token)

    # 确保 token 包含必要字段
    if "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return payload


async def optional_auth(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """FastAPI 依赖：可选 JWT 认证，不强制

    用法:
        @router.get("/optional")
        async def endpoint(user: Optional[dict] = Depends(optional_auth)):
            if user:
                return {"message": "authenticated"}
            return {"message": "anonymous"}
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split("Bearer ")[-1].strip()
        return await verify_supabase_jwt(token)
    except HTTPException:
        return None


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """FastAPI 依赖：要求管理员权限

    检查 Supabase JWT 中的 app_metadata.role == 'admin'
    """
    app_meta = user.get("app_metadata", {}) or {}
    role = app_meta.get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
