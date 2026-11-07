"""备注自动生成（P1-2）

口径对齐远端 docs/tool.html 的 buildSplitExport()：未套价 / 子目缺失
等情形要给出**可读的原因**，而不是一律写「未匹配」，便于人工复核时
一眼看出该补子目、该判定、还是该查编号。

纯函数，不读快照、不接触任何价格。
"""
from __future__ import annotations

CONFIDENCE_FLOOR = 60  # 与 SKILL.md 判定要点一致：< 60 视为未匹配


def build_remark(*, decision=None, picks=(), hit=(),
                 has_candidates: bool = True) -> str:
    """按优先级生成备注文本；无异常时返回空串。

    decision        : 该行的判定结果（可含 remark / confidence / subs）
    picks           : _picks() 产出的 [(code, team, extra), ...]
    hit             : _build_subs() 实际在快照里命中的 [(code, team), ...]
    has_candidates  : 候选召回是否非空（区分「没得选」与「没判定」）
    """
    d = decision or {}
    explicit = str(d.get("remark") or "").strip()
    if explicit:
        return explicit

    picks = list(picks)
    hit = list(hit)

    if not picks:
        return "未套价：无候选子目" if not has_candidates else "未套价：待判定子目"
    if not hit:
        return "子目缺失：编号或工种在基准价中不存在"
    if len(hit) < len(picks):
        return f"部分子目缺失（{len(hit)}/{len(picks)}），需复核"

    conf = d.get("confidence")
    if conf is not None:
        try:
            if float(conf) < CONFIDENCE_FLOOR:
                return f"低置信度({conf})，建议复核"
        except (TypeError, ValueError):
            pass
    return ""
