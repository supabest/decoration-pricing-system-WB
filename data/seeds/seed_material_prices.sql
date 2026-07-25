-- ============================================
-- 装修报价系统 - 辅材信息价库
-- 建表 + 31种初始信息价种子
-- 执行方式：Supabase SQL Editor
-- ============================================

-- 建表（如已存在则跳过）
CREATE TABLE IF NOT EXISTS public.material_prices (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,                        -- 规范材料名
    unit TEXT,                                  -- 单位
    price NUMERIC NOT NULL DEFAULT 0,           -- 信息价
    effective_month TEXT NOT NULL,              -- 生效月份，如 2026-07
    source TEXT DEFAULT '管理员录入',            -- 来源
    remark TEXT,                                -- 备注
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.material_prices IS '辅材信息价库（按月版本化）';
COMMENT ON COLUMN public.material_prices.price IS '当月信息价（元/单位）';
COMMENT ON COLUMN public.material_prices.effective_month IS '生效月份，格式YYYY-MM';

-- 索引
CREATE INDEX IF NOT EXISTS idx_material_prices_name ON public.material_prices(name);
CREATE INDEX IF NOT EXISTS idx_material_prices_month ON public.material_prices(effective_month);
CREATE UNIQUE INDEX IF NOT EXISTS idx_material_prices_name_month ON public.material_prices(name, effective_month);

-- 初始化首批31种材料信息价（2024基准价）
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('100mm隔音棉', '', 15.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('12mm阻燃板基层', '', 35.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('9mm石膏板', 'm²', 16.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('9mm防潮石膏板', '', 16.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('9mm阻燃夹板', '', 26.25, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('C15细石混凝土', '', 350.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('专用瓷砖背胶', '', 3.61, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('专用美缝剂', '', 18.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('单组份聚氨酯防水涂料(I型)', 'kg', 13.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('吊顶钢架', '', 3500.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('水泥砂浆', 'm³', 350.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('水泥自流平漆', '', 10.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('灰砂砖', '', 320.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('瓷砖粘合剂', '', 12.5, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('石材粘合剂', '', 16.5, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('聚合物水泥防水涂料(II型)', 'kg', 10.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('聚氨酯橡胶隔声垫', 'm²', 45.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('钢筋混凝土', 'm³', 1000.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('镀锌钢材', '', 3500.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('陶粒混凝土', 'm³', 400.0, '2024-01', '2024基准价表');
INSERT INTO public.material_prices (name, unit, price, effective_month, source) VALUES ('隔音涂料', 'm²', 15.0, '2024-01', '2024基准价表');

-- 共 21 种材料信息价种子导入完毕
