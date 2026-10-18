"""Excel 导出请求模型"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any


class ExportColumn(BaseModel):
    """导出列定义"""
    key: str           # seq/code/name/spec/unit/qty/lab/mat/waste/aux/mgmt/profit/usp/total/remark
    label: str         # 显示名（用户可自定义）
    num: bool = False  # 是否数字列
    width: int = 10    # 列宽（字符数）


class ExportSubItem(BaseModel):
    """子目（基准价条目）"""
    bid: str = ""                 # 基准价编号（如 NS-015、JD-145）
    name: str = ""
    spec: str = ""
    unit: str = ""
    coef: float = 1.0             # 系数
    conv: float = 1.0             # 换算系数
    unit_price: float = 0.0       # effPrice 计算后的单价
    mat_price: float = 0.0        # 子目专属主材单价
    waste_rate: float = 0.0       # 子目专属主材损耗率 %


class ExportRow(BaseModel):
    """清单项（BOQ 行）"""
    seq: int = 0
    name: str = ""
    spec: str = ""
    unit: str = ""
    qty: float = 0.0
    remark: str = ""
    mat_price: float = 0.0        # 主材单价
    waste_rate: float = 5.0       # 损耗率 %
    aux_cost: float = 0.0         # 辅材费
    labor_price: float = 0.0      # 人工单价（rowUnitPrice 计算值）
    subs: List[ExportSubItem] = []


class ExportSection(BaseModel):
    """分部（section）"""
    name: str = ""
    rows: List[ExportRow] = []


class ExportGroup(BaseModel):
    """分组（对应一个 Excel sheet 来源）"""
    sheet_name: str = ""
    sections: List[ExportSection] = []


class ExportRequest(BaseModel):
    """Excel 导出请求"""
    project_name: str = "套价表"
    columns: List[ExportColumn] = []
    groups: List[ExportGroup] = []
    mgmt_rate: float = 5.0        # 管理费率 %
    profit_rate: float = 7.0      # 利润率 %
    group_folding: bool = True    # 是否分组折叠
    show_subs: bool = False       # 是否显示子目明细
    use_formula: bool = True      # 是否写入 Excel 公式（否则静态数值）
    split_by_group: bool = False  # 是否按工种拆分多 Sheet
    include_summary_sheet: bool = False  # 是否额外生成汇总 Sheet
    # 对内核算参数：仅用于汇总 sheet 计算「占总成本比例」（总成本 = 合同金额×(1-目标利润率)），
    # 数值本身不出现在导出表中；contract_amount<=0 时比例列整体不输出
    contract_amount: float = 0.0      # 对甲合同金额（不含暂列金额），元
    target_profit_rate: float = 0.0   # 预估目标利润率 %

    # 允许额外字段（前端可能发送多余数据）
    model_config = ConfigDict(extra="ignore")


class TemplateExportRequest(ExportRequest):
    """模板导出请求 — 继承 ExportRequest，增加模板相关字段"""
    header_row: int = 0             # 模板中表头行的 0-based 行索引
    column_mapping: dict = {}       # {模板列索引(int或str): 数据字段key}


class AuxMaterialLine(BaseModel):
    """辅材清单品种行（工种内已按材料聚合）"""
    name: str = ""                    # 辅材名称；固定费行为「固定辅材费（定额包干）」
    unit: str = ""                    # 单位（固定费行为空）
    qty_total: Optional[float] = None  # 消耗量合计 Σ(清单qty×消耗量)，固定费行为 None
    price: Optional[float] = None      # 信息价单价，固定费行为 None
    subtotal: float = 0.0             # 合价
    is_fixed: bool = False            # 是否固定辅材费（定额包干，无单价/用量）


class AuxGroup(BaseModel):
    """辅材清单分组（一个工种 = 一个 sheet）"""
    sheet_name: str = ""
    lines: List[AuxMaterialLine] = []
    fixed_subtotal: float = 0.0     # 其中：固定辅材费
    material_subtotal: float = 0.0  # 其中：材料费
    total: float = 0.0              # 辅材合计


class AuxUnclassifiedItem(BaseModel):
    """未套子目的清单项（辅材费未计入汇总，单独列出供人工补充）"""
    name: str = ""                    # 项目名称
    spec: str = ""                    # 项目特征
    unit: str = ""                    # 单位
    qty: Optional[float] = None       # 工程量
    reason: str = ""                  # 原因：未套价 / 子目缺失 / 无工种


class AuxListExportRequest(BaseModel):
    """辅材费用清单导出请求（分工种·品种明细）"""
    project_name: str = "套价表"
    groups: List[AuxGroup] = []
    unclassified: List[AuxUnclassifiedItem] = []   # 未套子目清单项 → 「⚠️未套子目清单」sheet
    use_formula: bool = True         # 是否写入 Excel 公式（合价=消耗量×信息价、小计=SUM、汇总引用工种 sheet）
    # 对内核算参数：仅用于辅材汇总 sheet 计算「占总成本比例」，数值本身不出现在导出表中
    contract_amount: float = 0.0      # 对甲合同金额（不含暂列金额），元；<=0 时比例列不输出
    target_profit_rate: float = 0.0   # 预估目标利润率 %

