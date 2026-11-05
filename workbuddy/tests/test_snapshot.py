"""T1 · 加密快照解密 —— 测试先行（TDD 红灯）"""
import json
from pathlib import Path

import pytest

import snapshot


# ---------- 密钥解码 ----------

def test_decode_key_hex64():
    key = snapshot.decode_key("00" * 32)
    assert isinstance(key, bytes) and len(key) == 32


def test_decode_key_base64():
    import base64
    raw = base64.b64encode(b"\x01" * 32).decode()
    assert len(snapshot.decode_key(raw)) == 32


@pytest.mark.parametrize("bad", ["", "abc", "00" * 31, "zz" * 32])
def test_decode_key_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        snapshot.decode_key(bad)


# ---------- 加解密往返 ----------

def test_seal_unseal_roundtrip():
    payload = {"benchmark_items": [{"internal_code": "X-1"}], "waste_rates": {"a": 1}}
    blob = snapshot.seal_json(payload)
    assert snapshot.unseal_text(blob) == payload


def test_unseal_wrong_key_raises():
    blob = snapshot.seal_json({"benchmark_items": []})
    with pytest.raises(Exception):
        snapshot.unseal_text(blob, key=b"\x02" * 32)


# ---------- 真实快照 ----------

def test_real_snapshot_loads():
    data = snapshot.load_snapshot()
    assert len(data["benchmark_items"]) == 497
    assert len(data["waste_rates"]) == 475
    assert "generated_at" in data


def test_item_has_required_fields():
    item = snapshot.load_snapshot()["benchmark_items"][0]
    for field in ("internal_code", "item_name", "spec", "unit", "unit_price",
                  "trade_team", "aux_rule_type"):
        assert field in item, f"缺少字段 {field}"


# ---------- 失败降级：不抛异常 ----------

def test_missing_file_degrades():
    data = snapshot.load_snapshot("/tmp/__no_such_snapshot__.enc")
    assert data["benchmark_items"] == []
    assert data["waste_rates"] == {}


def test_corrupt_file_degrades():
    p = Path("/tmp/__corrupt_snapshot__.enc")
    p.write_text("not-a-valid-blob")
    try:
        data = snapshot.load_snapshot(p)
        assert data["benchmark_items"] == []
    finally:
        p.unlink(missing_ok=True)
