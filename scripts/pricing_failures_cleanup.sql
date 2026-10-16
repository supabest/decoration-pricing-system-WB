-- ══════════════════════════════════════════════════════════════════════════
-- pricing_failures 污染清理（对甲报价模式 AI 套价修复后的数据回填）
--
-- 背景：修复前 docs/tool.html 的失败上报无 `if (!gMode)` 护栏，且过滤条件用
--       allRows（全量清单）而非 targets（未套价行）。对甲模式下 ZS02-OTH 分部
--       的七个标准金额行天生无子目，每跑一次 AI 套价就白报 7 条「失败」，
--       经 report_pricing_failure RPC 累加进 fail_count，污染 admin 的内部补库决策。
--       代码修复见 docs/tool.html 的 `if (!gMode) try { ... }`（commit d08dafb
--       「对甲报价模式开放 AI 一键套价」同批落地，非 cb39a4d）。
--
-- 真实列名（2026-10-15 information_schema 实测，勿再按后端 RPC 形参 p_* 猜）：
--   id bigint NOT NULL · item_name varchar NOT NULL · item_spec text
--   item_unit varchar · fail_count int · last_seen timestamptz · created_at timestamptz
--   ⚠️ 后端 RPC 收的是 p_name/p_spec/p_unit，与列名不同名；failure-stats 用 select=*
--      所以 admin 面板一直正常，只有手写 SQL 会踩列名。
--
-- 用法：整段贴进 Supabase Dashboard → SQL Editor，按 STEP 逐段选中执行。
--       DELETE 前先跑 STEP 3 确认命中行数，别直接删。
--
-- 注意：表无 mode/purpose 列，集团口径的真实清单名（用户项目里的行）无法机器判别，
--       只能靠 STEP 2 人工过一遍后补进 STEP 4b。
-- ══════════════════════════════════════════════════════════════════════════


-- ── STEP 1：表结构（列名与本脚本假设不一致时先停下）───────────────────────
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'pricing_failures'
ORDER BY ordinal_position;


-- ── STEP 2：全量导出人工过一遍（fail_count 降序，污染项通常计数异常高）────
SELECT id, item_name, item_unit, fail_count, last_seen, created_at
FROM pricing_failures
ORDER BY fail_count DESC;


-- ── STEP 3a：统计「七个 OTH 标准金额行」命中情况（先看，不删）──────────────
--   这七个名字只存在于对甲 OTH 分部（docs/tool.html OTH_STD_ROWS → makeRow({name:t.name})），
--   内部基准价库永不产生同名行 → 命中即可安全整行删。
SELECT count(*) AS rows_to_delete, coalesce(sum(fail_count), 0) AS polluted_fail_count
FROM pricing_failures
WHERE item_name IN (
  '暂列金额',
  '暂估价',
  '精装修管理及配合费',
  '预算包干费',
  '合同变更费用',
  '装修类型涨幅费用',
  '赶工措施费'
);

-- STEP 3b：想看具体是哪几条、计数多少，换成明细
SELECT id, item_name, item_unit, fail_count, last_seen, created_at
FROM pricing_failures
WHERE item_name IN (
  '暂列金额','暂估价','精装修管理及配合费','预算包干费',
  '合同变更费用','装修类型涨幅费用','赶工措施费'
)
ORDER BY fail_count DESC;


-- ── STEP 4：删除（确认 STEP 3 输出后再执行）───────────────────────────────
-- 4a. 七个 OTH 标准行 —— 安全，内部口径不可能有同名行
DELETE FROM pricing_failures
WHERE item_name IN (
  '暂列金额','暂估价','精装修管理及配合费','预算包干费',
  '合同变更费用','装修类型涨幅费用','赶工措施费'
);

-- 4b. 从 STEP 2 人工认出的集团口径清单名，逐个补进来再跑。
--     ⚠️ 若某名字在对内口径也真实失败过，删掉会一并丢内部统计；
--        这种行改成只减计数不删行，见 STEP 5。
-- DELETE FROM pricing_failures
-- WHERE item_name IN ('<STEP2 里认出的集团行名 1>','<... 2>');


-- ── STEP 5（可选）：不删行、只把虚增计数扣回真实值 ─────────────────────────
--     适用：某行既被对甲白报 N 次、又在对内真实失败过，想保住内部统计。
--     把 <NAME> 与 <N> 换成实际值；GREATEST 兜底防负数。
-- UPDATE pricing_failures
-- SET fail_count = GREATEST(fail_count - <N>, 0)
-- WHERE item_name = '<NAME>';


-- ── STEP 6：复核剩余排行（admin 补库决策依据）─────────────────────────────
SELECT item_name, item_unit, fail_count, last_seen
FROM pricing_failures
ORDER BY fail_count DESC
LIMIT 50;


-- ══════════════════════════════════════════════════════════════════════════
-- 本次执行结论（2026-10-15，已跑完）
--
-- 1. 污染范围 = 七个 OTH 标准行（id 441–447），全部 fail_count=1、
--    created_at === last_seen === 2026-10-13 13:36:12 同一秒 → 对甲模式只跑过一轮，
--    从未在对内模式下被上报。STEP 4a 删除，零附带损失。
--
-- 2. id 448–454 断档【不是】ON CONFLICT 更新既有行。
--    判据：STEP 6 之后追加的窗口查询
--      WHERE last_seen >= '2026-10-13' AND last_seen < '2026-10-14'
--    只返回 1 行（id 455），无任何 created_at 更早的行 last_seen 落在当天。
--    → 那 7 个号是失败插入消耗的（nextval 先取号，事务回滚/RLS 拒绝后号不退回）。
--    → 无需 STEP 5 扣数。
--
-- 3. id 455「室内门安装」(item_unit=樘, fail_count=1, 13:38:58) 刻意保留：
--    内部库门工程子目 YQ-039/040/041 全是 m² 计价，无按樘项，
--    属真实的内部补库缺口信号，不是污染。
--
-- 复用提示：将来若再出现同类污染，先跑 STEP 2 看 created_at 是否 === last_seen
-- 且 fail_count===1（一次性的证据），再跑 last_seen 窗口查询确认有无被虚增的老行，
-- 两步都过了才决定删还是扣。
-- ══════════════════════════════════════════════════════════════════════════
