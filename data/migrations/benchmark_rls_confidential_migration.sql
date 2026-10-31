-- ══════════════════════════════════════════════════════════════════════════
-- 价表保密迁移：把「外部可读」收紧成「登录后可读」
--
-- 背景：497 条内部基准价 + 296 条集团 ZS02 基准价是机密数据。保密裁定是
--   「对已注册用户不需要保密，对外部绝对保密」，而库里这几张表的 SELECT 策略
--   写的是 TO public（= 匿名 key 也能全量读），anon/publishable key 本就公开，
--   所以 RLS 是唯一的门。本迁移把这些表改成 TO authenticated。
--
-- ⚠️ 执行顺序（很重要，别抢跑）：
--   1) 先把新后端 + 新前端发布上线（后端三个 loader 已改 service_role 优先，
--      前端离线兜底已改走 GET /api/v1/benchmark/snapshot）；
--   2) 再在 Supabase Dashboard → SQL Editor 执行本文件；
--   3) 最后按文件末尾「③ 关闭注册」在 Dashboard 关自助注册与匿名登录。
--   反过来的话，后端在 service_role 未生效的窗口里会读到空候选池（不报错，静默空）。
--
-- 用法：整段复制进 SQL Editor 执行。每步都可回滚（见文末 ROLLBACK）。
-- ══════════════════════════════════════════════════════════════════════════

-- ── ① 先看清楚现状（只读，不改任何东西；建议先单独跑这段核对）────────
SELECT c.relname AS table_name,
       c.relrowsecurity AS rls_enabled,
       p.polname,
       pg_get_expr(p.polqual, p.polrelid) AS using_expr,
       ARRAY(SELECT COALESCE(r::regrole::text, 'public') FROM unnest(p.polroles) r) AS roles,
       CASE p.polcmd WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT' WHEN 'w' THEN 'UPDATE'
                      WHEN 'd' THEN 'DELETE' WHEN '*' THEN 'ALL' ELSE p.polcmd::text END AS cmd
FROM pg_class c
LEFT JOIN pg_policy p ON p.polrelid = c.oid
WHERE c.relname IN ('benchmark_items','group_benchmark_items','group_pricing_rules',
                    'material_prices','main_material_catalog','pricing_failures','ai_knowledge')
ORDER BY c.relname, p.polname;

-- ── ② 收紧：价表只允许登录用户读 ──────────────────────────────────

-- 集团基准价两表：原先显式 TO public（localhost 免登录 anon 冒烟时留下的口子）
DROP POLICY IF EXISTS gbi_read_all ON public.group_benchmark_items;
CREATE POLICY gbi_read_auth ON public.group_benchmark_items
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS gpr_read_all ON public.group_pricing_rules;
CREATE POLICY gpr_read_auth ON public.group_pricing_rules
  FOR SELECT TO authenticated USING (true);

-- 内部基准价：策略本已是 TO authenticated，这里重复声明一次保证幂等
-- （若线上曾被人改成 TO public，这一步把它收回来）
DROP POLICY IF EXISTS benchmark_read_approved ON public.benchmark_items;
DROP POLICY IF EXISTS benchmark_read_auth ON public.benchmark_items;
CREATE POLICY benchmark_read_auth ON public.benchmark_items
  FOR SELECT TO authenticated USING (true);

-- 辅材信息价 + 主材目录：价目数据，同样只给登录用户
-- material_prices 原先可能根本没开 RLS，这里补上
ALTER TABLE public.material_prices ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS material_prices_read_all ON public.material_prices;
DROP POLICY IF EXISTS material_prices_read_auth ON public.material_prices;
CREATE POLICY material_prices_read_auth ON public.material_prices
  FOR SELECT TO authenticated USING (true);

ALTER TABLE public.main_material_catalog ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS main_material_catalog_read_all ON public.main_material_catalog;
DROP POLICY IF EXISTS main_material_catalog_read_auth ON public.main_material_catalog;
CREATE POLICY main_material_catalog_read_auth ON public.main_material_catalog
  FOR SELECT TO authenticated USING (true);

-- ── ③ 验证：匿名 key 必须读不到，登录 token 必须读得到 ─────────────
-- 这两条在 Dashboard 里跑不出「匿名」效果，请用 curl 或浏览器控制台验证：
--
--   # 匿名（期望：每张表都返回 []，且不报错——RLS 是静默过滤）
--   for t in benchmark_items group_benchmark_items group_pricing_rules material_prices main_material_catalog; do
--     echo -n "$t: "; curl -s "https://lnvtykghcpsjpwczbqsm.supabase.co/rest/v1/$t?select=*&limit=1" \
--       -H "apikey: sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q" \
--       -H "Authorization: Bearer sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q"; echo;
--   done
--
--   # 登录（把 <JWT> 换成浏览器 localStorage.getItem('sb-access-token')，期望：返回行）
--   curl -s "https://lnvtykghcpsjpwczbqsm.supabase.co/rest/v1/group_benchmark_items?select=code&limit=3" \
--     -H "apikey: sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q" -H "Authorization: Bearer <JWT>"
--
-- 后端侧（service_role 绕 RLS，不受本迁移影响）：
--   GET https://decoration-pricing-system.onrender.com/health → database: connected
--   AI 套价一条 → 有候选返回（若为空，先查 Render 是否配了 SUPABASE_SERVICE_ROLE_KEY）

-- ══════════════════════════════════════════════════════════════════════════
-- ROLLBACK（需要退回「公开可读」时执行）
--   DROP POLICY IF EXISTS gbi_read_auth ON public.group_benchmark_items;
--   CREATE POLICY gbi_read_all ON public.group_benchmark_items FOR SELECT TO public USING (true);
--   DROP POLICY IF EXISTS gpr_read_auth ON public.group_pricing_rules;
--   CREATE POLICY gpr_read_all ON public.group_pricing_rules FOR SELECT TO public USING (true);
--   DROP POLICY IF EXISTS benchmark_read_auth ON public.benchmark_items;
--   CREATE POLICY benchmark_read_auth ON public.benchmark_items FOR SELECT TO authenticated USING (true);
--   ALTER TABLE public.material_prices DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.main_material_catalog DISABLE ROW LEVEL SECURITY;
--
-- 注：pricing_failures / ai_knowledge 本次不动——
--   · pricing_failures 匿名可写是既有裁定（补库统计入口），行内是用户清单原文不是价；
--   · ai_knowledge 内容仍作为静态 ai_knowledge_base.json 发布在 Pages 上，
--     只收紧数据库这一侧等于没收（tool.html:840 也是不带 token 调 /api/v1/knowledge）。
--     要真收就得连静态文件一起下线，那是另一个决定。
-- ══════════════════════════════════════════════════════════════════════════
