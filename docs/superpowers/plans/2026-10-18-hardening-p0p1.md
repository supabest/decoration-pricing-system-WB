# 安全加固与工程基建（P0 缺陷修复 + P1 基建）实施计划

- **日期**: 2026-10-18
- **状态**: 用户已裁定范围 = 标准（P0 三项 + P1 四项）；死代码本轮只记录不删
- **基线**: JS 沙箱 539 断言全绿（group 406 / m_logic 54 / m_parity 43 / quote 25 / sub_edit 11）、后端 pytest 67 用例全绿

## 0. 问题清单（均为实测实证，非推测）

| # | 问题 | 实证 |
|---|------|------|
| P0-1 | `ai_pricing_logs` 匿名可读 | 用站点公开 anon key 只读探测：`GET /rest/v1/ai_pricing_logs` → 200，`content-range: 0-421/422`，含真实清单名/单位/时间；同法 `projects` 返回 `[]`（RLS 正常），证明是该表策略缺失 |
| P0-2 | 调试日志 HTML 页未转义（注入面） | `ai_pricing.py:_render_logs_html` 把清单名/特征/AI 响应直接拼 HTML，无转义 |
| P0-3 | 导出接口 500 回显内部异常文本 | `export.py` 4 处 `content={"error": str(e)}`，浏览器 toast 直接上屏；其余端点均通用文案，属风格漂移 |
| P1-4 | 双副本同步靠人工 diff | docs ↔ frontend/public 六文件，逐期人工核对 |
| P1-5 | 无统一测试入口 | 5 套 JS + pytest 需手工逐条拼命令 |
| P1-6 | Pydantic 弃用告警 17 条 | 17 处 `class Config`（Pydantic v2 已弃用，v3 移除） |
| P1-7 | 文档漂移 | CLAUDE.md/README 仍描述 LangChain / SQLAlchemy / Celery 技术栈，与实际（httpx 直调）不符 |

## 1. 修复口径（不可回退的契约）

### P0-1 `ai_pricing_logs` RLS 锁读

- **只锁 SELECT，保留匿名 INSERT**：泄露点是「读」，写路径（本机 `DEBUG_PRICING=true` 无 service_role）保持可用；与 `pricing_failures`「统计入口不设身份门槛」的既有裁定同构
- 后端读写头部**优先 service_role、未配则回退 anon**——Render 已配（user_lookup 在用），本机未配时行为不变，任何一端先落地都不炸
- 迁移幂等：DO 块遍历 `pg_policies` 全部 DROP（历史策略名未知，不依赖硬编码名）后重建唯一 INSERT 策略；附前后验证探测 SQL

### P0-2 HTML 转义

- `_render_logs_html` 所有插值（清单字段 / 候选 / 解析 / prompt 预览 / 时间戳）统一走 `html.escape`；数字不转义
- 回归用例钉住：`<script>` 必须变成 `&lt;script&gt;`

### P0-3 导出 500 通用化

- 500 返回 `{"error":"export_failed","message":<通用中文提示>}`，异常细节只进服务器日志
- **400 结构化 detail 契约不动**（前端有分支依赖：`fitout_area_required` / `pending[]` / `coord_fee_not_configured`），并为之加防回归用例
- 前端 tool/m 两端加同源 `beErrMsg(resp)` 助手：优先 `message`/`error`/`detail` 字段，纯文本兜底

## 2. 防线（回归闸门）

| 防线 | 载体 |
|------|------|
| 后端新用例 3 组 | `backend/tests/test_api/test_export_error_contract.py`（500 不泄露 + 400 契约）、`test_debug_logs_html.py`（转义）、`test_services/test_debug_logger_auth.py`（service_role 优先/回退） |
| 全量回归 | `scripts/run_tests.sh` = 5 套 JS 沙箱 + pytest + 双副本检查 |
| 双副本 | `scripts/check_dual_copy.sh` 六文件 diff 非零退出 |
| 前端错误提示 | `docs/superpowers/tests/beerrmsg_test.js` — beErrMsg 6 用例 × 两端对偶（后补，随 P0-3 收尾） |
| 弃用告警 | pytest 输出 0 条 Pydantic `class Config` 告警 |

## 3. 实施顺序（原子提交）

1. `fix(security)`: 日志表 RLS 迁移 + 后端 service_role 读写 + 用例 → 用户需在 Dashboard 执行迁移（**代码先上、迁移后执行，顺序可互换不炸**）
2. `fix(security)`: 调试日志 HTML 转义 + 用例
3. `fix(api)`: 导出 500 通用化 + 前端提示解析（tool/m 双副本四文件）+ 用例
4. `chore(scripts)`: 双副本守卫 + 一键回归
5. `refactor(schemas)`: ConfigDict 迁移 ×17
6. `docs`: CLAUDE.md / README 纠偏 + 遗留栈标注 + 新脚本与新移登记

## 4. 明确不做（本轮）

- GitHub Actions CI（私有仓 Actions 额度，用户未选）
- 死代码删除（8 个 deprecated 端点 / SQLAlchemy+Celery+LangChain 死栈 / docker-compose / backend/requirements/）→ 仅 README 标注为遗留
- 本机 3 个陈旧 venv（约 200MB）清理
- `pricing_failures` 匿名可写/可读 → 既有裁定，保持
- `benchmark_items` / 集团两表匿名读 → localhost 免登录的既有裁定，保持
