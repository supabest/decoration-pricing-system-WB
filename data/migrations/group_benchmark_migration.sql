-- ============================================================
-- 装修成本AI系统 — ZS02 集团基准价清单 + 集团取费参数 数据库迁移
-- （对甲报价引擎 P1）
-- 内容：group_benchmark_items / group_pricing_rules 建表 + 9 行费率种子 + RLS
-- 幂等：可重复执行（CREATE TABLE IF NOT EXISTS / ON CONFLICT DO NOTHING /
--        DROP POLICY IF EXISTS）
-- 执行方式：Supabase Dashboard → SQL Editor（本仓库脚本不直连 Supabase DDL）
-- 执行后冒烟 SQL（供执行者顺手跑）：
--   select id, is_admin from public.profiles where id = auth.uid();
-- ============================================================

-- ============================================================
-- 1. group_benchmark_items — ZS02 集团基准价清单（296 条，Task2 导入）
-- ============================================================
CREATE TABLE IF NOT EXISTS public.group_benchmark_items (
    code            TEXT PRIMARY KEY,              -- 'ZS02-A-009'
    discipline      TEXT NOT NULL CHECK (discipline IN ('A','B','C','D')),
    section_name    TEXT NOT NULL DEFAULT '',
    name            TEXT NOT NULL,
    spec            TEXT DEFAULT '',
    unit            TEXT NOT NULL,
    work_type       TEXT DEFAULT '',
    lab_price       NUMERIC DEFAULT 0,             -- A
    mats            JSONB DEFAULT '[]',            -- [{name,price,unit,consumption}] price=null 即甲供未定价
    aux_cost        NUMERIC DEFAULT 0,             -- D
    mech_cost       NUMERIC DEFAULT 0,             -- E
    is_owner_supply BOOLEAN DEFAULT false,
    raw_composite   NUMERIC,                       -- Excel 原 H（校验锚点）
    source_row      INT
);

-- ============================================================
-- 2. group_pricing_rules — 集团取费参数 / 规则（kind: rate|fee|rule_text）
-- ============================================================
CREATE TABLE IF NOT EXISTS public.group_pricing_rules (
    key      TEXT PRIMARY KEY,                     -- 'mgmt_rate' 等
    label    TEXT NOT NULL,
    value    NUMERIC,
    unit     TEXT DEFAULT '',
    kind     TEXT NOT NULL DEFAULT 'rate',
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 3. 费率种子（9 行；fee 类 value=NULL 待 admin 必填，重复执行不覆盖已有值）
-- ============================================================
INSERT INTO public.group_pricing_rules (key,label,value,unit,kind) VALUES
  ('mgmt_rate','管理费率',0.17,'×(人工+机械)','rate'),
  ('profit_rate','利润率',0.12,'×(人工+机械)','rate'),
  ('green_safety_rate','绿色施工安全防护措施费率',0.13,'×∑(分部分项人工+机械)','rate'),
  ('lump_sum_rate','预算包干费率',0.03,'×∑(分部分项人工+机械)','rate'),
  ('tax_rate','税金率',0.09,'×(一+二+三)','rate'),
  ('fitout_coordination_fee','精装修管理及配合费',NULL,'元/m2(装修面积,admin必填)','fee'),
  ('overtime_fee','赶工措施费',NULL,'手工金额','fee'),
  ('contract_change_fee','合同变更费用',NULL,'手工金额','fee'),
  ('inflation_fee','装修类型涨幅费用',NULL,'手工金额','fee')
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- 4. RLS：与 benchmark_items 同构（authenticated 可读；写需管理员）
--    管理员校验沿用库内既有可执行写法：profiles.is_admin 布尔列 + auth.uid() 关联，
--    而非 brief 草稿中的 public.is_admin() 函数（该函数在本仓库/库内未定义，
--    SQL Editor 执行会报 function does not exist）。
--    依据：supabase-profile-insert-policy.sql:9 (auth.uid() = id) +
--          admin.html:446 / tool.html:744 / CLAUDE.md:116 (profiles.is_admin boolean)
-- ============================================================
-- 依赖：public.profiles 存在且 authenticated 可读自身行（own-row SELECT policy）；
--       否则写策略静默拒绝。
ALTER TABLE public.group_benchmark_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.group_pricing_rules  ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS gbi_read_auth ON public.group_benchmark_items;
CREATE POLICY gbi_read_auth ON public.group_benchmark_items FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS gbi_write_admin ON public.group_benchmark_items;
CREATE POLICY gbi_write_admin ON public.group_benchmark_items FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin))
    WITH CHECK (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin));

DROP POLICY IF EXISTS gpr_read_auth ON public.group_pricing_rules;
CREATE POLICY gpr_read_auth ON public.group_pricing_rules FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS gpr_write_admin ON public.group_pricing_rules;
CREATE POLICY gpr_write_admin ON public.group_pricing_rules FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin))
    WITH CHECK (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin));
