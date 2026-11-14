"""基准价加密快照 —— 离线数据源

格式：base64( nonce(12) ‖ AES-256-GCM(plaintext) ‖ tag(16) )，明文为 JSON。
密钥来源优先级：环境变量 BENCHMARK_SNAPSHOT_KEY > skill 根目录 .env。
密文可随 skill 分发，密钥不随包走（无密钥时密文等同废纸）。
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "data" / "benchmark_snapshot.enc"
ENV_FILE = ROOT / ".env"
KEY_NAME = "BENCHMARK_SNAPSHOT_KEY"

NONCE_LEN = 12
KEY_LEN = 32
HEX_CHARS = set("0123456789abcdefABCDEF")


def empty() -> dict:
    return {
        "benchmark_items": [],
        "waste_rates": {},
        "material_prices": {},
        "aux_excel_items": [],
        "generated_at": None,
    }


def _read_env_key() -> str:
    raw = (os.environ.get(KEY_NAME) or "").strip()
    if raw:
        return raw
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(KEY_NAME + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def decode_key(raw: str) -> bytes:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError(f"{KEY_NAME} 未配置")
    if len(raw) == KEY_LEN * 2 and set(raw) <= HEX_CHARS:
        key = bytes.fromhex(raw)
    else:
        try:
            key = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise ValueError("密钥须为 64 位 hex 或 base64(32 字节)") from exc
    if len(key) != KEY_LEN:
        raise ValueError(f"密钥长度应为 {KEY_LEN} 字节，实际 {len(key)} 字节")
    return key


def _resolve_key(key=None) -> bytes:
    if isinstance(key, (bytes, bytearray)):
        if len(key) != KEY_LEN:
            raise ValueError(f"密钥长度应为 {KEY_LEN} 字节，实际 {len(key)} 字节")
        return bytes(key)
    return decode_key(key if key else _read_env_key())


def seal_json(payload: dict, key=None) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    k = _resolve_key(key)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(k).encrypt(nonce, json.dumps(payload, ensure_ascii=False).encode(), None)
    return base64.b64encode(nonce + ct).decode()


def unseal_text(blob: str, key=None) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    k = _resolve_key(key)
    raw = base64.b64decode((blob or "").strip())
    if len(raw) <= NONCE_LEN:
        raise ValueError("密文长度异常，疑似截断")
    return json.loads(AESGCM(k).decrypt(raw[:NONCE_LEN], raw[NONCE_LEN:], None).decode())


def load_snapshot(path=None) -> dict:
    """读并解密快照。任何失败都返回空结构 + 一条日志，不抛异常。

    调用方是套价候选池，抛异常会把「兜底数据不可用」放大成整体失败。
    """
    # 数据不随包走：clone 后可用 BENCHMARK_SNAPSHOT_PATH 指向自备密文，
    # 密钥由 BENCHMARK_SNAPSHOT_KEY 环境变量注入，两者都不写进仓库。
    p = Path(path or os.environ.get("BENCHMARK_SNAPSHOT_PATH") or DEFAULT_SNAPSHOT)
    try:
        data = unseal_text(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[SNAPSHOT] 文件不存在: {p}")
        return empty()
    except Exception as exc:
        print(f"[SNAPSHOT] 解密失败: {type(exc).__name__}: {exc}")
        return empty()

    if not isinstance(data.get("benchmark_items"), list):
        print("[SNAPSHOT] benchmark_items 缺失或非数组")
        return empty()
    # 向后兼容旧格式密文：新数据集缺失时补空结构，不抛异常
    data.setdefault("waste_rates", {})
    data.setdefault("material_prices", {})
    data.setdefault("aux_excel_items", [])
    data.setdefault("generated_at", None)
    return data


def stats(data: dict) -> dict:
    """只返回统计量，绝不回吐定价明细。"""
    items = data.get("benchmark_items") or []
    return {
        "items": len(items),
        "waste_rates": len(data.get("waste_rates") or {}),
        "material_prices": len(data.get("material_prices") or {}),
        "aux_excel_items": len(data.get("aux_excel_items") or []),
        "generated_at": data.get("generated_at"),
        "teams": len({i.get("trade_team") for i in items if i.get("trade_team")}),
    }
