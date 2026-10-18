"""集团汇总表（ZS02-T02）导出请求模型 — 与前端 docs/tool.html:collectGroupSummaryPayload() 逐字段对齐

payload 契约（Task 6 落地，14 键 / item，一条 = 「清单行 × 集团子目」）：
  {project_name, fitout_area, rates{mgmt,profit,green,baogan,tax,coordFee},
   manual_fees{overtime_fee,contract_change_fee,inflation_fee},
   items[{code,discipline,section_name,name,unit,spec,qty,work_type,lab,aux,mech,coef,conv,mats[]}]}

★ 前端不下发算得的 h —— 后端用同一公式重算（单一算账口径归后端）。
★ 费率一律来自本模型字段（缺省值 = T01 种子），业务逻辑分支内不写死费率。
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


def _blank_to(value, default):
    """前端数字输入清空会原样下发 ''（input.value），按缺省兜底而不是回 422。"""
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value


class GroupMat(BaseModel):
    """主材条目（ZS02 B~C 列，源结构见 scripts/import_group_benchmark.py:_mk_mat）"""
    name: str = ""
    unit: str = ""
    price: Optional[float] = None      # None = 甲供未限价（待询价）；0 是有效报价，两者语义不同
    consumption: float = 0.0           # 消耗量（源表已含损耗，不再乘损耗率）

    @field_validator('price', mode='before')
    @classmethod
    def _price_blank_to_none(cls, v):
        """'' / None 一律回 None（待询价），不能被当成 0 元报价。"""
        return None if (v is None or (isinstance(v, str) and not v.strip())) else v

    @field_validator('consumption', mode='before')
    @classmethod
    def _consumption_blank_to_zero(cls, v):
        return _blank_to(v, 0.0)

    model_config = ConfigDict(extra="ignore")   # 前端可能带 idx/pending/label/cost 等派生键


class GroupSummaryItem(BaseModel):
    """清单行 × 集团子目 的 raw 值（qty 之外均为字符串，来自 ZS02 库行原样）"""
    code: str = ""                      # 子目编码，如 ZS02-A-009
    discipline: str = ""                # 专业 A/B/C/D（D = 单价措施项目）
    section_name: str = ""              # 分部名，如 楼地面工程
    name: str = ""
    unit: str = ""
    spec: str = ""
    qty: float = 0.0                    # 清单行工程量
    work_type: str = ""                 # 工种，如 泥水
    lab: float = 0.0                    # A 人工
    mats: List[GroupMat] = []           # B×C 主材（price= None 即待询价）
    aux: float = 0.0                    # D 辅材
    mech: float = 0.0                   # E 机械
    coef: float = 1.0                   # 含量系数
    conv: float = 1.0                   # 子目单位 ↔ 清单单位换算系数

    @field_validator('qty', 'lab', 'aux', 'mech', mode='before')
    @classmethod
    def _num_blank_to_zero(cls, v):
        return _blank_to(v, 0.0)

    @field_validator('coef', 'conv', mode='before')
    @classmethod
    def _factor_blank_to_one(cls, v):
        """空值 → 1.0；0 同样按前端 parseFloat()||1.0 口径当 1.0（0 会让金额整体消失）。"""
        v = _blank_to(v, 1.0)
        try:
            return v if float(v) else 1.0
        except (TypeError, ValueError):
            return 1.0

    @model_validator(mode='before')
    @classmethod
    def _mats_must_be_list(cls, data):
        """库行/旧快照可能回传 JSON 文本或缺 mats（前端 groupSubCells 同款守卫）→ 兜空数组。"""
        if isinstance(data, dict):
            mats = data.get('mats')
            if mats is None or isinstance(mats, str):
                data = {**data, 'mats': []}
        return data

    model_config = ConfigDict(extra="ignore")


class GroupRates(BaseModel):
    """集团费率（小数）。缺省值 = T01 标准费率；coordFee 缺省 None = 参数未配置（≠ 0 元）。"""
    mgmt: float = 0.17       # 管理费率，基数 = 人工+机械
    profit: float = 0.12     # 利润率，基数 = 人工+机械
    green: float = 0.13      # 绿安费率，基数 = Σ(分部分项 人工+机械)
    baogan: float = 0.03     # 预算包干费率，基数 = Σ(分部分项 人工+机械)
    tax: float = 0.09        # 税金率，基数 = (一+二+三)
    coordFee: Optional[float] = None   # 精装修管理及配合费，元/m²（装修面积）

    @field_validator('mgmt', 'profit', 'green', 'baogan', 'tax', mode='before')
    @classmethod
    def _num_blank_to_seed(cls, v, info: ValidationInfo):
        """'' / None → 取该键缺省值（T01 种子），不报错也不静默当 0。"""
        if v is None or (isinstance(v, str) and not v.strip()):
            return cls.model_fields[info.field_name].default
        return v

    @field_validator('coordFee', mode='before')
    @classmethod
    def _coord_blank_to_none(cls, v):
        return None if (v is None or (isinstance(v, str) and not v.strip())) else v

    model_config = ConfigDict(extra="ignore")


class GroupManualFees(BaseModel):
    """手工金额行（其他项目费）：单位元，非费率"""
    overtime_fee: float = 0.0           # 赶工措施费
    contract_change_fee: float = 0.0    # 合同变更费用
    inflation_fee: float = 0.0          # 装修类型涨幅费用

    @field_validator('overtime_fee', 'contract_change_fee', 'inflation_fee', mode='before')
    @classmethod
    def _num_blank_to_zero(cls, v):
        return _blank_to(v, 0.0)

    model_config = ConfigDict(extra="ignore")


class GroupManualLine(BaseModel):
    """对甲补录手工行（措施/其他项目费）：直接录 综合单价×工程量=合价，不走 ZS02 引擎分解。
    amount 由后端用 qty×usp 重算（前端值不被信任），与前端 manualRowTotal 同口径。"""
    name: str = ""
    unit: str = ""
    qty: float = 0.0
    usp: float = 0.0                    # 手工综合单价
    remark: str = ""

    @field_validator('qty', 'usp', mode='before')
    @classmethod
    def _num_blank_to_zero(cls, v):
        return _blank_to(v, 0.0)

    model_config = ConfigDict(extra="ignore")   # 前端可能带 amount 等派生键（后端重算，忽略）


class GroupSummaryRequest(BaseModel):
    """POST /api/v1/export/group-summary 请求体"""
    project_name: str = "套价表"
    fitout_area: float = 0.0            # 装修面积 m²（<=0 时端点拦截，无法算单方造价/配合费）
    rates: GroupRates = Field(default_factory=GroupRates)
    manual_fees: GroupManualFees = Field(default_factory=GroupManualFees)
    items: List[GroupSummaryItem] = []
    manual_measures: List[GroupManualLine] = []   # 措施项目手工行 → 第二部分
    manual_others: List[GroupManualLine] = []     # 其他项目手工行 → 第三部分

    @field_validator('fitout_area', mode='before')
    @classmethod
    def _area_blank_to_zero(cls, v):
        return _blank_to(v, 0.0)

    model_config = ConfigDict(extra="ignore")
