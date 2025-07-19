import functools
import time
from typing import Callable, TypeVar

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.exc import (
    OperationalError,
    PendingRollbackError,
)
from sqlalchemy.orm import Session

from app.config import config

T = TypeVar("T")


class DatabaseSessionManager:
    """数据库会话管理器，负责创建和管理数据库会话"""

    def __init__(self, db_url: str):
        # 创建引擎时配置连接池
        pool_config = config.get_db_pool_config()
        self.engine = create_engine(db_url, echo=False, **pool_config)
        self._max_retries = 3
        self._retry_delays = [1, 2, 4]  # 指数退避延迟

    def get_session(self) -> Session:
        """创建新的数据库会话"""
        session = Session(self.engine, autoflush=False, autocommit=False)
        logger.debug("创建新的数据库会话")
        return session

    def close_session(self, session: Session) -> None:
        """安全关闭数据库会话"""
        try:
            if session.is_active:
                session.close()
            logger.debug("数据库会话已关闭")
        except Exception as e:
            logger.warning(f"关闭会话时发生错误: {e}")

    def rollback_session(self, session: Session) -> None:
        """安全回滚数据库会话"""
        try:
            if session.is_active:
                session.rollback()
                logger.debug("数据库会话已回滚")
        except Exception as e:
            logger.warning(f"回滚会话时发生错误: {e}")

    def _should_retry(self, exception: Exception) -> bool:
        """判断是否应该重试操作"""
        retryable_exceptions = (
            PendingRollbackError,
            OperationalError,
        )
        return isinstance(exception, retryable_exceptions)

    def _log_retry_attempt(self, attempt: int, exception: Exception) -> None:
        """记录重试尝试"""
        logger.warning(
            f"数据库操作失败，第 {attempt} 次重试: {type(exception).__name__}: {exception}"
        )


# 全局会话管理器实例
_session_manager = None


def get_session_manager() -> DatabaseSessionManager:
    """获取全局会话管理器实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager(config.db_url)
    return _session_manager


def with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    数据库会话装饰器，自动管理会话生命周期

    Args:
        func: 被装饰的函数

    Returns:
        装饰后的函数
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        session_manager = get_session_manager()
        session = None
        last_exception = None

        for attempt in range(session_manager._max_retries + 1):
            try:
                # 创建新会话
                session = session_manager.get_session()

                # 将session作为第一个参数传递给被装饰的函数
                # 假设被装饰的函数是实例方法，第一个参数是self
                if args and hasattr(args[0], "session"):
                    # 临时替换实例的session
                    original_session = args[0].session
                    args[0].session = session
                    try:
                        result = func(*args, **kwargs)
                        # 如果是写操作，自动提交
                        if session.is_modified:
                            session.commit()
                            logger.debug("数据库事务已提交")
                        return result
                    finally:
                        # 恢复原始session
                        args[0].session = original_session
                else:
                    # 直接调用函数
                    result = func(*args, **kwargs)
                    # 如果是写操作，自动提交
                    if session.is_modified:
                        session.commit()
                        logger.debug("数据库事务已提交")
                    return result

            except Exception as e:
                last_exception = e

                # 记录错误
                logger.error(f"数据库操作失败: {type(e).__name__}: {e}")

                # 回滚会话
                if session:
                    session_manager.rollback_session(session)

                # 判断是否需要重试
                if (
                    attempt < session_manager._max_retries
                    and session_manager._should_retry(e)
                ):
                    session_manager._log_retry_attempt(attempt + 1, e)
                    # 等待重试
                    time.sleep(session_manager._retry_delays[attempt])
                    continue
                else:
                    # 不再重试，抛出异常
                    break
            finally:
                # 确保会话被关闭
                if session:
                    session_manager.close_session(session)

        # 如果所有重试都失败了，抛出最后一个异常
        if last_exception:
            raise last_exception

        # 这行代码理论上不会执行，但为了类型检查需要加上
        raise RuntimeError("未知错误")

    return wrapper
