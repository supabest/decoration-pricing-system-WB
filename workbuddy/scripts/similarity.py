"""相似清单一致性校验 —— 逐字对齐后端 similarity_checker.py

纯本地算法（零第三方依赖、零联网）：字符 2-gram Jaccard + 四字段加权
+ Union-Find 分组 + 三类判据（子目不一致 / 未套价 / 置信度差）。
工程语义 parse 复用 retrieve.engineering_parse，不搬远端模块。

WB 侧只产出 JSON 报告：不做自动补全（auto_fix 仅作为建议字段保留）、
不做失败上报（离线无接收端）、不写 Excel。规格依据：
docs/WorkBuddy套价-与远端功能对齐规格.md:42「只做一致性校验，失败上报无意义」。

远端依据：backend/app/services/similarity_checker.py
"""
from __future__ import annotations

import re

import retrieve

# 权重与后端 compute_similarity 逐字一致，和恒为 1.0
W_NAME, W_SPEC, W_ENG, W_UNIT = 0.20, 0.50, 0.20, 0.10
DEFAULT_THRESHOLD = 0.90
CONFIDENCE_GAP = 20
DEFAULT_CONFIDENCE = 100

_CLEAN_RE = re.compile(r'[（）()\-—\/\s，。、；：！？\d]+')


def bigrams(text: str) -> set[str]:
    cleaned = _CLEAN_RE.sub('', text or '')
    return {cleaned[i:i + 2] for i in range(len(cleaned) - 1)}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _name_similarity(a: str, b: str) -> float:
    return jaccard(bigrams(a), bigrams(b))


def _spec_similarity(a: str, b: str) -> float:
    return jaccard(bigrams(a), bigrams(b))


def _engineering_similarity(eng_a: dict, eng_b: dict) -> float:
    def overlap(key: str) -> float:
        sa, sb = set(eng_a.get(key, [])), set(eng_b.get(key, []))
        return jaccard(sa, sb) if sa or sb else 1.0
    return (overlap('teams') + overlap('crafts') + overlap('materials')) / 3.0


def _unit_similarity(a: str, b: str) -> float:
    return 1.0 if a and b and a.strip() == b.strip() else 0.0


def compute_similarity(item_a: dict, item_b: dict) -> float:
    na, nb = item_a.get('name', ''), item_b.get('name', '')
    sa, sb = item_a.get('spec', ''), item_b.get('spec', '')
    ua, ub = item_a.get('unit', ''), item_b.get('unit', '')
    eng_a = retrieve.engineering_parse(na, sa)
    eng_b = retrieve.engineering_parse(nb, sb)
    sim = (W_NAME * _name_similarity(na, nb)
           + W_SPEC * _spec_similarity(sa, sb)
           + W_ENG * _engineering_similarity(eng_a, eng_b)
           + W_UNIT * _unit_similarity(ua, ub))
    return round(sim, 4)


def find_similar_groups(items: list[dict],
                        threshold: float = DEFAULT_THRESHOLD) -> list[list[int]]:
    """Union-Find 连通 sim >= threshold 的行，只返回 size > 1 的组。"""
    n = len(items)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            if compute_similarity(items[i], items[j]) >= threshold:
                union(i, j)

    grouped: dict[int, list[int]] = {}
    for i in range(n):
        grouped.setdefault(find(i), []).append(i)
    return [idx for idx in grouped.values() if len(idx) > 1]


def check_consistency(items: list[dict],
                      threshold: float = DEFAULT_THRESHOLD) -> dict:
    """返回 5 键（与远端逐字一致，无顶层 is_consistent）。

    threshold 是 WB 侧增强参数，默认 0.90 时行为与远端完全相同。
    """
    if len(items) < 2:
        return {
            'similar_groups': [], 'warnings': [], 'total_items': len(items),
            'groups_found': 0, 'warnings_count': 0,
        }

    groups = find_similar_groups(items, threshold)
    similar_groups, warnings = [], []

    for group_id, indices in enumerate(groups, start=1):
        group_items = [items[i] for i in indices]
        matched_sets = [set(gi.get('matched_ids') or []) for gi in group_items]
        non_empty = [s for s in matched_sets if s]
        matched_consistent = True
        if len(non_empty) >= 2:
            first = non_empty[0]
            matched_consistent = all(s == first for s in non_empty[1:])

        unpriced = [gi['index'] for gi in group_items
                    if not gi.get('matched_ids') or gi.get('overall_confidence', 0) == 0]
        has_unpriced = len(unpriced) > 0

        confidences = [gi.get('overall_confidence', 0) for gi in group_items
                       if gi.get('matched_ids')]
        conf_consistent = True
        if len(confidences) >= 2 and max(confidences) - min(confidences) > CONFIDENCE_GAP:
            conf_consistent = False

        is_consistent = matched_consistent and not has_unpriced and conf_consistent

        similar_groups.append({
            'group_id': group_id,
            'items': [{
                'index': gi['index'],
                'name': gi.get('name', ''),
                'matched_ids': gi.get('matched_ids', []),
                'overall_confidence': gi.get('overall_confidence', 0),
            } for gi in group_items],
            'is_consistent': is_consistent,
            'similarity_scores': [
                compute_similarity(group_items[i], group_items[j])
                for i in range(len(group_items))
                for j in range(i + 1, len(group_items))
            ],
        })

        if is_consistent:
            continue

        priced = [gi for gi in group_items if gi.get('matched_ids')]
        ref_indices = [gi['index'] for gi in priced]
        ref_ids = sorted({mid for gi in priced for mid in gi.get('matched_ids', [])})

        parts = []
        if has_unpriced:
            seq = ",".join(str(x) for x in unpriced)
            parts.append(f'发现高度相似清单套价冲突：序号{seq}未套价')
        if not matched_consistent and len(non_empty) >= 2:
            diff = '；'.join(
                f"序号{group_items[i]['index']}=[{','.join(sorted(matched_sets[i]))}]"
                for i in range(len(group_items)) if matched_sets[i]
            )
            parts.append(f'子目不匹配: {diff}')
        if not conf_consistent and len(confidences) >= 2:
            parts.append('置信度差异过大')
        message = '；'.join(parts) if parts else '相似清单套价结果不一致'

        if has_unpriced and priced:
            seq = ",".join(str(x) for x in ref_indices)
            suggestion = f'建议参考序号{seq}结果'
            if ref_ids:
                suggestion += f"（推荐子目: {'+'.join(ref_ids)}）"
        elif not matched_consistent and priced:
            suggestion = '请人工确认正确子目组合'
        else:
            suggestion = '请人工复核'

        severity = 'high' if has_unpriced else ('medium' if not matched_consistent else 'low')
        auto_fix = None
        if has_unpriced and priced and ref_ids:
            auto_fix = {'from_index': ref_indices[0], 'sub_ids': ref_ids}

        warnings.append({
            'group_id': group_id, 'severity': severity, 'message': message,
            'suggestion': suggestion, 'unpriced_items': unpriced,
            'reference_items': ref_indices, 'auto_fix': auto_fix,
        })

    return {
        'similar_groups': similar_groups, 'warnings': warnings,
        'total_items': len(items), 'groups_found': len(similar_groups),
        'warnings_count': len(warnings),
    }


def build_check_items(candidates: dict, decisions: dict,
                      default_confidence: int = DEFAULT_CONFIDENCE) -> list[dict]:
    """candidates.json + decisions.json → CheckItem 列表。

    matched_ids 取 decisions 的 code 或 subs[].code 去重排序；无决策为空。
    **必须显式填 overall_confidence**：远端把缺省 0 视为「未套价」，
    不填会把正常套价行全部误判成 high。decisions 可选 confidence 覆盖。
    sheet / section 额外保留，供 --group-by 收窄比较域（不参与相似度计算）。
    """
    items = []
    for row in candidates.get('rows', []):
        rid = str(row['row_id'])
        d = decisions.get(rid) or {}
        if d.get('subs'):
            codes = [s.get('code', '') for s in d['subs'] if s.get('code')]
        elif d.get('code'):
            codes = [d['code']]
        else:
            codes = []

        conf = d.get('confidence', default_confidence)
        try:
            conf = int(conf)
        except (TypeError, ValueError):
            conf = default_confidence

        items.append({
            'index': row['row_id'],
            'name': row.get('name', '') or '',
            'spec': row.get('spec', '') or '',
            'unit': row.get('unit', '') or '',
            'sheet': row.get('sheet', '') or '',
            'section': row.get('section', '') or '',
            'qty': row.get('qty', 0),
            'matched_ids': sorted(set(codes)),
            'overall_confidence': conf,
        })
    return items


def check_consistency_by_domain(items: list[dict], group_by: str,
                                threshold: float = DEFAULT_THRESHOLD) -> dict:
    """WB 增强：按 sheet / section 切域，各域独立校验后合并并重编 group_id。"""
    domains: dict[str, list[dict]] = {}
    for it in items:
        domains.setdefault(str(it.get(group_by) or ''), []).append(it)

    merged = {
        'similar_groups': [], 'warnings': [], 'total_items': len(items),
        'groups_found': 0, 'warnings_count': 0,
    }
    offset = 0
    for subset in domains.values():
        r = check_consistency(subset, threshold)
        for g in r['similar_groups']:
            g = dict(g)
            g['group_id'] += offset
            merged['similar_groups'].append(g)
        for w in r['warnings']:
            w = dict(w)
            w['group_id'] += offset
            merged['warnings'].append(w)
        offset += r['groups_found']
    merged['groups_found'] = len(merged['similar_groups'])
    merged['warnings_count'] = len(merged['warnings'])
    return merged
