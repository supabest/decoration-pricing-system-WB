# 套价工具移动端界面（m.html）设计文档

- 日期：2026-10-05
- 状态：待评审
- 作者：与用户共同头脑风暴产出
- 版本落点：V1.4.0 之后的独立迭代

## 1. 目标与定位

为装修套价工具提供**手机端操作界面**，覆盖**全过程**（导入清单 → AI 套价 → 导入主材询价 → 查看结果 → 导出 Excel），但移动端的哲学是**强调结果、不强调过程调节**：

- 每一步只呈现结论性数字与状态，明细默认折叠
- 不提供桌面级的过程性编辑（改子目、调系数、覆盖辅材价等）
- 文件选择、分享等交互采用手机原生方式

**与电脑端的关系：跨端接力（方案甲）**——手机和电脑共用同一个 Supabase 云端草稿槽，任何一端的确认类操作（如询价写入）直接写回草稿，另一端无缝继续。

## 2. 硬性约束

1. **电脑端零改动**：`docs/tool.html`、`docs/admin.html`、`frontend/public/tool.html`、`frontend/public/admin.html` 在整个移动端开发过程中**一个字符都不改**。
2. **后端零改动**：复用现有 FastAPI 端点（`/api/v1/pricing/single`、`/api/v1/export/excel`、`/api/v1/export/template`）与 Supabase（REST + Auth），不新增/修改任何后端代码。若实施中发现必须动后端，停下来重新评审。
3. 新页面遵循既有同步规则：`docs/m.html` ↔ `frontend/public/m.html` 两处保持一致（Pages 只部署 `frontend/public/`）。

## 3. 总体架构

```
手机浏览器 (Safari / Chrome)
    │
docs/m.html（新增，纯 HTML/CSS/JS 单文件，与 tool.html 同风格但代码完全独立）
    │
    ├── Supabase REST ── projects（草稿接力）/ benchmark_items / material_prices
    ├── Supabase Auth ── 登录（token 写 localStorage，与 tool.html 同源互通）
    ├── SheetJS (CDN 0.18.5) ── 客户端解析 BOQ / 询价 Excel
    └── FastAPI (Render) ── AI 套价 /pricing/single；Excel 导出 /export/*
```

- **不 import、不共享 tool.html 的任何代码**。tool.html 的函数逻辑（BOQ 解析规则、询价匹配、计价公式）在 m.html 中**按相同契约重新实现**，两者通过 `groups_json` 数据 schema 对齐，而非代码对齐。
- 访问入口：`https://decoration-pricing-system.pages.dev/m.html`；本地 `http://localhost:8080/m.html`。
- localhost 免登录规则与 tool.html 一致。

## 4. 数据层：跨端草稿接力（方案甲）

### 4.1 复用现有草稿契约（与 tool.html 完全同构）

`projects` 表每用户仅一条 `is_draft=true` 记录，payload 字段：

```
name, groups_json(完整BOQ树), price_overrides, mgmt_rate, profit_rate,
contract_amount, target_profit_rate, row_count, priced_count, is_draft, created_at
```

- m.html 读取/写回**同一 schema**，`created_at` 在每次保存时刷新（tool.html 现行行为，即"最后保存时间"语义）。
- upsert 方式与 tool.html 相同：先查 `user_id + is_draft=true` 取 id，有则 PATCH，无则 POST。
- m.html 写入的 `groups_json` 中每个 row/sub 字段必须与 tool.html 的 `makeRow()`/子目结构字段全集一致（`id/name/spec/unit/qty/remark/open/subs/aiNote/hourlyMode/matName/matPrice/wasteRate/auxCost` + 子目 `bid/bsh/matPrice/wasteRate/coef/conv/matName/...`），实施时以 tool.html 源码为 schema 权威逐字段核对。

### 4.2 冲突缓解（最后写入提醒）

- 进入项目时显示草稿保存时间：「云端草稿保存于 10-05 14:32（可能在其他设备修改）」。
- m.html 每次自动保存前重新读取草稿 `created_at`，若晚于自己上次读取时间 → 弹确认：「草稿在另一端有更新，覆盖将丢失对方改动。【仍覆盖 / 放弃本地改动并刷新】」。
- 手机端不做长时间离线编辑：所有编辑即时写回。

### 4.3 正式方案

- m.html 提供「另存为方案」（`is_draft=false`，同 tool.html saveProject 契约）；历史方案列表只读展示（名称/时间/行/套价进度），点开载入为本地可浏览快照（不提供桌面端"恢复编辑"，需要编辑时提示回电脑端）。

## 5. 界面设计：五步结果卡片流

### 5.0 全局框架

- 单列布局，最大宽度 480px 居中；触控目标 ≥ 44px；系统字体栈。
- 顶部步骤条 `① 导入 → ② 套价 → ③ 询价 → ④ 结果 → ⑤ 导出`，当前步高亮，可点击回看已完成步骤（只读）。
- 弹窗一律不用桌面式居中 modal：轻确认用底部抽屉（bottom sheet），流程页用全屏推入。
- 底部主操作区：每屏一个大主按钮（如「✨ 开始套价」「确认写入 (41)」）。

### 5.1 ① 导入清单

- 「📂 选择 Excel 文件」大按钮 → 唤起系统文件选择器（`<input type="file" accept=".xlsx,.xls">`；iOS 走"文件"App，微信文件经"用其他应用打开"进入）。
- 解析（SheetJS，BOQ 识别规则与 tool.html 同契约：多工作簿、分部标题识别、名称/特征/单位/工程量列映射）后**不渲染整表**，显示结果摘要卡：
  - 「✅ 识别 3 个工作表 · 86 条清单 · 12 个分部」
  - 「查看清单 ▸」折叠入口（展开为单列行卡片：名称 + 单位 + 工程量）
  - 「🔄 重新选择」
- 识别异常（0 行、分部未识别）时主动红色提示并给「查看原始解析 ▸」。

### 5.2 ② AI 套价

- 主按钮「✨ 开始套价」→ 逐行调 `/api/v1/pricing/single`（请求体契约与 tool.html 相同；API Key 由用户在折叠面板输入，仅本次使用不保存，与桌面端一致）。
- 进度：进度条 +「已处理 42/86」，可中断。
- 完成结果卡：**已套价 72 · 未套价 14 · ⚠️低置信 5**。
- 未套价/低置信列表默认收起；展开为紧凑卡（名称/单位/合价/匹配子目名）。
- **不提供**子目增删改；卡片底部统一提示「需要调整子目？请在电脑端完成」。

### 5.3 ③ 导入主材询价

- 选文件同 5.1。解析后进入**三组 Tab 卡片流**（对应桌面端预览弹窗）：
  - Tab：`✅ 自动匹配 41` / `⚠️ 待确认 6` / `❌ 未匹配 2`
- 每张询价行卡：名称（+特征副标）、单位、报价 `¥120 → ¥180`（旧价→新价，价格变化高亮）、匹配状态徽章（🔶 相似 78% / ⚠️ 单位不一致 m↔㎡ / ✅ 精确…）。
- 勾选 = 卡片右上角圆形 checkbox，默认勾选规则与桌面端一致（仅可靠匹配且非疑非本类）。
- 多候选（ambiguous）：卡片内「选择清单行 ▸」→ 底部抽屉列出候选清单行，点选后卡片更新为已匹配。
- 未匹配（❌ 增项）：只展示，不可勾选（增项自动插入功能本轮不做，与桌面端一致）。
- 右下角悬浮「确认写入 (41)」→ 走与桌面端相同的落点逻辑（routeRowMat 契约：暂存/按品类落子目/保留）→ 结果 toast（已套入 x · 暂存 y · 保留 z）→ 写回云端草稿。
- 品类识别与填价列选择：折叠面板中自动识别 + 可手动改（与桌面端弹窗的 ① 品类 ② 填价列 下拉同功能，移动端用底部抽屉单选列表）。

### 5.4 ④ 结果总览

- 汇总大数字卡：人工费 / 主材费 / 辅材 / 管理费 / 利润 / **总计 ¥xxx**（口径 = 现有 compUnitPrice/rowTotal 公式的移动端重实现）。
- 对内核算卡：合同金额 · 测算直接成本 · 测算利润率 xx%（字段来自草稿 payload）。
- 分部维度手风琴：每个分部一行显示合价，展开看清单行卡（名称/单位/量/合价/⚠️低置信标记）。
- 「💾 另存为方案」按钮。

### 5.5 ⑤ 导出

- 两个选项卡：「方式一 · 标准套价表」/「方式二 · 模板填入」。
  - 方式一：`collectExportData` 同契约收集 → POST `/api/v1/export/excel` → 拿回文件流。
  - 方式二：先「选择模板文件」（系统选择器）→ POST `/api/v1/export/template`。
- 拿到文件后：优先 `navigator.share({files})`（Web Share Level 2，iOS Safari/Android Chrome 支持）→ 用户可"存储到文件/发送微信/邮件"；不支持时降级为普通下载链接 `<a download>`。
- 导出内容与桌面端完全一致（同一后端引擎生成）。

## 6. 登录与会话

- m.html 内置迷你登录卡（邮箱+密码 → Supabase Auth password grant），token 写 `localStorage['sb-access-token']` 等既有键名——与 tool.html 同源同键，**登录一次两端通用**。
- 已登录（检测到有效 token）直接跳过登录视图。
- token 过期处理与 tool.html 一致（清 token → 回登录视图）。

## 7. 明确不做（Out of Scope）

- 手机端过程性调节：人工系数、管理费率/利润率修改、辅材覆盖价面板、子目增删改、行编辑。
- 供应商增项自动插入清单（桌面端同样未做，未来若做两端一起设计）。
- 版本公告/意见反馈/管理面板功能。
- 原生 App / PWA 离线包（后续迭代可加 manifest，本文档不含）。
- 任何对 tool.html / admin.html / 后端的修改。

## 8. 测试计划

1. **Schema 对齐测试**：m.html 保存草稿 → tool.html 恢复草稿，BOQ 树、询价落点、对内字段完整无损；反向同理。
2. **接力冲突测试**：两端先后编辑同一草稿，验证"最后写入提醒"按预期拦截。
3. **五步流程真机测试**（iPhone Safari + Android Chrome）：真实 BOQ 导入 → 套价 → 询价导入（覆盖 精确/相似/单位不一致/多候选/未匹配 五场景）→ 结果核对 → 导出分享。
4. **不变式抽查**：多主材行（含 coef/conv）在 m.html 结果卡的合价 = tool.html 同项目同数据合价。
5. **桌面回归零影响**：整个开发周期 `git diff` 确认 tool.html/admin.html 无改动。
6. **localhost 免登录**：本地 8080 直开 m.html 可用。

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| groups_json schema 漂移（桌面未来加字段，手机端漏同步） | 在 m.html 头部注释声明"schema 权威=tool.html makeRow"；列入 CLAUDE.md 同步规则清单（新增行：改 tool.html 行字段时同步 m.html） |
| Web Share API 在部分安卓浏览器不支持 files | 降级 `<a download>`；提示"如未弹出分享，请检查下载" |
| 大 BOQ（>500 行）手机解析慢 | SheetJS 已够快；解析放 setTimeout 让 loading 态可渲染；超 1000 行提示回电脑 |
| AI 套价逐行请求在手机端断网中断 | 支持断点续套（已完成的行不重跑）；结果实时写回草稿 |
| 双端同时编辑覆盖 | 4.2 最后写入提醒；手机端不做长离线编辑 |

## 10. 实施顺序建议（供 writing-plans 展开）

1. 骨架：m.html 路由视图（登录/项目/五步）+ 全局样式框架
2. 数据层：Supabase 封装 + 草稿读写 + 冲突提醒
3. ① 导入清单（BOQ 解析契约移植）
4. ④ 结果总览（先于套价/询价做，因为纯展示，可用桌面端造好的数据验证 schema）
5. ③ 导入询价（匹配/落点契约移植，逻辑测试对齐桌面端）
6. ② AI 套价（复用 /pricing/single）
7. ⑤ 导出（分享面板）
8. 真机联调 + 双向接力测试 + 同步 frontend/public/
