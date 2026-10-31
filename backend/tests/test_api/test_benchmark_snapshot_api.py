"""基准价快照端点鉴权回归（保密裁定的服务端入口）

docs/benchmark_data.json 原先是 Pages 公网上的明文全量价表，任何人 not-login 即可 fetch。
下线后兜底改走本端点，门槛必须钉在「有登录态」这一侧：匿名 401，登录用户拿到与原 JSON
同构的 {items, waste_rates, count}。另钉一条真实产物的解密检查——防止把 .enc 提交了
却没配密钥，线上到兜底那天才发现解不开。
"""
import pytest
from fastapi.testclient import TestClient

from app.core.auth import require_auth
from app.core.config import settings
from app.main import app
from app.services import benchmark_snapshot as bs

client = TestClient(app)

ROWS = [{"trade_team": "泥水班组", "internal_code": "NS-01", "item_name": "地砖铺贴",
         "spec": "300×300", "unit": "m2", "unit_price": 100}]


@pytest.fixture
def snapshot_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "BENCHMARK_SNAPSHOT_KEY", "11" * 32)
    path = tmp_path / "benchmark_snapshot.enc"
    path.write_text(bs.seal_json({"benchmark_items": ROWS, "waste_rates": {"NS-01": 3.5},
                                 "generated_at": "2026-10-31T00:00:00+00:00"}))
    monkeypatch.setattr(bs, "SNAPSHOT_PATH", str(path))
    bs.reset_cache()
    yield
    bs.reset_cache()


def test_anonymous_is_rejected():
    """外部无登录态 → 401，且响应体不带任何价格字段"""
    r = client.get("/api/v1/benchmark/snapshot")
    assert r.status_code == 401
    assert "NS-01" not in r.text


def test_authenticated_gets_snapshot(snapshot_file):
    app.dependency_overrides[require_auth] = lambda: {"sub": "u-1"}
    try:
        r = client.get("/api/v1/benchmark/snapshot")
    finally:
        app.dependency_overrides.pop(require_auth, None)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 1
    assert body["items"][0]["internal_code"] == "NS-01"
    assert body["waste_rates"] == {"NS-01": 3.5}
    assert body["generated_at"] == "2026-10-31T00:00:00+00:00"


@pytest.mark.skipif(not (settings.BENCHMARK_SNAPSHOT_KEY and __import__("os").path.exists(bs.SNAPSHOT_PATH)),
                    reason="本机未配 BENCHMARK_SNAPSHOT_KEY 或快照未生成")
def test_committed_snapshot_decrypts_with_local_key():
    """仓库里那份 .enc 必须能被本机能拿到的密钥解开（497 条）——产物与密钥同源校验"""
    bs.reset_cache()
    snap = bs.load_snapshot()
    assert len(snap["benchmark_items"]) == 497
    assert snap["waste_rates"]
