"""相似清单一致性校验 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


class CheckItem(BaseModel):
    """单条待校验的清单项目"""
    index: int = Field(..., description="清单行序号（对应前端 BOQ 行索引）")
    name: str = Field(..., description="清单名称")
    spec: Optional[str] = Field("", description="项目特征")
    unit: Optional[str] = Field("", description="单位")
    matched_ids: list[str] = Field(default_factory=list, description="已匹配的子目编号列表")
    overall_confidence: int = Field(0, description="AI 整体置信度 0-100")


class ConsistencyCheckRequest(BaseModel):
    """一致性校验请求"""
    items: list[CheckItem] = Field(..., description="所有已套价清单项目")


class SimilarGroupItem(BaseModel):
    """同组内的单个项目"""
    index: int
    name: str
    matched_ids: list[str]
    overall_confidence: int


class SimilarGroup(BaseModel):
    """相似清单分组"""
    group_id: int = Field(..., description="分组 ID")
    items: list[SimilarGroupItem] = Field(..., description="组内项目列表")
    is_consistent: bool = Field(..., description="组内结果是否一致")
    similarity_scores: list[float] = Field(default_factory=list, description="组内项目间的相似度矩阵")


class AutoFix(BaseModel):
    """自动修复建议"""
    from_index: int = Field(..., description="参考来源序号")
    sub_ids: list[str] = Field(..., description="推荐子目编号列表")


class ConsistencyWarning(BaseModel):
    """不一致警告"""
    group_id: int = Field(..., description="所属分组")
    severity: str = Field(..., description="严重程度: high / medium / low")
    message: str = Field(..., description="警告信息")
    suggestion: str = Field("", description="建议操作")
    unpriced_items: list[int] = Field(default_factory=list, description="未套价项目序号")
    reference_items: list[int] = Field(default_factory=list, description="参考项目序号")
    auto_fix: Optional[AutoFix] = Field(None, description="自动修复建议")


class ConsistencyCheckResponse(BaseModel):
    """一致性校验响应"""
    similar_groups: list[SimilarGroup] = Field(default_factory=list)
    warnings: list[ConsistencyWarning] = Field(default_factory=list)
    total_items: int = Field(0)
    groups_found: int = Field(0, description="发现的相似组数量")
    warnings_count: int = Field(0, description="警告数量")
