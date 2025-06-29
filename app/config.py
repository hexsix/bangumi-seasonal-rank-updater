import os

from dotenv import load_dotenv
from loguru import logger


class Config:
    def __init__(self):
        load_dotenv()
        self.app_version = self.get_app_version()
        self.log_level = self.get_log_level()
        self.db_file = self.get_db_file()
        self.bgmtv_token = self.get_bgmtv_token()
        logger.info(self.pretty_print())

    def pretty_print(self):
        return f"""
        app_version: {self.app_version}
        log_level: {self.log_level}
        bgmtv_token: {self.bgmtv_token_masked()}
        db_file: {self.db_file}
        """

    def get_log_level(self):
        return os.getenv("LOG_LEVEL", "INFO")

    def get_app_version(self):
        return os.getenv("APP_VERSION", "1.0.0")

    def get_bgmtv_token(self):
        return os.getenv("BGMTV_TOKEN")

    def get_db_file(self):
        return os.getenv("DB_FILE", "data/rank.db")

    def bgmtv_token_masked(self):
        if self.bgmtv_token is None:
            return "Not set"
        return self.bgmtv_token[:3] + "****" + self.bgmtv_token[-3:]


config = Config()
