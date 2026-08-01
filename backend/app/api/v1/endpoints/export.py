"""Excel 导出接口"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from urllib.parse import quote
import logging

from app.schemas.export import ExportRequest
from app.services.excel_export import ExcelExporter

router = APIRouter()
logger = logging.getLogger(__name__)


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
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
