import os

from dotenv import load_dotenv
from loguru import logger


class Config:
    def __init__(self):
        load_dotenv()
        self.app_version = self.get_app_version()
        self.log_level = self.get_log_level()
        self.redis_host = self.get_redis_host()
        self.redis_port = self.get_redis_port()
        self.redis_password = self.get_redis_password()
        self.bgmtv_token = self.get_bgmtv_token()
        logger.info(self.pretty_print())

    def pretty_print(self):
        return f"""
        app_version: {self.app_version}
        log_level: {self.log_level}
        bgmtv_token: {self.bgmtv_token_masked()}
        redis_host: {self.redis_host}
        redis_port: {self.redis_port}
        redis_password: {self.redis_password_masked()}
        """

    def get_log_level(self):
        return os.getenv("LOG_LEVEL", "INFO")

    def get_app_version(self):
        return os.getenv("APP_VERSION", "1.0.0")

    def get_bgmtv_token(self):
        return os.getenv("BGMTV_TOKEN")

    def get_redis_host(self):
        return os.getenv("REDIS_URL", "localhost")

    def get_redis_port(self):
        return int(os.getenv("REDIS_PORT", 6379))

    def get_redis_password(self):
        return os.getenv("REDIS_PASSWORD")

    def redis_password_masked(self):
        if self.redis_password is None:
            return "Not set"
        return "******"

    def bgmtv_token_masked(self):
        if self.bgmtv_token is None:
            return "Not set"
        return self.bgmtv_token[:3] + "****" + self.bgmtv_token[-3:]


config = Config()
