-- 对内成本测算：项目合同金额 + 预估目标利润率（2026-08-30）
-- 口径说明：两字段属「对内」成本测算范畴，与对外报价的 mgmt_rate/profit_rate 严格分离
-- 项目总成本（目标）= contract_amount × (1 - target_profit_rate/100)
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS contract_amount numeric;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS target_profit_rate numeric;
