"""调试日志 HTML 页转义回归（P0-2）

日志内容全部用户可控（清单名/特征、AI 原文、候选子目名），未转义即注入面。
本用例钉住：任何字段里的标签都不得原样进 HTML；历史脏行不得抛异常。
"""
from app.api.v1.endpoints.ai_pricing import _render_logs_html

PAYLOAD = "<script>alert('xss')</script>"


def _body(logs) -> str:
    return _render_logs_html(logs).body.decode("utf-8")


def test_escapes_all_user_controllable_fields():
    """清单字段 / 候选 / 结果 / prompt 预览 全量插值点逐一钉住"""
    logs = [{
        "item_name": PAYLOAD,
        "item_spec": f'"{PAYLOAD}"',
        "item_unit": PAYLOAD,
        "created_at": PAYLOAD,
        "final_result": {"matched": [{"id": PAYLOAD}], "overall_confidence": 88, "note": PAYLOAD},
        "candidate_json": {"top10": [{"code": PAYLOAD, "name": PAYLOAD, "team": PAYLOAD}]},
        "response_json": {"parsed": {"k": PAYLOAD}},
        "engineering_json": {"teams": [PAYLOAD]},
        "prompt_text": {"system": {"system_length": 1, "user_length": 2, "system_preview": PAYLOAD}},
        "route_json": [PAYLOAD],
    }]
    body = _body(logs)
    assert "<script>" not in body, "存在未转义插值点"
    assert "&lt;script&gt;" in body, "转义后应保留可读内容"


def test_renders_dirty_rows_without_crashing():
    """历史脏行：None / 字符串 JSON / 非法置信度 → 不抛异常、不出现 None 字面量"""
    logs = [{
        "item_name": None,
        "item_spec": None,
        "item_unit": None,
        "created_at": None,
        "final_result": '{"matched": [], "overall_confidence": "abc"}',
        "candidate_json": "not-json",
        "response_json": None,
        "engineering_json": None,
        "prompt_text": None,
        "route_json": None,
    }]
    body = _body(logs)
    assert "[0%] ? ()" in body     # 非法置信度规约成 0；item_name None → ? 占位、单位空
    assert "None" not in body      # str(None) 泄漏（json null 是合法显示，不在此列）
