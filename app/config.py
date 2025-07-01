import os
import re

from dotenv import load_dotenv
from loguru import logger


class Config:
    def __init__(self):
        load_dotenv()
        self.app_version = self.get_app_version()
        self.log_level = self.get_log_level()
        self.db_url = self.get_db_url()
        self.bgmtv_token = self.get_bgmtv_token()
        self.ds_api_key = self.get_ds_api_key()
        logger.info(self.pretty_print())

    def pretty_print(self):
        return f"""
        app_version: {self.app_version}
        log_level: {self.log_level}
        bgmtv_token: {self.bgmtv_token_masked()}
        db_url: {self.db_url_masked()}
        ds_api_key: {self.ds_api_key_masked()}
        """

    def get_log_level(self):
        return os.getenv("LOG_LEVEL", "INFO")

    def get_app_version(self):
        return os.getenv("APP_VERSION", "1.0.0")

    def get_bgmtv_token(self):
        return os.getenv("BGMTV_TOKEN")

    def get_db_url(self):
        db_url = os.getenv(
            "DB_URL", "postgresql://postgres:postgres@localhost:5432/bangumi_rank"
        )
        # 确保使用正确的SQLAlchemy驱动程序格式
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url

    def db_url_masked(self):
        if not self.db_url:
            return "Not set"
        masked_url = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", self.db_url)
        return masked_url

    def bgmtv_token_masked(self):
        if self.bgmtv_token is None:
            return "Not set"
        return self.bgmtv_token[:3] + "****" + self.bgmtv_token[-3:]

    def ds_api_key_masked(self):
        if self.ds_api_key is None:
            return "Not set"
        return self.ds_api_key[:3] + "****" + self.ds_api_key[-3:]

    def get_ds_api_key(self):
        return os.getenv("DS_API_KEY")


config = Config()
