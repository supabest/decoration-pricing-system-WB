"""Pydantic 模型 — 版本发布 + 邮件通知"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ═══════════ 请求模型 ═══════════

class ReleaseCreate(BaseModel):
    version: str = Field(..., min_length=1, max_length=32, description="版本号，如 V1.3.0")
    title: str = Field(..., min_length=1, max_length=256)
    summary: str = Field(default="", max_length=1024)
    content: str = Field(default="", max_length=65536)


class ReleaseUpdate(BaseModel):
    version: Optional[str] = Field(None, min_length=1, max_length=32)
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    summary: Optional[str] = Field(None, max_length=1024)
    content: Optional[str] = Field(None, max_length=65536)


class TestEmailRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=256)


# ═══════════ 响应模型 ═══════════

class ReleaseOut(BaseModel):
    id: int
    version: str
    title: str
    summary: str
    content: str
    status: str
    email_status: str
    email_started_at: Optional[datetime] = None
    email_sent_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    published_at: Optional[datetime] = None


class EmailLogOut(BaseModel):
    id: int
    release_id: int
    user_id: str
    email: str
    idempotency_key: str
    provider_message_id: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class SendEmailResult(BaseModel):
    ok: bool
    total_users: int
    new_pending: int
    already_sent: int


class RetryResult(BaseModel):
    ok: bool
    retried: int
