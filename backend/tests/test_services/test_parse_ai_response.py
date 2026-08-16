"""parse_ai_response 回归测试 — 防止 DeepSeek 截断 JSON 解析修复被回退。

运行方式：
  - pytest backend/tests/test_services/test_parse_ai_response.py
  - python backend/tests/test_services/test_parse_ai_response.py  （无 pytest 时也能跑）
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ai_pricing_service import parse_ai_response


def _cases():
    """返回 (描述, 输入, 期望的 matched id 列表)"""
    return [
        ("正常 JSON",
         '{"matched":[{"id":"YQ-025","sheet":"木工班组","confidence":90}],"overall_confidence":90}',
         ["YQ-025"]),
        ("代码块包裹",
         '```json\n{"matched":[],"overall_confidence":0}\n```',
         []),
        # 真实截断案例1：note 字段被切断（单行紧凑版）
        ("截断-单行 note 被切",
         '{"matched":[{"id":"TG-017","sheet":"铁工班组","confidence":90,"reason":"清单为不锈钢吊顶，与TG-017最匹配；"}],"overall_confidence":90,"note":"候选库无',
         ["TG-017"]),
        # 真实截断案例2：note 字段被切断（多行缩进版）
        ("截断-多行 note 被切",
         '{\n  "matched": [\n    {\n      "id": "MQ-034",\n      "sheet": "幕墙班组",\n      "confidence": 80,\n      "reason": "清单名称含铝百叶且特征含防尘网，与MQ-034相符。"\n    }\n  ],\n  "overall_confidence": 80,\n  "note": "清单按名称强信号词路由至幕墙班组，但防尘网与防鸟网',
         ["MQ-034"]),
        ("空字符串", "", None),
        ("纯空白", "   ", None),
        ("前后杂质",
         '前置说明 {"matched":[{"id":"NS-01","sheet":"泥水班组","confidence":95}],"overall_confidence":95} 后缀说明',
         ["NS-01"]),
    ]


def _extract_ids(result):
    if not result:
        return None
    return [m.get("id") for m in result.get("matched", [])]


def test_parse_ai_response():
    for desc, raw, expected in _cases():
        ids = _extract_ids(parse_ai_response(raw))
        assert ids == expected, f"[{desc}] 期望 {expected}, 实际 {ids}"


if __name__ == "__main__":
    failed = 0
    for desc, raw, expected in _cases():
        ids = _extract_ids(parse_ai_response(raw))
        ok = ids == expected
        print(f"{'✅' if ok else '❌'} {desc}: {ids}")
        if not ok:
            failed += 1
    sys.exit(1 if failed else 0)
