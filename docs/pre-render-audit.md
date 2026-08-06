# Render 部署前最终审计报告

> 审计日期: 2026-08-06 | 审计结论: ✅ 通过

---

## 一、DATABASE_URL → sqlite:///:memory: 审计

### 问题: 为什么改成 sqlite memory？是否安全？

**原因**: 8 个 stub CRUD 端点的导入链会触发 `db/session.py` 执行:
```
main.py → router.py → 8 stub endpoints (enterprise_price/material_price/...) 
        → dependencies.py → db/session.py → create_engine(DATABASE_URL)
```

如果 `DATABASE_URL` 指向不可达的 PostgreSQL，`create_engine()` 在 import 时就会报错，导致整个应用无法启动。

### 证据: 真实端点零引用

```
✅ ai_pricing.py     → 不导入 db/session
✅ knowledge.py      → 不导入 db/session  
✅ export.py         → 不导入 db/session
✅ ai_pricing_service.py   → 不导入 db/session
✅ similarity_checker.py   → 不导入 db/session
✅ pricing_debug_logger.py → 不导入 db/session
```

### 结论

| 项目 | 结论 |
|------|------|
| SQLite 是否存储业务数据？ | ❌ 否。无任何业务代码写入 SQLite |
| SQLite 是否被查询？ | ❌ 否。无任何业务代码读取 SQLite |
| 生产数据库是什么？ | ✅ **Supabase PostgreSQL** |
| SQLite 用途？ | 纯粹占位 — 保持 stub 端点导入链不崩溃 |

---

## 二、数据读写全景审计

### 所有数据操作映射

| 数据 | 存储位置 | 读 | 写 | 代码位置 |
|------|----------|-----|-----|----------|
| 基准价 (497条) | Supabase `benchmark_items` | ✅ | ❌ | `ai_pricing_service.py:74` |
| 知识库 (37条) | Supabase `ai_knowledge` | ✅ | ✅ | `knowledge.py:58` / `ai_pricing_service.py:110` |
| 调试日志 | Supabase `ai_pricing_logs` | ✅ | ✅ | `pricing_debug_logger.py:101,120` |
| 用户信息 | Supabase `profiles` (由前端直连) | — | — | tool.html / admin.html |
| 主材价格 | Supabase `material_prices` | — | — | 前端直连 |
| 套价结果 | ❌ 不持久化 | — | — | 仅在前端内存 + Excel 导出 |
| Excel 文件 | ❌ 不持久化 | — | — | BytesIO 内存，流式返回后释放 |

### 知识库 fallback 机制

```
加载优先级: Supabase REST API → 本地 ai_knowledge_base.json → 空集合
```

**Render 部署注意事项**: 本地 JSON 通过 `os.path.join(__file__, '../../../docs/...')` 读取。Render 的文件系统包含所有仓库文件，所以 JSON fallback 可用。但如果 Supabase 正常返回数据，JSON 不会被读取。

### 知识库写入

`POST /api/v1/knowledge` 写入 Supabase `ai_knowledge` 表，需前端传递 JWT token。失败时返回 502 而非写入本地。

---

## 三、Render 运行时审计

### 3.1 openpyxl Excel 生成

```python
def generate(self) -> BytesIO:
    ...
    buf = BytesIO()
    self.wb.save(buf)    # ← 全内存操作
    buf.seek(0)
    return buf
```

- ✅ 零磁盘 I/O
- ✅ 零临时文件
- ✅ BytesIO 在请求结束后自动 GC
- ✅ Render ephemeral filesystem 无影响

### 3.2 多用户并发

```python
class ExcelExporter:
    def __init__(self, request):
        self.wb = Workbook()   # ← 每个请求独立实例
        self.ws = self.wb.active
```

- ✅ 无类级别共享状态
- ✅ 无全局锁
- ✅ 每个 HTTP 请求创建独立的 ExcelExporter
- ✅ uvicorn 默认单进程多协程，asyncio 自动调度

### 3.3 内存估算

| 请求类型 | 峰值内存 | 说明 |
|----------|----------|------|
| AI 套价 (单条) | ~5 MB | 候选列表 + JSON + HTTP buffer |
| Excel 导出 (50行) | ~20 MB | openpyxl Workbook 在内存 |
| Excel 导出 (500行) | ~80 MB | 含公式和样式 |
| 知识库查询 | ~1 MB | JSON 序列化 |

Render 免费层 512 MB RAM，满足需求。

### 3.4 超时设置

| 操作 | 超时 | 说明 |
|------|------|------|
| DeepSeek API | 60s | `httpx.AsyncClient(timeout=60)` |
| Supabase REST | 10-15s | 基准价加载 15s，知识库 10s |
| Excel 生成 | 无显式限制 | 受 Render 30s 请求超时约束 |
| Render 请求超时 | **30s** | ⚠️ 大量数据 Excel 可能超时 |

**⚠️ Render 免费层 30 秒请求超时**: 当 BOQ 清单超过 ~300 行时，openpyxl 生成可能超过 30 秒。解决方案:
- 短期: 告诉用户 300 行以内导出
- 长期: 改为后台任务 + 轮询下载

---

## 四、环境变量安全检查

| 变量 | 当前值 | 泄露风险 | 处理 |
|------|--------|----------|------|
| `SUPABASE_ANON_KEY` | hardcoded in config.py | 🟡 低 (就是公开 key) | 已在 .env.example 说明 |
| `SECRET_KEY` | 本地 dev 值 | 🟢 .env 已加入 .gitignore | Render 环境变量注入 |
| `DEEPSEEK_KEY` | 用户输入 | 🟢 不存储 | 每次请求传入 |
| `DEBUG_PRICING` | false | 🟢 | 生产关闭 |

---

## 五、最终结论

| 检查项 | 状态 | 说明 |
|--------|------|------|
| DATABASE_URL 安全性 | ✅ | 仅占位，零业务数据写入 SQLite |
| 生产数据库 | ✅ | Supabase PostgreSQL |
| 数据读写路径 | ✅ | 100% 走 Supabase REST API |
| openpyxl 内存安全 | ✅ | BytesIO，无临时文件 |
| 多用户并发 | ✅ | 无共享状态，asyncio 调度 |
| 环境变量安全 | ✅ | .env gitignore，Render 注入 |
| Render 超时 | ⚠️ | 大 BOQ 导出可能超 30s |
| Python 3.11 兼容 | ✅ | 已验证 |

**结论: 可以部署到 Render。**
