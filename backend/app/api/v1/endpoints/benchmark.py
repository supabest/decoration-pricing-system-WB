"""基准价快照端点 —— 登录用户专用的兜底数据源

外部（未登录）拿不到，内部（注册用户）拿得到，正是本次保密裁定的分界线：
公网不再发布明文 benchmark_data.json，Supabase 不可达时前端改调这里。
返回内容与原 docs/benchmark_data.json + waste_rates.json 同构，前端无需改字段映射。
"""
import logging
from fastapi import APIRouter, Depends

from app.core.auth import require_auth
from app.services.benchmark_snapshot import load_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(tags=["基准价"])


@router.get("/snapshot")
async def get_snapshot(user: dict = Depends(require_auth)):
    """全量内部基准价 + 损耗率（加密快照解密结果，需登录）"""
    snap = load_snapshot()
    items = snap.get("benchmark_items") or []
    if not items:
        # 空快照通常意味着线上没配 BENCHMARK_SNAPSHOT_KEY 或快照未随代码发布；
        # 这里只报「兜底不可用」，不影响 Supabase 正常时的主流程
        logger.warning("benchmark snapshot empty (未配 BENCHMARK_SNAPSHOT_KEY 或快照缺失/损坏)")
    return {
        "items": items,
        "waste_rates": snap.get("waste_rates") or {},
        "count": len(items),
        "generated_at": snap.get("generated_at", ""),
    }


@router.get("/waste-rates")
async def get_waste_rates(user: dict = Depends(require_auth)):
    """损耗率字典（需登录）：库中 waste_rate 列为空时的补齐源

    单开这个轻端点是因为在线路径也要补损耗率，而公网不再放明文 waste_rates.json；
    只为 475 个数字就把 380KB 全量价表下发一次不合理。
    """
    wr = load_snapshot().get("waste_rates") or {}
    return {"waste_rates": wr, "count": len(wr)}
