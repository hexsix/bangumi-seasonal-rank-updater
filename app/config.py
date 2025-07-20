import os
import re

from dotenv import load_dotenv
from loguru import logger


class Config:
    def __init__(self) -> None:
        load_dotenv()
        self.app_version = self.get_app_version()
        self.app_log_level = self.get_app_log_level()
        self.app_api_password = self.get_app_api_password()
        self.bgmtv_token = self.get_bgmtv_token()
        self.cf_pages_hooks = self.get_cf_pages_hooks()
        self.db_url = self.get_db_url()
        logger.info(self.pretty_print())

    def pretty_print(self) -> str:
        return f"""
        app_version: {self.app_version}
        app_log_level: {self.app_log_level}
        app_api_password: {self.app_api_password_masked()}
        bgmtv_token: {self.bgmtv_token_masked()}
        cf_pages_hooks: {self.cf_pages_hooks_masked()}
        db_url: {self.db_url_masked()}
        """

    def get_app_version(self) -> str:
        return os.getenv("APP_VERSION", "1.0.0")

    def get_app_log_level(self) -> str:
        return os.getenv("APP_LOG_LEVEL", "INFO")

    def get_app_api_password(self) -> str:
        return os.getenv("APP_API_PASSWORD", "default_password")

    def app_api_password_masked(self) -> str:
        if self.app_api_password is None:
            return "Not set"
        return "****"

    def get_bgmtv_token(self) -> str | None:
        return os.getenv("BGMTV_TOKEN")

    def bgmtv_token_masked(self) -> str:
        if self.bgmtv_token is None:
            return "Not set"
        return self.bgmtv_token[:3] + "****" + self.bgmtv_token[-3:]

    def get_cf_pages_hooks(self) -> str | None:
        return os.getenv("CF_PAGES_HOOKS")

    def cf_pages_hooks_masked(self) -> str:
        if self.cf_pages_hooks is None:
            return "Not set"
        return "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/xxxx"

    def get_db_url(self) -> str:
        db_url = os.getenv(
            "DB_URL", "postgresql://postgres:postgres@localhost:5432/bangumi_rank"
        )
        # 确保使用正确的SQLAlchemy驱动程序格式
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url

    def db_url_masked(self) -> str:
        if not self.db_url:
            return "Not set"
        masked_url = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", self.db_url)
        return masked_url

    def get_db_pool_config(self) -> dict[str, int]:
        """获取数据库连接池配置"""
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
            "pool_pre_ping": True,  # 连接前ping测试
        }


config = Config()
