"""通过 Supabase Auth Admin API 获取用户邮箱

使用 service_role key 调用 GET /auth/v1/admin/users，分页获取所有用户。
"""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_all_user_emails(page_size: int = 200) -> list[dict]:
    """获取所有有效用户的邮箱。

    过滤条件:
      - 有 email
      - email_confirmed_at 不为空（邮箱已确认）
      - 未被 banned

    支持分页 — 当前 ~10 用户无需实际分页，但代码结构支持未来 100-500 人。

    Returns:
        [{"id": "<UUID>", "email": "user@example.com"}, ...]
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("SUPABASE_SERVICE_ROLE_KEY not configured, cannot fetch user emails")
        return []

    all_users = []
    page = 1

    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            r = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/admin/users",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                },
                params={"page": page, "per_page": page_size},
            )
            if r.status_code != 200:
                logger.error(f"Auth Admin API returned {r.status_code}: {r.text[:200]}")
                break

            data = r.json()
            users = data.get("users", [])
            if not users:
                break

            for u in users:
                email = u.get("email")
                if not email:
                    continue
                if not u.get("email_confirmed_at"):
                    continue
                if u.get("banned_until"):
                    continue
                all_users.append({"id": u["id"], "email": email})

            if len(users) < page_size:
                break
            page += 1

    return all_users
