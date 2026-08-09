-- ============================================================
-- 装修成本AI系统 — 版本发布 + 邮件通知 数据库迁移
-- 幂等：可重复执行
-- 执行方式：Supabase Dashboard → SQL Editor
-- ============================================================

-- ============================================================
-- 1. system_releases — 系统版本发布表
-- ============================================================
CREATE TABLE IF NOT EXISTS public.system_releases (
    id               BIGSERIAL PRIMARY KEY,
    version          TEXT NOT NULL,
    title            TEXT NOT NULL,
    summary          TEXT DEFAULT '',
    content          TEXT DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'draft'
                       CHECK (status IN ('draft', 'published')),
    email_status     TEXT NOT NULL DEFAULT 'not_sent'
                       CHECK (email_status IN ('not_sent', 'sending', 'completed', 'partial_failed')),
    email_started_at TIMESTAMPTZ,
    email_sent_at    TIMESTAMPTZ,
    created_by       UUID NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    published_at     TIMESTAMPTZ,
    CONSTRAINT uq_system_releases_version UNIQUE (version)
);

-- ============================================================
-- 2. email_logs — 邮件发送日志
-- ============================================================
CREATE TABLE IF NOT EXISTS public.email_logs (
    id                  BIGSERIAL PRIMARY KEY,
    release_id          BIGINT NOT NULL REFERENCES public.system_releases(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL,
    email               TEXT NOT NULL,
    idempotency_key     TEXT NOT NULL,
    provider_message_id TEXT DEFAULT '',
    status              TEXT NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'sent', 'failed')),
    error_message       TEXT DEFAULT '',
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_email_logs_release_user UNIQUE (release_id, user_id)
);

-- ============================================================
-- 3. email_test_logs — 测试邮件日志
-- ============================================================
CREATE TABLE IF NOT EXISTS public.email_test_logs (
    id            BIGSERIAL PRIMARY KEY,
    admin_id      UUID NOT NULL,
    email         TEXT NOT NULL,
    release_id    BIGINT,
    status        TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error_message TEXT DEFAULT '',
    sent_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_system_releases_status ON public.system_releases(status);
CREATE INDEX IF NOT EXISTS idx_system_releases_email_status ON public.system_releases(email_status);
CREATE INDEX IF NOT EXISTS idx_email_logs_release_id ON public.email_logs(release_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON public.email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_test_logs_admin_id ON public.email_test_logs(admin_id);

-- ============================================================
-- 5. RLS 策略
-- ============================================================
ALTER TABLE public.system_releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_test_logs ENABLE ROW LEVEL SECURITY;

-- system_releases: 任何人可读已发布版本
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'system_releases'
          AND policyname = 'releases_select_published'
    ) THEN
        CREATE POLICY releases_select_published ON public.system_releases
            FOR SELECT USING (status = 'published');
    END IF;
END $$;

-- email_logs / email_test_logs 仅 service_role 访问（不创建 public 策略）
