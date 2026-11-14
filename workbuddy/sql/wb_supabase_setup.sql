-- ============================================================
-- WorkBuddy 装修套价 · Supabase 接入准备（管理员在 SQL Editor 执行一次）
--
-- 目的：补齐「云端缺、只存在于本地加密快照」的三类辅材/损耗数据，
--       并把新表锁到与既有价表一致的 authenticated 读策略。
--
-- 本文件不含任何价格数值。数据由 `python cli.py sync-seeds` 用管理员令牌
-- 直接从加密快照 POST 到这三张表，全程不落盘、不打印价格。
--
-- 前置：既有价表的 RLS 收紧迁移 benchmark_rls_confidential_migration.sql
--       已在库中执行（2026-11-15 实测匿名读价表全部返回空集）。
-- ============================================================

-- ① 损耗率：475 条，按子目编号索引 --------------------------------
CREATE TABLE IF NOT EXISTS public.waste_rates (
    internal_code text PRIMARY KEY,
    waste_rate    numeric(10, 4) NOT NULL DEFAULT 0,
    updated_at    timestamptz NOT NULL DEFAULT now()
);

-- ② 辅材清单项：497 条，FIXED / RATE / GROUP 配方 -------------------
CREATE TABLE IF NOT EXISTS public.aux_excel_items (
    code          text PRIMARY KEY,
    name          text,
    unit          text,
    work_type     text,
    rate_mats     jsonb NOT NULL DEFAULT '[]'::jsonb,
    rule_type     text,
    source_sheet  text,
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_aux_excel_items_work_type
    ON public.aux_excel_items (work_type);

-- ③ 子目 ↔ 辅材规则映射：497 条 ------------------------------------
CREATE TABLE IF NOT EXISTS public.benchmark_aux_mapping (
    internal_code text PRIMARY KEY,
    rule_type     text,
    fixed_k       numeric(14, 4) NOT NULL DEFAULT 0,
    rate_detail   jsonb,
    rate_sum      numeric(14, 4),
    aux_total     numeric(14, 4),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

-- ④ RLS：与 benchmark_items 同口径，只允许登录用户读 ----------------
--    不建 INSERT/UPDATE 策略是刻意的：补库走 service_role（绕 RLS），
--    公共授权的只读账号永远无法改价。
ALTER TABLE public.waste_rates            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.aux_excel_items        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.benchmark_aux_mapping  ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS wb_waste_read_auth ON public.waste_rates;
CREATE POLICY wb_waste_read_auth ON public.waste_rates
    FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS wb_aux_read_auth ON public.aux_excel_items;
CREATE POLICY wb_aux_read_auth ON public.aux_excel_items
    FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS wb_auxmap_read_auth ON public.benchmark_aux_mapping;
CREATE POLICY wb_auxmap_read_auth ON public.benchmark_aux_mapping
    FOR SELECT TO authenticated USING (true);

GRANT SELECT ON public.waste_rates, public.aux_excel_items,
               public.benchmark_aux_mapping TO authenticated;

-- ============================================================
-- ⑤ 可选：收掉两个历史匿名可读面（改前请确认线上网页是否仍依赖）
--    2026-11-15 实测：profiles 匿名可读 9 行（含 email / is_admin / is_approved），
--    pricing_failures 匿名可读 114 行（含清单原文）。这两处与套价无关，
--    但会随 Pages 公网页面一起暴露。若已决定停用旧网页应用，可执行：
--
-- ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS profiles_select_all ON public.profiles;
-- CREATE POLICY profiles_read_auth ON public.profiles
--     FOR SELECT TO authenticated USING (true);
--
-- （pricing_failures 的匿名 INSERT 是既有裁定，只收 SELECT，不动写入：
--  DROP POLICY IF EXISTS <匿名 SELECT 策略名> ON public.pricing_failures;）
-- ============================================================

-- ⑥ 复核：三张新表 rls_enabled 应为 true，匿名 SELECT 应为 0 行
-- SELECT relname, relrowsecurity FROM pg_class
--  WHERE relname IN ('waste_rates','aux_excel_items','benchmark_aux_mapping');
