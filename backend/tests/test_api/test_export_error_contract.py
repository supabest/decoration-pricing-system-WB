"""导出端点错误契约回归（P0-3）

1. 500 不得回显内部异常文本（曾 content={"error": str(e)} 被前端 toast 直接上屏）
   → 统一 {"error": "export_failed", "message": <通用提示>}，细节只进服务器日志
2. 400 结构化 detail 契约不得变（前端分支依赖，见 tool.html:doGroupSummaryExport）：
   fitout_area_required / pending[去重编码] / coord_fee_not_configured

四个导出端点的 500 分支均以 monkeypatch 让 exporter.generate() 抛带特征串的异常，
断言该特征串不出现在响应体里。
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# 特征串模拟内部异常细节（路径/模块名），一旦回显即用例失败
_SECRET = "SECRET_INTERNAL:/app/backend/app/services/excel_export.py"


class _BoomExporter:
    """任意导出器替身：构造放行、generate 抛特征异常"""

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def pending_codes(cls, request):
        """端点在建实例前会先调它做待询价前置拦截（group-summary 专有）"""
        return []

    def generate(self):
        raise RuntimeError(_SECRET)


def _assert_no_leak(r):
    assert r.status_code == 500, r.text
    assert _SECRET not in r.text, "内部异常细节回显给了浏览器"
    body = r.json()
    assert body["error"] == "export_failed"
    assert body["message"], "通用提示不得为空"


def test_excel_500_hides_internal_error(monkeypatch):
    from app.api.v1.endpoints import export as export_ep
    monkeypatch.setattr(export_ep, "ExcelExporter", _BoomExporter)
    r = client.post("/api/v1/export/excel", json={"project_name": "冒烟"})
    _assert_no_leak(r)


def test_aux_500_hides_internal_error(monkeypatch):
    from app.api.v1.endpoints import export as export_ep
    monkeypatch.setattr(export_ep, "AuxListExporter", _BoomExporter)
    r = client.post("/api/v1/export/aux-excel", json={"project_name": "冒烟"})
    _assert_no_leak(r)


def test_group_summary_500_hides_internal_error(monkeypatch):
    from app.api.v1.endpoints import export as export_ep
    monkeypatch.setattr(export_ep, "GroupSummaryExporter", _BoomExporter)
    r = client.post("/api/v1/export/group-summary", json={
        "project_name": "冒烟", "fitout_area": 100,
        "rates": {"coordFee": 0}, "items": [],
    })
    _assert_no_leak(r)


def test_template_500_hides_internal_error(monkeypatch):
    from app.api.v1.endpoints import export as export_ep
    monkeypatch.setattr(export_ep, "TemplateExcelExporter", _BoomExporter)
    r = client.post(
        "/api/v1/export/template",
        files={"template": ("t.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"data": json.dumps({"project_name": "冒烟"})},
    )
    _assert_no_leak(r)


# ── 400 结构化契约（前端分支依赖，防手滑改坏）─────────────────────────


def _item(code="ZS02-A-009", price=100.0):
    return {
        "code": code, "discipline": "A", "unit": "m2", "qty": 10,
        "lab": 30, "aux": 2, "mech": 1,
        "mats": [{"name": "瓷砖", "unit": "m2", "price": price, "consumption": 1.02}],
    }


def test_group_summary_400_fitout_area_required():
    r = client.post("/api/v1/export/group-summary", json={
        "project_name": "x", "fitout_area": 0, "rates": {"coordFee": 0}, "items": [],
    })
    assert r.status_code == 400
    assert r.json()["detail"] == {"error": "fitout_area_required"}


def test_group_summary_400_pending_codes():
    r = client.post("/api/v1/export/group-summary", json={
        "project_name": "x", "fitout_area": 100, "rates": {"coordFee": 0},
        "items": [_item(price=None), _item(price=None), _item(price=0.0)],
    })
    assert r.status_code == 400
    detail = r.json()["detail"]
    # 去重且只含未定价项；price=0（甲供按 0 计）是合法价，不在列
    assert detail["pending"] == ["ZS02-A-009"]


def test_group_summary_400_coord_fee_not_configured():
    r = client.post("/api/v1/export/group-summary", json={
        "project_name": "x", "fitout_area": 100, "rates": {"coordFee": None},
        "items": [_item()],
    })
    assert r.status_code == 400
    assert r.json()["detail"] == {"error": "coord_fee_not_configured"}
