"""知识库 API 端点"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.ai_pricing_service import load_knowledge, _knowledge_cache
from app.core.config import settings
from app.core.auth import require_auth, optional_auth
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["知识库"])


class KnowledgeEntry(BaseModel):
    """知识库条目"""
    category: str = Field(..., description="分类: 技巧/同义词/规则")
    keyword: str = Field(..., description="关键词")
    content: str = Field(..., description="内容")
    team: Optional[str] = Field("", description="适用班组")


class KnowledgeResponse(BaseModel):
    """知识库完整内容"""
    tips: list[dict] = Field(default_factory=list)
    synonyms: list[dict] = Field(default_factory=list)
    rules: list[dict] = Field(default_factory=list)


@router.get("", response_model=KnowledgeResponse)
async def get_knowledge(user: Optional[dict] = Depends(optional_auth)):
    """获取全部知识库（tips + synonyms + rules）"""
    try:
        kb = await load_knowledge()
        return KnowledgeResponse(
            tips=kb.get('tips', []),
            synonyms=kb.get('synonyms', []),
            rules=kb.get('rules', []),
        )
    except Exception as e:
        logger.error(f"get_knowledge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
async def add_knowledge(entry: KnowledgeEntry,
                        user: dict = Depends(require_auth),
                        authorization: Optional[str] = Header(None)):
    """新增一条知识库条目 → 写入 Supabase (需登录)"""
    try:
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        headers["Authorization"] = authorization

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/ai_knowledge",
                headers=headers,
                json=[{
                    "category": entry.category,
                    "keyword": entry.keyword,
                    "content": entry.content,
                    "team": entry.team or "",
                }]
            )
            if r.status_code not in (200, 201, 204):
                raise HTTPException(status_code=502, detail="Storage service unavailable")

        # 清除缓存，下次查询时重新加载
        global _knowledge_cache
        _knowledge_cache = None

        return {"ok": True, "keyword": entry.keyword}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"add_knowledge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
