"""Cloudflare Worker 邮件发送客户端

调用部署在 Cloudflare Worker 上的邮件服务，透传幂等键。
Worker 负责验证 EMAIL_SERVICE_TOKEN → 调用 Resend → 返回结果。
"""
import html
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email_via_worker(
    to: str,
    subject: str,
    html: str,
    idempotency_key: str,
) -> dict:
    """通过 Cloudflare Worker 发送邮件。

    Args:
        idempotency_key: Resend 幂等键，如 "release-{id}-user-{uuid}"
                         重试同一邮件必须使用相同的 key。

    Returns:
        {"ok": bool, "message_id": str|None, "error": str|None}
    """
    if not settings.EMAIL_WORKER_URL or not settings.EMAIL_SERVICE_TOKEN:
        return {"ok": False, "message_id": None, "error": "EMAIL_WORKER_URL or EMAIL_SERVICE_TOKEN not configured"}

    # 清理换行符，防止 SMTP header injection
    safe_to = to.replace("\r", "").replace("\n", "")
    safe_subject = subject.replace("\r", "").replace("\n", "")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{settings.EMAIL_WORKER_URL}/",
                headers={
                    "Authorization": f"Bearer {settings.EMAIL_SERVICE_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": safe_to,
                    "subject": safe_subject,
                    "html": html,
                    "idempotency_key": idempotency_key,
                },
            )
            if r.status_code == 200:
                return r.json()
            return {
                "ok": False,
                "message_id": None,
                "error": f"Worker returned {r.status_code}: {r.text[:300]}",
            }
    except httpx.TimeoutException:
        return {"ok": False, "message_id": None, "error": "Worker request timed out"}
    except Exception as e:
        logger.error(f"send_email_via_worker error: {e}")
        return {"ok": False, "message_id": None, "error": str(e)[:500]}


async def send_test_email(to: str) -> dict:
    """发送测试邮件，验证 Worker → Resend 配置。"""
    subject = "【装修成本AI系统】测试邮件"
    html = _build_test_email_html()
    # 测试邮件使用时间戳幂等键（每次发送都是新的）
    from datetime import datetime
    test_key = f"test-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{to.replace('@', '-')}"
    return await send_email_via_worker(to, subject, html, test_key)


def build_release_email_html(version: str, title: str, content: str) -> str:
    """构建版本发布通知邮件 HTML。"""
    # 先转义 HTML 特殊字符，再将换行转为 <br>
    safe_content = html.escape(content)
    content_html = safe_content.replace("\n", "<br>")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f6fa;padding:30px">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
  <div style="font-size:14px;color:#6e8fa8;margin-bottom:8px">装修成本AI系统</div>
  <h1 style="font-size:22px;color:#1a2d3d;margin:0 0 8px">{html.escape(version)} 版本更新</h1>
  <h2 style="font-size:16px;color:#1d6fa5;margin:0 0 20px;font-weight:500">{html.escape(title)}</h2>
  <div style="font-size:14px;color:#3a5470;line-height:1.8;margin-bottom:28px;white-space:pre-wrap">{content_html}</div>
  <a href="{settings.FRONTEND_URL}/tool.html" style="display:inline-block;background:#1d6fa5;color:#fff;text-decoration:none;padding:12px 32px;border-radius:8px;font-size:14px;font-weight:600">进入系统</a>
  <div style="margin-top:24px;padding-top:16px;border-top:1px solid #e8e8e8;font-size:12px;color:#a0bcce">此邮件由系统自动发送，请勿回复</div>
</div></body></html>"""


def _build_test_email_html() -> str:
    """构建测试邮件 HTML。"""
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f6fa;padding:30px">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
  <h1 style="font-size:18px;color:#1d6fa5;margin:0 0 12px">&#x1f4e7; 测试邮件</h1>
  <p style="font-size:14px;color:#3a5470;line-height:1.8">
    这是一封测试邮件，用于验证装修成本AI系统的邮件发送配置是否正常。
  </p>
  <p style="font-size:12px;color:#a0bcce;margin-top:20px">
    如果您收到此邮件，说明邮件服务配置成功。
  </p>
</div></body></html>"""
