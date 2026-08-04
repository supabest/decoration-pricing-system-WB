"""相似清单一致性校验服务

在 AI 套价完成后，对所有已套价清单进行相似度计算和一致性校验。
检测同一工程中项目特征高度相似的清单是否得到了不同的套价结果。
"""
import re
from typing import Optional
from app.services.ai_pricing_service import engineering_parse


def _bigrams(text: str) -> set[str]:
    """对文本做 2-gram 分词，返回 set"""
    cleaned = re.sub(r'[（）()\-—\/\s，。、；：！？\d]+', '', text)
    result = set()
    for i in range(len(cleaned) - 1):
        bg = cleaned[i:i+2]
        result.add(bg)
    return result


def _jaccard(a: set, b: set) -> float:
    """Jaccard 相似系数"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _name_similarity(name_a: str, name_b: str) -> float:
    """清单名称相似度 (2-gram Jaccard)"""
    return _jaccard(_bigrams(name_a), _bigrams(name_b))


def _spec_similarity(spec_a: str, spec_b: str) -> float:
    """项目特征相似度 (2-gram Jaccard)"""
    return _jaccard(_bigrams(spec_a), _bigrams(spec_b))


def _engineering_similarity(eng_a: dict, eng_b: dict) -> float:
    """工程理解相似度：团队重叠 + 工艺重叠 + 材料匹配"""
    # 团队重叠率
    teams_a = set(eng_a.get('teams', []))
    teams_b = set(eng_b.get('teams', []))
    teams_overlap = _jaccard(teams_a, teams_b) if teams_a or teams_b else 1.0

    # 工艺关键词重叠率
    crafts_a = set(eng_a.get('crafts', []))
    crafts_b = set(eng_b.get('crafts', []))
    crafts_overlap = _jaccard(crafts_a, crafts_b) if crafts_a or crafts_b else 1.0

    # 材料类型匹配
    mats_a = set(eng_a.get('materials', []))
    mats_b = set(eng_b.get('materials', []))
    mats_match = _jaccard(mats_a, mats_b) if mats_a or mats_b else 1.0

    return (teams_overlap + crafts_overlap + mats_match) / 3.0


def _unit_similarity(unit_a: str, unit_b: str) -> float:
    """单位相似度：完全一致=1.0，否则=0.0"""
    return 1.0 if unit_a and unit_b and unit_a.strip() == unit_b.strip() else 0.0


def compute_similarity(item_a: dict, item_b: dict) -> float:
    """计算两条清单项目的综合相似度 (0.0~1.0)

    权重：
    - 清单名称: 20%
    - 项目特征: 50%
    - 工程理解: 20%
    - 单位: 10%
    """
    name_a, name_b = item_a.get('name', ''), item_b.get('name', '')
    spec_a, spec_b = item_a.get('spec', ''), item_b.get('spec', '')
    unit_a, unit_b = item_a.get('unit', ''), item_b.get('unit', '')

    # 工程理解
    eng_a = engineering_parse(name_a, spec_a)
    eng_b = engineering_parse(name_b, spec_b)

    sim = (
        0.20 * _name_similarity(name_a, name_b) +
        0.50 * _spec_similarity(spec_a, spec_b) +
        0.20 * _engineering_similarity(eng_a, eng_b) +
        0.10 * _unit_similarity(unit_a, unit_b)
    )
    return round(sim, 4)


def _find_similar_groups(items: list[dict], threshold: float = 0.90) -> list[list[int]]:
    """使用 Union-Find 对相似度 >= threshold 的项目分组"""
    n = len(items)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_similarity(items[i], items[j])
            if sim >= threshold:
                union(i, j)

    # 按根节点聚合
    groups_map: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        if root not in groups_map:
            groups_map[root] = []
        groups_map[root].append(i)

    # 只返回多于 1 个项目的组
    return [indices for indices in groups_map.values() if len(indices) > 1]


def check_consistency(items: list[dict]) -> dict:
    """对已套价清单进行一致性校验

    Args:
        items: 清单列表，每项含 index/name/spec/unit/matched_ids/overall_confidence

    Returns:
        {
            similar_groups: [...],
            warnings: [...],
            total_items: int,
            groups_found: int,
            warnings_count: int,
        }
    """
    if len(items) < 2:
        return {
            'similar_groups': [],
            'warnings': [],
            'total_items': len(items),
            'groups_found': 0,
            'warnings_count': 0,
        }

    groups = _find_similar_groups(items)

    similar_groups = []
    warnings = []
    group_id = 0

    for indices in groups:
        group_id += 1
        group_items = [items[i] for i in indices]

        # 收集组内子目集合
        all_matched_sets = []
        for gi in group_items:
            mids = gi.get('matched_ids', [])
            all_matched_sets.append(set(mids) if mids else set())

        # 检查组内一致性
        # 1. 子目编号是否一致
        non_empty_sets = [s for s in all_matched_sets if s]
        matched_consistent = True
        if len(non_empty_sets) >= 2:
            first = non_empty_sets[0]
            if not all(s == first for s in non_empty_sets[1:]):
                matched_consistent = False

        # 2. 是否存在未套价项目
        unpriced = [gi['index'] for gi in group_items
                    if not gi.get('matched_ids') or gi.get('overall_confidence', 0) == 0]
        has_unpriced = len(unpriced) > 0

        # 3. 置信度差异
        confidences = [gi.get('overall_confidence', 0) for gi in group_items
                       if gi.get('matched_ids')]
        conf_consistent = True
        if len(confidences) >= 2:
            if max(confidences) - min(confidences) > 20:
                conf_consistent = False

        is_consistent = matched_consistent and not has_unpriced and conf_consistent

        # 构建组内项目列表
        sim_items = []
        for gi in group_items:
            sim_items.append({
                'index': gi['index'],
                'name': gi.get('name', ''),
                'matched_ids': gi.get('matched_ids', []),
                'overall_confidence': gi.get('overall_confidence', 0),
            })

        # 计算组内相似度分数
        sim_scores = []
        for i in range(len(group_items)):
            for j in range(i + 1, len(group_items)):
                sim_scores.append(compute_similarity(group_items[i], group_items[j]))

        similar_groups.append({
            'group_id': group_id,
            'items': sim_items,
            'is_consistent': is_consistent,
            'similarity_scores': sim_scores,
        })

        # 生成警告
        if not is_consistent:
            # 找参考项（已套价的）
            priced = [gi for gi in group_items if gi.get('matched_ids')]
            ref_indices = [gi['index'] for gi in priced]

            warning_msg_parts = []
            if has_unpriced:
                names = [gi.get('name', '')[:20] for gi in group_items if gi['index'] in unpriced]
                warning_msg_parts.append(
                    f'发现高度相似清单套价冲突：'
                    f'序号{",".join(str(x) for x in unpriced)}未套价'
                )

            if not matched_consistent and len(non_empty_sets) >= 2:
                diff_desc = '；'.join(
                    f'序号{group_items[i]["index"]}=[{",".join(sorted(all_matched_sets[i]))}]'
                    for i in range(len(group_items)) if all_matched_sets[i]
                )
                warning_msg_parts.append(f'子目不匹配: {diff_desc}')

            if not conf_consistent and len(confidences) >= 2:
                warning_msg_parts.append('置信度差异过大')

            message = '；'.join(warning_msg_parts) if warning_msg_parts else '相似清单套价结果不一致'

            # 建议
            if has_unpriced and priced:
                ref_ids = sorted(set(
                    mid for gi in priced for mid in gi.get('matched_ids', [])
                ))
                suggestion = f'建议参考序号{",".join(str(x) for x in ref_indices)}结果'

                # 补充具体子目建议
                if ref_ids:
                    suggestion += f'（推荐子目: {"+".join(ref_ids)}）'
            elif not matched_consistent and priced:
                suggestion = '请人工确认正确子目组合'
            else:
                suggestion = '请人工复核'

            severity = 'high' if has_unpriced else ('medium' if not matched_consistent else 'low')

            # 自动修复：有参考项时，提供子目用于自动补全
            auto_fix = None
            if has_unpriced and priced:
                ref_ids = sorted(set(
                    mid for gi in priced for mid in gi.get('matched_ids', [])
                ))
                if ref_ids:
                    auto_fix = {
                        'from_index': ref_indices[0],
                        'sub_ids': ref_ids,
                    }

            warnings.append({
                'group_id': group_id,
                'severity': severity,
                'message': message,
                'suggestion': suggestion,
                'unpriced_items': unpriced,
                'reference_items': ref_indices,
                'auto_fix': auto_fix,
            })

    return {
        'similar_groups': similar_groups,
        'warnings': warnings,
        'total_items': len(items),
        'groups_found': len(similar_groups),
        'warnings_count': len(warnings),
    }
