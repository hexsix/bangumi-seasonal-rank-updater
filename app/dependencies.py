from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    从应用状态获取DBClient并创建会话
    使用方式: db: Session = Depends(get_db)
    """
    db_client = request.app.state.db_client
    session = None

    try:
        session = await db_client._get_session()
        yield session
    finally:
        if session:
            await db_client._close_session(session)
