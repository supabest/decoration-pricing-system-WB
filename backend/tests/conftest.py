"""测试配置"""
import pytest

# 既有缺陷最小修复（T2 裁定④ → T7 落地）：
#   原顶层 `from app.db.session import get_db` 在导入期就会读 settings.DATABASE_URL，
#   而该配置项已随 Supabase 迁移移除（现网走 SUPABASE_URL）；venv311 亦未安装 sqlalchemy。
#   两者任一都让 `pytest backend/tests` 在 conftest 阶段直接 ImportError → 整个目录无法收集。
#   本目录用例（导入脚本审计 / 套价解析 / 集团汇总导出）均不依赖真库，故把 DB 依赖栈下沉到
#   fixture 内 + getattr 守卫缺省 URL：依赖缺失时只 skip 用到它的用例，收集不再被拖垮。

TEST_DATABASE_URL = "sqlite:///./test.db"


def _database_url():
    """settings.DATABASE_URL 已移除 → 缺省回落本地 sqlite（getattr 守卫，不在导入期取值）。"""
    from app.core.config import settings
    return getattr(settings, "DATABASE_URL", None) or TEST_DATABASE_URL


def _require_db_stack():
    """DB 依赖栈（sqlalchemy + app.db.session）不可用 → skip，不影响其余用例收集。"""
    try:
        import sqlalchemy                       # noqa: F401
        from app.db.session import get_db       # noqa: F401
    except Exception as exc:                    # ImportError / AttributeError(DATABASE_URL)
        pytest.skip(f"DB 依赖栈不可用，跳过 DB 相关用例：{exc}")


@pytest.fixture
def db_session():
    _require_db_stack()
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.base import Base

    engine = create_engine(_database_url())
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()
