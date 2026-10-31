"""基准价加密快照 + service_role 读取回归

背景：docs/benchmark_data.json（497 条含价）曾以明文发布在 Pages 公网，任何人不登录
即可 fetch 全量价格。保密裁定是「注册用户不需保密、外部绝对保密」，所以下线公网明文
后，离线兜底的第二数据源只能是仓库里的密文快照，密钥留在环境变量。
本用例钉住：
  1. 密钥校验（hex/base64、长度）在解密前就报清楚；
  2. 快照缺失/密钥错时 load_snapshot 回空结构而不抛——兜底不能把主流程打成 500；
  3. Supabase 取不到时，候选池来自快照；两者都空时明确回空列表。
"""
import asyncio
import base64
import pytest

from app.core.config import settings
from app.services import ai_pricing_service as svc
from app.services import benchmark_snapshot as bs

HEX_KEY = "11" * 32
B64_KEY = base64.b64encode(b"\x22" * 32).decode()
OTHER_KEY = "22" * 32

ROWS = [
    {"trade_team": "泥水班组", "internal_code": "NS-01", "item_name": "地砖铺贴",
     "spec": "300×300", "unit": "m2", "unit_price": 100},
    {"trade_team": "木工班组", "internal_code": "MG-01", "item_name": "石膏板吊顶",
     "unit": "m2", "unit_price": 200},
]
SNAP = {"benchmark_items": ROWS, "waste_rates": {"NS-01": 3.5}, "generated_at": "2026-10-31T00:00:00+00:00"}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """每个用例独立：快照路径指向临时目录、进程内缓存清空、密钥默认给一把合法的"""
    monkeypatch.setattr(settings, "BENCHMARK_SNAPSHOT_KEY", HEX_KEY)
    monkeypatch.setattr(bs, "SNAPSHOT_PATH", str(tmp_path / "benchmark_snapshot.enc"))
    bs.reset_cache()
    svc._benchmark_cache = None
    yield
    bs.reset_cache()
    svc._benchmark_cache = None


def _write_snapshot(payload=SNAP):
    """用当前 settings 里的密钥封一份快照到临时路径"""
    with open(bs.SNAPSHOT_PATH, "w") as f:
        f.write(bs.seal_json(payload))


# ── 1. 密钥校验 ──

def test_decode_key_accepts_hex_and_base64():
    assert bs._decode_key(HEX_KEY) == b"\x11" * 32
    assert bs._decode_key(B64_KEY) == b"\x22" * 32
    assert bs._decode_key("  " + HEX_KEY + "  ") == b"\x11" * 32  # 复制粘贴带的空白


@pytest.mark.parametrize("bad", ["", "zzzz", "11" * 16])
def test_decode_key_rejects_before_decrypt(bad):
    """缺键/非法编码/长度不对都要在校验期报 ValueError——不能等到解密抛 InvalidNonce"""
    with pytest.raises(ValueError):
        bs._decode_key(bad)


def test_seal_unseal_roundtrip():
    assert bs.unseal_text(bs.seal_json(SNAP)) == SNAP


def test_unseal_with_wrong_key_raises():
    blob = bs.seal_json(SNAP)
    settings.BENCHMARK_SNAPSHOT_KEY = OTHER_KEY
    with pytest.raises(Exception):
        bs.unseal_text(blob)


# ── 2. load_snapshot 的降级分支 ──

def test_load_snapshot_missing_file_returns_empty(monkeypatch, capsys):
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    assert bs.load_snapshot() == bs.EMPTY
    assert "快照文件不存在" in capsys.readouterr().out


def test_load_snapshot_wrong_key_returns_empty(capsys):
    """密文在、密钥不对 → 回空并留日志，不抛（兜底数据不可用不该拖垮套价主流程）"""
    _write_snapshot()
    settings.BENCHMARK_SNAPSHOT_KEY = OTHER_KEY
    assert bs.load_snapshot() == bs.EMPTY
    assert "快照不可用" in capsys.readouterr().out


def test_load_snapshot_broken_payload_returns_empty():
    """密文里缺 benchmark_items（手动改过/版本不符）→ 规约成空结构"""
    _write_snapshot({"waste_rates": {}})
    assert bs.load_snapshot() == bs.EMPTY


def test_load_snapshot_reads_items_and_caches(tmp_path, monkeypatch):
    _write_snapshot()
    snap = bs.load_snapshot()
    assert len(snap["benchmark_items"]) == 2
    assert snap["waste_rates"] == {"NS-01": 3.5}
    # 结果常驻：删掉文件仍读得到（同进程不重复解密）
    import os
    os.remove(bs.SNAPSHOT_PATH)
    assert bs.load_snapshot() is snap


# ── 3. 读取认证头与兜底链 ──

def test_sb_headers_prefers_service_role(monkeypatch):
    """RLS 收紧到 authenticated 后，anon 读被静默返回空数组 → 后端必须用能绕过 RLS 的键"""
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "srk-test")
    h = svc._sb_headers()
    assert h["apikey"] == "srk-test" and h["Authorization"] == "Bearer srk-test"


def test_sb_headers_falls_back_to_anon(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    h = svc._sb_headers()
    assert h["apikey"] == settings.SUPABASE_ANON_KEY


def test_load_benchmark_data_falls_back_to_snapshot(monkeypatch):
    """Supabase 连不通（这里指向必然被拒的本地端口）→ 候选池来自加密快照"""
    monkeypatch.setattr(settings, "SUPABASE_URL", "http://127.0.0.1:1")
    _write_snapshot()

    async def main():
        return await svc.load_benchmark_data()

    items = asyncio.run(main())
    assert [d["internal_code"] for d in items] == ["NS-01", "MG-01"]
    assert items[1]["work_type"] == "" and items[1]["aux_rule_type"] == ""


def test_load_benchmark_data_empty_when_both_sources_fail(monkeypatch, capsys):
    """库不可达 + 无快照 → 空列表并显式报警，不静给出半截候选"""
    monkeypatch.setattr(settings, "SUPABASE_URL", "http://127.0.0.1:1")

    async def main():
        return await svc.load_benchmark_data()

    assert asyncio.run(main()) == []
    out = capsys.readouterr().out
    assert "基准价库为空" in out
