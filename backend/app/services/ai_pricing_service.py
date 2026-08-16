"""AI 套价服务 — 与 tool.html 逻辑完全一致的 Python 实现"""
import re, json, httpx
from typing import Optional
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


# ── 候选筛选 ──
def build_candidates(name: str, spec: str, unit: str, benchmark_items: list[dict]) -> list[dict]:
    teams = route_teams(name, spec)
    if len(teams) <= 2:
        teams = list(set(d['trade_team'] for d in benchmark_items))

    all_cands = [d for d in benchmark_items if d.get('trade_team') in teams]

    full_text = re.sub(r'[（）()\-—\/\s]+', ' ', name + ' ' + spec)
    words = []
    for i in range(len(full_text) - 1):
        bigram = full_text[i:i+2]
        if not re.search(r'[，。、；：！？\s\d]', bigram):
            words.append(bigram)
    words.extend(w for w in full_text.split() if len(w) >= 3)
    uniq_words = list(set(words))

    spec_lower = spec.lower()
    spec_keywords = [w for w in CRAFT_KEYWORDS if w in spec_lower]

    scored = []
    for it in all_cands:
        score = 0
        it_name = it.get('item_name', '')
        it_spec = it.get('spec', '')
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
    return [it for it, _ in scored[:80]]


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


# ── DeepSeek 调用 ──
async def call_deepseek(system_prompt: str, user_prompt: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={
                "model": settings.LLM_MODEL,
                "max_tokens": 8000,
                "temperature": 0,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            }
        )
        if r.status_code != 200:
            raise Exception(f"DeepSeek error {r.status_code}: {r.text[:200]}")
        data = r.json()
        msg = (data.get("choices") or [{}])[0].get("message") or {}
        # deepseek-v4-pro 是推理模型：答案可能落在 content 或 reasoning_content
        content = (msg.get("content") or "").strip()
        if not content:
            content = (msg.get("reasoning_content") or "").strip()
        return content


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
async def price_single(name: str, spec: str, unit: str, api_key: str,
                       debug_log=None) -> dict:
    benchmark = await load_benchmark_data()
    knowledge = await load_knowledge()

    # 🔍 调试日志
    if debug_log is None:
        from app.services.pricing_debug_logger import PricingDebugLog
        debug_log = PricingDebugLog(name, spec, unit, api_key)

    # 1. 班组路由
    teams = route_teams(name, spec)
    debug_log.log_route(teams)

    # 2. 候选筛选
    candidates = build_candidates(name, spec, unit, benchmark)
    debug_log.log_candidates(candidates, len(candidates))
    if not candidates:
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": "无候选子目"})
        await save_debug_log(debug_log)
        return {"matched": [], "overall_confidence": 0, "note": "无候选子目"}

    # 3. 工程理解
    eng = engineering_parse(name, spec)
    debug_log.log_engineering(eng)

    # 4. Prompt 构建
    sys_prompt = build_system_prompt(knowledge)
    user_prompt = build_user_prompt(name, spec, unit, candidates)
    debug_log.log_prompt(sys_prompt, user_prompt)

    # 5. DeepSeek 调用
    try:
        raw = await call_deepseek(sys_prompt, user_prompt, api_key)
        result = parse_ai_response(raw)
        debug_log.log_response(raw, result)
    except Exception as e:
        debug_log.log_error(str(e))
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": str(e)[:100]})
        await save_debug_log(debug_log)
        raise

    if not result:
        debug_log.log_final({"matched": [], "overall_confidence": 0, "note": f"AI返回解析失败: {raw[:100]}"})
        await save_debug_log(debug_log)
        return {"matched": [], "overall_confidence": 0, "note": f"AI返回解析失败: {raw[:100]}"}

    # 6. 校验返回的子目真实存在
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
async def price_batch(items: list[dict], api_key: str) -> list[dict]:
    results = []
    for item in items:
        try:
            r = await price_single(item['name'], item.get('spec', ''), item.get('unit', ''), api_key)
            results.append({**item, **r})
        except Exception as e:
            results.append({**item, "matched": [], "overall_confidence": 0, "note": str(e)[:100]})
    return results
