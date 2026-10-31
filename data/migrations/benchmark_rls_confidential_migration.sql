-- ══════════════════════════════════════════════════════════════════════════
-- 价表保密迁移 v2：把「外部可读」收紧成「登录后可读」
--
-- v1 作废原因（2026-10-31 用只读查询核对线上 pg_policy 后确认）：
--   · v1 里 DROP 的是 benchmark_read_approved / benchmark_read_auth —— 库里
--     这两个名字都不存在，真实策略叫 benchmark_read_public（SELECT TO PUBLIC）。
--     DROP POLICY IF EXISTS 对不存在的名字静默跳过，所以 v1 跑完「显示成功」
--     但 497 条价表照样匿名全量可读。CLAUDE.md 原写「benchmark_items 已是
--     authenticated」是错的，已一并纠正。
--   · v1 漏了 main_material_catalog / main_material_categories /
--     main_material_prices 三张表：rls_enabled = false，一条策略都没有，
--     anon key 直连即可全量读（main_material_prices 是真正带主材单价的表）。
--   · v1 给 material_prices 造了个新策略名，而库里 mat_read_auth 早就写好了
--     ——它只是因为 RLS 没开而空转。这张表只需要 ENABLE RLS。
--
-- 线上现状（本文件据此编写，2026-10-31 取证）：
--   benchmark_items        rls_on   benchmark_read_public  SELECT TO PUBLIC  USING true   ← 洞
--   group_benchmark_items  rls_on   gbi_read_all           SELECT TO PUBLIC  USING true   ← 洞
--   group_pricing_rules    rls_on   gpr_read_all           SELECT TO PUBLIC  USING true   ← 洞
--   material_prices        rls_OFF  （mat_read_auth / mat_write_admin 空转，RLS 未开）      ← 洞
--   main_material_*        rls_OFF  （无任何策略）                                          ← 洞
--   ai_pricing_logs        rls_on   pricing_logs_select    SELECT TO PUBLIC               ← 洞
--   （*_write_admin 一批是 ALL TO PUBLIC 但 USING is_admin()，非匿名可写，本次不动）
--
-- ⚠️ 执行前提（都已满足，留作复跑时的检查）：
--   1) 新后端已上线且 Render 配了 SUPABASE_SERVICE_ROLE_KEY —— 后端三个价表
--      loader 走 service_role 绕 RLS；没配的话收紧后候选池会静默变空。
--   2) 新前端已上线 —— 离线兜底已改走 GET /api/v1/benchmark/snapshot（需登录态）。
--   3) 后端不读 material_prices / main_material_*（已 grep 确认无 REST 调用），
--      所以这三张表开 RLS 不影响 AI 套价；辅材/主材价由前端带着登录 token 读。
--   4) ai_pricing_logs 的读写都走 _rest_auth()（service_role 优先），
--      锁 SELECT 不会关掉刚上线的耗时统计 /pricing/timing-stats。
--
-- 用法：整段复制进 Supabase Dashboard → SQL Editor 执行。可回滚（见文末）。
-- ══════════════════════════════════════════════════════════════════════════

-- ── ① 内部基准价：关掉 PUBLIC 读，只留登录用户 ──────────────────────
DROP POLICY IF EXISTS benchmark_read_public ON public.benchmark_items;
DROP POLICY IF EXISTS benchmark_read_approved ON public.benchmark_items;
CREATE POLICY benchmark_read_auth ON public.benchmark_items
  FOR SELECT TO authenticated USING (true);

-- ── ② 集团基准价 + 集团费率 ────────────────────────────────────────
DROP POLICY IF EXISTS gbi_read_all ON public.group_benchmark_items;
CREATE POLICY gbi_read_auth ON public.group_benchmark_items
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS gpr_read_all ON public.group_pricing_rules;
CREATE POLICY gpr_read_auth ON public.group_pricing_rules
  FOR SELECT TO authenticated USING (true);

-- ── ③ 辅材信息价：库里策略已存在，只差把 RLS 开关打开 ───────────────
ALTER TABLE public.material_prices ENABLE ROW LEVEL SECURITY;

-- ── ④ 三张主材表：原先根本没开 RLS（= 全开放）
--    只给 SELECT 建登录可读策略；不建写策略是刻意的——全仓库代码没有任何
--    写这三张表的地方（已 grep 确认）。今后要改主材价，走 Dashboard 的
--    Table Editor（超级用户角色不受 RLS 限制），不要用未登录接口写。
ALTER TABLE public.main_material_catalog  ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS mmc_read_auth ON public.main_material_catalog;
CREATE POLICY mmc_read_auth ON public.main_material_catalog
  FOR SELECT TO authenticated USING (true);

ALTER TABLE public.main_material_categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS mmc_cat_read_auth ON public.main_material_categories;
CREATE POLICY mmc_cat_read_auth ON public.main_material_categories
  FOR SELECT TO authenticated USING (true);

ALTER TABLE public.main_material_prices   ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS mmp_read_auth ON public.main_material_prices;
CREATE POLICY mmp_read_auth ON public.main_material_prices
  FOR SELECT TO authenticated USING (true);

-- ── ⑤ 调试日志：锁 SELECT（这份已覆盖 2026-10-18 那份待执行文件，二选一即可）
--    行里没有价格，但有用户清单原文；写入必须保留，否则本机 DEBUG_PRICING 与
--    计时落库会静默失败。
DROP POLICY IF EXISTS pricing_logs_select ON public.ai_pricing_logs;
DROP POLICY IF EXISTS ai_logs_insert ON public.ai_pricing_logs;
DROP POLICY IF EXISTS pricing_logs_insert ON public.ai_pricing_logs;
CREATE POLICY ai_logs_insert ON public.ai_pricing_logs
  FOR INSERT TO anon, authenticated WITH CHECK (true);

-- ── ⑥ 复核：跑完这段，三列都应为 0（还有 PUBLIC/anon 可读的价表）────
SELECT c.relname AS table_name,
       c.relrowsecurity AS rls_enabled,
       (SELECT count(*) FROM pg_policy p
         WHERE p.polrelid = c.oid AND p.polcmd IN ('r','*')
           AND (0 = ANY(p.polroles)
                OR 'anon' = ANY(SELECT x::regrole::text FROM unnest(p.polroles) x)))
       AS still_open_anon_select
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
WHERE c.relname IN ('benchmark_items','group_benchmark_items','group_pricing_rules',
                    'material_prices','main_material_catalog','main_material_categories',
                    'main_material_prices','ai_pricing_logs')
ORDER BY c.relname;

-- ── ⑦ 外部验收（这条必须在 Dashboard 里跑不出效果，用终端或浏览器控制台）──
--   # 匿名：期望每张表都返回 []（RLS 是静默过滤，不报错，所以 [] 就是关好了）
--   for t in benchmark_items group_benchmark_items group_pricing_rules \
--            material_prices main_material_catalog main_material_prices ai_pricing_logs; do
--     echo -n "$t: "; curl -s "https://lnvtykghcpsjpwczbqsm.supabase.co/rest/v1/$t?select=*&limit=1" \
--       -H "apikey: sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q" \
--       -H "Authorization: Bearer sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q"; echo;
--   done
--
--   # 登录（把 <JWT> 换成线上站点 localStorage.getItem('sb-access-token')，期望返回行）
--   curl -s "https://lnvtykghcpsjpwczbqsm.supabase.co/rest/v1/benchmark_items?select=internal_code&limit=3" \
--     -H "apikey: sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q" -H "Authorization: Bearer <JWT>"
--
--   # 线上功能不能被打破：
--   #   GET https://decoration-pricing-system.onrender.com/health → database: connected
--   #   站点登录后 AI 套价一条 → 有候选返回（空 = service_role 没生效，先查 Render）
--   #   GET /api/v1/pricing/timing-stats → count 不为 0（证明日志写入没被锁死）

-- ══════════════════════════════════════════════════════════════════════════
-- ROLLBACK（需要退回「公开可读」时执行；把 ⑥ 恢复成原样即可）
--   DROP POLICY IF EXISTS benchmark_read_auth ON public.benchmark_items;
--   CREATE POLICY benchmark_read_public ON public.benchmark_items FOR SELECT USING (true);
--   DROP POLICY IF EXISTS gbi_read_auth ON public.group_benchmark_items;
--   CREATE POLICY gbi_read_all ON public.group_benchmark_items FOR SELECT USING (true);
--   DROP POLICY IF EXISTS gpr_read_auth ON public.group_pricing_rules;
--   CREATE POLICY gpr_read_all ON public.group_pricing_rules FOR SELECT USING (true);
--   ALTER TABLE public.material_prices      DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.main_material_catalog  DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.main_material_categories DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.main_material_prices   DISABLE ROW LEVEL SECURITY;
--   DROP POLICY IF EXISTS mmc_read_auth ON public.main_material_catalog;
--   DROP POLICY IF EXISTS mmc_cat_read_auth ON public.main_material_categories;
--   DROP POLICY IF EXISTS mmp_read_auth ON public.main_material_prices;
--   -- ai_pricing_logs 的 SELECT 策略原本就不该有，回滚时不需要恢复
-- ══════════════════════════════════════════════════════════════════════════

-- 本次刻意不动，及原因：
--   · pricing_failures（SELECT TO PUBLIC + INSERT TO anon）：匿名可写是既有裁定，
--     行内是用户清单原文不是价。但它确实对外可读清单原文，要不要一起收是业务决定。
--   · ai_knowledge / knowledge_read_approved（TO PUBLIC 但 USING auth.uid() IS NOT NULL）：
--     匿名实际读不到，无需动。
--   · auxiliary_rules / benchmark_notes / feedback / projects / profiles：
--     这些表也有 TO PUBLIC 的策略，但 USING 表达式尚未取证（多半是 is_admin 判定）。
--     取证前不盲改——改错会让管理面板保存失败，且 RLS 的错误是静默的。
