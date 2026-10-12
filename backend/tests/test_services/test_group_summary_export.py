"""ZS02-T02 集团汇总表导出端点回归测试（Task 7）— 重算 + 勾稽 + 待询价/参数拦截。

运行：
  - backend/venv311/bin/python -m pytest backend/tests -q
  - backend/venv311/bin/python -m pytest backend/tests/test_services/test_group_summary_export.py -v

数学契约与前端 docs/tool.html:buildGroupSummary / groupSubPrice 同源（plan Global Constraints）；
跨端黄金值取自 docs/superpowers/tests/group_pricing_test.js H 段同一夹具
（A-009 补价×5m² + D-003×10m²，area=100），容差 0.01。
"""
import asyncio
import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

# 仓库根入 sys.path（scripts/ 需仓库根可见；沿用同目录 test_import_group_benchmark.py 的 shim 惯例）
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.group_export import GroupSummaryRequest             # noqa: E402
from app.services.group_summary_export import GroupSummaryExporter   # noqa: E402
from app.api.v1.endpoints.export import export_group_summary         # noqa: E402
import scripts.import_group_benchmark as gb                          # noqa: E402


# ── 夹具：与 group_pricing_test.js G009/D003 逐字段同值（payload 14 键契约）──────
_A009 = {
    'code': 'ZS02-A-009', 'discipline': 'A', 'section_name': '楼地面工程',
    'name': '瓷砖地面', 'unit': 'm2', 'spec': 'SA级600×600', 'qty': 5, 'work_type': '泥水',
    'lab': 61.65, 'aux': 1.98, 'mech': 0, 'coef': 1, 'conv': 1,
    'mats': [{'name': '瓷砖', 'price': 100, 'unit': 'm2', 'consumption': 1.4469},
             {'name': '1:3干硬性水泥砂浆', 'price': 300, 'unit': 'm3', 'consumption': 0.0147}],
}
_D003 = {
    'code': 'ZS02-D-003', 'discipline': 'D', 'section_name': '单价措施项目',
    'name': '成品保护-PVC保护膜', 'unit': 'm2', 'spec': '厚2mm', 'qty': 10, 'work_type': '油漆',
    'lab': 1.51, 'aux': 0.23, 'mech': 0, 'coef': 1, 'conv': 1,
    'mats': [{'name': 'PVC保护膜', 'price': 2, 'unit': 'm2', 'consumption': 0.95}],
}
SHEET1, SHEET2 = '清单明细', '单位工程计价汇总表'


def build_req():  # 两行夹具：D-003×10 + 补价A-009×5（B=100），area=100
    return GroupSummaryRequest.model_validate({
        'project_name': '天河精装一期',
        'fitout_area': 100,
        'rates': {'mgmt': 0.17, 'profit': 0.12, 'green': 0.13,
                  'baogan': 0.03, 'tax': 0.09, 'coordFee': None},
        'manual_fees': {'overtime_fee': 0, 'contract_change_fee': 0, 'inflation_fee': 0},
        'items': [dict(_D003), dict(_A009)],
    })


# ── brief Step 1（逐字保留）──────────────────────────────────────────────

def test_summary_identity():
    rows = GroupSummaryExporter(build_req()).summary_rows()
    d = {r['label']: r['amount'] for r in rows}
    assert abs(d['税金'] - (d['分部分项'] + d['措施项目'] + d['其他项目']) * 0.09) < 0.01
    assert abs(d['总造价'] - sum(d[k] for k in ('分部分项', '措施项目', '其他项目', '税金'))) < 0.01
    assert abs(d['单方造价'] - d['总造价'] / 100) < 0.01


def test_green_base_excludes_discipline_d():
    # 绿安 = Σ(A类+B类+C类的人工+机械) × 13%，D 类不算基数
    c = GroupSummaryExporter(build_req()).compute()
    assert abs(c['labor_mech_base'] - 308.25) < 0.01     # 只含 (61.65+0)×1×1×5；D 行 (1.51+0)×10 不进
    assert abs(c['green'] - 308.25 * 0.13) < 0.01
    assert abs(c['d_measures'] - 40.779) < 0.01          # D 类合价只进 part2，不进 part1
    assert all(not s['name'].startswith('D') for s in c['sections'])


def test_pending_blocks_export():
    req = build_req(); req.items[1].mats[0].price = None
    with pytest.raises(HTTPException) as e: export_group_summary(req)
    assert e.value.status_code == 400


def test_h_recalc_matches_excel_anchor():
    # 后端重算 D-003 h=4.0779（与 Excel 原值一致，双端公式同源断言）
    exp = GroupSummaryExporter(build_req())
    assert abs(exp.sub_price(exp.req.items[0])['h'] - 4.0779) < 0.001
    assert abs(exp.sub_price(exp.req.items[1])['h'] - 230.6085) < 0.001


# ── 跨端黄金值（group_pricing_test.js H1/H3/H4/H5/H6b/H7b/H8b）───────────────

def test_cross_end_golden_numbers():
    c = GroupSummaryExporter(build_req()).compute()
    assert abs(c['part1'] - 1153.0425) < 0.01
    assert abs(c['labor_mech_base'] - 308.25) < 0.01
    assert abs(c['part2'] - 80.8515) < 0.01
    assert abs(c['part3'] - 9.2475) < 0.01
    assert abs(c['part4'] - 111.8827) < 0.01
    assert abs(c['total'] - 1355.0242) < 0.01
    assert abs(c['per_sqm'] - 13.5502) < 0.01
    # 勾稽：Σ分部小计 = 一
    assert abs(sum(s['amount'] for s in c['sections']) - c['part1']) < 0.01


def test_recalc_same_as_import_script():
    """双端公式同源的仓内实证：与 scripts/import_group_benchmark.recalc_h 逐条对齐。"""
    exp = GroupSummaryExporter(build_req())
    for item in exp.req.items:
        bench = {'lab_price': item.lab, 'aux_cost': item.aux, 'mech_cost': item.mech,
                 'mats': [{'price': m.price, 'consumption': m.consumption} for m in item.mats]}
        assert abs(exp.sub_price(item)['h'] - gb.recalc_h(bench)) < 1e-9


# ── 费率不硬编码：一律走 payload.rates ─────────────────────────────────────

def test_rates_drive_the_math_not_hardcoded():
    req = build_req()
    req.rates.green, req.rates.baogan, req.rates.tax = 0.20, 0.05, 0.10
    c = GroupSummaryExporter(req).compute()
    assert abs(c['part2'] - (40.779 + 308.25 * 0.20)) < 0.01
    assert abs(c['part3'] - 308.25 * 0.05) < 0.01
    assert abs(c['part4'] - (c['part1'] + c['part2'] + c['part3']) * 0.10) < 0.01


def test_rates_missing_keys_fall_back_to_t01_seeds():
    """缺省回落 = T01 种子（0.17/0.12/0.13/0.03/0.09；coordFee 缺省 None），不报错。"""
    req = GroupSummaryRequest.model_validate(
        {'project_name': 'P', 'fitout_area': 100, 'items': [dict(_D003), dict(_A009)]})
    assert (req.rates.mgmt, req.rates.profit, req.rates.green,
            req.rates.baogan, req.rates.tax) == (0.17, 0.12, 0.13, 0.03, 0.09)
    assert req.rates.coordFee is None
    assert req.manual_fees.overtime_fee == 0
    assert req.items[0].coef == 1.0 and req.items[0].conv == 1.0
    # 种子值真的驱动计算（与黄金值同结果，而非空值报错）
    assert abs(GroupSummaryExporter(req).compute()['part3'] - 9.2475) < 0.01
    # 部分缺键同样逐项回落
    req2 = GroupSummaryRequest.model_validate(
        {'fitout_area': 100, 'rates': {'mgmt': 0.2}, 'items': [dict(_A009)]})
    assert req2.rates.mgmt == 0.2 and req2.rates.profit == 0.12 and req2.rates.tax == 0.09


def test_manual_fees_and_coord_fee_enter_part3():
    req = build_req()
    req.rates.coordFee = 50
    req.manual_fees.overtime_fee, req.manual_fees.contract_change_fee = 1000, 500
    c = GroupSummaryExporter(req).compute()
    assert c['coord_configured'] is True
    assert abs(c['coord_amount'] - 5000) < 0.01            # 单价 × 装修面积
    assert abs(c['manual_total'] - 1500) < 0.01
    assert abs(c['part3'] - (9.2475 + 5000 + 1500)) < 0.01


def test_negative_manual_fees_clamped():
    """M-1 同款护栏：负手工费逐项钳 0，不倒扣第三部分。"""
    req = build_req()
    req.rates.coordFee = 50
    req.manual_fees.overtime_fee = -1000
    c = GroupSummaryExporter(req).compute()
    assert abs(c['manual_total']) < 1e-9
    assert abs(c['part3'] - (9.2475 + 5000)) < 0.01


# ── coordFee：null≠0（服务层不计取 + 备注留痕；端点层拦截导出）─────────────────

def test_coord_fee_none_not_counted_and_remarked():
    req = build_req()
    assert req.rates.coordFee is None
    c = GroupSummaryExporter(req).compute()
    assert c['coord_configured'] is False and abs(c['coord_amount']) < 1e-9
    assert abs(c['part3'] - c['baogan']) < 0.01            # 第三部分只剩预算包干
    ws2 = load_workbook(GroupSummaryExporter(req).generate())[SHEET2]
    assert _has_text(ws2, '参数未配置（未计取）')
    assert _amount(ws2, '精装修管理及配合费') == 0


def test_coord_fee_configured_remark_shows_unit_price():
    req = build_req()
    req.rates.coordFee = 50
    ws2 = load_workbook(GroupSummaryExporter(req).generate())[SHEET2]
    assert not _has_text(ws2, '参数未配置（未计取）')
    assert _has_text(ws2, '50 元/m²')
    assert abs(_amount(ws2, '精装修管理及配合费') - 5000) < 0.01


def test_endpoint_blocks_coord_fee_none():
    """裁定 1：coordFee=None → 端点级 400，对甲导出绝不静默漏计配合费。"""
    req = build_req()
    assert req.items[0].mats[0].price is not None          # 非 pending 触发，专测 coordFee 闸
    with pytest.raises(HTTPException) as e:
        export_group_summary(req)
    assert e.value.status_code == 400
    assert e.value.detail.get('error') == 'coord_fee_not_configured'


# ── 端点拦截：面积 / 待询价 ────────────────────────────────────────────────

def test_fitout_area_not_positive_blocks():
    for area in (0, -100):
        req = build_req()
        req.fitout_area = area
        req.rates.coordFee = 50
        with pytest.raises(HTTPException) as e:
            export_group_summary(req)
        assert e.value.status_code == 400
        assert e.value.detail.get('error') == 'fitout_area_required'


def test_pending_detail_carries_deduped_codes():
    req = build_req()
    req.rates.coordFee = 50
    req.items[1].mats[0].price = None
    with pytest.raises(HTTPException) as e:
        export_group_summary(req)
    assert e.value.status_code == 400
    assert e.value.detail['pending'] == ['ZS02-A-009']

    # 同编码两条子目分别待询价 → codes 去重（且不牵连已定价的 D-003）
    dup = GroupSummaryRequest.model_validate({
        'fitout_area': 100, 'rates': {'coordFee': 50},
        'items': [dict(_A009), dict(_A009), dict(_D003)]})
    dup.items[0].mats[0].price = None
    dup.items[1].mats[1].price = None
    with pytest.raises(HTTPException) as e2:
        export_group_summary(dup)
    assert e2.value.detail['pending'] == ['ZS02-A-009']


def test_service_excludes_pending_items_from_all_parts():
    """服务层自洽：pending 子目不进任何部分（端点已前置拦截，此处防绕过口径）。"""
    req = build_req()
    req.items[1].mats[0].price = None
    c = GroupSummaryExporter(req).compute()
    assert abs(c['part1']) < 1e-9 and abs(c['total'] - c['part2'] - c['part3'] - c['part4']) < 0.01
    assert abs(c['d_measures'] - 40.779) < 0.01
    assert c['unpriced'] == 1


def test_f1_pending_excluded_at_item_level_mirror():
    """F1 双向钉：同一「清单行挂 2 个集团子目、其一 pending」的数值夹具（前端平铺后 = 同编码两
    items，qty 同行为 5），断言与 group_pricing_test.js F1a/F1c/F1e 镜像：后端 part1 只含
    已定价子目合价 230.6085×5，unpriced 按子目级计数。"""
    pending_pair = {**_A009, 'mats': [
        {'name': '瓷砖', 'price': None, 'unit': 'm2', 'consumption': 1.4469},
        {'name': '1:3干硬性水泥砂浆', 'price': None, 'unit': 'm3', 'consumption': 0.0147}]}
    req = GroupSummaryRequest.model_validate({
        'project_name': '镜像夹具', 'fitout_area': 100,
        'rates': {'mgmt': 0.17, 'profit': 0.12, 'green': 0.13,
                  'baogan': 0.03, 'tax': 0.09, 'coordFee': None},
        'items': [dict(_A009), pending_pair],   # 同行两子目：一价一 pending（前端 F1 夹具同数值）
    })
    c = GroupSummaryExporter(req).compute()
    assert abs(c['part1'] - 1153.0425) < 2e-6          # = 前端 SUMF1.part1 镜像常数
    assert c['unpriced'] == 1                           # 子目级计数（一条 pending = 1）
    assert abs(c['labor_mech_base'] - 308.25) < 2e-6    # 基数也只认已定价子目的人工
    assert abs(sum(s['amount'] for s in c['sections']) - c['part1']) < 2e-6


def test_endpoint_returns_xlsx_stream():
    req = build_req()
    req.rates.coordFee = 50
    resp = export_group_summary(req)
    assert resp.media_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    cd = resp.headers['content-disposition']
    assert 'attachment' in cd and "filename*=UTF-8''" in cd
    body = asyncio.run(_drain(resp))
    wb = load_workbook(BytesIO(body))
    assert wb.sheetnames == [SHEET1, SHEET2]

# ── HTTP 层（ASGITransport直调）：状态码 + detail 体形状 + 前端真实 payload 不 422 ──

def test_http_layer_status_codes():
    import httpx
    from app.main import app

    async def call(payloads):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as cli:
            out = []
            for p in payloads:
                r = await cli.post('/api/v1/export/group-summary', json=p)
                out.append((r.status_code, r.content))
        return out

    ok = build_req(); ok.rates.coordFee = 50
    pend = build_req(); pend.rates.coordFee = 50; pend.items[1].mats[0].price = None
    area = build_req(); area.fitout_area = 0
    # 前端真实形态：mats 带派生键（idx/pending/label/cost）+ 字符串数字 → 模型容忍，不弹 422
    front = build_req().model_dump(mode='json')
    front['rates']['coordFee'] = 50
    front['items'][1]['lab'] = '61.65'
    front['items'][1]['mats'][0].update({'idx': 0, 'pending': False, 'label': '', 'cost': 144.69})
    front['items'][1]['mats'][1]['price'] = None        # 造一条甲供待询价位
    results = asyncio.run(call([ok.model_dump(mode='json'),
                                pend.model_dump(mode='json'),
                                area.model_dump(mode='json'),
                                front]))
    (s_ok, b_ok), (s_pend, b_pend), (s_area, b_area), (s_front, b_front) = results
    assert s_ok == 200 and b_ok[:2] == b'PK', '应返回 xlsx 二进制流'
    assert s_pend == 400 and 'ZS02-A-009' in b_pend.decode()
    assert s_area == 400 and b'fitout_area_required' in b_area
    assert s_front == 400 and b'ZS02-A-009' in b_front   # 前端形态同样走 pending 拦截（非 422）


# ── 工作簿结构：2 sheet + 合计/汇总公式单元格（只求值口径存在，不代入计算）──────

def test_generate_workbook_structure_and_formulas():
    wb = load_workbook(GroupSummaryExporter(build_req()).generate())
    assert wb.sheetnames == [SHEET1, SHEET2]
    ws1, ws2 = wb[SHEET1], wb[SHEET2]
    # sheet1 合计行 = SUM(数据行合价)，口径同方式一（只汇总父行）
    total = _amount(ws1, '合计', col_label='合价')
    assert isinstance(total, str) and total.startswith('=SUM(')
    # sheet2：四 =（一+二+三）× 税率；五 = 一+二+三+四；单方 = 五 ÷ 面积
    m = get_column_letter(_col_index(ws2, '金额（元）'))
    assert _amount(ws2, '税金').startswith(f'=({m}') and _amount(ws2, '税金').endswith('*0.09')
    assert _amount(ws2, '总造价').startswith(f'={m}')
    assert _amount(ws2, '单方造价').endswith('/100')
    assert _has_text(ws2, '暂列金额') and _has_text(ws2, '集团规定不予计取')


def test_sheet1_columns_are_zs02_ah_decomposition():
    ws1 = load_workbook(GroupSummaryExporter(build_req()).generate())[SHEET1]
    header = [c.value for c in ws1[2]]
    for label in ('A 人工', 'B 主材费', 'D 辅材', 'E 机械', 'F 管理费', 'G 利润', 'H 综合单价', '合价'):
        assert label in header, header
    row = _row_index(ws1, 'ZS02-A-009')
    lab_l = get_column_letter(_col_index(ws1, 'A 人工'))
    mech_l = get_column_letter(_col_index(ws1, 'E 机械'))
    mgmt_c = ws1.cell(row=row, column=_col_index(ws1, 'F 管理费'))
    profit_c = ws1.cell(row=row, column=_col_index(ws1, 'G 利润'))
    # 管理费/利润基数 = 人工+机械（不是主材/辅材），费率来自 payload 而非写死在分支里
    assert mgmt_c.value == f'=({lab_l}{row}+{mech_l}{row})*0.17', mgmt_c.value
    assert profit_c.value == f'=({lab_l}{row}+{mech_l}{row})*0.12', profit_c.value
    # 主材费按消耗量口径：100×1.4469 + 300×0.0147
    assert abs(ws1.cell(row=row, column=_col_index(ws1, 'B 主材费')).value - 149.10) < 0.001


# ── 小工具 ──────────────────────────────────────────────────────────────

async def _drain(resp):
    return b''.join([chunk async for chunk in resp.body_iterator])


def _has_text(ws, needle):
    for row in ws.iter_rows(values_only=True):
        for v in row:
            if isinstance(v, str) and needle in v:
                return True
    return False


def _col_index(ws, label, header_row=2):
    for cell in ws[header_row]:
        if cell.value == label:
            return cell.column
    raise AssertionError('列不存在：' + label)


def _row_index(ws, needle):
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if isinstance(v, str) and needle in v:
                return r
    raise AssertionError('行不存在：' + needle)


def _amount(ws, label, col_label='金额（元）'):
    """按「名称」定位行，取该行金额列的值（sheet2 默认；sheet1 传 col_label）。"""
    col = _col_index(ws, col_label) if col_label else 3
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if isinstance(v, str) and v.strip() == label:
                return ws.cell(row=r, column=col).value
    raise AssertionError('行不存在：' + label)
