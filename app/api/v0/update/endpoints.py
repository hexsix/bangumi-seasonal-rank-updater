from datetime import datetime

from fastapi import APIRouter, Depends
from loguru import logger

from app.api.v0.update.models import Empty
from app.api.v0.utils import (
    ancient_season_ids,
    future_season_ids,
    older_season_ids,
    recent_season_ids,
    trigger_deploy_hooks,
    verify_password,
)
from app.dependencies import get_db_client
from app.services import DBClient

router = APIRouter(prefix="/update", tags=["update"])


@router.post("/index")
async def update_index(
    _request: Empty,
    db: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
):
    raise NotImplementedError()


@router.post("/subjects")
async def update_subjects(
    _request: Empty,
    db: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
):
    raise NotImplementedError()


async def update_season_subjects(season_id: int) -> None:
    raise NotImplementedError()


async def update_multiple_seasons_subjects(season_ids: list[int], task_name: str):
    """后台任务：批量更新多个季度的条目"""
    logger.info(f"开始执行 {task_name} 季度条目更新任务，共 {len(season_ids)} 个季度")
    try:
        for season_id in season_ids:
            logger.info(f"开始更新 {season_id} 季度条目")
            await update_season_subjects(season_id)
        logger.info(f"{task_name} 季度条目更新任务完成")
    except Exception as e:
        logger.error(f"{task_name} 季度条目更新任务失败: {e}")


async def scheduled_update_all_subjects():
    logger.info("开始执行全量更新任务")
    start_time = datetime.now()
    try:
        all_season_ids = list(
            future_season_ids()
            | recent_season_ids()
            | older_season_ids()
            | ancient_season_ids()
        )
        all_season_ids = sorted(all_season_ids, reverse=True)
        await update_multiple_seasons_subjects(all_season_ids, "scheduled_all")
        end_time = datetime.now()
        logger.info(f"全量更新任务完成，耗时 {end_time - start_time}")
        await trigger_deploy_hooks()
    except Exception as e:
        logger.error(f"定时任务：更新所有条目失败: {e}")
