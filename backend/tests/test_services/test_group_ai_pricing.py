"""集团口径 AI 套价（mode='group'）回归测试 — ZS02 候选/路由/prompt/校验/待询价。

运行方式：
  - backend/venv311/bin/python -m pytest backend/tests/test_services/test_group_ai_pricing.py -q
  - backend/venv311/bin/python -m pytest backend/tests -q

不发真实 LLM 请求：call_deepseek / load_* / save_debug_log 全部打桩。
关键不变式：
  1) group 模式只碰 group_benchmark_items，绝不拉内部 497 条库（口径隔离）
  2) AI 编造的编号（含内部码）一律被校验层剔掉，剔空则 overall_confidence 归 0
  3) 不传 mode 时的行为与旧版逐字等价（向后兼容 m.html 与对内调用）
  4) null≠0：mats 里只有 price is None 才算待询价，0（甲供按 0 计）合法
"""
import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.services.ai_pricing_service as svc                                    # noqa: E402
from app.services.ai_pricing_service import (                                     # noqa: E402
    route_disciplines, build_group_candidates, build_group_system_prompt,
    build_group_user_prompt, _group_pending_mats, _validate_group_matches,
)
from app.schemas.ai_pricing import PriceSingleRequest, PriceResponse               # noqa: E402

GROUP_KB = {'tips': [{'keyword': '多工序', 'content': '一道清单可能含多道工序', 'team': ''}],
            'synonyms': [{'keyword': '扇灰', 'content': '刮腻子', 'team': ''}],
            'rules': [{'keyword': '门槛石', 'content': '单列子目', 'team': ''}]}


def _g(code, name, disc='A', section='楼地面工程', unit='m2', spec='', mats=None):
    """group_benchmark_items 行夹具（字段名与线上表一致，含 _group_text 预拼）"""
    row = {'code': code, 'discipline': disc, 'section_name': section, 'name': name,
           'spec': spec, 'unit': unit, 'work_type': '', 'lab_price': 10,
           'aux_cost': 1, 'mech_cost': 0, 'mats': mats or []}
    row['_group_text'] = ((row['spec'] or '') + ' ' + (row['section_name'] or '')).strip()
    return row


# ── 1. discipline 路由 ──
def test_route_disciplines_拆除走C():
    assert 'C' in route_disciplines('拆除原有瓷砖墙面', '凿除并清运'), route_disciplines('拆除原有瓷砖墙面', '')


def test_route_disciplines_措施走D():
    ds = route_disciplines('装修满堂脚手架', '')
    assert 'D' in ds, ds


def test_route_disciplines_水电走B():
    ds = route_disciplines('插座回路布线', '电线 桥架')
    assert 'B' in ds, ds


def test_route_disciplines_精装走A且可多命中():
    ds = route_disciplines('瓷砖地面铺贴', '含找平')
    assert 'A' in ds, ds


def test_route_disciplines_无命中返回空():
    assert route_disciplines('看不懂的东西', '') == []


# ── 2. 候选筛选 ──
def test_group_candidates_section_name参与匹配():
    """同名同特征，只有分部名不同 → 靠 _group_text(spec+section_name) 分出高下（地面/墙面不互串的依据）"""
    rows = [
        _g('ZS02-A-009', '瓷砖地面', section='墙柱面工程', spec='800×800'),   # 故意的错配行放前面
        _g('ZS02-A-010', '瓷砖地面', section='楼地面工程', spec='800×800'),
    ]
    got = build_group_candidates('楼地面瓷砖', '800×800', 'm2', rows)
    assert got[0]['code'] == 'ZS02-A-010', [c['code'] for c in got]


def test_group_candidates_discipline加分不改文本相关性主次():
    rows = [
        _g('ZS02-A-100', '脚手架', disc='A', section='其他'),
        _g('ZS02-D-002', '脚手架', disc='D', section='措施项目'),
    ]
    got = build_group_candidates('满堂脚手架', '', 'm2', rows)
    assert got[0]['code'] == 'ZS02-D-002', [c['code'] for c in got]


def test_group_candidates_单位一致加权():
    rows = [
        _g('ZS02-A-001', '金属踢脚线', unit='m2'),
        _g('ZS02-A-002', '金属踢脚线', unit='m'),
    ]
    got = build_group_candidates('金属踢脚线', '', 'm', rows)
    assert got[0]['code'] == 'ZS02-A-002', [c['code'] for c in got]


def test_group_candidates_上限80与空库():
    big = [_g(f'ZS02-A-{i:03d}', f'瓷砖地面铺贴 {i}') for i in range(100)]
    assert len(build_group_candidates('瓷砖地面', '铺贴', 'm2', big)) == 80
    assert build_group_candidates('瓷砖地面', '', 'm2', []) == []


# ── 3. Prompt ──
def test_group_system_prompt_面向ZS02且剥掉内部口径硬编码():
    p = build_group_system_prompt(GROUP_KB)
    assert 'ZS02' in p
    assert '每增减' in p, '增减子目陷阱规则必须在位（ZS02 库里大量「每增减5mm」行）'
    assert '班组归属' not in p, '集团口径没有班组概念'
    assert '辅材配方' not in p, '集团子目自带 A/C/D/E 分解，没有辅材配方'
    assert 'YQ-025 + YQ-07' not in p, '内部工序映射不得带进集团 prompt'
    assert '禁止编造' in p


def test_group_system_prompt_保留知识库同义词做名称翻译():
    p = build_group_system_prompt(GROUP_KB)
    assert '扇灰 → 刮腻子' in p, p[:400]


def test_group_user_prompt_候选行格式():
    rows = [_g('ZS02-A-009', '瓷砖地面', section='楼地面工程', spec='SA级600×600')]
    up = build_group_user_prompt('瓷砖地面', 'SA级600×600', 'm2', rows)
    assert 'ZS02-A-009|瓷砖地面|SA级600×600|m2|楼地面工程' in up, up
    assert '"matched"' in up and 'overall_confidence' in up


def test_group_user_prompt_特征截断120字():
    rows = [_g('ZS02-A-009', '瓷砖地面', spec='长' * 200)]
    up = build_group_user_prompt('瓷砖地面', 'x', 'm2', rows)
    assert ('长' * 121) not in up and ('长' * 120) in up


# ── 4. 待询价与校验 ──
def test_pending_mats_null算待询价格式合法():
    row = _g('ZS02-A-009', '瓷砖地面', mats=[
        {'name': '瓷砖', 'price': None, 'unit': 'm2', 'consumption': 1.4469},
        {'name': '甲供砂浆', 'price': 0, 'unit': 'm3', 'consumption': 0.01},
        {'name': None, 'price': None},
    ])
    assert _group_pending_mats(row) == ['瓷砖'], _group_pending_mats(row)


def test_pending_mats_mats缺失不报错():
    assert _group_pending_mats({'code': 'X'}) == []
    assert _group_pending_mats({'mats': ['不是dict']}) == []


def test_validate_group_未知与内部码被剔_合法项补sheet与待询价():
    rows = [_g('ZS02-A-009', '瓷砖地面', disc='A',
               mats=[{'name': '瓷砖', 'price': None, 'unit': 'm2', 'consumption': 1.4469}])]
    matched = [
        {'id': 'ZS02-A-009', 'confidence': 90, 'reason': '精确'},
        {'id': ' zy-01 ', 'confidence': 80},              # 内部码 → 剔
        {'id': 'ZS02-A-999', 'confidence': 70},           # 库里没有 → 剔
        '不是dict',                                        # 脏数据 → 忽略
    ]
    got = _validate_group_matches(matched, rows)
    assert len(got) == 1, got
    assert got[0]['id'] == 'ZS02-A-009'
    assert got[0]['sheet'] == 'ZS02-A', got[0]
    assert got[0]['pending_mats'] == ['瓷砖'], got[0]


def test_validate_group_重复编号只留一条():
    rows = [_g('ZS02-D-003', '成品保护', disc='D')]
    got = _validate_group_matches([{'id': 'ZS02-D-003'}, {'id': 'zs02-d-003'}], rows)
    assert len(got) == 1, got


# ── 打桩夹具：拦住网络与 LLM ──
def _patch(monkeypatch, group_rows, llm_payload):
    calls = {'group_load': 0, 'internal_load': 0, 'llm': 0, 'saved': 0}

    async def fake_group():
        calls['group_load'] += 1
        return group_rows

    async def fake_internal():
        calls['internal_load'] += 1
        return [{'internal_code': 'ZY-01', 'item_name': 'x', 'trade_team': '泥水班组',
                 'unit': 'm2', 'spec': '', 'unit_price': 0}]

    async def fake_kb():
        return GROUP_KB

    async def fake_call(system_prompt, user_prompt, api_key, model=None):
        calls['llm'] += 1
        calls['system_prompt'] = system_prompt
        calls['user_prompt'] = user_prompt
        return json.dumps(llm_payload, ensure_ascii=False)

    async def fake_save(log):
        calls['saved'] += 1

    monkeypatch.setattr(svc, 'load_group_benchmark_data', fake_group)
    monkeypatch.setattr(svc, 'load_benchmark_data', fake_internal)
    monkeypatch.setattr(svc, 'load_knowledge', fake_kb)
    monkeypatch.setattr(svc, 'call_deepseek', fake_call)
    monkeypatch.setattr(svc, 'save_debug_log', fake_save)
    return calls


# ── 5. price_single 分支 ──
def test_price_single_group_只拉集团库且命中带sheet与待询价(monkeypatch):
    rows = [_g('ZS02-A-009', '瓷砖地面', section='楼地面工程', spec='SA级600×600',
               mats=[{'name': '瓷砖', 'price': None, 'unit': 'm2', 'consumption': 1.4469}])]
    calls = _patch(monkeypatch, rows,
                   {'matched': [{'id': 'ZS02-A-009', 'confidence': 88, 'reason': '名称与分部一致'}],
                    'overall_confidence': 88, 'note': '主材待询价'})
    res = asyncio.run(svc.price_single('瓷砖地面', 'SA级600×600', 'm2', 'k', mode='group'))

    assert calls['group_load'] == 1 and calls['internal_load'] == 0, '集团模式不得拉内部 497 条库'
    assert calls['llm'] == 1
    assert 'ZS02' in calls['system_prompt'] and '班组归属' not in calls['system_prompt']
    assert res['matched'][0]['id'] == 'ZS02-A-009'
    assert res['matched'][0]['sheet'] == 'ZS02-A'
    assert res['matched'][0]['pending_mats'] == ['瓷砖']
    assert res['overall_confidence'] == 88
    PriceResponse(**res)      # 响应模型必须能吃下集团结果（含 pending_mats）


def test_price_single_group_编造编号被拦且置信度归零(monkeypatch):
    rows = [_g('ZS02-A-009', '瓷砖地面')]
    calls = _patch(monkeypatch, rows,
                   {'matched': [{'id': 'NS-029', 'confidence': 95},
                               {'id': 'ZS02-A-777', 'confidence': 95}],
                    'overall_confidence': 95, 'note': ''})
    res = asyncio.run(svc.price_single('瓷砖地面', '', 'm2', 'k', mode='group'))
    assert res['matched'] == [], res
    assert res['overall_confidence'] == 0, '全部被剔后不能保留高置信度'


def test_price_single_group_库为空时不调LLM并明确报因(monkeypatch):
    calls = _patch(monkeypatch, [], {'matched': [], 'overall_confidence': 0, 'note': ''})
    res = asyncio.run(svc.price_single('瓷砖地面', '', 'm2', 'k', mode='group'))
    assert calls['llm'] == 0, '库空还去问 AI 是浪费 token'
    assert '集团基准价库不可用' in res['note'], res
    assert res['matched'] == [] and res['overall_confidence'] == 0


def test_price_single_默认internal走老路径向后兼容(monkeypatch):
    """不传 mode（m.html / 对内 tool.html 现状）→ 拉内部库、内部 prompt、不碰集团库"""
    calls = _patch(monkeypatch, [_g('ZS02-A-009', '瓷砖地')],
                   {'matched': [{'id': 'ZY-01', 'sheet': '泥水班组', 'confidence': 90}],
                    'overall_confidence': 90, 'note': ''})
    res = asyncio.run(svc.price_single('瓷砖地面', '', 'm2', 'k'))
    assert calls['internal_load'] == 1 and calls['group_load'] == 0, calls
    assert '## 班组归属' in calls['system_prompt'], '必须还是内部版 prompt'
    assert res['matched'][0]['id'] == 'ZY-01'
    assert 'pending_mats' not in res['matched'][0], '对内结果不该长出集团字段'


def test_request_schema_mode默认internal():
    req = PriceSingleRequest(item={'name': '瓷砖地面'}, api_key='k')
    assert req.mode == 'internal', req.mode
    assert PriceSingleRequest(item={'name': 'x'}, api_key='k', mode='group').mode == 'group'


if __name__ == '__main__':
    print('本文件含 monkeypatch 用例，请用 pytest 运行：pytest backend/tests/test_services/test_group_ai_pricing.py -q')
    sys.exit(0)
