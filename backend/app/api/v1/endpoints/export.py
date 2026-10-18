"""Excel 导出接口"""
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from urllib.parse import quote
import logging
import json

from app.schemas.export import ExportRequest, TemplateExportRequest, AuxListExportRequest
from app.schemas.group_export import GroupSummaryRequest
from app.services.excel_export import ExcelExporter
from app.services.template_export import TemplateExcelExporter
from app.services.aux_export import AuxListExporter
from app.services.group_summary_export import GroupSummaryExporter

router = APIRouter()
logger = logging.getLogger(__name__)

# 500 错误体（P0-3）：异常细节只进服务器日志，绝不回显给浏览器。
# 曾为 content={"error": str(e)}——内部异常文本（路径/依赖信息）会被前端 toast 直接上屏。
# ⚠️ 400 的结构化 detail 契约（fitout_area_required / pending[] / coord_fee_not_configured）
#    是前端分支依赖，不在此列、不得改动。
_EXPORT_FAILED_MESSAGE = "导出服务异常，请重试；若持续失败请联系管理员"


def _export_failed() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "export_failed", "message": _EXPORT_FAILED_MESSAGE},
    )


@router.post("/excel")
async def export_excel(request: ExportRequest):
    """
    生成套价结果 Excel 文件

    - 接收前端 BOQ 数据 + 列配置 + 全局参数
    - 使用 openpyxl 生成标准 Excel（公式、折叠、样式）
    - 返回 xlsx 文件流
    """
    try:
        exporter = ExcelExporter(request)
        buffer = exporter.generate()

        filename = f"{request.project_name}_套价结果.xlsx"
        # 使用 URL 编码处理中文文件名
        encoded_name = quote(filename)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Excel export error: {e}", exc_info=True)
        return _export_failed()


@router.post("/aux-excel")
async def export_aux_excel(request: AuxListExportRequest):
    """
    生成辅材费用清单 Excel（分工种·品种明细）

    - 每个工种一个 sheet：辅材品种行（消耗量合计×信息价=合价）+ 固定辅材费行 + 小计
    - 末尾「辅材汇总」sheet：工种 → 材料费/固定费/合计 + 总计
    - 返回 xlsx 文件流
    """
    try:
        exporter = AuxListExporter(request)
        buffer = exporter.generate()

        filename = f"{request.project_name}_辅材费用清单.xlsx"
        encoded_name = quote(filename)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Aux list export error: {e}", exc_info=True)
        return _export_failed()


@router.post("/group-summary")
def export_group_summary(request: GroupSummaryRequest):
    """
    生成集团对甲报价汇总表（ZS02-T02）Excel 文件

    - 接收前端 collectGroupSummaryPayload()（清单行 × 集团子目 raw 值 + 费率 + 手工费用）
    - 后端用同一公式重算 H 并汇总四部分，勾稽：五 = 一+二+三+四、四 =（一+二+三）× 税率
    - 前置拦截（均 400，detail 带机器可读键）：
        · fitout_area <= 0            → 无法算单方造价/配合费
        · 任一 mats[].price is None   → 待询价（返回去重 codes，绝不带未定价数据出表）
        · rates.coordFee is None      → 精装修配合费未配置（null≠0，对甲导出不能静默漏计）
    - 返回 xlsx 文件流（sheet1 清单明细 A~H 分解 + sheet2 单位工程计价汇总表）

    同步 def：openpyxl 生成为 CPU 阻塞操作，交给 Starlette 线程池，不卡事件循环。
    """
    if request.fitout_area <= 0:
        raise HTTPException(status_code=400, detail={"error": "fitout_area_required"})
    pending = GroupSummaryExporter.pending_codes(request)
    if pending:
        raise HTTPException(status_code=400, detail={"pending": pending})
    if request.rates.coordFee is None:
        raise HTTPException(status_code=400, detail={"error": "coord_fee_not_configured"})

    try:
        exporter = GroupSummaryExporter(request)
        buffer = exporter.generate()

        filename = f"{request.project_name}_集团汇总表.xlsx"
        encoded_name = quote(filename)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Group summary export error: {e}", exc_info=True)
        return _export_failed()


@router.post("/template")
async def export_template(
    template: UploadFile = File(...),
    data: str = Form(...),
):
    """
    模板导出：在用户上传的 Excel 模板上填入 BOQ 数据

    - template: 用户上传的 xlsx 模板文件
    - data: JSON 字符串，包含 ExportRequest 全部字段 + header_row + column_mapping
    - 支持子目行插入、保留原模板格式
    - 返回 xlsx 文件流
    """
    try:
        req = TemplateExportRequest(**json.loads(data))
        template_bytes = await template.read()

        exporter = TemplateExcelExporter(req, template_bytes)
        buffer = exporter.generate()

        filename = f"{req.project_name}_套价结果.xlsx"
        encoded_name = quote(filename)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Template export error: {e}", exc_info=True)
        return _export_failed()
