-- ============================================================
-- 装修成本AI系统 — ai_pricing_logs 增加套价耗时列（elapsed_ms）
--
-- 目的：回答「几百条清单 AI 套价要跑多久」这类问题，不再靠猜。
--   写入方：backend/app/services/ai_pricing_service.py::price_single 的计时壳，
--           经 pricing_debug_logger.schedule_timing 旁路异步落库（不等回包）；
--           每行只填 item_name / item_spec / item_unit / elapsed_ms，
--           不落 prompt、候选、AI 原文（与 DEBUG_PRICING 开关无关）。
--   读取方：GET /api/v1/pricing/timing-stats?hours=24（聚合值，不含清单内容）
--           直接读表也可（需 service_role，本表 RLS 锁读）。
--
-- 执行顺序（重要）：本迁移必须先于后端新版本上线执行。
--   未执行时计时插入因「列不存在」被 PostgREST 400 拒绝，日志里会出现
--   [TIMING] 保存失败: … elapsed_ms …；套价本身不受影响（旁路 + 已 catch），
--   只是统计数据为空。
--
-- 幂等：可重复执行。
-- 执行方式：Supabase Dashboard → SQL Editor（本仓库脚本不直连 Supabase DDL）
-- ============================================================

-- 1. 加列
ALTER TABLE public.ai_pricing_logs
    ADD COLUMN IF NOT EXISTS elapsed_ms INTEGER;

COMMENT ON COLUMN public.ai_pricing_logs.elapsed_ms IS
    '单条套价耗时(ms)：从进 price_single 到返回/抛异常，含取数与候选筛选；NULL=旧行或调试日志整行';

-- 2. 验证（只读）
-- SELECT column_name, data_type FROM information_schema.columns
--  WHERE table_name = 'ai_pricing_logs' AND column_name = 'elapsed_ms';

-- 3. 手工看均速（可随时跑；聚合口径与 /timing-stats 一致）
-- SELECT count(*) AS 条数,
--        round(avg(elapsed_ms)) AS 均值ms,
--        percentile_disc(0.5)  WITHIN GROUP (ORDER BY elapsed_ms) AS p50,
--        percentile_disc(0.95) WITHIN GROUP (ORDER BY elapsed_ms) AS p95,
--        max(elapsed_ms) AS 最慢ms
--   FROM public.ai_pricing_logs
--  WHERE elapsed_ms IS NOT NULL
--    AND created_at >= now() - interval '24 hours';

-- 4. 最慢的几类清单（内部补库/提示词优化的依据）
-- SELECT item_name, count(*) AS 次数, round(avg(elapsed_ms)) AS 均值ms, max(elapsed_ms) AS 最慢ms
--   FROM public.ai_pricing_logs
--  WHERE elapsed_ms IS NOT NULL
--    AND created_at >= now() - interval '7 days'
--  GROUP BY item_name
--  ORDER BY 均值ms DESC
--  LIMIT 20;
