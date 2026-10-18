-- ============================================================
-- 装修成本AI系统 — ai_pricing_logs RLS 锁读迁移
-- （安全加固 P0-1）
-- 背景（2026-10-18 只读探测实证）：用站点公开的 anon key 即可
--   GET /rest/v1/ai_pricing_logs → 200，content-range 0-421/422，
--   含真实清单名/单位/时间戳与 prompt/响应预览；同法 projects 返回 []（RLS 正常），
--   证明该表读策略缺失或未启用 RLS。
-- 口径：
--   · 只锁 SELECT —— 任何匿名/登录用户直连 Supabase 不再能读到日志；
--     后端读取改走 service_role（绕 RLS，见 pricing_debug_logger._rest_auth）
--   · 保留匿名 INSERT —— 本机 DEBUG_PRICING=true 且未配 service_role 时写入不受影响；
--     与 pricing_failures「统计入口不设身份门槛」的既有裁定同构
-- 幂等：可重复执行（DO 块遍历 pg_policies 全部 DROP，不依赖历史策略名；
--       兜底覆盖「RLS 未启用 / 存在未知旧策略」两种现状）
-- 执行方式：Supabase Dashboard → SQL Editor（本仓库脚本不直连 Supabase DDL）
-- ============================================================

-- 1. 启用 RLS：未启用时，anon 可无视策略直读；启用后无策略即拒绝
ALTER TABLE public.ai_pricing_logs ENABLE ROW LEVEL SECURITY;

-- 2. 撤销一切既有策略（历史策略名未知，逐个 DROP；含任何 SELECT/ALL 放行策略）
DO $$
DECLARE
    p record;
BEGIN
    FOR p IN
        SELECT policyname
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'ai_pricing_logs'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.ai_pricing_logs', p.policyname);
    END LOOP;
END $$;

-- 3. 重建唯一策略：只放行 INSERT（后端写入 / 本机调试写入），SELECT 一律拒绝
DROP POLICY IF EXISTS ai_logs_insert ON public.ai_pricing_logs;
CREATE POLICY ai_logs_insert ON public.ai_pricing_logs
    FOR INSERT TO anon, authenticated WITH CHECK (true);

-- ============================================================
-- 4. 执行后验证（在终端跑，只读探测）
--   ① 匿名读 → 期望 []（200 空数组）；仍返回行 = 有策略漏网，回到第 2 步排查
--      curl "$SUPABASE_URL/rest/v1/ai_pricing_logs?select=id&limit=1" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY"
--   ② service_role 读 → 期望返回行（service_role 绕 RLS，后端 /pricing/debug-logs 同款）
--      curl "$SUPABASE_URL/rest/v1/ai_pricing_logs?select=id&limit=1" \
--        -H "apikey: $SERVICE_ROLE_KEY" -H "Authorization: Bearer $SERVICE_ROLE_KEY"
--   ③ 匿名写 → 期望 201/204（保留放行，本机调试写入不炸）
--      curl -X POST "$SUPABASE_URL/rest/v1/ai_pricing_logs" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
--        -H "Content-Type: application/json" -H "Prefer: return=minimal" \
--        -d '[{"item_name":"__rls_probe__"}]'
--      ⚠️ 探测③会留下一条 __rls_probe__ 垃圾行，验证完请用 SQL 删除：
--         DELETE FROM public.ai_pricing_logs WHERE item_name = '__rls_probe__';
--
-- 5. 与代码发布的顺序：可互换，互不炸
--    · 代码先上：本机未配 service_role 时读取回退 anon → 迁移前照常可读
--    · 迁移先跑：本机未配 service_role 时 /pricing/debug-logs 返回空（写入不受影响）；
--      要在本机看日志，在 backend/.env 补 SUPABASE_SERVICE_ROLE_KEY 即可（可选）
-- ============================================================
