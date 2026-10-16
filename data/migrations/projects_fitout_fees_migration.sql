-- T02 对甲报价汇总：装修面积 + 三项手工费 持久化列（2026-10-11）
-- 口径说明：四列均为项目级属性，由 docs/tool.html 云端草稿（doAutoSave）/正式保存（saveProject）
--   写入，恢复时写回（restoreProject）；类型 numeric 与 contract_amount/target_profit_rate 同构，
--   未填落 0（前端采集点已钳到 ≥0，负值不进库）
--   fitout_area          —— 装修面积 m²：T02 单方造价分母 + 精装修配合费（元/m²）基数
--   overtime_fee         —— 赶工措施费（手工金额，进第三部分「其他项目费」）
--   contract_change_fee  —— 合同变更费用（手工金额，同上）
--   inflation_fee        —— 装修类型涨幅费用（手工金额，同上）
-- 执行顺序：须先于/与 group_benchmark_migration.sql 同批执行 —— 后者建基准价/费率表（算费前置），
--   本文件补 projects 列（存档前置）；T8 上线前置清单将按此顺序引用本文件。
--   缺列后果：PostgREST 对未知列返回 400 → doAutoSave 仅 console.warn（草稿从此不再保存）、
--   saveProject 的 _post/_patch 不校验 HTTP 状态（仍弹「✓ 方案已保存」假成功），实为数据丢失。
-- 幂等：可重复执行（ADD COLUMN IF NOT EXISTS）
-- 执行方式：Supabase Dashboard → SQL Editor（本仓库脚本不直连 Supabase DDL）
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS fitout_area numeric;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS overtime_fee numeric;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS contract_change_fee numeric;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS inflation_fee numeric;

-- 执行后冒烟 SQL（供执行者顺手跑）：应返回 4 行，data_type 均为 numeric
SELECT column_name, data_type FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'projects'
   AND column_name IN ('fitout_area', 'overtime_fee', 'contract_change_fee', 'inflation_fee')
 ORDER BY column_name;
