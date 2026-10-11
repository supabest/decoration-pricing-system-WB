#!/usr/bin/env python3
"""ZS02 附录2《广州地区房地产开发项目精装修工程基准价》导入脚本

功能：
  1. 解析 xlsx 的 4 张清单 sheet（A 精装修 / B 水电 / C 拆除 / D 措施），产出
     与 `group_benchmark_items` 表列同名的 dict 列表（296 条 = A146+B106+C33+D11）。
  2. 按集团公式重算综合单价 H，与 Excel 原 H 逐条审计（阈值 |Δ| ≤ 0.01）。
  3. `--write` 经 Supabase REST upsert 入库（PostgREST，不依赖 SQLAlchemy）。

集团公式（docs/superpowers/specs/2026-10-11-group-benchmark-pricing-design.md）：
    管理费 F = (人工A + 机械E) × 17%
    利润   G = (人工A + 机械E) × 12%
    综合单价 H = A + Σ(Bi × Ci) + D + E + F + G      （Bi=主材单价，Ci=消耗量，损耗已含于 Ci）

Excel 列位（sheet A/B/C/D 相同，0-based）：
    0序号 1名称 2特征 3单位 4工种 5人工 6主材名 7主材价 8主材单位 9消耗量
    10辅材 11机械 12管理费 13利润 14综合单价
    （sheet A 有 16324 个垃圾列，必须 iter_rows(max_col=15) 截断）

用法：
    backend/venv311/bin/python scripts/import_group_benchmark.py --dry-run
    SUPABASE_SERVICE_KEY=... backend/venv311/bin/python scripts/import_group_benchmark.py --write

CLI 契约（--dry-run/--write、SUPABASE_SERVICE_KEY 环境变量、退出码语义）来自 brief；
输出风格（argparse / 进度打印 / 📥✅❌ 前缀）参照 scripts/import_benchmark_prices.py。
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

import openpyxl

# ── 数据源与目标 ────────────────────────────────────────────────────────────
XLSX_DEFAULT = os.path.join(os.path.dirname(__file__), '..',
    'knowledge/Group benchmark price/附录2：广州地区房地产开发项目精装修工程基准价.xlsx')

SHEETS = [('ZS02-A-精装修工程', 'A'), ('ZS02-B- 精装修水电', 'B'),
          ('ZS02-C-拆除工程', 'C'), ('ZS02-D-措施项目费', 'D')]

SUPABASE_URL_DEFAULT = 'https://lnvtykghcpsjpwczbqsm.supabase.co'
TABLE = 'group_benchmark_items'

# ── 常量 ────────────────────────────────────────────────────────────────────
MAX_COL = 15                                  # 只读前 15 列
DELTA_THRESHOLD = 0.01                        # 审计阈值，禁止放宽
DEFAULT_RATES = {'mgmt': 0.17, 'profit': 0.12}

CODE_RE = re.compile(r'^ZS02-[A-D]-\d{3}$')
SEC_RE = re.compile(r'^([一二三四五六七八九十]+|（[一二三四五六七八九十]+）)$')

# 源表数字列里的「杂质」写法：全角破折号（=该项无金额）、长破折号、半角横线、斜杠、空串
BLANK_TOKENS = ('', '——', '—', '－', '-', '–', '/', '无')

# I2：不可解析（非 BLANK 且 float() 失败）的数字单元格记录 (列位, 原值)；
#     main 据其长度决定是否放行（>0 → 审计未过 exit 1，与阈值同级护栏）。
PARSE_FAILURES = []

# 表列顺序（与 data/migrations/group_benchmark_migration.sql 一致）
COLUMNS = ['code', 'discipline', 'section_name', 'name', 'spec', 'unit', 'work_type',
           'lab_price', 'mats', 'aux_cost', 'mech_cost', 'is_owner_supply',
           'raw_composite', 'source_row']

# ── 源数据异常登记（R1 选项A：登记制）───────────────────────────────────────────
# 引擎口径一律以 T01 公式重算为准；raw_composite 存 Excel 原值仅作对账留档，
# 偏差不得算进「通过」口径。审计闸门：|Δ|>0.01 的条目必须全部命中下表且仅这 8 条。
KNOWN_ANOMALIES = {
    'ZS02-A-069': '源表 H 公式漏算续行主材（9mm阻燃夹板 26.25×1.05=27.5625）',
    'ZS02-A-070': '源表 H 公式漏算续行主材（9mm阻燃夹板 26.25×1.05=27.5625）',
    'ZS02-B-100': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
    'ZS02-B-102': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
    'ZS02-B-103': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
    'ZS02-B-104': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
    'ZS02-B-105': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
    'ZS02-B-106': '管理费/利润列手填值隐含 15%+10%，违反 T01 17%/12%',
}
# R3：A-补01 / A-补02（楼板隔音垫 / 地面隔声涂料）按 CODE_RE 排除、不入库，维持 296 条口径；
#     补录子目未入库待集团确认。

# R2：「——」不是主材——主材名命中下列占位符的行，mats 里根本不放这条（材料费已含于 A/D/E），
#     用以消除 44 条「待询价」误判。注意 A-069 的续行「9mm阻燃夹板」是真主材，必须保留。
NON_MAT_NAMES = {'', '——', '-', '—'}


# ── 取数助手 ────────────────────────────────────────────────────────────────
def _txt(x):
    """单元格 → 去首尾空白的字符串（None → ''）。"""
    return str(x).strip() if x is not None else ''


def _flat(x):
    """文本单元格 → 去掉内嵌换行（主材名/单位入库后用于列表展示与模糊匹配）。"""
    return _txt(x).replace('\n', '').replace('\r', '')


def _num(x, default=None, col=None):
    """数字单元格容错取数。

    None / '' / '——' 等占位写法 → default；数字字符串（'108.46'）→ float。
    非 BLANK 且 float() 失败（如 '5%'）→ 记录 (col, 原值) 到 PARSE_FAILURES 后
    回落 default；此类静默数据丢失由 main 的审计闸门拦截（I2）。
    """
    if x is None:
        return default
    if isinstance(x, bool):
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(',', '').replace('，', '')
    if s in BLANK_TOKENS:
        return default
    try:
        return float(s)
    except ValueError:
        PARSE_FAILURES.append((col, str(x)))
        return default


# ── 解析 ────────────────────────────────────────────────────────────────────
def _is_real_mat_name(name):
    """主材名非空且不属于占位符（'——'/'-'/'—'）才算真主材（R2）。"""
    return name not in NON_MAT_NAMES


def _mk_mat(row):
    """主材行（序号列可为空的续行）→ {name, price, unit, consumption}。

    price 为 None 即「甲供/未限价」（计价说明第 4 条：已列明主材名称及消耗量但无
    主材价格 → 主材价按计价办法第十五条按实计取），前端据此置「待询价」。
    """
    return {
        'name': _flat(row[6]),
        'price': _num(row[7], col=7),                   # '——'/''/None → None（未定价）
        'unit': _flat(row[8]),
        'consumption': _num(row[9], default=0, col=9),  # '——'/None → 0
    }


def _mk_item(disc, section, ri, row):
    """子目起始行（col0 命中 ZS02-x-nnn）→ 表列同名字典。"""
    c = [_txt(x) for x in row]
    spec = c[2]                                     # 特征多行文本，保留换行
    first_mat = _mk_mat(row)
    return {
        'code': c[0],
        'discipline': disc,
        'section_name': section.replace('\n', ''),
        'name': c[1].replace('\n', ''),
        'spec': spec,
        'unit': c[3].replace('\n', ''),
        'work_type': c[4].replace('\n', ''),
        'lab_price': _num(row[5], default=0, col=5),    # A 人工，'——' → 0
        # B×C；'——'/'-'/'—' 等非主材名不入库（R2），只有占位主材的子目 mats==[]；续行追加
        'mats': [first_mat] if _is_real_mat_name(first_mat['name']) else [],
        'aux_cost': _num(row[10], default=0, col=10),   # D 辅材
        'mech_cost': _num(row[11], default=0, col=11),  # E 机械
        'is_owner_supply': '甲供' in spec,
        'raw_composite': _num(row[14], default=0, col=14),  # Excel 原 H（校验锚点）
        'source_row': ri,
    }


def parse_workbook(path):
    """解析 xlsx 四张清单 sheet → list[dict]（字段名与 group_benchmark_items 列一致）。"""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    items = []
    try:
        for sheet, disc in SHEETS:
            ws = wb[sheet]
            section = ''
            cur = None
            for ri, row in enumerate(ws.iter_rows(max_col=MAX_COL, values_only=True), 1):
                row = tuple(row) + (None,) * (MAX_COL - len(row))
                c = [_txt(x) for x in row]
                if CODE_RE.match(c[0]):
                    cur = _mk_item(disc, section, ri, row)
                    items.append(cur)
                elif SEC_RE.match(c[0]) and c[1]:
                    section = c[1]                   # 分部标题行
                    cur = None                       # M-sec：分部切换，续行不得跨分部挂靠
                elif cur and not c[0] and _is_real_mat_name(_flat(row[6])):
                    cur['mats'].append(_mk_mat(row))   # 多主材续行（如 A-009 的干硬性砂浆）；'——' 不算主材
    finally:
        wb.close()
    return items


# ── 重算与审计 ──────────────────────────────────────────────────────────────
def recalc_h(item, rates=None):
    """H = A + Σ(Bi×Ci) + D + E + (A+E)×mgmt + (A+E)×profit。"""
    r = dict(DEFAULT_RATES)
    if rates:
        r.update(rates)
    A, E = item['lab_price'] or 0, item['mech_cost'] or 0
    mat = sum((m['price'] or 0) * (m['consumption'] or 0) for m in item['mats'])
    F, G = (A + E) * r['mgmt'], (A + E) * r['profit']
    return A + mat + (item['aux_cost'] or 0) + E + F + G


def audit(items, rates=None):
    """逐条重算 → [(code, 重算H, 原H, Δ, item)]，Δ = 重算H − 原H。"""
    rows = []
    for it in items:
        h = recalc_h(it, rates)
        rows.append((it['code'], h, it['raw_composite'], h - it['raw_composite'], it))
    return rows


def _fmt_row(code, h, raw, delta, flag=''):
    return '{:<12} {:>12.4f} {:>12.4f} {:>10.4f} {}'.format(code, h, raw, delta, flag)


def classify_anomalies(bad_codes):
    """bad_codes: set。返回 (unknown, missing)：
    unknown = |Δ|>阈值但未登记的偏差（闸门必须拦下）；
    missing = 已登记但本次未复现（计数对不上，同样拦下）。"""
    registered = set(KNOWN_ANOMALIES)
    bad_codes = set(bad_codes)
    unknown = sorted(bad_codes - registered)
    missing = sorted(registered - bad_codes)
    return unknown, missing


def print_audit(items, rates=None, threshold=DELTA_THRESHOLD):
    """打印审计表 + 摘要 + 超阈值明细（登记条目列为 WARN 并打 reason）。
    返回 (bad, unknown, missing)。"""
    rows = audit(items, rates)
    bad = [r for r in rows if abs(r[3]) > threshold]
    bad_codes = {r[0] for r in bad}
    unknown, missing = classify_anomalies(bad_codes)

    print('=' * 78)
    print('ZS02 附录2 综合单价 H 重算审计  阈值 |Δ| ≤ {}  '
          '（引擎口径：T01 公式重算；raw_composite 存 Excel 原值仅作对账留档）'.format(threshold))
    print('=' * 78)
    print('{:<12} {:>12} {:>12} {:>10} {}'.format('code', '重算H', '原H', 'Δ', '判定'))
    for code, h, raw, delta, _ in rows:
        if abs(delta) <= threshold:
            flag = 'ok'
        elif code in KNOWN_ANOMALIES:
            flag = '⚠️ WARN(已登记)'
        else:
            flag = '❌ 未登记偏差'
        print(_fmt_row(code, h, raw, delta, flag))
    print('-' * 78)

    by_disc = {}
    for it in items:
        by_disc[it['discipline']] = by_disc.get(it['discipline'], 0) + 1
    print('-' * 78)
    print('分科条数：' + '  '.join('{}={}'.format(k, by_disc[k]) for k in sorted(by_disc)))
    print('mats==[] 子目（主材全为『——』等占位符，已按 R2 过滤）：{} 条；'
          '含续行多主材子目：{} 条'.format(
              sum(1 for i in items if not i['mats']),
              sum(1 for i in items if len(i['mats']) > 1)))
    max_delta = max((abs(r[3]) for r in rows), default=0.0)
    print('最大 |Δ| = {:.4f}'.format(max_delta))

    known_n = sum(1 for r in bad if r[0] in KNOWN_ANOMALIES)
    if bad:
        print('-' * 78)
        rr = dict(DEFAULT_RATES)
        if rates:
            rr.update(rates)
        print('超阈值 {} 条明细（重算口径 A+Σ(Bi×Ci)+D+E+F+G，F={}%、G={}% ×(A+E)）：'.format(
            len(bad), int(round(rr['mgmt'] * 100)), int(round(rr['profit'] * 100))))
        for code, h, raw, delta, it in bad:
            registered = code in KNOWN_ANOMALIES
            print('  {} [{}] sheet={} 行={} 分部={}'.format(
                code, 'WARN 已登记' if registered else '❌ 未登记',
                it['discipline'], it['source_row'], it['section_name']))
            print('     A人工={} D辅材={} E机械={} 原H={:.4f} 重算H={:.4f} Δ={:+.4f}'.format(
                it['lab_price'], it['aux_cost'], it['mech_cost'], raw, h, delta))
            print('     mats={}'.format(json.dumps(it['mats'], ensure_ascii=False)))
            print('     原 H 隐含综合取费率（管理+利润）/（A+E）={}'.format(_implied_rate(it)))
            if registered:
                print('     reason={}'.format(KNOWN_ANOMALIES[code]))
    print('-' * 78)
    print('共 {} 条：{} ok，{} WARN(命中登记表)，{} 未登记'.format(
        len(items), len(items) - len(bad), known_n, len(unknown)))
    if missing:
        print('   登记表 {} 条本次未复现：{}'.format(len(KNOWN_ANOMALIES), missing))
    return bad, unknown, missing


def _implied_rate(item):
    """由 Excel 原 H 反推综合取费率：(原H − A − Σ(Bi×Ci) − D − E) / (A+E)。

    用于区分两类超阈值根因：取费硬编码（费率≠29%）与 H 公式漏项（费率=29% 但
    Σ(Bi×Ci) 少算续行主材）。A+E=0 时无法判定 → 'n/a'。
    """
    A, E = item['lab_price'] or 0, item['mech_cost'] or 0
    mat = sum((m['price'] or 0) * (m['consumption'] or 0) for m in item['mats'])
    base = A + E
    if not base:
        return 'n/a（A+E=0）'
    return round((item['raw_composite'] - A - mat - (item['aux_cost'] or 0) - E) / base, 5)


# ── 写库（Supabase REST / PostgREST upsert） ────────────────────────────────
def _to_payload(item):
    """表列 → PostgREST JSON 行（mats 作为 JSONB 直接送嵌套数组，由服务端转 jsonb）。"""
    return {k: item[k] for k in COLUMNS}


def write_supabase(items, batch_size=100):
    """POST {SUPABASE_URL}/rest/v1/group_benchmark_items，Prefer: resolution=merge-duplicates。"""
    service_key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not service_key:
        raise RuntimeError(
            '缺少环境变量 SUPABASE_SERVICE_KEY（service role key），无法写库；'
            '用法：SUPABASE_SERVICE_KEY=... python scripts/import_group_benchmark.py --write')
    base = os.environ.get('SUPABASE_URL', SUPABASE_URL_DEFAULT).rstrip('/')
    url = '{}/rest/v1/{}'.format(base, TABLE)
    ctx = ssl.create_default_context()

    total = 0
    for start in range(0, len(items), batch_size):
        chunk = [_to_payload(i) for i in items[start:start + batch_size]]
        body = json.dumps(chunk, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('apikey', service_key)
        req.add_header('Authorization', 'Bearer ' + service_key)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Prefer', 'resolution=merge-duplicates')
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                resp.read()
                print('  ✅ 批次 {}-{} → HTTP {}'.format(start + 1, start + len(chunk), resp.status))
        except urllib.error.HTTPError as e:
            raise RuntimeError('批次 {}-{} → HTTP {} {}'.format(
                start + 1, start + len(chunk), e.code, e.read().decode('utf-8', 'replace')[:500]))
        except urllib.error.URLError as e:
            raise RuntimeError('网络错误：{}'.format(e.reason))
        total += len(chunk)
    print('✅ upsert 完成：{} 条 → {}'.format(total, url))
    return total


# ── CLI ─────────────────────────────────────────────────────────────────────
def main(argv=None):
    parser = argparse.ArgumentParser(
        description='ZS02 附录2 集团基准价清单导入（解析 + 296 条 H 重算审计 + 写库）')
    parser.add_argument('--xlsx', default=XLSX_DEFAULT, help='附录2 xlsx 路径')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--dry-run', action='store_true', help='只解析并打印 H 重算审计表')
    g.add_argument('--write', action='store_true',
                   help='审计通过后经 Supabase REST upsert 写库（需 SUPABASE_SERVICE_KEY）')
    parser.add_argument('--batch-size', type=int, default=100, help='--write 每批行数')
    args = parser.parse_args(argv)

    if not (args.dry_run or args.write):
        parser.error('需指定 --dry-run 或 --write')
    if not os.path.exists(args.xlsx):
        print('❌ 数据源不存在：{}（knowledge/ 不入 git，请在持有该文件的机器上运行）'.format(args.xlsx))
        return 1

    print('📥 解析 {}'.format(os.path.relpath(args.xlsx)))
    items = parse_workbook(args.xlsx)
    print('   解析得 {} 条子目'.format(len(items)))

    bad, unknown, missing = print_audit(items)

    # I2 解析护栏：任何非 BLANK 却无法解析的数字单元格，视为审计未过（与阈值同级）。
    n_unparsed = len(PARSE_FAILURES)
    print('未能解析的数字单元格: {} 个'.format(n_unparsed))
    if n_unparsed:
        print('❌ 审计闸门未过：{} 个数字单元格无法解析（口径性数据丢失，不写库）：{}'.format(
            n_unparsed, PARSE_FAILURES[:10]))
        return 1

    # R1 审计闸门：|Δ|>0.01 必须全部命中登记表且仅这 8 条；否则 exit 1。
    if unknown:
        print('❌ 审计闸门未过：{} 条 |Δ|>{} 未命中登记表：{}（不写库）'.format(
            len(unknown), DELTA_THRESHOLD, unknown))
        return 1
    if missing:
        print('❌ 审计闸门未过：登记表 {} 条本次未全部复现，缺：{}（计数对不上，不写库）'.format(
            len(KNOWN_ANOMALIES), missing))
        return 1
    print('✅ 审计通过：{} 条 |Δ|≤{}，另 {} 条 |Δ|>{} 全部命中 KNOWN_ANOMALIES 登记表'
          '（以重算 H 为准入库，raw_composite 留档 Excel 原值）'.format(
              len(items) - len(bad), DELTA_THRESHOLD, len(KNOWN_ANOMALIES), DELTA_THRESHOLD))

    if args.write:
        print('📤 写库（Supabase REST upsert，code 为主键冲突列）')
        try:
            write_supabase(items, batch_size=args.batch_size)
        except RuntimeError as e:
            print('❌ 写库失败：{}'.format(e))
            return 1
    else:
        print('ℹ️ --dry-run：未写库。写库请执行 '
              'SUPABASE_SERVICE_KEY=... python scripts/import_group_benchmark.py --write')
    return 0


if __name__ == '__main__':
    sys.exit(main())
