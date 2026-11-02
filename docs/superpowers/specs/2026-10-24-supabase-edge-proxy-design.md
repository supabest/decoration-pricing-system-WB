# 同源反代 Supabase（/sb）设计 — 解决客户端到 supabase.co 不可达

**日期**：2026-10-24　**分支**：dev　**状态**：待用户评审

## 1. 根因（已证，非推测）

| 目标 | 用户 Safari | 本机 Chromium | Render 服务器 |
|---|---|---|---|
| `…pages.dev`（前端） | ✅ | ✅ | — |
| `…onrender.com`（后端） | ✅（Swagger 截图） | ✅ | ✅ |
| `…supabase.co`（数据+登录） | ❌ Load failed | ❌ 4s 超时（10-24 复测） | ✅ 1.5–2.0s 返回真实数据 |

- 10-19 只有 Safari 不通（当时判断为 iCloud 私密中继）；10-24 两个浏览器都不通 → **本机网络到 `*.supabase.co` 的链路在退化**，与浏览器设置无关，关中继无效。
- Supabase 项目本身健康：Render 侧读 `system_releases` / `pricing_failures` 均 200 带数据；dashboard 里唯一 Unhealthy 的是 **Edge Functions**（本项目不使用，不构成解释）。
- 为什么只有「ZS02 库未加载」暴露：内部基准价库有同域静态兜底（`tool.html:1100` 读 `benchmark_data.json`），集团库刻意无兜底（价格不入 git）→ 断网时只有它空，前次误判为 RLS 权限，已更正。

## 2. 目标 / 非目标

**目标**：浏览器只要能打开 `pages.dev`，就能登录、能读写全部 Supabase 数据。
**非目标**：不解决 Supabase 免费档容量（RAM/升配）、不做数据库备份方案（另案待用户选）、不改后端与 Render 的直连方式（服务器侧链路正常，无需动）。

## 3. 设计

### 3.1 边缘反代（Cloudflare Pages Function）

`<Pages 项目>/functions/sb/[[path]].js`（module worker 形式）：

- **只放行两个前缀**：`/sb/rest/v1/*` → `https://<project>.supabase.co/rest/v1/*`；`/sb/auth/v1/*` → `…/auth/v1/*`。其余一律 400 拒绝（防变成开放代理 / SSRF）。
- 查询串原样保留（PostgREST 的 `select=`、`order=`、`eq.` 等语义不变）。
- 方法透传 GET/POST/PATCH/DELETE，**请求体流式转发**；`apikey`、`Authorization`、`Prefer`、`Range`、`Content-Type` 原样透传。
- **只注入 anon key 作为缺省**（该 key 已在公开 bundle 中，不新增泄露面）；**service_role key 绝不出现在前端与函数中**。
- 响应原样回传，包含 `Content-Range`（前端分页/计数依赖）；上游 4xx/5xx 状态码不被吞。
- 超时 15s，超时返回 504 + JSON `{error:'upstream_timeout', host:'…supabase.co'}`，供前端显示。

### 3.2 `_routes.json`（关键，漏了会把整站变成计费函数调用）

官方文档：Pages 项目一旦加 Functions，**默认所有请求都会调用函数**；需在**构建输出目录**放 `_routes.json` 排除静态路由。

`frontend/public/_routes.json`（Vite 会复制到 `dist/`）：

```json
{ "version": 1, "include": ["/sb/*"], "exclude": ["/assets/*"] }
```

> ⚠️ 2026-11-02 复盘：本节与落地文件原先都写的 `"exclude": ["/*"]`，`sb_proxy_test.js` 的 F5
> 还把这一错误字符串当断言钉住，于是错误被测试合法化、一个多月没人发现。官方规则是
> **exclude 命中即走静态资源，优先级高于 include**，`/*` 连 `/sb/...` 一起排除 → 函数从不调用
> → 线上所有 Supabase 请求（登录 `auth/v1/token`、集团 ZS02 库、草稿保存）都拿到 SPA 外壳
> `index.html`（200 + text/html），表现即「登录不正常」「集团子目加载失败」。
> 下面第 5 节的验收（`curl …/sb/auth/v1/health` 出 JSON）当时只在 `wrangler pages dev` 本地跑过，
> **没在线上部署跑过**。改路由后必须在线上部署上补跑这条，只看构建成功不算验证。

### 3.3 前端 URL 收口

- 线上：`SUPABASE_URL = location.origin + '/sb'`（必须绝对 URL —— supabase-js 内部 `new URL()` 不接受相对路径）。
- **localhost 保持直连 supabase.co**（本机 `python -m http.server` 没有函数运行时；沿用现状，开发路径零变化）。
- 判定单点写死：`hostname === 'localhost' || hostname === '127.0.0.1'` → 直连，否则走 `/sb`。
- 需改文件（每处都是同一个常量赋值）：`docs/{tool,admin,m,login,app,debug,editor,import-knowledge,import-rules,restore_benchmark}.html` + `frontend/public/` 对应副本 + `frontend/src/lib/supabaseClient.ts`。
- 双副本同步规则不变（`docs/` ↔ `frontend/public/`，shasum 校验）。

### 3.4 错误可见性（本次排查的直接代价补偿）

- `_get` 不再 `.catch(() => [])` 静默：把 HTTP 状态码 / 超时 / 上游域名记入 `_lastDbError`，面板与 toast 显示「连不上 <域> （HTTP 状态 / 耗时）」，重试按钮保留。
- `authErrors.ts` 网络分支补 `Load failed`（Safari）与 `NetworkError`，不再把英文原文吐给用户。
- 集团库空库面板区分三种原因：网络不通 / 权限拒绝 / 表内确实无数据。

### 3.5 保活（防免费档闲置暂停）

GitHub Actions 定时工作流（免费、无需新增服务器），每 10 分钟：

1. `GET /sb/rest/v1/profiles?select=id&limit=1` —— 同时验证「代理链路 + Supabase 活动」；
2. `GET https://…onrender.com/docs` —— 保活 Render。

失败仅让 workflow 变红（邮件通知），不自动改动任何状态。

## 4. 配额与性能

- Functions 免费档 **10 万请求/天**（UTC 零点重置）；配 `_routes.json` 后静态请求不计。
- 单次会话估算：内部库 1 + 集团库 1 + 费率 1 + projects 列表/草稿读写（自动保存 3s 防抖）≈ 每活跃用户每小时 20–60 请求 → 需 ~1700–5000 并发活跃用户才触顶，余量充足。
- 延迟：多一跳 Cloudflare 边缘，实测应在 +20–50ms 量级；上线时对比记录。

## 5. 回滚

前端 URL 判定是单点常量：revert 该 commit 并重新部署即回到直连 `supabase.co`；函数与 `_routes.json` 留着不影响直连。**数据层零改动**（不迁库、不改 RLS、不改任何表结构）。

## 6. 验收标准（全部要跑，不接受"应该可以"）

1. `wrangler pages dev` 本地起含函数的构建产物，`/sb/rest/v1/group_benchmark_items` 返回 296 条；非白名单路径（如 `/sb/rest/v1/pg_catalog`）被拒。
2. 部署后 `curl https://…pages.dev/sb/auth/v1/health` 出 JSON。
3. **用户 Safari 实测**：登录成功 → 切「对甲报价」→ 侧栏「共 296 条子目」；内部模式「共 497 条子目」不变。
4. 五套前端回归 + backend pytest 全绿；`docs/` ↔ `frontend/public/` shasum 一致。
5. 故意断网/超时场景下，界面显示的是域名+状态码而不是「库未加载」。

## 7. 待用户确认的输入

- Pages 项目的 **根目录 / 构建命令 / 构建输出目录** 三项（决定 `functions/` 放仓库根还是 `frontend/` 下）——这是我唯一无法从仓库或接口看到的一环。

## 8. 遗留（不在本设计内）

- Supabase 免费档：`No backups`（数据丢失风险，可选：每周从 Render 侧导 CSV 到网盘 / 或升 PRO 拿每日备份+PITR）、RAM 49%（水位正常，余量小，真要治是升配）。
- 本机网络到 supabase.co 不通的成因（DNS 污染 / SNI 拦截 / 运营商）未定性，本设计选择绕开而非修复。
