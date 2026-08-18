"""AI 套价请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PricingItem(BaseModel):
    name: str = Field(..., description="清单项目名称")
    spec: Optional[str] = Field("", description="项目特征")
    unit: Optional[str] = Field("", description="单位")


class PriceSingleRequest(BaseModel):
    item: PricingItem
    api_key: str = Field(..., description="DeepSeek API Key")
    model: Optional[str] = Field(None, description="模型名，如 deepseek-v4-pro / deepseek-v4-flash，默认 pro")


class PriceBatchRequest(BaseModel):
    items: list[PricingItem] = Field(..., description="清单项目列表")
    api_key: str = Field(..., description="DeepSeek API Key")
    model: Optional[str] = Field(None, description="模型名，如 deepseek-v4-pro / deepseek-v4-flash，默认 pro")


class MatchedSubItem(BaseModel):
    id: str = Field(..., description="基准价子目编号")
    sheet: str = Field(..., description="班组名称")
    confidence: int = Field(..., description="置信度 0-100")
    reason: str = Field("", description="匹配理由")


class PriceResponse(BaseModel):
    matched: list[MatchedSubItem] = Field(default_factory=list)
    overall_confidence: int = Field(0)
    note: str = Field("")


class PriceBatchResponse(BaseModel):
    results: list[dict] = Field(default_factory=list)
    total: int = 0
    success: int = 0
    failed: int = 0
