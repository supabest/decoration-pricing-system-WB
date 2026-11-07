"""S2 · 知识库脱敏注入 —— 测试先行

断言只用规则条数与渲染形态，绝不输出任何定价明细。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import knowledge
import retrieve

PRICING_RE = re.compile(
    r"¥\s*\d|\d+\.\d+\s*/\s*m|综合单价|≈\s*\d|基价\s*[:：]?\s*\d|单价\s*[:=]\s*\d"
)


def test_load_knowledge_shape_and_counts():
    kb = knowledge.load_knowledge()
    assert kb["total"] == 43
    assert len(kb["tips"]) == 4
    assert len(kb["synonyms"]) == 15
    assert len(kb["rules"]) == 24
    assert kb["sanitized_count"] == 7


def test_sanitized_rules_have_no_pricing():
    kb = knowledge.load_knowledge()
    for r in kb["rules"]:
        if r["keyword"] in knowledge.SANITIZED_RULES:
            assert r["content"] == knowledge.SANITIZED_RULES[r["keyword"]]
            assert not PRICING_RE.search(r["content"]), r["keyword"]


def test_prompt_block_has_no_pricing_anywhere():
    block = knowledge.build_prompt_block(knowledge.load_knowledge())
    assert not PRICING_RE.search(block)


def test_assert_no_pricing_is_fail_closed():
    # 守卫样例一律用明显虚构的占位数字，避免进仓库后被误读成真实基准价
    with pytest.raises(ValueError):
        knowledge.assert_no_pricing("基价¥999999/m2")
    with pytest.raises(ValueError):
        knowledge.assert_no_pricing("综合单价=999999+1=1000000/m2")
    knowledge.assert_no_pricing("拆2工序：①找平→泥水班组 ②铺贴→泥水班组")


def test_load_knowledge_rejects_new_priced_entry(tmp_path):
    """源库未来新增含价条目（不在脱敏表里）必须炸掉，而不是悄悄泄露。"""
    src = Path(knowledge.DEFAULT_KB_PATH).read_text(encoding="utf-8")
    import json
    raw = json.loads(src)
    raw["rules"].append({"keyword": "虚构新增", "content": "基价¥123456.0/m2", "team": ""})
    p = tmp_path / "kb.json"
    p.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        knowledge.load_knowledge(p)


def test_prompt_block_renders_three_buckets_and_full_injection():
    block = knowledge.build_prompt_block(knowledge.load_knowledge())
    assert block.startswith("你是精装修工程造价专家")
    assert "## 当前知识库（必须遵守）" in block
    assert "## 工序拆解原则" in block and "## 班组归属" in block
    assert "严格规则：" in block
    assert "【技巧】多工序项目：" in block
    assert "【同义词】扇灰 → 批灰" in block
    assert "【规则】轻钢龙骨夹板基层天花硬包：" in block
    # 全量注入：43 条都在，没有按 team / 关键词 / 启用状态过滤
    assert block.count("【技巧】") == 4
    assert block.count("【同义词】") == 15
    assert block.count("【规则】") == 24
    assert "（）" not in block


def test_team_suffix_only_when_nonempty():
    kb = {
        "tips": [{"keyword": "虚构技巧", "content": "虚构内容", "team": ""}],
        "synonyms": [{"keyword": "虚构词", "content": "虚构同义", "team": "油漆班组"}],
        "rules": [],
    }
    block = knowledge.build_prompt_block(kb)
    assert "【技巧】虚构技巧：虚构内容\n" in block
    assert "【技巧】虚构技巧：虚构内容（" not in block
    assert "【同义词】虚构词 → 虚构同义（油漆班组）" in block


def test_module_has_no_network_imports():
    src = Path(knowledge.__file__).read_text(encoding="utf-8")
    for mod in ("import httpx", "import requests", "import socket",
                "import supabase", "import openai"):
        assert mod not in src


def test_retrieve_recall_is_unchanged():
    """知识库移植不得改动确定性召回口径。"""
    words, crafts = retrieve.query_terms("地面水泥砂浆找平", "20mm厚1:3水泥砂浆")
    assert isinstance(words, list) and isinstance(crafts, list) and words
    parsed = retrieve.engineering_parse("墙面-木饰面（常规）", "木饰面 挂贴")
    assert set(parsed) == {"teams", "crafts", "materials"}
