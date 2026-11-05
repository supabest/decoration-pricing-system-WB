"""候选召回 —— 从后端 ai_pricing_service.py 移植的确定性规则

纯规则、零 token：先按班组收窄，再按 2-gram 与工艺词打分排序。
与后端口径保持一致；任何改动都必须同步 backend/app/services/ai_pricing_service.py。
"""
from __future__ import annotations

import re

# ── 班组路由关键词（与后端逐字一致）──
TEAM_KEYWORDS = [
    (['泥水', '瓷砖', '石材', '地面', '墙面', '铺贴', '找平', '砂浆', '陶粒', '回填', '自流平', '勾缝',
      '门槛', '波打线', '拼花', '踢脚', '防水', '堵漏', '止水', '防潮', '卷材', '涂膜', '背胶', '挂贴', '大板'],
     ['泥水班组']),
    (['木工', '木饰面', '柜', '门套', '窗套', '龙骨', '石膏板', '硅钙板', '天花', '吊顶', '间墙', '隔墙',
      '夹板', '灯槽', '木线', '踢脚线', '轻钢', '硬包', '软包', '饰面板', '挂板'],
     ['木工班组']),
    (['油漆', '涂料', '乳胶漆', '批灰', '扇灰', '刮腻子', '腻子', '刷漆', '喷漆', '木器漆', '防锈',
      '墙纸', '壁纸', '墙布', '无机涂料', '满刮'],
     ['油漆班组']),
    (['铁', '钢', '焊接', '铁件', '预埋', '钢架', '钢板', '角铁', '槽钢', '金属压条', '金属装饰线', '不锈钢'],
     ['铁工班组']),
    (['玻璃', '镜', '夹胶', '钢化', '玻璃砖', '镜面'], ['玻璃班组']),
    (['拆除', '拆卸', '凿除', '打拆', '移除', '脚手架', '开荒', '保洁', '成品保护'], ['其他班组']),
    (['幕墙', '铝板', '铝单板', '铝格栅', '蜂窝', '干挂', '石材幕墙', '玻璃幕墙', '外墙'], ['幕墙班组']),
    (['水管', '电线', '电缆', '桥架', '线槽', '开关', '插座', '灯具', '消防', '喷淋', '空调', '风管',
      '排水', '给水', '强电', '弱电', '机电', '水电'], ['机电班组']),
]

CRAFT_KEYWORDS = ['找平', '铺贴', '刮腻子', '扇灰', '批灰', '涂料', '背胶', '挂贴', '龙骨', '石膏板',
                  '夹板', '硬包', '软包', '墙布', '墙纸', '踢脚线', '防水', '填缝', '卡扣', '抹灰',
                  '砌筑', '干挂', '湿挂']

MATERIAL_KEYWORDS = {
    '瓷砖': ['瓷砖', '大板砖', '防滑砖', '木纹砖', '瓷片', '玻化砖', '釉面砖', '通体砖'],
    '石材': ['石材', '大理石', '花岗岩', '人造石', '门槛石', '窗台石', '挡水条', '波打线'],
    '涂料': ['涂料', '乳胶漆', '无机涂料', '防潮涂料', '油漆', '真石漆'],
    '木地板': ['木地板', '复合地板', '实木地板', '竹地板', '强化地板'],
    '墙纸墙布': ['墙纸', '墙布', '壁纸', '壁布', '裱贴'],
    '吊顶': ['吊顶', '天棚', '天花', '石膏板', '蜂窝铝板', '铝扣板', '矿棉板'],
    '金属': ['不锈钢', '铝合金', '金属踢脚线', '金属装饰线', '金属门窗套'],
    '木制品': ['木饰面', '硬包', '软包', '窗帘盒', '木线', '踢脚线'],
    '防水': ['防水', '堵漏', '止水', 'JS防水', '聚氨酯'],
    '脚手架': ['脚手架', '活动脚手架'],
    '玻璃': ['玻璃', '镜面', '钢化玻璃', '夹胶玻璃'],
    '其他': [],
}

_UNIT_ALIASES = {
    '㎡': 'm2', 'm²': 'm2', 'm2': 'm2', 'M2': 'm2', '平方米': 'm2', '平米': 'm2',
    'm': 'm', 'M': 'm', '米': 'm',
    'm3': 'm3', 'm³': 'm3', '立方米': 'm3',
}


def normalize_unit(raw) -> str:
    u = (raw or '').strip()
    return _UNIT_ALIASES.get(u, u)


def route_teams(name: str, spec: str) -> list[str]:
    txt = ((name or '') + ' ' + (spec or '')).lower()
    matched: set[str] = set()
    for keywords, teams in TEAM_KEYWORDS:
        if any(k in txt for k in keywords):
            matched.update(teams)
    return list(matched)


def engineering_parse(name: str, spec: str) -> dict:
    spec_lower = (spec or '').lower()
    crafts = [w for w in CRAFT_KEYWORDS if w in spec_lower]
    full_text = ((name or '') + ' ' + (spec or '')).lower()
    materials = [mat for mat, kws in MATERIAL_KEYWORDS.items() if any(k in full_text for k in kws)]
    return {'teams': route_teams(name, spec), 'crafts': crafts, 'materials': materials}


# 清单特征里的表格标签与通用填充词 —— 它们不是语义，参与 2-gram 会把噪声条目顶上来
# （例：「1.名称:镀锌线槽；2.规格型号:100*100；3.安装方式:综合考虑」里的「名称/规格型号/安装方式」）
_LABEL_RE = re.compile(r'\d+\s*[.、．]\s*')
_NOISE_WORDS = (
    '工作内容', '规格型号', '安装方式', '敷设方式', '材料种类', '面层材料品种', '连接形式',
    '综合考虑', '未尽事宜', '其他一切', '名称', '规格', '型号', '安装', '敷设', '方式',
    '完成', '一切', '其他', '包含', '以及',
)


def clean_text(raw) -> str:
    """剥掉编号与表格标签，只留语义。"""
    s = _LABEL_RE.sub(' ', str(raw or ''))
    for w in _NOISE_WORDS:
        s = s.replace(w, ' ')
    return re.sub(r'\s+', ' ', s).strip()


def query_terms(name: str, spec: str) -> tuple[list[str], list[str]]:
    """清单文本 → (2-gram + ≥3 字词, 命中的工艺关键词)"""
    full_text = re.sub(r'[（）()\-—\/\s]+', ' ', clean_text(name) + ' ' + clean_text(spec))
    words = []
    for i in range(len(full_text) - 1):
        bigram = full_text[i:i + 2]
        if not re.search(r'[，。、；：！？\s\d]', bigram):
            words.append(bigram)
    words.extend(w for w in full_text.split() if len(w) >= 3)
    spec_keywords = [w for w in CRAFT_KEYWORDS if w in clean_text(spec).lower()]
    return list(set(words)), spec_keywords


def rank_items(cands: list[dict], uniq_words: list[str], spec_keywords: list[str],
               unit: str, name_key: str = 'item_name', spec_key: str = 'spec') -> list[tuple[dict, int]]:
    """文本命中打分：名称含词 +2 / 特征含词 +1 / 名称含二字词 +1 / 单位一致 +3 / 工艺词命中名称 +4"""
    target_unit = normalize_unit(unit)
    scored: list[tuple[dict, int]] = []
    for it in cands:
        score = 0
        it_name = it.get(name_key, '') or ''
        it_spec = it.get(spec_key, '') or ''
        for w in uniq_words:
            if w in it_name:
                score += 2
            if w in it_spec:
                score += 1
        if any(len(w) == 2 and w in it_name for w in uniq_words):
            score += 1
        if target_unit and normalize_unit(it.get('unit')) == target_unit:
            score += 3
        for w in spec_keywords:
            if w in it_name:
                score += 4
        scored.append((it, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def build_candidates(name: str, spec: str, unit: str, benchmark_items: list[dict],
                     limit: int = 80) -> list[dict]:
    teams = route_teams(name, spec)
    if len(teams) <= 2:
        # 班组命中的太少说明路由不确定，放开全库，避免误杀
        teams = list({d['trade_team'] for d in benchmark_items})

    pool = [d for d in benchmark_items if d.get('trade_team') in teams]
    uniq_words, spec_keywords = query_terms(name, spec)
    ranked = rank_items(pool, uniq_words, spec_keywords, unit)
    return [it for it, _ in ranked[:limit]]


def identify(item: dict) -> tuple[str, str]:
    """候选的唯一标识 —— 编号在不同班组间重复，必须带上班组。"""
    return (item.get('internal_code', ''), item.get('trade_team', ''))
