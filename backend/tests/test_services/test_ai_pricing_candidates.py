"""对内候选筛选回归基线 — route_teams / build_candidates 行为钉。

为什么先有这支测试：集团模式 AI 套价（mode='group'）要复用同一套 2-gram 打分骨架，
打分块会被抽成共享函数（_query_terms / _rank_items）。抽取属于「内部模式零行为变更」
硬约束下的高危重构，故先把现网行为钉死：重构前后本文件必须逐条同色通过，
任何候选顺序变化都会被这里拦下。

运行方式：
  - backend/venv311/bin/python -m pytest backend/tests/test_services/test_ai_pricing_candidates.py -q
  - backend/venv311/bin/python -m pytest backend/tests -q
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ai_pricing_service import route_teams, build_candidates   # noqa: E402


def _bench(code, name, team, unit='m2', spec=''):
    """内部基准价最小夹具（字段名与 benchmark_items 一致：internal_code/item_name/trade_team）"""
    return {'internal_code': code, 'item_name': name, 'trade_team': team,
            'unit': unit, 'spec': spec, 'work_type': '', 'unit_price': 0}


# 夹具：同一关键词「瓷砖地面铺贴」下，谁该排前面是人为可控的（名称含词多、单位一致 +3）
FIXTURE = [
    _bench('NS-001', '地面瓷砖铺贴', '泥水班组', 'm2', '干硬性砂浆铺贴'),
    _bench('NS-002', '墙面瓷砖铺贴', '泥水班组', 'm2', '背靠背粘贴'),
    _bench('NS-003', '地面水泥砂浆找平层', '泥水班组', 'm2', '20mm厚'),
    _bench('YQ-002', '墙面乳胶漆', '油漆班组', 'm2', '一底两面'),
    _bench('TG-008', '金属踢脚线', '油漆班组', 'm', '卡扣式'),
    _bench('NS-004', '地面石材铺贴', '泥水班组', 'm2', '大板砖'),
]


def test_route_teams_命中泥水班组():
    teams = route_teams('客厅地面瓷砖铺贴', '300×600 瓷砖 干硬性砂浆')
    assert '泥水班组' in teams, teams


def test_route_teams_木工关键词():
    teams = route_teams('轻钢龙骨石膏板吊顶', '')
    assert '木工班组' in teams, teams


def test_route_teams_无命中返回空列表():
    assert route_teams('随便一条看不懂的清单', '') == []


def test_build_candidates_精确名称排首位():
    got = build_candidates('客厅地面瓷砖铺贴', '300×600 瓷砖 干硬性砂浆', 'm2', FIXTURE)
    codes = [c['internal_code'] for c in got]
    assert codes[0] == 'NS-001', codes
    # 名称含「地面」+「瓷砖」的行必须整体压过只含其一的行
    assert codes.index('NS-001') < codes.index('NS-002'), codes
    assert codes.index('NS-001') < codes.index('YQ-002'), codes


def test_build_candidates_单位一致加权胜过纯文本相似():
    # 询价单位 m 时，m 单位的踢脚线因 +3 单位分应压过 m2 的瓷砖行
    got = build_candidates('金属踢脚线', '卡扣式', 'm', FIXTURE)
    assert got[0]['internal_code'] == 'TG-008', [c['internal_code'] for c in got]


def test_build_candidates_班组路由过窄时放开全库():
    """route_teams 命中 ≤2 个班组 → 走全库打分（现网既有策略，勿改成先过滤）"""
    got = build_candidates('墙面乳胶漆', '一底两面 刮腻子', 'm2', FIXTURE)
    codes = {c['internal_code'] for c in got}
    assert 'NS-001' in codes, codes      # 泥水班组行仍在候选池内
    assert len(got) == len(FIXTURE), len(got)


def test_build_candidates_上限80条():
    big = [_bench(f'X-{i:03d}', f'瓷砖地面铺贴 编号{i}', '泥水班组') for i in range(100)]
    got = build_candidates('瓷砖地面', '铺贴', 'm2', big)
    assert len(got) == 80, len(got)


def test_build_candidates_空库返回空():
    assert build_candidates('瓷砖地面', '', 'm2', []) == []


if __name__ == '__main__':
    fails = 0
    for fn in sorted(k for k in dir() if k.startswith('test_')):
        try:
            globals()[fn]()
            print(f'  ✓ {fn}')
        except Exception as exc:
            fails += 1
            print(f'  ✗ {fn}: {exc}')
    print('全部通过' if not fails else f'{fails} 支失败')
    sys.exit(1 if fails else 0)
