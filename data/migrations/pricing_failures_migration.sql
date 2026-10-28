-- ============================================================
-- 装修成本AI系统 — pricing_failures 套价失败统计 留档迁移
-- （AI 一键套价 · 对内口径的库缺口统计表，admin「失败统计」排行数据源）
-- 来源：2026-10-16 从生产库（lnvtykghcpsjpwczbqsm）只读快照逐字转录，
--       非凭空重建。转录出处：
--   · 列/默认值  ← information_schema.columns
--   · 索引      ← pg_indexes（pkey / 唯一键 / idx_failures_count）
--   · RLS       ← pg_class.relrowsecurity + pg_policy
--   · 函数体    ← pg_get_functiondef('report_pricing_failure')，12 行全文
--   · 函数签名  ← pg_get_function_arguments：
--       p_name character varying, p_spec text, p_unit character varying
-- 幂等：可重复执行（IF NOT EXISTS / IF EXISTS / OR REPLACE / DROP POLICY IF EXISTS）
-- 执行方式：Supabase Dashboard → SQL Editor（本仓库脚本不直连 Supabase DDL）
-- ⚠️ 本文件为「留档 + 灾备重建」用途，生产已存在全部对象，无需再执行。
-- ⚠️ 本快照含已知缺陷：RPC 是 SECURITY INVOKER + 表无 UPDATE 策略 → 同名重复上报
--    走 DO UPDATE 被 RLS 拒绝，fail_count / last_seen 从未更新过一次
--    （2026-10-28 实测 114 / 0 / 0）。灾备重建须按序执行：
--    本文件 → pricing_failures_upsert_fix_migration.sql
-- ============================================================

-- ============================================================
-- 1. pricing_failures — 套价失败条目累加计数
--    写入方：backend /api/v1/pricing/report-failure → PostgREST
--            rpc/report_pricing_failure（anon key，靠 failures_insert 策略放行）
--    去重键：UNIQUE (item_name, item_spec) —— RPC 的 ON CONFLICT 依赖它，删之则累加变报错
--    空串口径：item_spec / item_unit 默认 ''（非 NULL），RPC 直传 p_spec，
--              前端未填规格时以「空串」参与唯一键匹配
-- ============================================================
CREATE TABLE IF NOT EXISTS public.pricing_failures (
    id          BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,  -- nextval('pricing_failures_id_seq')
    item_name   CHARACTER VARYING NOT NULL,        -- 清单名（后端截 200 字符）
    item_spec   TEXT DEFAULT ''::TEXT,             -- 清单特征/规格（后端截 2000 字符）
    item_unit   CHARACTER VARYING DEFAULT ''::CHARACTER VARYING,  -- 单位（后端截 20 字符）
    fail_count  INTEGER DEFAULT 1,                 -- 累计失败次数（设计 +1/次；2026-10-28 前从未累加，见修复迁移）
    last_seen   TIMESTAMP WITH TIME ZONE DEFAULT now(),  -- 最近一次失败时间
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 排行索引：/failure-stats 按 fail_count 倒序取 top N
CREATE INDEX IF NOT EXISTS idx_failures_count
    ON public.pricing_failures USING btree (fail_count DESC);

-- ============================================================
-- 2. RLS — 生产实测：relrowsecurity = true
--    failures_insert: INSERT 无 using（PG 语义），check = true
--                     —— 匿名可写，统计入口不设身份门槛
--    failures_select: SELECT using = true —— 匿名可读（admin 面板直查）
--    未配置 UPDATE/DELETE 策略 → anon 不可改删（那 7 条污染行当时是用
--    Dashboard 的 service_role 会话手删的，非应用权限）
-- ============================================================
ALTER TABLE public.pricing_failures ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS failures_insert ON public.pricing_failures;
CREATE POLICY failures_insert ON public.pricing_failures
    FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS failures_select ON public.pricing_failures;
CREATE POLICY failures_select ON public.pricing_failures
    FOR SELECT TO anon USING (true);

-- ============================================================
-- 3. report_pricing_failure — 失败上报 RPC（PostgREST /rpc/report_pricing_failure）
--    行为（设计）：首次见 (p_name, p_spec) → 插新行 fail_count=1；
--          已存在 → fail_count+1、last_seen=NOW()（item_unit 不更新）
--    ⚠️ 下面转录的是「修复前」的定义：INVOKER + 无 UPDATE 策略，累加分支实际不可达。
--    逐字转录自生产 pg_get_functiondef，含签名默认值。
-- ============================================================
CREATE OR REPLACE FUNCTION public.report_pricing_failure(
    p_name character varying,
    p_spec text DEFAULT ''::text,
    p_unit character varying DEFAULT ''::character varying
)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
  INSERT INTO pricing_failures (item_name, item_spec, item_unit)
  VALUES (p_name, p_spec, p_unit)
  ON CONFLICT (item_name, item_spec)
  DO UPDATE SET fail_count = pricing_failures.fail_count + 1, last_seen = NOW();
END;
$function$;

-- ============================================================
-- 冒烟验证（只读，随时可跑）：
--   SELECT proname, pg_get_function_arguments(oid) AS sig, pg_get_functiondef(oid) AS def
--     FROM pg_proc WHERE proname = 'report_pricing_failure';
--   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'pricing_failures';
--   SELECT relrowsecurity FROM pg_class WHERE relname = 'pricing_failures';
-- ============================================================
