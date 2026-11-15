# Supabase 云端价表 · WorkBuddy 项目接入说明

> 适用：多人协作的 WorkBuddy 项目。基准价只存在 Supabase 云端，项目成员共用一份；
> 同事不需要 Supabase 账号，也接触不到任何凭据。
> 本文不含任何定价明细、密钥或令牌值。

## 一、2026-11-15 只读体检结论

| 项 | 实测 | 判定 |
|---|---|---|
| REST 连通 | 用户侧直连 `*.supabase.co` 失败（SSL EOF，绕开本机代理仍失败）；经同源反代 `/sb` 可达 | ⚠️ 网络通道需按环境选择 |
| 既有价表 RLS | `benchmark_items`、`group_benchmark_items`、`group_pricing_rules`、`material_prices`、`main_material_catalog`、`main_material_categories`、`main_material_prices`、`auxiliary_rules`、`ai_knowledge`、`ai_pricing_logs` 匿名读取**全部返回空集** | ✅ 收紧迁移已生效，匿名拿不到价表 |
| 价表主体 | 上述表均存在，含人工基准价、集团价、辅材信息价、辅材规则、主材三表 | ✅ 已在库 |
| 缺失表 | `waste_rates`、`aux_excel_items`、`benchmark_aux_mapping` → REST 404 | ❌ 475 条损耗率、497 条辅材清单项、497 条辅材映射**只在加密快照里，未上云** |
| 本地种子 | `data/seeds/` 已从 git 索引移除，工作区目录也已不存在 | 加密快照是这三类数据的现存副本 |
| 历史匿名面 | `profiles` 匿名可读 9 行（含 email、is_admin、is_approved）；`pricing_failures` 匿名可读 114 行（含清单原文） | ⚠️ 与套价无关，待旧网页停用时一并收紧 |
| 平台授权 | 项目 supabase 连接器当前为 `personal`（个人授权）；官方规定「多人协作任务仅支持公共授权连接器」 | ❌ 需改为公共授权 |

**结论**：库本身是好的、RLS 也是好的；要「适合 WorkBuddy 平台调用」缺的是三件事 —— **公共授权身份**、**三张缺失表**、**可达的网络通道**。

## 二、目标架构

```
WorkBuddy 项目（交互 / 模型判子目 / 脚本计价与成本分析 / 项目资产存产物）
        │  项目公共授权（管理员一次授权，成员共用，凭据平台云端代持）
        ▼
Supabase（唯一数据源：人工 + 辅材 + 主材基准价，RLS 只允许 authenticated 读）
```

- 不需要网页前端；不需要独立部署的运算后端。确定性计价由项目 Skill 的脚本完成。
- 清单、报价表、成本分析结果存**项目资产**（云端），不生成本地 xlsx。
- 旧 Pages / Render 不参与新链路，是否下线另行决定，本项目不改动它们。

> **架构唯一基线**：`docs/系统设计-最终架构.md`（六层落点、数据契约、成本分析规格、项目资产规范、阶段路线与验收）。本文只负责接入配置。

## 三、配置步骤（管理员操作，共 4 步）

### 1. Supabase 建专用只读账号

Dashboard → Authentication → Add user，用专用邮箱（如 `wb-readonly@<公司域>`），勾选 **Auto Confirm**。
这是普通 `authenticated` 用户，**不要给 service_role**。既有读策略是 `TO authenticated USING (true)`，
该账号自动可读全部价表；不建任何写策略，因此改不了价。可随时在 Dashboard 删除该用户完成撤销。

**「只给专用账号读」的两档处理**（详见 `sql/wb_readonly_access.sql` 与系统设计 §3.3）：

| 档 | 做法 | 触发条件 |
|---|---|---|
| **A 档（当前默认）** | 不改既有读策略。专用账号是唯一被平台代持的身份，无写权限、可随时撤销 | 立即生效，配公共授权即可 |
| **B 档（强隔离）** | 白名单表 + `is_pricing_reader()`，把 12 张价表 SELECT 策略改为仅白名单账号可读 | **旧网页确认停用后**；会让旧网页普通登录用户读不到价表 |

Supabase 的 `authenticated` 是共享角色，无法按账号做表级 GRANT，所以严格意义上的「只给专用账号」在行级只能靠 B 档实现。B 档脚本已备好但**不自动执行**。

> 若平台连接器复用网页登录态并校验 `profiles.is_approved`，需给此账号在 `profiles` 补一行
> `is_approved = true`；纯 REST + JWT 不需要。

### 2. 补齐三张缺失表

在 Supabase SQL Editor 执行 `workbuddy/sql/wb_supabase_setup.sql`（只建表结构与 RLS，无数据）。
然后在受控环境一次性执行：

```bash
export WB_SUPABASE_URL=<REST 地址>
export WB_SUPABASE_ANON_KEY=<publishable key>
export WB_SUPABASE_SYNC_TOKEN=<管理员级令牌，仅本次补库用，用完立即撤销>
python cli.py sync-seeds
```

`sync-seeds` 从加密快照读出三类数据直接 POST 到云端，**不落盘、不打印任何价格**，
只回传每张表的行数与 HTTP 状态。执行完立刻清除 `WB_SUPABASE_SYNC_TOKEN`。

### 3. 项目公共授权

项目详情页 → 右侧 **项目配置** → 连接器 → 把 `supabase` 配成**公共授权**，用第 1 步的专用账号授权一次。
按官方定义：公共授权由管理员统一完成，项目成员共享同一凭据，**协作任务中可用**，调用日志仅管理员可见。
个人授权的凭据只存成员本地、协作任务中不可用，不能满足多人共用。

### 4. 运行环境注入

| 变量 | 说明 |
|---|---|
| `WB_PRICING_SOURCE` | 设为 `supabase`（默认 `snapshot`，离线兜底） |
| `WB_SUPABASE_URL` | REST 根地址，见下节「网络通道」 |
| `WB_SUPABASE_ANON_KEY` | publishable / anon key（apikey 头） |
| `WB_SUPABASE_TOKEN` | 公共授权注入的 authenticated JWT |
| `WB_SUPABASE_EMAIL` / `WB_SUPABASE_PASSWORD` | 可选；公共授权未注入 JWT 时，用专用账号密码换一次令牌 |
| `WB_PRICING_FALLBACK` | 不设。仅调试时才设 `1` 允许云端失败回退本地快照 |

兼容读取 `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_ACCESS_TOKEN` 等常见变量名。
**以上值一律不写进仓库、不写进文档、不贴进对话。**

## 四、网络通道（重要）

实测用户侧网络到 `*.supabase.co` 被干扰（原项目注释亦记载「实测需 VPN 才通」），
且绕开本机代理仍失败，说明不是代理配置问题。三种选择：

| 通道 | `WB_SUPABASE_URL` | 适用 |
|---|---|---|
| 云端任务直连 | `https://<project>.supabase.co` | WorkBuddy 云端沙箱走腾讯云出口，**待实测**是否可达；若可达，这是最干净的方案，不依赖任何网页设施 |
| 同源反代 | `https://<pages 域名>/sb` | 当前已验证可达；反代只转发 `rest/v1` 与 `auth/v1`，是数据通道而非网页应用 |
| VPN | 直连地址 | 仅本地调试 |

`datasource.py` 的 REST 根地址完全由变量决定，两种通道无需改代码。
**建议在云端任务里先跑一次 `python cli.py probe` 验证直连**，通过即可把反代从依赖里去掉。

## 五、验证

```bash
python cli.py probe          # 只读：逐表输出状态 / 行数 / 字段名，绝不输出价格
WB_PRICING_SOURCE=supabase python cli.py stats
```

`probe` 全表 `ok` 且行数非零 = 公共授权生效、价表可读。
若 `benchmark_items` 为 0 行，几乎都是没带 authenticated 身份（RLS 拦截），回到第 3 步检查授权类型。

## 六、保密边界

- 价表只在进程内存：不落盘、不写日志、不进模型上下文（`prepare` 仍只产无价候选）。
- 云端取数失败**明确报错**，不静默回退本地旧快照，避免用过期价出表。
- 公共授权按项目共享身份，隔离粒度由「按人」变「按项目」；审计靠平台调用日志 +
  应用层记录「成员 / 任务 / 子目编号」，不记金额。
- 技能配成**项目 Skill**（云端统一管理），产物存**项目资产**；同事不需要 GitHub collaborator，
  因此 `main` 历史明文价表不会因加人而外泄。
- 禁止使用 `service_role` 作为日常取数身份（绕 RLS）。

## 七、后续阶段（规格已定稿，见系统设计 §7 / §8 / §12）

| 阶段 | 待办 | 规格位置 |
|---|---|---|
| 2 三费补全 | `main_material_prices` / `main_material_catalog` 已带入内存，但「子目 ↔ 主材」映射未建立；当前 `mat_price` 仍为 0，是最大成本失真来源。缺价行须显式标注，禁止静默按 0 | 系统设计 §7.1 |
| 3 成本分析 | `analysis.py` + `cli.py analyze`：三费构成与占比、按班组/分部汇总、单方造价、目标对比、异常行清单；`sink` 抽象把产物写项目资产 | 系统设计 §8 / §9 |
| B 档 / 匿名面 | `profiles` / `pricing_failures` 匿名 SELECT 收紧，与 12 张价表白名单策略一并执行 | `sql/wb_readonly_access.sql` ⑤、系统设计 §3.3 |
| 4 多人验收 | 配项目 Skill、邀请成员、第二位成员零配置跑同一清单结果一致 | 系统设计 §10 / §12 |

以上均为**实现与平台动作**，架构不再变动；实施时直接按规格开工，不需要重新确认数据放哪、身份怎么授权。
