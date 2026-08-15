"""版本发布 + 邮件通知 API 端点"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.core.auth import require_admin, optional_auth
from app.core.config import settings
from app.schemas.release import (
    ReleaseCreate, ReleaseUpdate, ReleaseOut,
    EmailLogOut, SendEmailResult, RetryResult,
    TestEmailRequest,
)
from app.services.mail_client import send_email_via_worker, build_release_email_html, send_test_email
from app.services.user_lookup import get_all_user_emails

logger = logging.getLogger(__name__)

router = APIRouter()
SUPABASE_REST = f"{settings.SUPABASE_URL}/rest/v1"

STALE_TIMEOUT_MINUTES = 30  # sending 超过此时间视为异常中断


# ═══════════ Helpers ═══════════

def _service_role_headers() -> dict:
    return {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_release(release_id: int, headers: dict) -> Optional[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{SUPABASE_REST}/system_releases",
            headers=headers,
            params={"select": "*", "id": f"eq.{release_id}"},
        )
        if r.status_code != 200:
            return None
        rows = r.json()
        return rows[0] if rows else None


async def _patch_release(release_id: int, data: dict, headers: dict) -> int:
    """返回 affected_rows"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.patch(
            f"{SUPABASE_REST}/system_releases",
            headers={**headers, "Prefer": "return=representation"},
            params={"id": f"eq.{release_id}"},
            json=data,
        )
        return 1 if r.status_code == 200 and r.json() else 0


async def _conditional_patch_release(release_id: int, data: dict, match_email_status: list, headers: dict) -> int:
    """条件更新 — 原子抢锁。返回 affected_rows。"""
    async with httpx.AsyncClient(timeout=10) as client:
        # 构造 filter: id=eq.X&email_status=in.(a,b)
        status_filter = ",".join(match_email_status)
        params = {
            "id": f"eq.{release_id}",
            "email_status": f"in.({status_filter})",
        }
        r = await client.patch(
            f"{SUPABASE_REST}/system_releases",
            headers={**headers, "Prefer": "return=representation"},
            params=params,
            json=data,
        )
        rows = r.json() if r.status_code == 200 else []
        return len(rows)


async def _get_email_logs(release_id: int, headers: dict, status: str | None = None) -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        params = {
            "select": "*",
            "release_id": f"eq.{release_id}",
            "order": "created_at.asc",
            "limit": "1000",
        }
        if status:
            params["status"] = f"eq.{status}"
        r = await client.get(f"{SUPABASE_REST}/email_logs", headers=headers, params=params)
        return r.json() if r.status_code == 200 else []


async def _upsert_email_log(release_id: int, user_id: str, email: str, headers: dict) -> bool:
    """INSERT ... ON CONFLICT DO NOTHING。返回 True 表示新插入，False 表示已存在（跳过）。"""
    idempotency_key = f"release-{release_id}-user-{user_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{SUPABASE_REST}/email_logs",
            headers={**headers, "Prefer": "return=minimal"},
            json={
                "release_id": release_id,
                "user_id": user_id,
                "email": email,
                "idempotency_key": idempotency_key,
                "status": "pending",
            },
        )
        if r.status_code == 409:  # duplicate
            return False
        return r.status_code in (200, 201, 204)


async def _update_email_log(log_id: int, data: dict, headers: dict):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.patch(
            f"{SUPABASE_REST}/email_logs",
            headers={**headers, "Prefer": "return=minimal"},
            params={"id": f"eq.{log_id}"},
            json=data,
        )


async def _insert_test_log(admin_id: str, email: str, release_id: int | None, status: str, error: str | None):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{SUPABASE_REST}/email_test_logs",
            headers=_service_role_headers(),
            json={
                "admin_id": admin_id,
                "email": email,
                "release_id": release_id,
                "status": status,
                "error_message": error or "",
            },
        )


async def _recover_stale_sending(release_id: int):
    """如果 email_status='sending' 且 email_started_at 超过 30 分钟 → 恢复为 partial_failed"""
    h = _service_role_headers()
    release = await _fetch_release(release_id, h)
    if not release or release["email_status"] != "sending":
        return

    started = release.get("email_started_at")
    if not started:
        await _patch_release(release_id, {"email_status": "partial_failed"}, h)
        return

    from datetime import datetime as dt
    elapsed = dt.now(timezone.utc) - dt.fromisoformat(started.replace("Z", "+00:00"))
    if elapsed < timedelta(minutes=STALE_TIMEOUT_MINUTES):
        return

    logger.warning(f"Release {release_id} email_status=sending stale (started={started}), recovering")
    # 将超时的 pending 标记为 failed
    pending_logs = await _get_email_logs(release_id, h, status="pending")
    for log in pending_logs:
        await _update_email_log(log["id"], {
            "status": "failed",
            "error_message": "Background email task timeout/recovery",
        }, h)
    await _patch_release(release_id, {"email_status": "partial_failed"}, h)


# ═══════════ Public Endpoints ═══════════

@router.get("", response_model=List[ReleaseOut])
async def list_releases(
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
):
    """列出已发布版本（公开）。"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{SUPABASE_REST}/system_releases",
            headers={"apikey": settings.SUPABASE_ANON_KEY},
            params={
                "select": "*",
                "status": "eq.published",
                "order": "published_at.desc",
                "limit": str(limit),
            },
        )
        r.raise_for_status()
        return r.json()


@router.get("/{release_id}", response_model=ReleaseOut)
async def get_release(
    release_id: int,
    user: Optional[dict] = Depends(optional_auth),
):
    """查看版本详情。

    普通用户：仅能查看 published → draft 返回 404
    管理员：可查看 draft + published
    """
    is_admin = user and user.get("app_metadata", {}).get("role") == "admin"

    if is_admin:
        release = await _fetch_release(release_id, _service_role_headers())
    else:
        release = await _fetch_release(release_id, {"apikey": settings.SUPABASE_ANON_KEY})
        if release and release["status"] != "published":
            release = None

    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    return release


# ═══════════ Admin Endpoints ═══════════

@router.get("/debug/smtp")
async def smtp_debug():
    """诊断接口：查看后端实际读到的 SMTP 配置 + 解析结果 + 连通性（不含密码）。"""
    import socket
    import smtplib

    out = {
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_use_ssl": settings.SMTP_USE_SSL,
        "smtp_password_set": bool(settings.SMTP_PASSWORD),
    }
    try:
        addrs = socket.getaddrinfo(settings.SMTP_HOST, settings.SMTP_PORT)
        out["resolved"] = [
            {"family": "IPv6" if a[0] == socket.AF_INET6 else "IPv4", "addr": a[4][0]}
            for a in addrs
        ]
    except Exception as e:
        out["resolved_error"] = f"{type(e).__name__}: {e}"

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8)
        out["connect"] = "OK"
        try:
            server.quit()
        except Exception:
            pass
    except Exception as e:
        out["connect"] = f"FAILED: {type(e).__name__}: {e}"

    return out


@router.get("/admin/releases", response_model=List[ReleaseOut])
async def admin_list_releases(
    user: dict = Depends(require_admin),
):
    """管理员：查看全部版本（含 draft）。"""
    h = _service_role_headers()
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{SUPABASE_REST}/system_releases",
            headers=h,
            params={"select": "*", "order": "created_at.desc", "limit": "50"},
        )
        # 每次查看时检查 stale sending 并恢复
        for release in r.json():
            if release["email_status"] == "sending":
                await _recover_stale_sending(release["id"])
        # 重新获取最新数据
        r2 = await client.get(
            f"{SUPABASE_REST}/system_releases",
            headers=h,
            params={"select": "*", "order": "created_at.desc", "limit": "50"},
        )
        return r2.json()


@router.post("/admin/releases", response_model=ReleaseOut, status_code=201)
async def create_release(
    body: ReleaseCreate,
    user: dict = Depends(require_admin),
):
    """管理员：创建版本草稿。"""
    h = _service_role_headers()

    # 检查版本号唯一性
    async with httpx.AsyncClient(timeout=10) as client:
        check = await client.get(
            f"{SUPABASE_REST}/system_releases",
            headers=h,
            params={"select": "id", "version": f"eq.{body.version}"},
        )
        if check.status_code == 200 and check.json():
            raise HTTPException(status_code=409, detail=f"版本号 {body.version} 已存在")

        r = await client.post(
            f"{SUPABASE_REST}/system_releases",
            headers={**h, "Prefer": "return=representation"},
            json={
                "version": body.version,
                "title": body.title,
                "summary": body.summary,
                "content": body.content,
                "status": "draft",
                "email_status": "not_sent",
                "created_by": user.get("sub"),
            },
        )
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Supabase error: {r.text[:200]}")
        return r.json()[0]


@router.patch("/admin/releases/{release_id}", response_model=ReleaseOut)
async def update_release(
    release_id: int,
    body: ReleaseUpdate,
    user: dict = Depends(require_admin),
):
    """管理员：修改版本（仅 draft 可修改）。"""
    h = _service_role_headers()
    release = await _fetch_release(release_id, h)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release["status"] == "published":
        raise HTTPException(status_code=400, detail="已发布版本不可修改，请创建新版本修正")

    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")

    # 版本号唯一性检查
    if "version" in patch:
        async with httpx.AsyncClient(timeout=10) as client:
            vcheck = await client.get(
                f"{SUPABASE_REST}/system_releases",
                headers=h,
                params={"select": "id", "version": f"eq.{patch['version']}"},
            )
            for row in (vcheck.json() or []):
                if row["id"] != release_id:
                    raise HTTPException(status_code=409, detail=f"版本号 {patch['version']} 已存在")

    await _patch_release(release_id, patch, h)
    updated = await _fetch_release(release_id, h)
    return updated


@router.post("/admin/releases/{release_id}/publish", response_model=ReleaseOut)
async def publish_release(
    release_id: int,
    user: dict = Depends(require_admin),
):
    """管理员：发布版本（draft → published，不可逆）。"""
    h = _service_role_headers()
    release = await _fetch_release(release_id, h)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release["status"] != "draft":
        raise HTTPException(status_code=400, detail="只有草稿可以发布")

    await _patch_release(release_id, {
        "status": "published",
        "published_at": _now_iso(),
    }, h)
    return await _fetch_release(release_id, h)


@router.post("/admin/releases/{release_id}/send-email", response_model=SendEmailResult)
async def send_release_emails(
    release_id: int,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_admin),
):
    """管理员：发送邮件通知。

    幂等保证：
    - 已 sent 的用户不重复创建 pending
    - 条件更新抢锁，防止并发
    - 使用 Resend Idempotency-Key 防重复投递
    """
    h = _service_role_headers()

    # 1. 验证版本
    release = await _fetch_release(release_id, h)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release["status"] != "published":
        raise HTTPException(status_code=400, detail="只有已发布版本才能发送邮件")

    # 2. 恢复检查
    if release["email_status"] == "sending":
        await _recover_stale_sending(release_id)
        release = await _fetch_release(release_id, h)
        if release["email_status"] == "sending":
            raise HTTPException(status_code=409, detail="邮件正在发送中，请等待完成")

    # 3. 并发保护：原子抢锁
    locked = await _conditional_patch_release(
        release_id,
        {"email_status": "sending", "email_started_at": _now_iso(), "email_sent_at": None},
        ["not_sent", "partial_failed"],
        h,
    )
    if locked == 0:
        raise HTTPException(status_code=409, detail="邮件发送已被其他请求抢占，请刷新后重试")

    # 4. 获取用户
    all_users = await get_all_user_emails()
    if not all_users:
        # 回退状态
        await _patch_release(release_id, {"email_status": "not_sent"}, h)
        raise HTTPException(status_code=400, detail="没有可发送的用户")

    # 5. 创建 pending email_logs（INSERT ... ON CONFLICT DO NOTHING）
    created = 0
    for u in all_users:
        if await _upsert_email_log(release_id, u["id"], u["email"], h):
            created += 1

    # 6. 后台发送
    background_tasks.add_task(_send_emails_background, release_id, release)

    return SendEmailResult(
        ok=True,
        total_users=len(all_users),
        new_pending=created,
        already_sent=len(all_users) - created,
    )


@router.post("/admin/releases/{release_id}/retry-failed", response_model=RetryResult)
async def retry_failed_emails(
    release_id: int,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_admin),
):
    """管理员：重试失败的邮件。

    规则：
    - sent → 永久跳过
    - failed → 重置为 pending，使用相同 idempotency_key
    - 不删除、不重建 email_logs
    """
    h = _service_role_headers()
    release = await _fetch_release(release_id, h)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release["status"] != "published":
        raise HTTPException(status_code=400, detail="只有已发布版本才能重试邮件")

    # 恢复检查
    if release["email_status"] == "sending":
        await _recover_stale_sending(release_id)
        release = await _fetch_release(release_id, h)
        if release["email_status"] == "sending":
            raise HTTPException(status_code=409, detail="邮件正在发送中")

    if release["email_status"] not in ("partial_failed",):
        raise HTTPException(status_code=400, detail=f"当前状态 {release['email_status']} 不需要重试")

    # 条件抢锁
    locked = await _conditional_patch_release(
        release_id,
        {"email_status": "sending", "email_started_at": _now_iso(), "email_sent_at": None},
        ["partial_failed"],
        h,
    )
    if locked == 0:
        raise HTTPException(status_code=409, detail="状态已变更，请刷新后重试")

    # 只取 failed 记录 → 重置为 pending（保留 idempotency_key）
    failed_logs = await _get_email_logs(release_id, h, status="failed")
    for log in failed_logs:
        await _update_email_log(log["id"], {
            "status": "pending",
            "error_message": "",
        }, h)

    if not failed_logs:
        await _patch_release(release_id, {"email_status": "completed"}, h)
        return RetryResult(ok=True, retried=0)

    background_tasks.add_task(_send_emails_background, release_id, release)
    return RetryResult(ok=True, retried=len(failed_logs))


@router.get("/admin/releases/{release_id}/email-logs", response_model=List[EmailLogOut])
async def get_email_logs_endpoint(
    release_id: int,
    user: dict = Depends(require_admin),
):
    """管理员：查看邮件发送日志。"""
    h = _service_role_headers()
    logs = await _get_email_logs(release_id, h)
    return logs


@router.delete("/admin/releases/{release_id}")
async def delete_release(
    release_id: int,
    user: dict = Depends(require_admin),
):
    """管理员：删除版本（仅 draft 可删除）。"""
    h = _service_role_headers()
    release = await _fetch_release(release_id, h)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release["status"] == "published":
        raise HTTPException(status_code=400, detail="已发布版本禁止删除")
    async with httpx.AsyncClient(timeout=10) as client:
        await client.delete(
            f"{SUPABASE_REST}/system_releases",
            headers=h,
            params={"id": f"eq.{release_id}"},
        )
    return {"ok": True}


@router.post("/admin/test-email")
async def test_email_endpoint(
    body: TestEmailRequest,
    user: dict = Depends(require_admin),
):
    """管理员：发送测试邮件，验证 Worker → Resend 链路。"""
    result = await send_test_email(body.email)
    await _insert_test_log(
        admin_id=user.get("sub", ""),
        email=body.email,
        release_id=None,
        status="sent" if result.get("ok") else "failed",
        error=result.get("error"),
    )
    return result


# ═══════════ Background Task ═══════════

async def _send_emails_background(release_id: int, release: dict):
    """后台任务：逐用户发送邮件。

    使用 email_logs 作为状态来源，每封邮件独立处理。
    成功 → sent + provider_message_id
    失败 → failed + error_message
    最后更新 release email_status。

    异常处理：如果整个任务因意外崩溃，标记 partial_failed 以便管理员恢复。
    """
    h = _service_role_headers()
    pending = await _get_email_logs(release_id, h, status="pending")
    failed_count = 0

    try:
        for log in pending:
            html_body = build_release_email_html(
                version=release["version"],
                title=release["title"],
                content=release["content"],
            )
            # 去除 version 中的换行符，防止邮件头注入
            subject = f"【装修成本AI系统】{release['version'].replace(chr(10), '').replace(chr(13), '')} 版本更新通知"

            result = await send_email_via_worker(
                to=log["email"],
                subject=subject,
                html=html_body,
                idempotency_key=log["idempotency_key"],
            )

            if result.get("ok"):
                await _update_email_log(log["id"], {
                    "status": "sent",
                    "sent_at": _now_iso(),
                    "provider_message_id": result.get("message_id") or "",
                }, h)
            else:
                await _update_email_log(log["id"], {
                    "status": "failed",
                    "error_message": (result.get("error") or "Unknown error")[:500],
                }, h)
                failed_count += 1

        # 更新 release 状态
        new_status = "completed" if failed_count == 0 else "partial_failed"
        await _patch_release(release_id, {
            "email_status": new_status,
            "email_sent_at": _now_iso(),
        }, h)
    except Exception as e:
        logger.error(f"Background email task crashed for release {release_id}: {e}", exc_info=True)
        # 将未处理的 pending 标记为 failed，方便管理员恢复
        remaining_pending = await _get_email_logs(release_id, h, status="pending")
        for log in remaining_pending:
            await _update_email_log(log["id"], {
                "status": "failed",
                "error_message": f"Background task crashed: {str(e)[:200]}",
            }, h)
        await _patch_release(release_id, {
            "email_status": "partial_failed",
            "email_sent_at": _now_iso(),
        }, h)
