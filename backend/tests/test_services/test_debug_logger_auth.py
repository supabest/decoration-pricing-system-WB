"""调试日志认证头：service_role 优先、anon 回退（P0-1 锁表配套回归）

背景：ai_pricing_logs 曾被匿名全量可读（422 行），迁移改为 RLS 锁读后，
后端读取必须走 service_role；本机未配该键时回退 anon（写入不受影响）。
本用例钉住两条分支，防止后续把 service_role 优先逻辑改回去。
"""
from app.core.config import settings
from app.services.pricing_debug_logger import _rest_auth


def test_prefers_service_role(monkeypatch):
    """已配 service_role → 两个头都用它（读取才不会被 RLS 拦成空）"""
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "srk-test")
    h = _rest_auth()
    assert h["apikey"] == "srk-test"
    assert h["Authorization"] == "Bearer srk-test"


def test_falls_back_to_anon(monkeypatch):
    """未配 service_role → 回退 anon（本机开发/迁移未执行时行为不变）"""
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    h = _rest_auth()
    assert h["apikey"] == settings.SUPABASE_ANON_KEY
    assert h["Authorization"] == f"Bearer {settings.SUPABASE_ANON_KEY}"
