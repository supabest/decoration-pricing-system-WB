"""AI 套价服务 — 与 tool.html 逻辑完全一致的 Python 实现"""
import re, json, asyncio, httpx
from typing import List, Optional
from app.core.config import settings
from app.services.pricing_debug_logger import PricingDebugLog, save_debug_log

# ── 班组路由关键词 ──
TEAM_KEYWORDS = [
    (['泥水','瓷砖','石材','地面','墙面','铺贴','找平','砂浆','陶粒','回填','自流平','勾缝','门槛','波打线','拼花','踢脚','防水','堵漏','止水','防潮','卷材','涂膜','背胶','挂贴','大板'], ['泥水班组']),
    (['木工','木饰面','柜','门套','窗套','龙骨','石膏板','硅钙板','天花','吊顶','间墙','隔墙','夹板','灯槽','木线','踢脚线','轻钢','硬包','软包','饰面板','挂板'], ['木工班组']),
    (['油漆','涂料','乳胶漆','批灰','扇灰','刮腻子','腻子','刷漆','喷漆','木器漆','防锈','墙纸','壁纸','墙布','无机涂料','满刮'], ['油漆班组']),
    (['铁','钢','焊接','铁件','预埋','钢架','钢板','角铁','槽钢','金属压条','金属装饰线','不锈钢'], ['铁工班组']),
    (['玻璃','镜','夹胶','钢化','玻璃砖','镜面'], ['玻璃班组']),
    (['拆除','拆卸','凿除','打拆','移除','脚手架','开荒','保洁','成品保护'], ['其他班组']),
    (['幕墙','铝板','铝单板','铝格栅','蜂窝','干挂','石材幕墙','玻璃幕墙','外墙'], ['幕墙班组']),
    (['水管','电线','电缆','桥架','线槽','开关','插座','灯具','消防','喷淋','空调','风管','排水','给水','强电','弱电','机电','水电'], ['机电班组']),
]

CRAFT_KEYWORDS = ['找平','铺贴','刮腻子','扇灰','批灰','涂料','背胶','挂贴','龙骨','石膏板','夹板','硬包','软包','墙布','墙纸','踢脚线','防水','填缝','卡扣','抹灰','砌筑','干挂','湿挂']

# ── 材料类型关键词 ──
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

# ── 集团口径（mode='group'）专属关键词表 ──
# discipline 只作加分项不作硬过滤（与内部班组路由的关键差异）：ZS02 仅 A/B/C/D 四类，
# 内部那条「命中 ≤2 就放开全库」的规则在这里等于不过滤，反而会让措辞含糊的清单丢掉
# 正确候选。296 条库靠 2-gram 打分 + top80 截断收窄已足够，discipline 命中 +2 分。
DISCIPLINE_KEYWORDS = {
    'C': ['拆除', '拆卸', '凿除', '打拆', '破除', '移除', '清运', '垃圾', '开荒', '剔凿'],
    'D': ['脚手架', '成品保护', '保护', '垂直运输', '二次搬运', '安全', '防护', '围挡', '临时'],
    'B': ['给水', '排水', '排污', '水管', '管道', '电线', '电缆', '线路', '布线', '桥架', '线槽',
          '开关', '插座', '灯具', '照明', '配电', '弱电', '强电', '空调', '通风', '消防', '喷淋', '风口'],
    'A': ['瓷砖', '石材', '地板', '涂料', '乳胶漆', '吊顶', '天棚', '天花', '龙骨', '石膏板',
          '饰面', '门', '窗', '踢脚', '防水', '找平', '墙面', '地面', '木饰面', '墙纸', '墙布'],
}

# 部位词 → ZS02 section_name 常见写法（section_name 拼进被匹配文本后由 2-gram 自然吃到，
# 这里只用于日志与「地面/墙面不互串」的可解释性）
PART_KEYWORDS = ['地面', '楼面', '墙面', '墙身', '天棚', '天花', '吊顶', '楼梯', '踢脚', '门窗', '柜']

def engineering_parse(name: str, spec: str) -> dict:
    """提取工程语义：班组归属 + 工艺关键词 + 材料类型"""
    # 班组
    teams = route_teams(name, spec)

    # 工艺关键词
    spec_lower = spec.lower()
    crafts = [w for w in CRAFT_KEYWORDS if w in spec_lower]

    # 材料类型
    full_text = (name + ' ' + spec).lower()
    materials = []
    for mat_type, keywords in MATERIAL_KEYWORDS.items():
        if any(k in full_text for k in keywords):
            materials.append(mat_type)

    return {
        'teams': teams,
        'crafts': crafts,
        'materials': materials,
    }

# ── 加载基准价数据 ──
_benchmark_cache = None
_group_benchmark_cache = None
_knowledge_cache = None


async def load_benchmark_data() -> list[dict]:
    """加载全量基准价：先 Supabase，RLS 拦截时从本地 JSON 备用"""
    global _benchmark_cache
    if _benchmark_cache:
        return _benchmark_cache
    items = []
    # 尝试 Supabase
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/benchmark_items?select=*&order=trade_team.asc",
                headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"}
            )
            items = r.json() if r.status_code == 200 else []
    except Exception:
        pass
    # Supabase 返回空（RLS）→ 加载本地 JSON
    if not items:
        import json, os
        json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'benchmark_data.json')
        try:
            with open(json_path) as f:
                raw = json.load(f)
            items = [{
                'trade_team': d['trade_team'], 'internal_code': d['internal_code'],
                'work_type': d.get('work_type', ''), 'item_name': d['item_name'],
                'spec': d.get('spec', ''), 'unit': d['unit'],
                'unit_price': d['unit_price'], 'remark': d.get('remark', ''),
                'aux_rule_type': d.get('aux_rule_type', ''), 'aux_fixed_k': d.get('aux_fixed_k', 0),
                'aux_rate_detail': d.get('aux_rate_detail'),
            } for d in raw]
        except Exception:
            pass
    _benchmark_cache = items
    return items


# ── 集团基准价库（mode='group' 候选池）──
# 无本地 JSON 兜底：对甲口径的数据只有 group_benchmark_items 一个权威源，
# 静默降级到 benchmark_data.json（内部 497 条）会把错误口径的价送到对甲报价里。
# 拉不到就回空列表，由 price_single 显式报「集团基准价库不可用」。
async def load_group_benchmark_data() -> list[dict]:
    """加载全量集团基准价（ZS02）：仅 Supabase，失败回空列表"""
    global _group_benchmark_cache
    if _group_benchmark_cache:
        return _group_benchmark_cache
    items = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/group_benchmark_items?select=*&order=code.asc",
                headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"}
            )
            items = r.json() if r.status_code == 200 else []
    except Exception:
        pass
    if not isinstance(items, list):
        items = []
    # 预拼被匹配文本：spec + section_name（「楼地面工程/墙柱面工程」这类分部名是 ZS02 区分
    # 地面/墙面同种面层的关键信号，仅看 spec 会把它们规约成同一候选）
    for d in items:
        d['_group_text'] = ((d.get('spec') or '') + ' ' + (d.get('section_name') or '')).strip()
    _group_benchmark_cache = items
    return items


async def load_knowledge() -> dict:
    """加载 AI 知识库：先 Supabase，RLS 时本地 JSON 备用"""
    global _knowledge_cache
    if _knowledge_cache:
        return _knowledge_cache
    rows = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/ai_knowledge?select=*",
                headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"}
            )
            rows = r.json() if r.status_code == 200 else []
    except Exception:
        pass
    if not rows:
        import json, os
        json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'ai_knowledge_base.json')
        try:
            with open(json_path) as f:
                kb = json.load(f)
            cats = {'tips': '技巧', 'synonyms': '同义词', 'rules': '规则'}
            for key, label in cats.items():
                for item in kb.get(key, []):
                    rows.append({'category': label, 'keyword': item.get('keyword', ''), 'content': item.get('content', ''), 'team': item.get('team', '')})
        except Exception:
            pass
    tips = [r for r in rows if '技巧' in (r.get('category') or '')]
    synonyms = [r for r in rows if '同义词' in (r.get('category') or '')]
    rules = [r for r in rows if '规则' in (r.get('category') or '')]
    _knowledge_cache = {"tips": tips, "synonyms": synonyms, "rules": rules}
    return _knowledge_cache


# ── 班组路由 ──
def route_teams(name: str, spec: str) -> list[str]:
    txt = (name + ' ' + spec).lower()
    matched = set()
    for keywords, teams in TEAM_KEYWORDS:
        if any(k in txt for k in keywords):
            matched.update(teams)
    return list(matched) if matched else []


# ── 候选筛选（对内/集团共用打分骨架）──
def _query_terms(name: str, spec: str) -> tuple[list[str], list[str]]:
    """清单文本 → (2-gram + ≥3 字词, 命中的工艺关键词)。对内/集团同一套切词口径。"""
    full_text = re.sub(r'[（）()\-—\/\s]+', ' ', name + ' ' + spec)
    words = []
    for i in range(len(full_text) - 1):
        bigram = full_text[i:i+2]
        if not re.search(r'[，。、；：！？\s\d]', bigram):
            words.append(bigram)
    words.extend(w for w in full_text.split() if len(w) >= 3)
    spec_keywords = [w for w in CRAFT_KEYWORDS if w in spec.lower()]
    return list(set(words)), spec_keywords


def _rank_items(cands: list[dict], uniq_words: list[str], spec_keywords: list[str],
                unit: str, name_key: str = 'item_name', spec_key: str = 'spec') -> list[tuple[dict, int]]:
    """文本命中打分：名称含词 +2 / 特征含词 +1 / 名称含二字词 +1 / 单位一致 +3 / 工艺词命中名称 +4。

    返回 (行, 分数) 降序列表，并列分保持库内原序（sort 稳定），截断交给调用方。
    name_key / spec_key 使两个口径的字段名差异止步于参数，打分逻辑不再各写一份。
    """
    scored = []
    for it in cands:
        score = 0
        it_name = it.get(name_key, '')
        it_spec = it.get(spec_key, '')
        for w in uniq_words:
            if w in it_name: score += 2
            if w in it_spec: score += 1
        if any(len(w) == 2 and w in it_name for w in uniq_words):
            score += 1
        if unit and it.get('unit') == unit:
            score += 3
        for w in spec_keywords:
            if w in it_name: score += 4
        scored.append((it, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def build_candidates(name: str, spec: str, unit: str, benchmark_items: list[dict]) -> list[dict]:
    teams = route_teams(name, spec)
    if len(teams) <= 2:
        teams = list(set(d['trade_team'] for d in benchmark_items))

    all_cands = [d for d in benchmark_items if d.get('trade_team') in teams]

    uniq_words, spec_keywords = _query_terms(name, spec)
    return [it for it, _ in _rank_items(all_cands, uniq_words, spec_keywords, unit)[:80]]


def route_disciplines(name: str, spec: str) -> list[str]:
    """清单文本 → ZS02 discipline（A精装/B水电/C拆除/D措施），可多命中。"""
    txt = (name + ' ' + spec).lower()
    return [d for d, kws in DISCIPLINE_KEYWORDS.items() if any(k in txt for k in kws)]


def build_group_candidates(name: str, spec: str, unit: str, group_items: list[dict]) -> list[dict]:
    """集团候选：与对内共用 2-gram 打分（字段名换成 name / _group_text=spec+section_name），
    discipline 命中 +2 作软提示而不硬过滤；top80 截断，与对内同宽度。"""
    uniq_words, spec_keywords = _query_terms(name, spec)
    ranked = _rank_items(group_items, uniq_words, spec_keywords, unit,
                         name_key='name', spec_key='_group_text')
    wanted = set(route_disciplines(name, spec))
    adjusted = [(it, sc + (2 if it.get('discipline') in wanted else 0)) for it, sc in ranked]
    adjusted.sort(key=lambda x: x[1], reverse=True)
    return [it for it, _ in adjusted[:80]]


# ── Prompt 构建 ──
def build_system_prompt(knowledge: dict) -> str:
    tips = '\n'.join(f"【技巧】{t['keyword']}：{t['content']}{'（'+t['team']+'）' if t.get('team') else ''}" for t in knowledge.get('tips', []))
    syns = '\n'.join(f"【同义词】{s['keyword']} → {s['content']}{'（'+s['team']+'）' if s.get('team') else ''}" for s in knowledge.get('synonyms', []))
    rules = '\n'.join(f"【规则】{r['keyword']}：{r['content']}{'（'+r['team']+'）' if r.get('team') else ''}" for r in knowledge.get('rules', []))

    return f"""你是精装修工程造价专家，负责将清单项目与企业基准价定额子目精确匹配。

## 当前知识库（必须遵守）
{tips}
{syns}
{rules}

## 工序拆解原则
仔细分析【项目特征】中的每条描述，识别所有独立工序：
1. 找平/结合层/水泥砂浆 → 找平子目
2. 龙骨/石膏板 → 吊顶基层
3. 刮腻子 → 涂料子目已含刮腻子（不套YQ-05水泥膏。水泥膏≠刮腻子）
4. 涂料/乳胶漆 → YQ-02（墙）/ YQ-07（天棚），已含刮腻子
5. 背胶 → NS-029
6. 铺贴/粘贴 → 面层铺贴子目
7. 卡扣金属踢脚线 → TG-08一道工序
8. 吊顶天棚 → YQ-025 + YQ-07（2工序，不套YQ-05）

## 班组归属
- 硬包/软包/轻钢龙骨/石膏板/夹板 → 木工班组
- 墙纸/墙布裱贴/扇灰/乳胶漆/涂料 → 油漆班组
- 找平/铺贴/瓷砖/背胶/防水 → 泥水班组
- 钢架/铁件/金属装饰线 → 铁工班组
- 涂料子目已含刮腻子+底漆+面漆全部工序，不单独套水泥膏YQ-05

严格规则：
1. 不限制子目数量，按实际工序匹配
2. 禁止同时选同类型的多个规格子目（如YQ-025和YQ-026）
3. 置信度85+精确匹配，60-84可接受，<60不采用
4. 找不到合适子目返回空matched
5. 只返回JSON，不含其他文字"""


def build_user_prompt(name: str, spec: str, unit: str, candidates: list[dict]) -> str:
    cand_strs = []
    for c in candidates:
        code = c.get('internal_code', '')
        cname = c.get('item_name', '')
        cspec = (c.get('spec') or '')[:120]
        cunit = c.get('unit', '')
        team = c.get('trade_team', '')
        cand_strs.append(f"{code}|{cname}|{cspec}|{cunit}|{team}")

    return f"""清单项目：
【名称】{name}
【特征】{spec or '（无）'}
【单位】{unit or '（未知）'}

候选子目（格式：编号|名称|特征|单位|班组）：
{chr(10).join(cand_strs)}

返回JSON格式：
{{"matched":[{{"id":"子目编号","sheet":"班组名称","confidence":85,"reason":"理由"}}],"overall_confidence":85,"note":"备注"}}"""


# ── 集团口径 Prompt（mode='group'）──
# 与内部版的根本差异：内部版写死了 YQ-02/NS-029/TG-08 这类内部编号与班组归属，
# 直接沿用会让模型把内部码当候选输出（已拦：校验按 group 库过滤），且「辅材配方」
# 在集团口径里根本不存在（子目自带 A/C/D/E 分解）。知识库里的 synonyms 仍有用
# （扇灰→刮腻子这类名称翻译），故保留注入但注明「不得作为输出编号」。
def build_group_system_prompt(knowledge: dict) -> str:
    tips = '\n'.join(f"【技巧】{t['keyword']}：{t['content']}" for t in knowledge.get('tips', []))
    syns = '\n'.join(f"【同义词】{s['keyword']} → {s['content']}" for s in knowledge.get('synonyms', []))
    return f"""你是精装修工程造价专家，负责把清单项目匹配到**集团精装修基准价子目（ZS02 编码）**。

## 目标库（只能从这里选）
候选来自集团基准价表，编号形如 ZS02-A-009，前缀字母含义：
- A 精装：装饰面层、基层/找平、龙骨罩面、门窗、踢脚、防水等实体工序
- B 水电：给排水、电气、暖通、消防、弱电
- C 拆除：打拆、凿除、清运、开荒
- D 措施：脚手架、成品保护、垂直运输等措施性费用

## 名称翻译与通用技巧（仅供理解清单措辞，其中出现的内部编号禁止当作输出）
{syns}
{tips}

## 工序拆解原则
1. 面层与找平/结合层是两道工序 → 分别挂对应子目
2. 龙骨与石膏板/饰面板是两道工序（基层 + 面层）
3. 涂料类子目已含刮腻子；清单写「扇灰/批灰」按刮腻子理解，不另外找子目
4. 拆除类一律走 C，不得用 A 子目代替
5. 脚手架/成品保护等只在清单单列措施项时才匹配 D
6. 地面与墙面同种面层是不同子目（看分部名 楼地面/墙柱面），不可互串
7. 单位不一致（清单 m2 / 子目 m 等）仍可匹配，但要在 reason 里说明需设换算系数

严格规则：
1. matched[].id 只能是候选里出现过的 ZS02 编号，禁止编造或输出内部编号
2. 不限制子目数量，按实际工序匹配
3. 名称含「每增减」「每增加」的增减子目，仅在清单明确写了增减尺寸时才选；基础子目与增减子目不得同时选
4. 置信度 85+ 精确匹配，60-84 可接受，<60 不采用
5. 找不到合适子目返回空 matched
6. 不估价、不填主材价格（主材价由用户询价录入），note 里也不得给出金额
7. 只返回 JSON，不含其他文字"""


def build_group_user_prompt(name: str, spec: str, unit: str, candidates: list[dict]) -> str:
    cand_strs = []
    for c in candidates:
        cand_strs.append('|'.join([
            str(c.get('code', '')),
            str(c.get('name', '')),
            (c.get('spec') or '')[:120],
            str(c.get('unit', '')),
            str(c.get('section_name', '')),
        ]))
    return f"""清单项目：
【名称】{name}
【特征】{spec or '（无）'}
【单位】{unit or '（未知）'}

候选子目（格式：编号|名称|特征|单位|分部）：
{chr(10).join(cand_strs)}

返回JSON格式：
{{"matched":[{{"id":"ZS02-X-NNN","confidence":85,"reason":"理由"}}],"overall_confidence":85,"note":"备注"}}"""


# ── DeepSeek 调用 ──
def _resolve_base_url(use_model: Optional[str]) -> str:
    """按 model 前缀路由 LLM 端点：glm* → 智谱，其余 → DeepSeek"""
    if use_model and use_model.lower().startswith('glm'):
        return settings.LLM_BASE_URL_ZHIPU.rstrip('/')
    return settings.LLM_BASE_URL.rstrip('/')


# 限流/瞬时错误重试：前端并发已提至 6，编码套餐/低限额 key 仍可能触发智谱 1302，
# 指数退避重试让请求从容排队（总等待 ≤29s，远小于单次 180s 超时预算）
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_RETRY_BACKOFF_SECONDS = [2, 4, 8, 15]


def _llm_candidates(use_model: str) -> List[str]:
    """按 model 返回候选端点（依序尝试）：glm → 智谱按量计费端点 + Coding Plan 套餐备端点，其余 → DeepSeek。

    两类智谱 key 计费端点不同：普通 key 只在 paas 端点有钱，套餐 key 只在
    coding 端点有额度。先试主端点（按量），鉴权/余额类错误时由 call_deepseek 换备端点。
    """
    if use_model.lower().startswith('glm'):
        urls = [settings.LLM_BASE_URL_ZHIPU.rstrip('/')]
        fb = (settings.LLM_BASE_URL_ZHIPU_FALLBACK or '').rstrip('/')
        if fb and fb not in urls:
            urls.append(fb)
        return urls
    return [settings.LLM_BASE_URL.rstrip('/')]


def _is_endpoint_mismatch(status_code: int, body: str) -> bool:
    """鉴权/余额类错误 → 大概率 key 类型与端点不匹配，值得换端点重试"""
    if status_code in (401, 402, 403):
        return True
    return '1113' in body   # 智谱「余额不足或无可用资源包」


async def call_deepseek(system_prompt: str, user_prompt: str, api_key: str,
                        model: Optional[str] = None) -> str:
    use_model = model or settings.LLM_MODEL
    payload = {
        "model": use_model,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "temperature": 0,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    candidates = _llm_candidates(use_model)
    last_err: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        for ci, base in enumerate(candidates):
            url = base + '/chat/completions'
            for attempt in range(len(_RETRY_BACKOFF_SECONDS) + 1):
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    msg = (data.get("choices") or [{}])[0].get("message") or {}
                    # deepseek-v4-pro 是推理模型：答案可能落在 content 或 reasoning_content
                    content = (msg.get("content") or "").strip()
                    if not content:
                        content = (msg.get("reasoning_content") or "").strip()
                    return content
                body = r.text[:200]
                mismatch = _is_endpoint_mismatch(r.status_code, body)
                # 限流(1302 等)退避重试；计费/鉴权类(1113/401/402/403)等待无意义，立即换端点。
                # 注意智谱的 1113 余额不足也返回 HTTP 429，不能只看状态码
                if r.status_code in _RETRYABLE_STATUS and not mismatch and attempt < len(_RETRY_BACKOFF_SECONDS):
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                if mismatch and ci < len(candidates) - 1:
                    last_err = Exception(f"LLM error {r.status_code}: {body}")
                    break   # 换备端点
                raise Exception(f"LLM error {r.status_code}: {body}")
    raise last_err or Exception("LLM error: all endpoints exhausted")


def parse_ai_response(raw: str) -> Optional[dict]:
    """解析 AI 返回的 JSON，兼容代码块、前后杂质、以及被截断的 JSON。"""
    if not raw or not str(raw).strip():
        return None
    text = re.sub(r'```json|```', '', str(raw)).strip()
    # 1) 直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) 提取第一个完整 JSON 对象（兼容前后杂质）
    obj = _extract_balanced_json(text)
    if obj is not None:
        return obj
    # 3) 截断修复：闭合未闭合的字符串和括号
    return _repair_truncated_json(text)


def _extract_balanced_json(text: str) -> Optional[dict]:
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
    return None


def _repair_truncated_json(text: str) -> Optional[dict]:
    start = text.find('{')
    if start == -1:
        return None
    out = []
    stack = []
    in_str = False
    esc = False
    for c in text[start:]:
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
                out.append(c)
            elif c in '{[':
                stack.append(c)
                out.append(c)
            elif c in '}]':
                if stack:
                    top = stack[-1]
                    if (top == '{' and c == '}') or (top == '[' and c == ']'):
                        stack.pop()
                out.append(c)
            else:
                out.append(c)
    if in_str:
        out.append('"')  # 闭合被截断的字符串
    for open_ch in reversed(stack):  # 闭合未闭合的括号
        out.append('}' if open_ch == '{' else ']')
    try:
        return json.loads(''.join(out))
    except Exception:
        return None


# ── 单行套价 ──
def _group_pending_mats(row: dict) -> list[str]:
    """该集团子目里价格仍为 NULL 的主材名（待询价）。

    null≠0 是集团端全局判据：price=0（甲供按 0 计）合法，只有 None 才算未定价。
    只回名称不回金额——AI 不代填价。
    """
    out = []
    for m in (row.get('mats') or []):
        if isinstance(m, dict) and m.get('price') is None and m.get('name'):
            out.append(str(m['name']))
    return out


def _validate_group_matches(matched: list, group_rows: list[dict]) -> list[dict]:
    """按集团库校验 AI 返回的编号；未知编号、编造的内部编号都在这一层被剔掉。

    sheet 由服务端按库内 discipline 填 'ZS02-<discipline>'，与前端 addGroupSub 的 bsh 同形，
    使两个口径的响应体共用同一个 MatchedSubItem 契约（前端无需区分字段集）。
    """
    by_code = {str(d.get('code') or '').upper(): d for d in group_rows if d.get('code')}
    valid, seen = [], set()
    for m in matched:
        if not isinstance(m, dict):
            continue
        raw = str(m.get('id') or m.get('code') or '').strip().upper()
        row = by_code.get(raw)
        if not row or raw in seen:
            continue
        seen.add(raw)
        item = dict(m)
        item['id'] = row.get('code')
        item['sheet'] = 'ZS02-' + str(row.get('discipline') or '')
        pend = _group_pending_mats(row)
        if pend:
            item['pending_mats'] = pend
        valid.append(item)
    return valid


async def price_single(name: str, spec: str, unit: str, api_key: str,
                       model: Optional[str] = None, debug_log=None,
                       mode: str = 'internal') -> dict:
    """单行套价。mode='internal'（默认，向后兼容）走内部 497 条基准价；'group' 走 ZS02 集团库。"""
    is_group = (mode == 'group')
    # 两个口径的候选池互斥加载：集团模式不拉内部库（反之亦然），避开无意义的 497 条流量
    benchmark = [] if is_group else await load_benchmark_data()
    group_rows = await load_group_benchmark_data() if is_group else []
    knowledge = await load_knowledge()

    # 🔍 调试日志
    if debug_log is None:
        from app.services.pricing_debug_logger import PricingDebugLog
        debug_log = PricingDebugLog(name, spec, unit, api_key)

    # 1~2. 路由 + 候选筛选（内部=班组过滤，集团=2-gram 打分 + discipline 加分）
    if is_group:
        disciplines = route_disciplines(name, spec)
        debug_log.log_route(disciplines)
        candidates = build_group_candidates(name, spec, unit, group_rows)
    else:
        teams = route_teams(name, spec)
        debug_log.log_route(teams)
        candidates = build_candidates(name, spec, unit, benchmark)
    debug_log.log_candidates(candidates, len(candidates))
    if not candidates:
        empty_note = "集团基准价库不可用（group_benchmark_items 无数据）" if is_group else "无候选子目"
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": empty_note})
        await save_debug_log(debug_log)
        return {"matched": [], "overall_confidence": 0, "note": empty_note}

    # 3. 工程理解（班组归属属内部口径，集团只留工艺/材料类型）
    eng = engineering_parse(name, spec)
    debug_log.log_engineering(
        {'disciplines': disciplines, 'crafts': eng['crafts'], 'materials': eng['materials']}
        if is_group else eng)

    # 4. Prompt 构建
    sys_prompt = build_group_system_prompt(knowledge) if is_group else build_system_prompt(knowledge)
    user_prompt = (build_group_user_prompt(name, spec, unit, candidates) if is_group
                   else build_user_prompt(name, spec, unit, candidates))
    debug_log.log_prompt(sys_prompt, user_prompt)

    # 5. DeepSeek 调用
    try:
        raw = await call_deepseek(sys_prompt, user_prompt, api_key, model=model)
        result = parse_ai_response(raw)
        debug_log.log_response(raw, result)
    except Exception as e:
        err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        debug_log.log_error(err_msg)
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": err_msg[:100]})
        await save_debug_log(debug_log)
        raise

    if not result:
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": f"AI返回解析失败: {raw[:100]}"})
        await save_debug_log(debug_log)
        return {"matched": [], "overall_confidence": 0, "note": f"AI返回解析失败: {raw[:100]}"}

    # 6. 校验返回的子目真实存在（内部按 编号+班组 双键，集团按 ZS02 编号）
    if is_group:
        valid = _validate_group_matches(result.get('matched', []), group_rows)
    else:
        valid = []
        for m in result.get('matched', []):
            bid, bsh = m.get('id', ''), m.get('sheet', '')
            found = any(
                d.get('internal_code') == bid and d.get('trade_team') == bsh
                for d in benchmark
            )
            if found:
                valid.append(m)

    result['matched'] = valid
    if not valid:
        result['overall_confidence'] = 0

    # 7. 最终结果
    debug_log.log_final(result)
    await save_debug_log(debug_log)
    return result


# ── 批量套价 ──
async def price_batch(items: list[dict], api_key: str, model: Optional[str] = None,
                      mode: str = 'internal') -> list[dict]:
    results = []
    for item in items:
        try:
            r = await price_single(item['name'], item.get('spec', ''), item.get('unit', ''),
                                   api_key, model=model, mode=mode)
            results.append({**item, **r})
        except Exception as e:
            results.append({**item, "matched": [], "overall_confidence": 0, "note": str(e)[:100]})
    return results
