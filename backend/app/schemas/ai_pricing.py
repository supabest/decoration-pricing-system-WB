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
    # 'internal'（默认）=对内 497 条基准价；'group'=对甲 ZS02 集团库。
    # 默认值就是旧行为，现有调用方（tool.html 对内、m.html）不需传字段也不受影响。
    mode: str = Field('internal', description="套价口径：internal（默认）/ group（集团 ZS02）")


class PriceBatchRequest(BaseModel):
    items: list[PricingItem] = Field(..., description="清单项目列表")
    api_key: str = Field(..., description="DeepSeek API Key")
    model: Optional[str] = Field(None, description="模型名，如 deepseek-v4-pro / deepseek-v4-flash，默认 pro")
    mode: str = Field('internal', description="套价口径：internal（默认）/ group（集团 ZS02）")


class MatchedSubItem(BaseModel):
    id: str = Field(..., description="基准价子目编号（集团口径为 ZS02 编号）")
    sheet: str = Field("", description="班组名称；集团口径为 'ZS02-<discipline>'")
    confidence: int = Field(0, description="置信度 0-100")
    reason: str = Field("", description="匹配理由")
    # 仅集团口径会填：该子目里 price 仍为 NULL 的主材名（待补价清单，不含金额）
    pending_mats: list[str] = Field(default_factory=list, description="待询价主材名称（仅 group）")


class PriceResponse(BaseModel):
    matched: list[MatchedSubItem] = Field(default_factory=list)
    overall_confidence: int = Field(0)
    note: str = Field("")


class PriceBatchResponse(BaseModel):
    results: list[dict] = Field(default_factory=list)
    total: int = 0
    success: int = 0
    failed: int = 0
