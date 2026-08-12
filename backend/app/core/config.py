"""应用配置管理 — 生产环境通过环境变量注入"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── 应用基础 ──
    APP_NAME: str = "装修工程AI套价系统"
    APP_VERSION: str = "1.2.0"
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # 🔒 生产环境必须设置 (openssl rand -hex 32)
    SECRET_KEY: str = ""

    # ── AI / LLM ──
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"

    # ── Supabase ──
    SUPABASE_URL: str = "https://lnvtykghcpsjpwczbqsm.supabase.co"
    SUPABASE_ANON_KEY: str = "sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q"
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── QQ SMTP 邮件 ──
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USE_SSL: bool = True
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "装修成本分析系统"

    # ── 前端地址 ──
    FRONTEND_URL: str = "https://decoration-pricing-system.pages.dev"

    # ── CORS (逗号分隔，如: https://xxx.pages.dev,https://admin.xxx.com) ──
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://decoration-pricing-system.pages.dev",
    ]

    # ── 文件上传 ──
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # ── 计价默认费率 ──
    DEFAULT_PROFIT_RATE: float = 7.0
    DEFAULT_MANAGEMENT_RATE: float = 5.0
    DEFAULT_TAX_RATE: float = 9.0

    # ── 调试 ──
    DEBUG_PRICING: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = True


settings = Settings()
