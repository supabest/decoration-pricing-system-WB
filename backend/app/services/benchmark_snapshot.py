"""基准价加密快照 —— 离线兜底的第二数据源

为什么是「仓库里的密文」而不是直接读库：兜底场景就是 Supabase 整体不可达，此时后端必须
还有第二个价格源；而这个源跟着 git 和部署产物走，所以对甲/内部价格表只能以密文存在。
密钥 BENCHMARK_SNAPSHOT_KEY 不进仓库（Render 环境变量 + 本机 backend/.env）。

格式：base64( nonce(12) ‖ AES-256-GCM(plaintext) ‖ tag(16) )，明文是 JSON。
"""
import base64, json, os
from app.core.config import settings

SNAPSHOT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_snapshot.enc"))
NONCE_LEN = 12
KEY_LEN = 32

EMPTY: dict = {"benchmark_items": [], "waste_rates": {}}

_snapshot_cache = None


def _decode_key(raw: str) -> bytes:
    """密钥接受 hex64（与 SECRET_KEY 同风格）或 base64，两种都得正好解出 32 字节。

    做两种是因为手抄 64 个 hex 字符容易截断，而截断后的报错长得像「解密失败」，
    排查成本高；这里直接在校验阶段说清楚。
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("BENCHMARK_SNAPSHOT_KEY 未配置")
    try:
        if len(raw) == KEY_LEN * 2 and all(c in "0123456789abcdefABCDEF" for c in raw):
            key = bytes.fromhex(raw)
        else:
            key = base64.b64decode(raw, validate=True)
    except ValueError as e:
        # base64 非法字符抛的是 binascii.Error（ValueError 子类）。
        # 抄错的密钥若不在这里拦住，到了解密那步只会得到一句 "InvalidNonce"，
        # 看起来像文件损坏而不是密钥问题
        raise ValueError("密钥须是 64 位 hex 或解出 32 字节的 base64") from e
    if len(key) != KEY_LEN:
        raise ValueError(f"密钥长度应为 {KEY_LEN} 字节，实际 {len(key)} 字节")
    return key


def seal_json(payload: dict) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _decode_key(settings.BENCHMARK_SNAPSHOT_KEY)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, json.dumps(payload, ensure_ascii=False).encode(), None)
    return base64.b64encode(nonce + ct).decode()


def unseal_text(blob: str) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _decode_key(settings.BENCHMARK_SNAPSHOT_KEY)
    raw = base64.b64decode((blob or "").strip())
    nonce, ct = raw[:NONCE_LEN], raw[NONCE_LEN:]
    return json.loads(AESGCM(key).decrypt(nonce, ct, None).decode())


def load_snapshot() -> dict:
    """读并解密快照，结果常驻进程。任何一环失败都回空结构 + 一条 [SNAPSHOT] 日志。

    回空而不是抛异常：调用方是套价候选池，抛异常会把「兜底数据不可用」变成 500，
    而 Supabase 正常时这条路径根本不该影响主流程。
    """
    global _snapshot_cache
    if _snapshot_cache is not None:
        return _snapshot_cache

    snap = dict(EMPTY)
    try:
        with open(SNAPSHOT_PATH) as f:
            snap = unseal_text(f.read())
        if not isinstance(snap.get("benchmark_items"), list):
            print("[SNAPSHOT] 快照内 benchmark_items 缺失或非数组")
            snap = dict(EMPTY)
    except FileNotFoundError:
        print(f"[SNAPSHOT] 快照文件不存在: {SNAPSHOT_PATH}（跑 scripts/encrypt_benchmark_snapshot.py 生成）")
    except Exception as e:
        print(f"[SNAPSHOT] 快照不可用（密钥不匹配或文件损坏）: {type(e).__name__}: {e}")

    _snapshot_cache = snap
    return snap


def reset_cache():
    """测试用：清掉进程内缓存"""
    global _snapshot_cache
    _snapshot_cache = None
