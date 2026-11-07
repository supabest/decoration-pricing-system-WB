"""知识库注入判定 —— 移植后端 build_system_prompt 的三桶渲染口径

源数据 docs/ai_knowledge_base.json（43 条：tips 4 / synonyms 15 / rules 24）
按 category 全量注入模型提示，不做 team / 关键词 / 启用状态过滤（对齐 load_knowledge）。

保密是这里的首要约束：源 JSON 有 **7 条 rules 内嵌真实基准价金额**，
与 SKILL.md「prepare 候选绝不能出现 price」红线冲突。本模块按 keyword
把它们覆盖为纯工序描述，并用 assert_no_pricing() 做 fail-closed 守卫 ——
源库以后若新增含价条目，直接报错而不是悄悄带进提示块。

不做知识库 CRUD / 查看器 / 导入导出（规格 §1 已列入「平台域 —— 不做」）；
不改 retrieve.py：确定性召回与后端逐字一致，同义词不进召回打分。

远端依据：backend/app/services/ai_pricing_service.py:285-320 build_system_prompt
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_KB_PATH = Path(__file__).resolve().parents[2] / "docs" / "ai_knowledge_base.json"

# 7 条含价规则的纯工序改写：保留「拆几道工序 / 选哪个子目」的全部信息，
# 去掉金额、基价、综合单价、≈ 等定价痕迹；随源码入库、可 review。
SANITIZED_RULES: dict[str, str] = {
    "金属门窗套套价": (
        "金属门窗套（不锈钢饰面+夹板基层）拆2工序：①夹板基层→木工YQ-014"
        "（墙面基层-轻钢龙骨/夹板基层）②不锈钢饰面→铁工TG-010"
        "（墙面-不锈钢常规金属类）。304#不锈钢装饰线属于常规金属饰面，"
        "不选TG-09造型/零星"
    ),
    "瓷砖门槛石套价": (
        "瓷砖门槛石(CT.01等)直接套NS-012(门槛/波打线瓷砖铺贴)。CT.01=瓷砖,"
        "不套NS-017(石材门槛)。仅当特征明确描述找平层/墙面抹灰/墙面批挡/"
        "水泥砂浆找平及厚度时才加NS-01;仅描述结合层/水泥胶浆不加找平层"
        "——结合层≠找平层"
    ),
    "墙面涂料刮腻子": (
        "项目名称含'涂料/乳胶漆/无机涂料'且单位=m2(墙面类),特征含"
        "'刮腻子/扇灰/批灰/腻子两遍'时直接套YQ-02(墙面-乳胶漆)。"
        "YQ-02的spec已含刮腻子三遍+底漆+面漆,不额外套YQ-05。"
        "仅当天花/天棚/吊顶类涂料时选YQ-07"
    ),
    "吊顶天棚套价": (
        "天棚吊顶含龙骨+石膏板+涂料拆2工序:①龙骨+石膏板→木工YQ-025 "
        "②涂料→油漆YQ-07(已含刮腻子+底漆+面漆,不套YQ-05)"
    ),
    "天棚灯槽套价": (
        "天棚灯槽（含客厅灯槽/主卧灯槽等）拆1工序：灯槽基层+石膏板→"
        "木工YQ-030（天棚灯槽展开宽度500mm以内）。涂料面层面积小已含在"
        "灯槽工费中，不单独套涂料子目。注意灯槽是m单位，涂料子目是m²单位，"
        "单位不匹配不能混套"
    ),
    "窗帘盒套价": (
        "窗帘盒套木工YQ-032(spec展开300mm=200+100)。若特征含宽×高尺寸"
        "(如200×200),实际展开=宽+高,尺寸系数=实际展开/300"
        "(如200×200→400/300),子目YQ-032×尺寸系数。涂料面层面积小已含在"
        "工费中,不单独套涂料子目。电动开合装置无匹配子目→备注标记"
    ),
    "假梁天花侧板套价": (
        "假梁/天花侧板(立面吊顶)拆2工序:①立面基层→木工YQ-026"
        "(石膏板吊顶立面,spec已含阻燃夹板+石膏板+轻钢龙骨)②涂料面层→"
        "油漆YQ-07(天棚-乳胶漆,已含刮腻子+底漆+面漆)。注意:假梁/侧板/"
        "立面关键词必须路由木工班组,切不可路由泥水班组地面子目"
    ),
}

# 定价痕迹。刻意收窄，避免误伤 9mm / 900x1800 / 300mm=200+100 / CT.01
# 这类尺寸与编号；命中即为「价格」，拒绝注入。
_PRICING_RE = re.compile(
    r"¥\s*\d"
    r"|\d+\.\d+\s*/\s*m"
    r"|综合单价"
    r"|≈\s*\d"
    r"|基价\s*[:：]?\s*\d"
    r"|单价\s*[:=]\s*\d"
)

_INTRO = "你是精装修工程造价专家，负责将清单项目与企业基准价定额子目精确匹配。"

# 与后端 build_system_prompt 逐字一致（不含价、硬编码规则）
_PRINCIPLES = """## 工序拆解原则
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


def assert_no_pricing(text: str) -> None:
    """fail-closed：文本含任何定价痕迹即抛 ValueError，绝不悄悄放行。"""
    m = _PRICING_RE.search(text or "")
    if m:
        raise ValueError(f"知识库含定价明细，禁止注入：{m.group()!r}")


def load_knowledge(path: str | Path | None = None) -> dict:
    """读源 JSON → 三桶 + 脱敏覆盖 + 全库金额守卫。

    返回 {tips, synonyms, rules, total, sanitized_count}；total 为源库条数，
    sanitized_count 为被改写的含价规则数（可审计）。
    """
    src = Path(path) if path else DEFAULT_KB_PATH
    raw = json.loads(src.read_text(encoding="utf-8"))
    kb = {
        "tips": [dict(x) for x in raw.get("tips", [])],
        "synonyms": [dict(x) for x in raw.get("synonyms", [])],
        "rules": [dict(x) for x in raw.get("rules", [])],
    }

    sanitized = 0
    for r in kb["rules"]:
        replacement = SANITIZED_RULES.get(r.get("keyword", ""))
        if replacement is not None:
            r["content"] = replacement
            sanitized += 1
    kb["total"] = sum(len(kb[k]) for k in ("tips", "synonyms", "rules"))
    kb["sanitized_count"] = sanitized

    # 整库扫描：源库未来新增含价条目（不在脱敏表里）会在此炸掉
    for bucket in ("tips", "synonyms", "rules"):
        for entry in kb[bucket]:
            assert_no_pricing(f"{entry.get('keyword', '')}：{entry.get('content', '')}")
    return kb


def _render(entries: list[dict], label: str, arrow: bool = False) -> str:
    sep = " → " if arrow else "："
    lines = []
    for e in entries:
        suffix = f"（{e['team']}）" if e.get("team") else ""
        lines.append(
            f"【{label}】{e.get('keyword', '')}{sep}{e.get('content', '')}{suffix}"
        )
    return "\n".join(lines)


def build_prompt_block(knowledge: dict) -> str:
    """完整系统提示块，三桶渲染口径逐字对齐远端 build_system_prompt。"""
    tips = _render(knowledge.get("tips", []), "技巧")
    syns = _render(knowledge.get("synonyms", []), "同义词", arrow=True)
    rules = _render(knowledge.get("rules", []), "规则")
    block = (
        f"{_INTRO}\n\n"
        f"## 当前知识库（必须遵守）\n{tips}\n{syns}\n{rules}\n\n"
        f"{_PRINCIPLES}"
    )
    assert_no_pricing(block)
    return block
