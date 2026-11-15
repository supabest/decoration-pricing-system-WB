# 阶段 1 · 平台配置 Runbook

> 目标：让 WorkBuddy 项目在**项目公共授权**下读到 Supabase 云端唯一一份价表，补齐三张缺失表，并通过 `probe` 验收。
> 架构基线：`docs/系统设计-最终架构.md` v1.0（已同步项目资产）。
> 本文件不含任何价格数值、不含任何凭据值。

## 0. 进入阶段 1 时已核实的状态

| 项 | 实测结果 |
|---|---|
| 价表主体 | 8 张表在库，匿名读全部返回空集 → **RLS 收紧迁移已生效** |
| 缺失表 | `waste_rates`、`aux_excel_items`、`benchmark_aux_mapping` → REST 404，需建表 + 补库 |
| 历史匿名面 | `profiles` 9 行、`pricing_failures` 114 行匿名可读（与套价无关，待旧网页停用后收） |
| supabase 连接器 | `auth_mode = personal`，**尚未改公共授权**（官方：协作任务中不可用） |
| 网络 | 用户侧直连 `*.supabase.co` HTTP 000（绕开代理仍失败）；经 `/sb` 反代可达 |
| 反代能力 | 放行 `GET/POST/PATCH/DELETE`，白名单含 `authorization` / `apikey` / `prefer` / `content-type`；上游超时 15s |
| 本地 `probe` 基线 | 8 张 `empty`（匿名被 RLS 拦）+ 3 张 `missing`，退出码 2 |
| 补库载荷 | `waste_rates` 475 / `aux_excel_items` 497 / `benchmark_aux_mapping` 497 行，字段与建表列一致 |

## 1. 本轮已完成的阶段 1 代码准备（不需要管理员操作）

| 改动 | 作用 |
|---|---|
| `cli.py preflight`（新命令） | 只回报「数据源 / REST 通道 / apikey / 身份 / 兜底开关」是否配置，**绝不回显值**；退出码 2 表示未就绪 |
| `probe()` 状态细分 | `ok` / `empty`（表在但 0 行，多半未带身份）/ `missing`（REST 404，未建表）/ `error`；退出码 2=缺表、3=0 行、4=连接异常 |
| `sync_seeds()` 分批 POST | 每批 100 行，避开反代 15s 超时；失败报批次号，`merge-duplicates` 保证重跑幂等 |
| `cli.py sync-seeds --dry-run` | 只预演行数与批次数：不联网、不需要令牌、不写任何数据 |
| 全量回归 | **203/203 通过**（原 198 + 新增 5 项） |

## 2. 管理员侧 5 步（按序执行）

### ① 建专用只读账号

Supabase Dashboard → **Authentication → Users → Add user**，建一个普通账号。

- 必须是普通 `authenticated` 用户，**不是 service_role**
- 只授价表相关表 SELECT；`sql/wb_supabase_setup.sql` 不建任何写策略，因此该账号天然改不了价
- 可随时在 Dashboard 删除该用户完成撤销
- 既有读策略是 `TO authenticated USING (true)`，任何登录用户都能读；**默认 A 档**不改线上策略，靠「平台只代持这一个账号」实现最小授权。要按账号强隔离，需旧网页停用后执行 `sql/wb_readonly_access.sql` **B 档**

### ② 执行补表 SQL

SQL Editor 新建 query，粘贴 `workbuddy/sql/wb_supabase_setup.sql` 全文并执行。

- 建 `waste_rates` / `aux_excel_items` / `benchmark_aux_mapping` 三表 + 索引
- 三表启用 RLS，只建 `FOR SELECT TO authenticated USING (true)`，**不建 INSERT/UPDATE 策略**
- 文件末尾第 ⑤ 段（收紧 `profiles` / `pricing_failures` 匿名读）是**注释状态**，旧网页未停用前不要执行
- 复核：文件末尾第 ⑥ 段查询应返回三张表 `relrowsecurity = true`

### ③ 一次性补库 `sync-seeds`

在**有加密快照的环境**（管理员本机），设临时环境变量后执行：

```bash
cd workbuddy/scripts

# 先预演：不联网、不写库，只看行数与批次
python cli.py sync-seeds --dry-run
# 期望输出：475 / 497 / 497 行，各 5 批，status=dry-run

# 确认无误后正式补库（需一次性管理员写令牌）
python cli.py sync-seeds
# 期望：每张表 rows / batches / HTTP 201
```

本步需要的环境变量（**只在当前终端设置，不写文件、不进仓库、不贴对话，用完 `unset`**）：

| 变量 | 值来源 |
|---|---|
| `WB_SUPABASE_URL` | 直连 `https://<project>.supabase.co`，或反代 `https://<pages 域名>/sb` |
| `WB_SUPABASE_ANON_KEY` | Supabase → Project Settings → API → publishable / anon key |
| `WB_SUPABASE_SYNC_TOKEN` | 一次性管理员写令牌（service_role 或可写账号 JWT），**用完立即清除** |
| `BENCHMARK_SNAPSHOT_KEY` | 加密快照解密密钥（自备，不入库） |
| `BENCHMARK_SNAPSHOT_PATH` | 自备加密快照路径（仓库不含数据） |

> **为什么这一步允许 service_role**：它是一次性数据迁移，执行者是你本人，用完即清。红线禁的是「用 service_role 作为日常取数身份」——日常取数始终走专用只读账号 + RLS。补库完成并 `probe` 通过后，该令牌不再需要。

预期：`waste_rates` 475 行（5 批）、`aux_excel_items` 497 行（5 批）、`benchmark_aux_mapping` 497 行（5 批）。全部写入内存后直接 POST，**不落盘、不打印任何价格**。

### ④ 改为公共授权

项目详情页 → 右侧**项目配置** → **连接器** → 找到 `supabase` → 改为 / 新增**公共授权**，用 ① 建的专用只读账号授权一次。

- 官方定义：公共授权 = 管理员统一授权一次，成员共享同一账号或凭据，**协作任务中可用**，调用日志仅管理员可见
- 当前是 `personal`，官方明确「多人协作任务仅支持公共授权连接器」，必须改
- 凭据由平台云端代持：不给 AI、不给同事、不写文件、不贴对话、不进仓库
- 同事只需是 WorkBuddy 项目成员，**不需要 Supabase 账号，也不必是 GitHub collaborator**

### ⑤ 验收

```bash
python cli.py preflight   # 期望 exit 0：数据源 supabase / URL 已配置 / apikey 有 / 身份有 / 兜底关闭
python cli.py probe       # 期望 exit 0：11 张表全部 ok 且行数非零，末行「云端价表全部可读」
```

再做一个**匿名对照**：只用 anon key（不带 authenticated 身份）跑一次 `probe`，期望全部 `empty`（或 `missing`），证明 RLS 仍拦匿名。

> 关于「去掉 `/sb` 反代」：已挂一次性云端探测任务 `15718979`（11:34，绑 `supabase` 连接器）验证腾讯云出口能否直连 `*.supabase.co` 并回报凭据注入情况。直连成功 → `WB_SUPABASE_URL` 改直连地址，反代依赖可下线；不通 → 保留 `/sb` 作纯数据通道。Pages 属原远端部署，本项目不擅自改动或下线。

## 3. 一个必须在阶段 1 说清的平台能力边界

**实证**（`mcp__wb-issues__automation_create` 参数 schema + 腾讯云《项目》文档）：项目级云端自动化的创建参数**没有 secrets / env / cwds 字段**；文档只说明「项目配置的连接器可在任务中复用、公共授权优先展示」，**没有说明会把凭据注入为脚本可读的环境变量**。

也就是说，「公共授权连接器」与「`datasource.py` 能读到 `WB_SUPABASE_TOKEN`」是两件事，后者尚未证实。

**已决策的默认方案（不挂起、不改架构）**：

| 场景 | 处理方式 |
|---|---|
| 阶段 1 的库 / 表 / SQL / 脚本链路验证 | 管理员本机用一次性环境变量跑 `preflight` / `probe` / `sync-seeds`。这验证的是数据正确性，**不涉及多人凭据分发**，值用完即清 |
| 云端探测任务回报「已注入 env」 | 阶段 2/3 按现设计实现：项目 Skill 的脚本在云端任务里直接读 REST，成员零配置 |
| 回报「未注入 env」 | 在取数层补一个**连接器代理通道**（`connector_source.py`），由平台代持的授权完成取数；**价表位置、公共授权、保密红线全部不变**，绝不退回本地加密快照主路径 |
| 需要分级授权 | 叠加应用层权限（记录 WB 成员 / 任务 / 子目编号，不记金额），不改数据位置 |

一句话：**价表永远只在你的 Supabase 账号里；变的是「脚本怎么拿到授权」，不是「数据放在哪」。**

## 4. 失败处置

| 现象 | 原因 | 处置 |
|---|---|---|
| `preflight` 报「缺 authenticated 身份」 | 未注入 JWT，也没给专用账号邮箱/密码 | 检查 ④ 公共授权是否生效；或临时设 `WB_SUPABASE_EMAIL` / `WB_SUPABASE_PASSWORD` 让脚本换一次令牌 |
| `probe` 8 张 `empty` | 用的是 anon key，被 RLS 拦 | 换 authenticated JWT；**不要用 service_role 当日常身份** |
| `probe` 3 张 `missing` | ② 建表 SQL 未执行 | 执行 `wb_supabase_setup.sql` |
| `probe` 全表 `error` | REST 地址不通或 apikey 缺失 | 直连不通改 `/sb` 反代；检查 `WB_SUPABASE_URL` / `WB_SUPABASE_ANON_KEY` |
| `sync-seeds` HTTP 401 / 403 | 令牌权限不足或表未建 | 确认 ② 已执行；用一次性 service_role 令牌 |
| `sync-seeds` HTTP 504 | 反代上游 15s 超时 | 已改为每批 100 行；仍失败则减小 `datasource.SYNC_BATCH` 或改直连 |
| `sync-seeds` 某批失败 | 网络抖动 | 直接重跑：`resolution=merge-duplicates` 按主键幂等，不会重复插入 |

## 5. 阶段 1 完成判据

- [ ] 专用只读账号已建，且**不是** service_role
- [ ] 三张新表已建，`relrowsecurity = true`
- [ ] 补库完成：475 / 497 / 497 行，`probe` 里三张表不再是 `missing`
- [ ] supabase 连接器 `auth_mode = public`
- [ ] `preflight` exit 0；`probe` exit 0、11 张表全 `ok` 且行数非零
- [ ] 匿名对照 `probe` 仍读不到任何行
- [ ] 一次性 service_role 令牌已从环境中清除

全部达成后进入**阶段 2（三费补全 / 主材映射）**。阶段 2 的代码与单测可用 fixture 先开工，不依赖本阶段收尾。
