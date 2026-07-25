-- ============================================
-- 装修报价系统 - 辅材字段迁移
-- 为 benchmark_items 增加辅材基准价字段
-- 执行方式：Supabase SQL Editor
-- ============================================

-- 增加辅材字段
ALTER TABLE public.benchmark_items ADD COLUMN IF NOT EXISTS aux_rule_type TEXT;
COMMENT ON COLUMN public.benchmark_items.aux_rule_type IS '辅材规则类型: FIXED | RATE | GROUP';

ALTER TABLE public.benchmark_items ADD COLUMN IF NOT EXISTS aux_fixed_k NUMERIC DEFAULT 0;
COMMENT ON COLUMN public.benchmark_items.aux_fixed_k IS '固定辅材K值（元/单位）';

ALTER TABLE public.benchmark_items ADD COLUMN IF NOT EXISTS aux_rate_detail JSONB;
COMMENT ON COLUMN public.benchmark_items.aux_rate_detail IS 'RATE/GROUP规则的材料配方JSON（不含价格，价格从material_prices取）：
RATE: {"type":"RATE","materialName":"1:3水泥砂浆","consume":0.0355,"unit":"m³"}
GROUP: {"type":"GROUP","items":[{"name":"灰砂砖","consume":0.558,"unit":"千块"},...]}
FIXED: NULL';
