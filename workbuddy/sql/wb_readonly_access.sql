-- ============================================================================
-- WorkBuddy 装修套价 · 专用只读账号与最小授权
-- 管理员在 Supabase Dashboard → SQL Editor 执行；本文件不含任何价格、密钥或令牌值。
--
-- 背景（2026-11-15 实测）：
--   既有价表的 RLS 收紧迁移已生效，匿名读全部返回空集；但读策略形如
--     FOR SELECT TO authenticated USING (true)
--   即「任何 Supabase 登录用户都能读全量价表」，并不等价于「只有专用账号能读」。
--   最终架构要求：项目公共授权共用「一个专用只读账号」，只给价表相关表 SELECT。
--
-- Supabase 里 authenticated 是共享角色，无法按账号做表级 GRANT；
-- 「只给专用账号」在行级只能靠白名单 + RLS 策略实现。
--
-- ── 分档（见 docs/系统设计-最终架构.md §3.3）────────────────────────────
--   A 档（当前默认，本文件不改动线上）：不改既有读策略。
--        专用账号是唯一被平台公共授权代持的身份；不建写策略、不设 is_admin、
--        可随时在 Dashboard 删除该用户完成撤销。旧网页应用不受影响。
--   B 档（强隔离，旧网页确认停用后执行）：执行本文件 ② ③ ④ 段，
--        把 12 张价表的 SELECT 策略改为「仅白名单内账号可读」。
--        ⚠️ 影响：旧网页普通登录用户将读不到价表；其前端直读
--           material_prices / main_material_* 会失效。后端走 service_role 的部分不受影响。
--
-- 前置：先执行 workbuddy/sql/wb_supabase_setup.sql 建好 3 张缺失表；
--       并已在 Authentication → Add user 创建专用账号（勾选 Auto Confirm），
--       该账号为普通 authenticated 用户，绝不是 service_role。
-- ============================================================================


-- ── ① A 档复核（只读，随时可跑，不改动任何对象）────────────────────────
-- 期望：下列价表的 SELECT 策略均为 TO authenticated、USING true；
--       且不存在任何向 anon / PUBLIC 开放的 SELECT 策略。
SELECT c.relname                                   AS table_name,
       c.relrowsecurity                           AS rls_enabled,
       p.polname                                  AS select_policy,
       pg_get_expr(p.polqual, p.polrelid)         AS using_expr,
       (0 = ANY(p.polroles))                     AS applies_to_public
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
LEFT JOIN pg_policy p ON p.polrelid = c.oid AND p.polcmd = 'r'
WHERE c.relname IN (
    'benchmark_items','group_benchmark_items','group_pricing_rules',
    'material_prices','main_material_catalog','main_material_categories',
    'main_material_prices','auxiliary_rules','ai_knowledge',
    'waste_rates','aux_excel_items','benchmark_aux_mapping')
ORDER BY c.relname, p.polname;

-- 专用账号身份自查（把邮箱换成实际值；UUID 是标识，不是凭据）
-- SELECT id, email, created_at FROM auth.users WHERE email = 'wb-readonly@<公司域>';

-- 确认专用账号没有管理员标记（若 profiles 表存在该列）
-- SELECT id, is_admin, is_approved FROM public.profiles WHERE id = '<专用账号 UUID>';


-- ============================================================================
-- ② B 档 · 白名单表与判定函数
--    只在决定「收紧到仅专用账号」时执行；A 档不要跑这一段之后的部分。
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.pricing_readers (
    user_id     uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    note        text,
    active      boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- 白名单表启用 RLS 且**不建任何读策略**：普通登录用户看不到名单，
-- 只有表所有者 / service_role 能维护；下面用 SECURITY DEFINER 函数代查。
ALTER TABLE public.pricing_readers ENABLE ROW LEVEL SECURITY;

-- SECURITY DEFINER 是必需的：价表策略里若直接子查询白名单表，
-- 会触发白名单表自身的 RLS，形成读不到 / 递归的问题。
-- search_path = '' 防止 search_path 劫持；所有对象写全限定名。
CREATE OR REPLACE FUNCTION public.is_pricing_reader()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.pricing_readers r
        WHERE r.user_id = (SELECT auth.uid())
          AND r.active
    );
$$;

REVOKE ALL ON FUNCTION public.is_pricing_reader() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_pricing_reader() TO authenticated;

-- 把专用账号加入白名单（UUID 从 ① 的自查语句取得）。
-- 这里刻意注释掉：占位符不是合法 uuid，直接执行会中断整段脚本。
-- 管理员把下面两处的 <专用账号 UUID> 换成真实 UUID 后单独执行一次：
--
-- INSERT INTO public.pricing_readers (user_id, note)
-- VALUES ('<专用账号 UUID>', 'WorkBuddy 项目公共授权 · 只读套价账号')
-- ON CONFLICT (user_id) DO UPDATE SET active = true, note = EXCLUDED.note;


-- ============================================================================
-- ③ B 档 · 12 张价表 SELECT 策略重建
--    只删 / 建 FOR SELECT 策略，**不触碰** INSERT / UPDATE / ALL 等写策略，
--    因此既有 *_write_admin（USING is_admin()）仍保持原样。
--    表不存在时跳过并提示，不会中断整段脚本。
-- ============================================================================

DO $$
DECLARE
    t        text;
    tbl_oid  oid;
    p        record;
    tables   text[] := ARRAY[
        'benchmark_items','group_benchmark_items','group_pricing_rules',
        'material_prices','main_material_catalog','main_material_categories',
        'main_material_prices','auxiliary_rules','ai_knowledge',
        'waste_rates','aux_excel_items','benchmark_aux_mapping'
    ];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        tbl_oid := to_regclass(format('public.%I', t));
        IF tbl_oid IS NULL THEN
            RAISE NOTICE '跳过 %：表不存在，请先执行 wb_supabase_setup.sql', t;
            CONTINUE;
        END IF;

        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);

        -- 删掉全部现有 SELECT 策略（名字各异，含历史 PUBLIC 策略）
        FOR p IN
            SELECT polname FROM pg_policy
            WHERE polrelid = tbl_oid AND polcmd = 'r'
        LOOP
            EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', p.polname, t);
        END LOOP;

        EXECUTE format('DROP POLICY IF EXISTS wb_read_pricing_reader ON public.%I', t);
        EXECUTE format(
            'CREATE POLICY wb_read_pricing_reader ON public.%I '
            'FOR SELECT TO authenticated USING (public.is_pricing_reader())', t);
        EXECUTE format('GRANT SELECT ON public.%I TO authenticated', t);
    END LOOP;
END $$;


-- ============================================================================
-- ④ B 档复核（只读）
-- ============================================================================

-- 期望：每张价表都有 wb_read_pricing_reader，且 using_expr 为
--       public.is_pricing_reader()，没有其它 FOR SELECT 策略。
SELECT c.relname AS table_name,
       p.polname AS select_policy,
       pg_get_expr(p.polqual, p.polrelid) AS using_expr
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
LEFT JOIN pg_policy p ON p.polrelid = c.oid AND p.polcmd = 'r'
WHERE c.relname IN (
    'benchmark_items','group_benchmark_items','group_pricing_rules',
    'material_prices','main_material_catalog','main_material_categories',
    'main_material_prices','auxiliary_rules','ai_knowledge',
    'waste_rates','aux_excel_items','benchmark_aux_mapping')
ORDER BY c.relname, p.polname;

-- 外部验收（在终端跑，不要在 SQL Editor 里跑）：
--   · 用专用账号 JWT 请求 /rest/v1/benchmark_items?select=internal_code&limit=1 → 应返回 1 行
--   · 用其它任何登录账号的 JWT 请求同一地址 → 应返回 []（RLS 静默过滤）
--   · 用 anon key 请求 → 应返回 []
--   · 专用账号对任意价表执行 INSERT / UPDATE / DELETE → 应被拒绝
--   · 本项目 CLI：python cli.py probe → 全表 ok 且行数非零，输出中不含价格


-- ============================================================================
-- ⑤ 可选：收紧两个历史匿名可读面（与套价无关，旧网页停用后执行）
--    profiles 匿名可读含 email / is_admin / is_approved；
--    pricing_failures 匿名可读含清单原文。只收 SELECT，不动既有写入。
--    执行前先确认没有其它功能依赖匿名读这两张表。
-- ============================================================================
-- ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS profiles_select_all ON public.profiles;
-- CREATE POLICY profiles_read_auth ON public.profiles
--     FOR SELECT TO authenticated USING (true);
--
-- SELECT polname FROM pg_policy
--  WHERE polrelid = 'public.pricing_failures'::regclass AND polcmd = 'r';
-- DROP POLICY IF EXISTS <上一步查到的匿名 SELECT 策略名> ON public.pricing_failures;


-- ============================================================================
-- ⑥ 撤销与回滚
-- ============================================================================

-- 6.1 撤销专用账号（立即失效）：
--     a) DELETE FROM public.pricing_readers WHERE user_id = '<专用账号 UUID>';
--     b) Dashboard → Authentication → 删除该用户
--     c) 项目配置 → 连接器 → 重新做一次公共授权（新账号）
--     d) 轮换后调用 datasource.clear_cache() 或重启任务

-- 6.2 回滚 B 档到 A 档（恢复「任何登录用户可读」）：
-- DO $$
-- DECLARE t text;
-- BEGIN
--   FOREACH t IN ARRAY ARRAY[
--     'benchmark_items','group_benchmark_items','group_pricing_rules',
--     'material_prices','main_material_catalog','main_material_categories',
--     'main_material_prices','auxiliary_rules','ai_knowledge',
--     'waste_rates','aux_excel_items','benchmark_aux_mapping'] LOOP
--     IF to_regclass(format('public.%I', t)) IS NULL THEN CONTINUE; END IF;
--     EXECUTE format('DROP POLICY IF EXISTS wb_read_pricing_reader ON public.%I', t);
--     EXECUTE format('CREATE POLICY wb_read_auth_rollback ON public.%I '
--                    'FOR SELECT TO authenticated USING (true)', t);
--   END LOOP;
-- END $$;
