-- ============================================================
-- pricing_failures — 失败计数累加修复（RPC 改 SECURITY DEFINER）
--
-- 【问题】report_pricing_failure 是 SECURITY INVOKER，后端用 anon key 调用；
--   表上只有 failures_insert / failures_select 两条策略，没有 UPDATE 策略。
--   → 首次上报（新名称）插入成功；同名再报走 ON CONFLICT DO UPDATE 被 RLS 拒绝，
--     整个函数抛异常 —— 后端 except 吞掉返回 ok:false，前端 .catch(()=>{}) 也不看。
--   实测证据（2026-10-28 生产只读查询）：
--     SELECT count(*), count(*) FILTER (WHERE fail_count>1),
--            count(*) FILTER (WHERE last_seen<>created_at) FROM pricing_failures;
--     → 114 / 0 / 0：累加与 last_seen 更新从未发生过一次。
--
-- 【修法】函数改 SECURITY DEFINER（以属主 postgres 身份执行，绕过 RLS），
--   并钉死 search_path 防定义者函数被 search_path 劫持。
--   不新增任何 UPDATE 策略 —— anon 依旧不能直接改表，写入口只剩这一个 RPC。
--
-- 【执行】Supabase Dashboard → SQL Editor，按 STEP 顺序。
--   STEP 1 幂等（CREATE OR REPLACE），可重复执行。
--   不改表结构、不改数据；已有 114 行 fail_count 维持原值，
--   从下一次「重复失败」开始正常累加。
-- ============================================================

-- ── STEP 0（只读预检）─────────────────────────────────────────
-- relforcerowsecurity = true 时连属主也受 RLS 约束，本修法无效，
-- 需退回「补一条 UPDATE 策略」方案（代价：anon 可改整表）。
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class
WHERE relname = 'pricing_failures' AND relnamespace = 'public'::regnamespace;

-- ── STEP 1：修复（函数体与生产逐字一致，仅加 SECURITY DEFINER + search_path）──
CREATE OR REPLACE FUNCTION public.report_pricing_failure(
    p_name character varying,
    p_spec text DEFAULT ''::text,
    p_unit character varying DEFAULT ''::character varying
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $function$
BEGIN
  INSERT INTO pricing_failures (item_name, item_spec, item_unit)
  VALUES (p_name, p_spec, p_unit)
  ON CONFLICT (item_name, item_spec)
  DO UPDATE SET fail_count = pricing_failures.fail_count + 1, last_seen = NOW();
END;
$function$;

-- ── STEP 2（空跑验证，整段贴；事务 ROLLBACK，不留任何数据）──────────────
-- 以 anon 身份连调两次：第二次走 DO UPDATE，回读应得 fail_count = 2。
-- 修复前这一步会报 RLS 错误（new row violates row-level security policy）。
BEGIN;
SET LOCAL ROLE anon;
SELECT public.report_pricing_failure('__rls_probe__', 'probe', '项');
SELECT public.report_pricing_failure('__rls_probe__', 'probe', '项');
SELECT fail_count FROM public.pricing_failures WHERE item_name = '__rls_probe__';
ROLLBACK;

-- 若 STEP 2 报「permission denied to set role anon」：当前会话无权模拟 anon，
-- 跳过 STEP 2，改用真实前端跑一次 AI 套价（对内模式）后再跑下面这句，
-- 有任一 fail_count > 1 即证明累加已通：
--   SELECT item_name, fail_count, last_seen <> created_at AS updated
--   FROM pricing_failures WHERE fail_count > 1 ORDER BY fail_count DESC;

-- ── STEP 3（回读函数属性，应见 prosecdef = true 与 proconfig 含 search_path）──
SELECT proname, prosecdef, proconfig
FROM pg_proc
WHERE proname = 'report_pricing_failure';
