"""统一数据源：本地加密快照 / Supabase 云端价表。

目标是让 WorkBuddy 项目在「项目公共授权」下直接读云端基准价，
所有成员共用同一份数据，本机不保存任何价表。

保密约束（不可放宽）：
- 价表只在进程内存，不落盘、不写日志；prepare 仍只产出无价格候选。
- 凭据只从环境变量读取，不写文件、不进仓库、不回显到任何输出。
- 云端取数失败必须明确报错，**不静默回退本地旧快照**（避免用过期价），
  只有显式设置 WB_PRICING_FALLBACK=1 才允许回退。

环境变量（由 WorkBuddy 项目公共授权 / 运行环境注入，勿写进仓库）：
  WB_PRICING_SOURCE        supabase | snapshot，默认 snapshot（向后兼容）
  WB_SUPABASE_URL          REST 根地址；可直连 https://<id>.supabase.co，
                           也可走同源反代 https://<site>/sb
  WB_SUPABASE_ANON_KEY     publishable / anon key（apikey 头）
  WB_SUPABASE_TOKEN        authenticated JWT（Authorization: Bearer）
  WB_SUPABASE_EMAIL        可选；与下一项配合，用密码换取 JWT
  WB_SUPABASE_PASSWORD     可选
  WB_PRICING_FALLBACK      设为 1 时，云端失败才允许回退本地快照
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any

import snapshot

PAGE_LIMIT = 5000

# 平台注入的变量名可能因连接器版本不同，做兼容读取（只读，不回显）
_ENV_ALIASES = {
    "url": ("WB_SUPABASE_URL", "SUPABASE_URL"),
    "anon": ("WB_SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEY"),
    "token": ("WB_SUPABASE_TOKEN", "SUPABASE_ACCESS_TOKEN", "WB_SUPABASE_JWT"),
    "email": ("WB_SUPABASE_EMAIL", "SUPABASE_EMAIL"),
    "password": ("WB_SUPABASE_PASSWORD", "SUPABASE_PASSWORD"),
}

# 库表字段 → 技能内部字段。云端表结构可能与历史快照命名不同，逐项回退。
_BENCH_ALIASES = {
    "internal_code": ("internal_code", "code", "item_code", "quota_code"),
    "trade_team": ("trade_team", "team", "work_team", "trade"),
    "work_type": ("work_type", "craft", "category", "type"),
    "item_name": ("item_name", "name", "work_name", "item"),
    "spec": ("spec", "specification", "feature", "item_spec"),
    "unit": ("unit", "measure_unit", "uom"),
    "unit_price": ("unit_price", "price", "labor_price", "labor_cost"),
    "remark": ("remark", "note", "remarks", "memo"),
    "aux_rule_type": ("aux_rule_type", "rule_type", "calc_method"),
    "aux_fixed_k": ("aux_fixed_k", "fixed_k", "fixed_price"),
    "aux_rate_detail": ("aux_rate_detail", "rate_detail", "rule_config"),
    "waste_rate": ("waste_rate", "loss_rate", "wastage"),
}


def _env(key: str) -> str:
    for name in _ENV_ALIASES[key]:
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return ""


def source_name() -> str:
    return os.environ.get("WB_PRICING_SOURCE", "snapshot").strip().lower()


def is_cloud() -> bool:
    return source_name() == "supabase"


class SourceError(RuntimeError):
    """云端取数失败。刻意不带凭据或响应正文，避免泄露。"""


def _base_url() -> str:
    url = _env("url").rstrip("/")
    if not url:
        raise SourceError("未配置 WB_SUPABASE_URL（项目公共授权应注入 Supabase REST 地址）")
    return url


@lru_cache(maxsize=1)
def _access_token() -> str:
    """优先用注入的 JWT；否则在提供了专用只读账号时用密码换一次。"""
    token = _env("token")
    if token:
        return token
    email, password = _env("email"), _env("password")
    if not (email and password):
        raise SourceError(
            "缺少 authenticated 身份：需要 WB_SUPABASE_TOKEN，或公共授权专用的"
            " WB_SUPABASE_EMAIL / WB_SUPABASE_PASSWORD（匿名 key 读不到价表，RLS 已收紧）"
        )
    payload = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        _base_url() + "/auth/v1/token?grant_type=password",
        data=payload,
        headers={
            "apikey": _env("anon"),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        raise SourceError(f"专用账号换取访问令牌失败：{type(exc).__name__}") from None
    tok = data.get("access_token") if isinstance(data, dict) else None
    if not tok:
        raise SourceError("专用账号换取访问令牌失败：响应缺少 access_token")
    return tok


def _request(path: str, extra: dict | None = None, method: str = "GET",
             data: bytes | None = None) -> tuple[int, dict, bytes]:
    anon = _env("anon")
    if not anon:
        raise SourceError("未配置 apikey（WB_SUPABASE_ANON_KEY / SUPABASE_ANON_KEY）")
    # extra 若显式覆盖 Authorization（补库用管理员令牌），就不必再取只读身份
    token = _env("token") if (extra or {}).get("Authorization") else _access_token()
    headers = {
        "apikey": anon,
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "WorkBuddy-Pricing/1.0",
        **(extra or {}),
    }
    req = urllib.request.Request(_base_url() + path, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as exc:
        raise SourceError(f"Supabase 连接失败：{type(exc).__name__}") from None


def fetch_table(table: str, select: str = "*", limit: int = PAGE_LIMIT) -> list[dict] | None:
    """读一张表；表不存在（404）返回 None，其它错误抛 SourceError。"""
    qs = urllib.parse.urlencode({"select": select, "limit": limit})
    status, _headers, body = _request(f"/rest/v1/{table}?{qs}")
    if status == 404:
        return None
    if status not in (200, 206):
        raise SourceError(f"读取 {table} 失败：HTTP {status}")
    try:
        rows = json.loads(body)
    except Exception as exc:
        raise SourceError(f"读取 {table} 失败：响应不是 JSON") from exc
    if not isinstance(rows, list):
        raise SourceError(f"读取 {table} 失败：响应不是数组")
    return rows


def probe() -> list[dict]:
    """只读体检：表是否存在、可读行数、字段名。永不返回任何价格数值。

    状态必须能区分三类情况，否则管理员无法判断阶段 1 卡在哪一步：
      ok      —— 表在、有可读行（字段名非空）
      empty   —— 表在但 0 行可读（多半未带 authenticated 身份，RLS 已收紧）
      missing —— REST 404，表还没建（执行 sql/wb_supabase_setup.sql）
      error   —— 连接/取身份失败（检查 REST 地址与授权注入）
    """
    tables = (
        "benchmark_items", "group_benchmark_items", "group_pricing_rules",
        "material_prices", "main_material_catalog", "main_material_categories",
        "main_material_prices", "auxiliary_rules", "waste_rates",
        "aux_excel_items", "benchmark_aux_mapping",
    )
    out = []
    for t in tables:
        qs = urllib.parse.urlencode({"select": "*", "limit": 1})
        try:
            status, headers, body = _request(f"/rest/v1/{t}?{qs}", {"Prefer": "count=exact"})
        except SourceError as exc:
            out.append({"table": t, "status": "error", "count": "?",
                        "fields": [], "hint": str(exc)[:120]})
            continue
        cr = next((v for k, v in headers.items() if k.lower() == "content-range"), "")
        count = cr.split("/")[-1] if "/" in cr else "?"
        fields = []
        if status in (200, 206):
            try:
                arr = json.loads(body)
                fields = list(arr[0].keys())[:16] if arr else []
            except Exception:
                pass
        if status == 404:
            state, hint = "missing", "表未创建：执行 sql/wb_supabase_setup.sql"
        elif status not in (200, 206):
            state, hint = f"http_{status}", "检查 REST 地址与授权身份"
        elif not fields:
            state, hint = "empty", "0 行可读：多半未带 authenticated 身份（RLS 已收紧）或表为空"
        else:
            state, hint = "ok", ""
        out.append({
            "table": t,
            "status": state,
            "count": count,
            "fields": fields,
            "hint": hint,
        })
    return out


def preflight() -> dict:
    """阶段 1 验收：只回报运行环境「有没有」配置，绝不回显任何值。

    云端任务目前没有 secrets / env 注入字段，本函数用于判断脚本能否直连 REST，
    以及管理员本机临时验证时凭据是否齐备。
    """
    url = _env("url")
    if not url:
        channel = "none"
    elif ".supabase.co" in url:
        channel = "direct"
    else:
        channel = "proxy"
    if _env("token"):
        identity = "jwt"
    elif _env("email") and _env("password"):
        identity = "password"
    else:
        identity = "none"
    return {
        "source": source_name(),
        "url_configured": bool(url),
        "channel": channel,
        "anon_key": bool(_env("anon")),
        "identity": identity,
        "sync_token": bool(os.environ.get("WB_SUPABASE_SYNC_TOKEN", "").strip()),
        "fallback": os.environ.get("WB_PRICING_FALLBACK", "").strip() == "1",
    }


def _pick(row: dict, *names: str, default: Any = None) -> Any:
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return default


def _normalize_items(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        item = {key: _pick(r, *aliases) for key, aliases in _BENCH_ALIASES.items()}
        item["internal_code"] = str(item["internal_code"] or "").strip()
        item["item_name"] = str(item["item_name"] or "").strip()
        item["trade_team"] = str(item["trade_team"] or "").strip()
        item["unit_price"] = float(item["unit_price"] or 0)
        item["aux_fixed_k"] = float(item["aux_fixed_k"] or 0)
        item["waste_rate"] = float(item["waste_rate"] or 0)
        if item["internal_code"]:
            out.append(item)
    return out


def _waste_rates(items: list[dict], table_rows: list[dict] | None) -> dict:
    if table_rows is not None:
        rates = {}
        for r in table_rows:
            code = _pick(r, "internal_code", "code", "item_code")
            val = _pick(r, "waste_rate", "loss_rate", "rate", "value")
            if code not in (None, ""):
                rates[str(code).strip()] = float(val or 0)
        if rates:
            return rates
    return {i["internal_code"]: i["waste_rate"] for i in items if i["waste_rate"]}


def _material_prices(rows: list[dict] | None) -> dict:
    lib = {}
    for r in rows or []:
        name = _pick(r, "material_name", "name", "item_name", "material")
        price = _pick(r, "price", "unit_price", "price_ex_tax", "info_price")
        if name not in (None, ""):
            try:
                lib[str(name).strip()] = float(price or 0)
            except (TypeError, ValueError):
                continue
    return lib


def _aux_items(rows: list[dict] | None) -> list[dict]:
    out = []
    for r in rows or []:
        out.append({
            "code": str(_pick(r, "code", "internal_code", "item_code", default="") or "").strip(),
            "name": str(_pick(r, "name", "item_name", "material_name", default="") or "").strip(),
            "unit": str(_pick(r, "unit", default="") or "").strip(),
            "work_type": str(_pick(r, "work_type", "craft", default="") or "").strip(),
            "rate_mats": _pick(r, "rate_mats", "rule_config", "items", default=[]),
            "rule_type": str(_pick(r, "rule_type", "calc_method", "aux_rule_type", default="") or "").strip(),
            "source_sheet": str(_pick(r, "source_sheet", default="") or "").strip(),
        })
    return out


@lru_cache(maxsize=1)
def load_snapshot() -> dict:
    """统一入口：结构与 snapshot.load_snapshot() 完全一致。"""
    if not is_cloud():
        return snapshot.load_snapshot()
    try:
        items_raw = fetch_table("benchmark_items")
        if items_raw is None:
            raise SourceError("云端缺少 benchmark_items 表")
        items = _normalize_items(items_raw)
        if not items:
            raise SourceError("benchmark_items 读到 0 行（多半是未带 authenticated 身份，RLS 已收紧）")

        waste_rows = fetch_table("waste_rates")
        mat_rows = fetch_table("material_prices")
        aux_rows = fetch_table("aux_excel_items")
        if aux_rows is None:
            aux_rows = fetch_table("auxiliary_rules")

        data = snapshot.empty()
        data["benchmark_items"] = items
        data["waste_rates"] = _waste_rates(items, waste_rows)
        data["material_prices"] = _material_prices(mat_rows)
        data["aux_excel_items"] = _aux_items(aux_rows)
        # 主材三表：阶段 2 建立子目↔主材映射时消费，先原样带入内存
        data["main_material_prices"] = fetch_table("main_material_prices") or []
        data["main_material_catalog"] = fetch_table("main_material_catalog") or []
        data["main_material_categories"] = fetch_table("main_material_categories") or []
        data["generated_at"] = "supabase-live"
        return data
    except SourceError:
        if os.environ.get("WB_PRICING_FALLBACK", "").strip() == "1":
            return snapshot.load_snapshot()
        raise


def seed_payload_from_snapshot() -> dict:
    """把加密快照里「云端缺失」的三类辅材/损耗数据导出为上云载荷。

    仅供一次性补库使用；返回值只在内存，调用方决定写到哪个云端位置，
    本函数不落盘、不打印任何价格。
    """
    data = snapshot.load_snapshot()
    waste = data.get("waste_rates") or {}
    mapping = []
    for it in data.get("benchmark_items") or []:
        mapping.append({
            "internal_code": it.get("internal_code", ""),
            "rule_type": it.get("aux_rule_type", ""),
            "fixed_k": it.get("aux_fixed_k", 0),
            "rate_detail": it.get("aux_rate_detail"),
        })
    return {
        "waste_rates": [
            {"internal_code": str(k), "waste_rate": float(v)} for k, v in waste.items()
        ],
        "aux_excel_items": data.get("aux_excel_items") or [],
        "benchmark_aux_mapping": mapping,
    }


SYNC_BATCH = 100  # 反代 Worker 上游超时 15s，单次 POST 整表 497 行有超时风险


def sync_seeds(dry_run: bool = False) -> dict:
    """一次性补库：把加密快照里云端缺失的三类数据直接 POST 到 Supabase。

    需要管理员级写凭据（WB_SUPABASE_SYNC_TOKEN），**普通公共授权只读账号无权执行**。
    分批 POST（每批 100 行）以避开反代超时；全程不落盘、不打印任何价格，
    只回传每张表的条数、批次数与 HTTP 状态。dry_run 时不联网、不要求令牌。
    """
    def batches(rows: list) -> int:
        return (len(rows) + SYNC_BATCH - 1) // SYNC_BATCH if rows else 0

    if dry_run:
        payload = seed_payload_from_snapshot()
        return {
            table: {"rows": len(payload.get(table) or []),
                    "batches": batches(payload.get(table) or []),
                    "status": "dry-run"}
            for table in ("waste_rates", "aux_excel_items", "benchmark_aux_mapping")
        }

    sync_token = os.environ.get("WB_SUPABASE_SYNC_TOKEN", "").strip()
    if not sync_token:
        raise SourceError("补库需要管理员级 WB_SUPABASE_SYNC_TOKEN（只读公共授权账号无权写）")
    payload = seed_payload_from_snapshot()
    result = {}
    for table in ("waste_rates", "aux_excel_items", "benchmark_aux_mapping"):
        rows = payload.get(table) or []
        if not rows:
            result[table] = {"rows": 0, "batches": 0, "status": "skipped"}
            continue
        statuses = []
        for start in range(0, len(rows), SYNC_BATCH):
            body = json.dumps(rows[start:start + SYNC_BATCH], ensure_ascii=False).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
                # 补库用管理员令牌覆盖只读身份
                "Authorization": "Bearer " + sync_token,
            }
            status, _h, _b = _request(f"/rest/v1/{table}", extra=headers,
                                      method="POST", data=body)
            if status not in (200, 201, 204):
                raise SourceError(
                    f"补库 {table} 第 {start // SYNC_BATCH + 1} 批失败：HTTP {status}"
                    "（前序批次可能已写入，重跑因 merge-duplicates 幂等）"
                )
            statuses.append(status)
        result[table] = {"rows": len(rows), "batches": len(statuses),
                         "status": statuses[-1]}
    return result


def clear_cache() -> None:
    load_snapshot.cache_clear()
    _access_token.cache_clear()
