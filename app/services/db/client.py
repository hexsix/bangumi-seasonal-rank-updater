import asyncio
from typing import Awaitable, Callable, Sequence, TypeVar

from loguru import logger
from returns.result import Failure, Result, Success
from sqlalchemy import Column
from sqlalchemy.exc import (
    OperationalError,
    PendingRollbackError,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select

from app.config import config
from app.services.db.schemas import Index, Subject

T = TypeVar("T")


class DBClient:
    """数据库客户端，集成会话管理和数据访问功能"""

    def __init__(self, db_url: str):
        pool_config = config.get_db_pool_config()
        self.engine = create_async_engine(db_url, echo=False, **pool_config)
        self._max_retries = 3
        self._retry_delays = [1, 2, 4]  # 指数退避延迟

    async def _get_session(self) -> AsyncSession:
        """创建新的数据库会话"""
        session = AsyncSession(self.engine, autoflush=False, autocommit=False)
        logger.debug("创建新的数据库会话")
        return session

    async def _close_session(self, session: AsyncSession) -> None:
        """安全关闭数据库会话"""
        try:
            if session.is_active:
                await session.close()
            logger.debug("数据库会话已关闭")
        except Exception as e:
            logger.warning(f"关闭会话时发生错误: {e}")

    async def _rollback_session(self, session: AsyncSession) -> None:
        """安全回滚数据库会话"""
        try:
            if session.is_active:
                await session.rollback()
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

    async def _execute_with_retry(
        self, operation: Callable[[AsyncSession], Awaitable[T]]
    ) -> Result[T, Exception]:
        """执行数据库操作，支持重试机制"""
        last_exception = Exception("未知错误")

        for attempt in range(self._max_retries + 1):
            session = None
            try:
                session = await self._get_session()
                result = await operation(session)
                if session.dirty or session.new or session.deleted:
                    await session.commit()
                    logger.debug("数据库事务已提交")
                return Success(result)

            except Exception as e:
                last_exception = e
                logger.error(f"数据库操作失败: {type(e).__name__}: {e}")

                if session:
                    await self._rollback_session(session)

                if attempt < self._max_retries and self._should_retry(e):
                    self._log_retry_attempt(attempt + 1, e)
                    await asyncio.sleep(self._retry_delays[attempt])
                    continue
                else:
                    break
            finally:
                if session:
                    await self._close_session(session)

        if last_exception:
            return Failure(last_exception)

        return Failure(RuntimeError("未知错误"))

    async def close(self) -> None:
        """关闭数据库引擎"""
        await self.engine.dispose()
        logger.info("数据库引擎已关闭")

    async def get_available_seasons(self) -> Result[list[int], Exception]:
        async def operation(session: AsyncSession) -> list[int]:
            stmt = select(Index.season_id).distinct()
            result = await session.execute(stmt)
            season_ids = result.scalars().all()
            return list(season_ids)

        return await self._execute_with_retry(operation)

    async def get_season_subjects(
        self, season_id: int
    ) -> Result[list[Subject], Exception]:
        async def operation(session: AsyncSession) -> list[Subject]:
            stmt = select(Index.subject_ids).where(Index.season_id == season_id)
            result = await session.execute(stmt)
            subject_ids = result.scalar_one_or_none()
            if subject_ids:
                subject_stmt = select(Subject).where(Column("id").in_(subject_ids))
                result = await session.execute(subject_stmt)
                subjects: Sequence[Subject] = result.scalars().all()
                return [subject for subject in subjects if subject is not None]
            else:
                return []

        return await self._execute_with_retry(operation)

    async def get_subject(self, id: int) -> Result[Subject, Exception]:
        async def operation(session: AsyncSession) -> Subject:
            stmt = select(Subject).where(Subject.id == id)
            result = await session.execute(stmt)
            subject = result.scalar_one_or_none()
            if subject:
                return subject
            else:
                raise Exception(f"Subject with id {id} not found")

        return await self._execute_with_retry(operation)

    async def get_index(self, season_id: int) -> Result[Index, Exception]:
        async def operation(session: AsyncSession) -> Index:
            stmt = select(Index).where(Index.season_id == season_id)
            result = await session.execute(stmt)
            index = result.scalar_one_or_none()
            if index:
                return index
            else:
                raise Exception(f"Index with season_id {season_id} not found")

        return await self._execute_with_retry(operation)

    async def get_all_index(self) -> Result[list[Index], Exception]:
        async def operation(session: AsyncSession) -> list[Index]:
            stmt = select(Index)
            result = await session.execute(stmt)
            return [index for index in result.scalars().all()]

        return await self._execute_with_retry(operation)
