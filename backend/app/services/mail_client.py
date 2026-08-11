"""QQ SMTP 邮件发送客户端

使用 Python 标准库 smtplib + email.message 通过 QQ 邮箱 SMTP 发送邮件。
保留所有 XSS 防护、Header Injection 防护和数据库幂等机制。
"""
import html
import logging
import smtplib
import uuid
from datetime import datetime
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _smtp_config_ok() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)


def _clean_header(value: str) -> str:
    """清理 CRLF，防止 SMTP header injection。"""
    return value.replace("\r", "").replace("\n", "")


def _make_message_id() -> str:
    """生成唯一 Message-ID 用于追踪。"""
    return f"<{uuid.uuid4()}@decoration-pricing>"


async def send_email_via_worker(
    to: str,
    subject: str,
    html_body: str,
    idempotency_key: str,
) -> dict:
    """通过 QQ SMTP 发送邮件。

    Args:
        idempotency_key: 数据库幂等键，保留用于日志追踪（QQ SMTP 不支持 API 级幂等）

    Returns:
        {"ok": bool, "message_id": str|None, "error": str|None}
    """
    if not _smtp_config_ok():
        return {"ok": False, "message_id": None, "error": "SMTP not configured (SMTP_HOST/USERNAME/PASSWORD missing)"}

    # Header injection 防护
    safe_to = _clean_header(to)
    safe_subject = _clean_header(subject)

    try:
        msg = EmailMessage()
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = safe_to
        msg["Subject"] = safe_subject
        msg["Message-ID"] = _make_message_id()
        msg.set_content("请使用支持 HTML 的邮件客户端查看此邮件。")
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=30,
        ) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        message_id = msg["Message-ID"]
        logger.info(f"Email sent to {safe_to} (idempotency_key={idempotency_key}, message_id={message_id})")
        return {"ok": True, "message_id": message_id, "error": None}

    except smtplib.SMTPAuthenticationError as e:
        err = f"SMTP authentication failed: {e}"
        logger.error(err)
        return {"ok": False, "message_id": None, "error": err[:500]}
    except smtplib.SMTPConnectError as e:
        err = f"SMTP connection failed: {e}"
        logger.error(err)
        return {"ok": False, "message_id": None, "error": err[:500]}
    except smtplib.SMTPException as e:
        err = f"SMTP error: {e}"
        logger.error(err)
        return {"ok": False, "message_id": None, "error": err[:500]}
    except TimeoutError as e:
        err = f"SMTP timeout: {e}"
        logger.error(err)
        return {"ok": False, "message_id": None, "error": err[:500]}
    except OSError as e:
        err = f"SMTP network error: {e}"
        logger.error(err)
        return {"ok": False, "message_id": None, "error": err[:500]}
    except Exception as e:
        logger.error(f"send_email_via_worker unexpected error: {e}", exc_info=True)
        return {"ok": False, "message_id": None, "error": str(e)[:500]}


async def send_test_email(to: str) -> dict:
    """发送测试邮件，验证 SMTP 配置。"""
    subject = "【装修成本AI系统】测试邮件"
    html_body = _build_test_email_html()
    test_key = f"test-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{to.replace('@', '-')}"
    return await send_email_via_worker(to, subject, html_body, test_key)


def build_release_email_html(version: str, title: str, content: str) -> str:
    """构建版本发布通知邮件 HTML。"""
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
