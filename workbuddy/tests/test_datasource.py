"""云端数据层回归：字段映射、失败不静默回退、体检不泄露价格、补库需管理员令牌。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import datasource  # noqa: E402
import snapshot  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("WB_", "SUPABASE_")):
            monkeypatch.delenv(key, raising=False)
    datasource.clear_cache()
    yield
    datasource.clear_cache()


def _cloud(monkeypatch):
    monkeypatch.setenv("WB_PRICING_SOURCE", "supabase")
    monkeypatch.setenv("WB_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("WB_SUPABASE_ANON_KEY", "publishable")
    monkeypatch.setenv("WB_SUPABASE_TOKEN", "jwt")


def test_default_source_is_local_snapshot():
    assert datasource.source_name() == "snapshot"
    assert datasource.is_cloud() is False


def test_normalize_items_accepts_cloud_column_aliases():
    rows = [{
        "code": "NS-01", "trade": "泥水班组", "name": "地砖铺贴",
        "specification": "600*600", "unit": "m2", "price": 12.5,
        "rule_type": "FIXED", "fixed_k": 3.0, "loss_rate": 5,
    }]
    out = datasource._normalize_items(rows)
    assert out[0]["internal_code"] == "NS-01"
    assert out[0]["trade_team"] == "泥水班组"
    assert out[0]["spec"] == "600*600"
    assert out[0]["unit_price"] == 12.5
    assert out[0]["aux_rule_type"] == "FIXED"
    assert out[0]["aux_fixed_k"] == 3.0
    assert out[0]["waste_rate"] == 5.0


def test_fetch_table_distinguishes_missing_table(monkeypatch):
    monkeypatch.setattr(datasource, "_request",
                        lambda *a, **k: (200, {}, b'[{"a": 1}]'))
    assert datasource.fetch_table("benchmark_items") == [{"a": 1}]
    monkeypatch.setattr(datasource, "_request",
                        lambda *a, **k: (404, {}, b'{}'))
    assert datasource.fetch_table("waste_rates") is None


def test_fetch_table_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(datasource, "_request",
                        lambda *a, **k: (401, {}, b'{"message":"bad"}'))
    with pytest.raises(datasource.SourceError):
        datasource.fetch_table("benchmark_items")


def test_cloud_snapshot_shape_matches_local(monkeypatch):
    _cloud(monkeypatch)
    tables = {
        "benchmark_items": [{
            "internal_code": "NS-01", "trade_team": "泥水班组",
            "item_name": "地砖", "unit": "m2", "unit_price": 12.5,
            "aux_rule_type": "FIXED", "aux_fixed_k": 3.0, "waste_rate": 5,
        }],
        "waste_rates": [{"internal_code": "NS-01", "waste_rate": 5}],
        "material_prices": [{"material_name": "水泥", "price": 8.0}],
        "aux_excel_items": [{"code": "NS-01", "name": "地砖", "unit": "m2",
                             "work_type": "泥水", "rule_type": "FIXED"}],
        "main_material_prices": [],
        "main_material_catalog": [],
        "main_material_categories": [],
    }
    monkeypatch.setattr(datasource, "fetch_table",
                        lambda table, select="*", limit=5000: tables.get(table))
    data = datasource.load_snapshot()
    assert set(snapshot.empty()) <= set(data)
    assert data["generated_at"] == "supabase-live"
    assert data["benchmark_items"][0]["internal_code"] == "NS-01"
    assert data["waste_rates"] == {"NS-01": 5.0}
    assert data["material_prices"] == {"水泥": 8.0}
    assert len(data["aux_excel_items"]) == 1
    assert data["main_material_prices"] == []


def test_waste_rates_fall_back_to_item_column(monkeypatch):
    items = [{"internal_code": "A", "waste_rate": 3.0},
             {"internal_code": "B", "waste_rate": 0.0}]
    assert datasource._waste_rates(items, None) == {"A": 3.0}


def test_cloud_failure_never_silently_uses_stale_local_prices(monkeypatch):
    _cloud(monkeypatch)

    def boom(*_a, **_k):
        raise datasource.SourceError("云端不可达")

    monkeypatch.setattr(datasource, "fetch_table", boom)
    monkeypatch.setattr(snapshot, "load_snapshot", lambda *a, **k: {"stale": True})
    with pytest.raises(datasource.SourceError):
        datasource.load_snapshot()


def test_explicit_fallback_is_opt_in(monkeypatch):
    _cloud(monkeypatch)
    monkeypatch.setenv("WB_PRICING_FALLBACK", "1")

    def boom(*_a, **_k):
        raise datasource.SourceError("云端不可达")

    monkeypatch.setattr(datasource, "fetch_table", boom)
    monkeypatch.setattr(snapshot, "load_snapshot", lambda *a, **k: {"stale": True})
    assert datasource.load_snapshot() == {"stale": True}


def test_empty_benchmark_result_is_treated_as_auth_failure(monkeypatch):
    _cloud(monkeypatch)
    monkeypatch.setattr(datasource, "fetch_table", lambda *a, **k: [])
    with pytest.raises(datasource.SourceError, match="0 行"):
        datasource.load_snapshot()


def test_probe_returns_fields_and_counts_but_never_values(monkeypatch):
    _cloud(monkeypatch)

    def fake_request(path, extra=None, method="GET", data=None):
        if "benchmark_items" in path:
            body = json.dumps([{"internal_code": "NS-01", "unit_price": 123.45}]).encode()
            return 200, {"Content-Range": "0-0/497"}, body
        return 404, {}, b'{}'

    monkeypatch.setattr(datasource, "_request", fake_request)
    rows = datasource.probe()
    bm = next(r for r in rows if r["table"] == "benchmark_items")
    assert bm["status"] == "ok" and bm["count"] == "497"
    assert bm["fields"] == ["internal_code", "unit_price"]
    assert "123.45" not in json.dumps(rows, ensure_ascii=False)


def test_missing_base_url_is_reported_without_echoing_secrets(monkeypatch):
    monkeypatch.setenv("WB_PRICING_SOURCE", "supabase")
    monkeypatch.setenv("WB_SUPABASE_ANON_KEY", "publishable")
    monkeypatch.setenv("WB_SUPABASE_TOKEN", "jwt")
    # probe 逐表降级为 error 行而不抛出；关键是错误信息里不能带任何凭据
    rows = datasource.probe()
    assert rows and all(r["status"] == "error" for r in rows)
    assert "publishable" not in json.dumps(rows, ensure_ascii=False)
    assert "jwt" not in json.dumps(rows, ensure_ascii=False)


def test_seed_payload_shape(monkeypatch):
    monkeypatch.setattr(snapshot, "load_snapshot", lambda *a, **k: {
        "waste_rates": {"NS-01": 5.0},
        "benchmark_items": [{"internal_code": "NS-01", "aux_rule_type": "FIXED",
                             "aux_fixed_k": 3.0, "aux_rate_detail": []}],
        "aux_excel_items": [{"code": "NS-01", "name": "地砖"}],
    })
    payload = datasource.seed_payload_from_snapshot()
    assert set(payload) == {"waste_rates", "aux_excel_items", "benchmark_aux_mapping"}
    assert payload["waste_rates"] == [{"internal_code": "NS-01", "waste_rate": 5.0}]
    assert payload["benchmark_aux_mapping"][0]["rule_type"] == "FIXED"


def test_sync_seeds_requires_admin_token(monkeypatch):
    with pytest.raises(datasource.SourceError, match="WB_SUPABASE_SYNC_TOKEN"):
        datasource.sync_seeds()


def test_sync_seeds_posts_without_printing_values(monkeypatch, capsys):
    _cloud(monkeypatch)
    monkeypatch.setenv("WB_SUPABASE_SYNC_TOKEN", "admin-token")
    monkeypatch.setattr(datasource, "seed_payload_from_snapshot", lambda: {
        "waste_rates": [{"internal_code": "NS-01", "waste_rate": 5.0}],
        "aux_excel_items": [{"code": "NS-01"}],
        "benchmark_aux_mapping": [{"internal_code": "NS-01", "fixed_k": 3.0}],
    })
    seen = {}

    def fake_request(path, extra=None, method="GET", data=None):
        seen[path] = (method, extra or {}, data)
        return 201, {}, b''

    monkeypatch.setattr(datasource, "_request", fake_request)
    result = datasource.sync_seeds()
    assert all(v["rows"] == 1 for v in result.values())
    assert all(v[0] == "POST" for v in seen.values())
    assert all(b"admin-token" not in (v[2] or b"") for v in seen.values())
    assert "5.0" not in capsys.readouterr().out


# --- 阶段 1：体检状态可区分、环境预检不回显、补库分批 ---

def test_probe_distinguishes_missing_empty_and_ok(monkeypatch):
    _cloud(monkeypatch)

    def fake_request(path, extra=None, method="GET", data=None):
        if "benchmark_items" in path:
            return 200, {"Content-Range": "0-0/497"}, b'[{"internal_code":"NS-01"}]'
        if "material_prices" in path:
            # 表在、RLS 拦截 → 200 但 0 行
            return 200, {"Content-Range": "0-0/0"}, b'[]'
        return 404, {}, b'{}'

    monkeypatch.setattr(datasource, "_request", fake_request)
    rows = {r["table"]: r for r in datasource.probe()}
    assert rows["benchmark_items"]["status"] == "ok"
    assert rows["material_prices"]["status"] == "empty"
    assert "authenticated" in rows["material_prices"]["hint"]
    assert rows["waste_rates"]["status"] == "missing"
    assert "wb_supabase_setup.sql" in rows["waste_rates"]["hint"]


def test_preflight_reports_presence_only_never_values(monkeypatch):
    monkeypatch.setenv("WB_PRICING_SOURCE", "supabase")
    monkeypatch.setenv("WB_SUPABASE_URL", "https://decoration-pricing-system.pages.dev/sb")
    monkeypatch.setenv("WB_SUPABASE_ANON_KEY", "publishable-secret")
    monkeypatch.setenv("WB_SUPABASE_TOKEN", "jwt-secret")
    pf = datasource.preflight()
    assert pf["channel"] == "proxy"
    assert pf["identity"] == "jwt"
    assert pf["anon_key"] is True
    assert pf["fallback"] is False
    out = json.dumps(pf, ensure_ascii=False)
    assert "publishable-secret" not in out and "jwt-secret" not in out


def test_preflight_detects_direct_channel_and_password_identity(monkeypatch):
    monkeypatch.setenv("WB_PRICING_SOURCE", "supabase")
    monkeypatch.setenv("WB_SUPABASE_URL", "https://lnvtykghcpsjpwczbqsm.supabase.co")
    monkeypatch.setenv("WB_SUPABASE_EMAIL", "reader@example.com")
    monkeypatch.setenv("WB_SUPABASE_PASSWORD", "pw-secret")
    pf = datasource.preflight()
    assert pf["channel"] == "direct" and pf["identity"] == "password"
    assert "reader@example.com" not in json.dumps(pf, ensure_ascii=False)
    assert "pw-secret" not in json.dumps(pf, ensure_ascii=False)


def test_sync_seeds_dry_run_needs_no_token_and_never_calls_network(monkeypatch):
    monkeypatch.setattr(datasource, "seed_payload_from_snapshot", lambda: {
        "waste_rates": [{"internal_code": str(i), "waste_rate": 1.0} for i in range(250)],
        "aux_excel_items": [{"code": str(i)} for i in range(101)],
        "benchmark_aux_mapping": [],
    })

    def forbidden(*_a, **_k):
        raise AssertionError("dry-run 不应触发任何网络请求")

    monkeypatch.setattr(datasource, "_request", forbidden)
    result = datasource.sync_seeds(dry_run=True)
    assert result["waste_rates"] == {"rows": 250, "batches": 3, "status": "dry-run"}
    assert result["aux_excel_items"]["batches"] == 2
    assert result["benchmark_aux_mapping"]["batches"] == 0


def test_sync_seeds_posts_in_batches_and_reports_batch_failure(monkeypatch):
    _cloud(monkeypatch)
    monkeypatch.setenv("WB_SUPABASE_SYNC_TOKEN", "admin-token")
    monkeypatch.setattr(datasource, "seed_payload_from_snapshot", lambda: {
        "waste_rates": [{"internal_code": str(i), "waste_rate": 1.0} for i in range(250)],
        "aux_excel_items": [], "benchmark_aux_mapping": [],
    })
    calls = []

    def fake_request(path, extra=None, method="GET", data=None):
        calls.append((path, data))
        return 201, {}, b''

    monkeypatch.setattr(datasource, "_request", fake_request)
    result = datasource.sync_seeds()
    assert result["waste_rates"]["batches"] == 3
    assert len(calls) == 3
    assert [len(json.loads(c[1])) for c in calls] == [100, 100, 50]

    def failing(path, extra=None, method="GET", data=None):
        return 500, {}, b''

    monkeypatch.setattr(datasource, "_request", failing)
    with pytest.raises(datasource.SourceError, match="第 1 批失败"):
        datasource.sync_seeds()
