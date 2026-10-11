"""ZS02 附录2 集团基准价导入脚本回归测试 — 解析 + 296 条 H 重算审计（异常登记制）。

运行方式（从仓库根；conftest 失效属既有缺陷，用 --confcutdir 绕过，见 T2 report §2）：
  - python3 -m pytest backend/tests/test_services/test_import_group_benchmark.py -v \
        --confcutdir=backend/tests/test_services
  - python3 backend/tests/test_services/test_import_group_benchmark.py  （无 pytest 时也能直跑）
"""
import os
import sys
from pathlib import Path

import pytest

# 仓库根入 sys.path（scripts/ 是命名空间包，需仓库根可见；沿用同目录
# test_parse_ai_response.py:10-12 的 parents[N] shim 惯例）
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.import_group_benchmark import (  # noqa: E402
    parse_workbook, recalc_h, XLSX_DEFAULT, KNOWN_ANOMALIES,
)

HAS_XLSX = os.path.exists(XLSX_DEFAULT)

# R1：审计登记表——|Δ|>0.01 的条目必须全部命中此表且仅这 8 条（不得把偏差算进通过口径）
EXPECTED_ANOMALY_CODES = {
    'ZS02-A-069', 'ZS02-A-070',
    'ZS02-B-100', 'ZS02-B-102', 'ZS02-B-103', 'ZS02-B-104', 'ZS02-B-105', 'ZS02-B-106',
}

# R2：主材名命中以下占位符的行不算主材（材料费已含于 A/D/E），mats 里根本不应放这条
NON_MAT_NAMES = {'', '——', '-', '—'}


def test_recalc_h_owner_supply_zero_mat():
    # ZS02-A-009 瓷砖楼梯面铺贴：甲供空价按 0 → 81.5085（Excel 原值）
    item = dict(lab_price=61.65, mats=[{'price': None, 'consumption': 1.4469},
                                       {'price': None, 'consumption': 0.0147}],
                aux_cost=1.98, mech_cost=0)
    assert abs(recalc_h(item) - 81.5085) <= 0.01


def test_recalc_h_with_mat_price():
    # ZS02-D-003 楼地面成品保护膜：2×0.95=1.9 → 4.0779
    item = dict(lab_price=1.51, mats=[{'price': 2, 'consumption': 0.95}],
                aux_cost=0.23, mech_cost=0)
    assert abs(recalc_h(item) - 4.0779) <= 0.01


def test_known_anomalies_registry_is_exactly_8():
    """R1：登记表必须是精确的 8 条异常码，每条都有非空 reason。"""
    assert set(KNOWN_ANOMALIES) == EXPECTED_ANOMALY_CODES
    assert len(KNOWN_ANOMALIES) == 8
    assert all(isinstance(v, str) and v.strip() for v in KNOWN_ANOMALIES.values())


@pytest.mark.skipif(not HAS_XLSX, reason='附录2 xlsx 不在本机（knowledge/ 不入 git）')
def test_full_audit_296_items():
    items = parse_workbook(XLSX_DEFAULT)
    assert len(items) == 296
    bad = {i['code'] for i in items
           if abs(recalc_h(i) - i['raw_composite']) > 0.01}
    # R1：偏差条目必须全部命中登记表，且仅这 8 条（期望值来自裁定，不迁就数据）
    assert bad == EXPECTED_ANOMALY_CODES
    assert bad == set(KNOWN_ANOMALIES)
    assert sum(1 for i in items if i['discipline'] == 'A') == 146
    assert sum(1 for i in items if i['discipline'] == 'B') == 106
    assert sum(1 for i in items if i['discipline'] == 'C') == 33
    assert sum(1 for i in items if i['discipline'] == 'D') == 11


@pytest.mark.skipif(not HAS_XLSX, reason='附录2 xlsx 不在本机（knowledge/ 不入 git）')
def test_dash_placeholder_not_treated_as_material():
    """R2：主材名为『——』等的子目，mats 里根本不放这条；C-013 只有『——』→ mats==[]。"""
    items = {i['code']: i for i in parse_workbook(XLSX_DEFAULT)}

    # ZS02-C-013 拆除隔墙：首行主材名 '——'、无续行 → 过滤后不含任何主材
    assert items['ZS02-C-013']['mats'] == []

    # 全局：任何子目的 mats 都不应残留占位主材名
    for code, it in items.items():
        for m in it['mats']:
            assert m['name'] not in NON_MAT_NAMES, (code, m)

    # 消除误判：44 条『——』单子目现在 mats==[]（不再被当作含未定价主材）
    empty = [c for c, it in items.items() if it['mats'] == []]
    assert len(empty) == 44

    # A-069 的续行『9mm阻燃夹板』是真主材，必须保留（26.25×1.05=27.5625 → 该条属登记表异常）
    a069 = items['ZS02-A-069']
    assert any(m['name'] == '9mm阻燃夹板' and m['price'] == 26.25 and m['consumption'] == 1.05
               for m in a069['mats']), a069['mats']


if __name__ == '__main__':
    # 无 pytest 环境下的降级入口（CLAUDE.md:94 惯例）
    _tests = [
        test_recalc_h_owner_supply_zero_mat,
        test_recalc_h_with_mat_price,
        test_known_anomalies_registry_is_exactly_8,
        test_full_audit_296_items,
        test_dash_placeholder_not_treated_as_material,
    ]
    failed = []
    for fn in _tests:
        if not HAS_XLSX and fn in (test_full_audit_296_items,
                                   test_dash_placeholder_not_treated_as_material):
            print('SKIP {}（xlsx 不在本机）'.format(fn.__name__))
            continue
        try:
            fn()
            print('PASS {}'.format(fn.__name__))
        except AssertionError as exc:
            failed.append((fn.__name__, exc))
            print('FAIL {} -> {}'.format(fn.__name__, exc))
    sys.exit(1 if failed else 0)
