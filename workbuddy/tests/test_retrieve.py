"""T2 · 候选召回 —— 测试先行

断言只用「编号 + 班组」复合键，绝不写价格：
internal_code 在不同班组间重复（YQ-/ZY- 各有两个班组共用），单用编号会误判。
"""
import pytest

import retrieve
import snapshot

# (名称, 特征, 单位, 期望命中 (编号, 班组))
CASES = [
    ("ST-01石材门槛石",
     "1.材料种类:水泥砂浆 3.材料厚度:50mm 4.面层材料:ST-01石材门槛石 5.结合层:10mm厚1:3干硬性水泥砂浆",
     "m2", ("NS-017", "泥水班组")),
    ("ST-07石材地面铺贴",
     "1.面层材料:20mm厚石材 2.结合层:10mm厚1:3干硬性水泥砂浆 3.嵌缝:专用勾缝剂",
     "m2", ("NS-015", "泥水班组")),
    ("平面石膏板吊顶 及扇灰油乳胶漆",
     "轻钢龙骨 9.5mm石膏板 满刮腻子 乳胶漆饰面",
     "m2", ("YQ-025", "木工班组")),
    ("墙面-木饰面（常规）",
     "木饰面 基层板 挂贴",
     "m2", ("YQ-011", "木工班组")),
    ("镀锌电线管 DN20",
     "明暗敷设 穿引线 锯管 套丝",
     "m", ("JD-014", "机电班组")),
]

ITEMS = None


def items():
    global ITEMS
    if ITEMS is None:
        ITEMS = snapshot.load_snapshot()["benchmark_items"]
    return ITEMS


# ---------- 班组路由 ----------

def test_route_teams_stone_hits_masonry():
    assert "泥水班组" in retrieve.route_teams("石材门槛石", "水泥砂浆结合层")


def test_route_teams_electrical():
    assert "机电班组" in retrieve.route_teams("镀锌电线管 DN20", "明暗敷设")


def test_route_teams_unknown_returns_empty():
    assert retrieve.route_teams("zzz", "qqq") == []


# ---------- 单位归一化 ----------

@pytest.mark.parametrize("raw,expect", [
    ("㎡", "m2"), ("m2", "m2"), ("m²", "m2"), ("M2", "m2"),
    ("m", "m"), ("M", "m"), ("个", "个"),
])
def test_normalize_unit(raw, expect):
    assert retrieve.normalize_unit(raw) == expect


# ---------- 候选召回 ----------

@pytest.mark.parametrize("name,spec,unit,expected", CASES)
def test_top20_contains_expected(name, spec, unit, expected):
    cands = retrieve.build_candidates(name, spec, unit, items())[:20]
    got = {retrieve.identify(c) for c in cands}
    assert expected in got, f"top20 未命中 {expected}；实际: {list(got)[:5]}"


def test_candidates_respect_limit():
    cands = retrieve.build_candidates("地面找平", "水泥砂浆", "m2", items())
    assert 0 < len(cands) <= 80


def test_candidates_unique_by_code_and_team():
    cands = retrieve.build_candidates("墙面乳胶漆", "满刮腻子", "m2", items())
    keys = [(c["internal_code"], c["trade_team"]) for c in cands]
    assert len(keys) == len(set(keys)), "候选出现重复 (编号,班组)"


def test_scores_are_descending():
    scored = retrieve.rank_items(
        items()[:50], *retrieve.query_terms("地面-水泥砂浆找平", "20mm"), "m2")
    scores = [s for _, s in scored]
    assert scores == sorted(scores, reverse=True)


# ---------- 工程语义解析 ----------

def test_engineering_parse_shape():
    parsed = retrieve.engineering_parse("墙面-木饰面（常规）", "木饰面 挂贴")
    assert set(parsed) == {"teams", "crafts", "materials"}
    assert "木工班组" in parsed["teams"]
    assert "木制品" in parsed["materials"]
