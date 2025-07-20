from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI
from loguru import logger
from returns.result import Failure, Success

from app.api.v0.update.data import DATA
from app.api.v0.update.models import Empty, UpdateResponse
from app.api.v0.utils import (
    trigger_deploy_hooks,
    verify_password,
)
from app.dependencies import get_bgmtv_client, get_db_client
from app.services import BGMTVClient, DBClient

router = APIRouter(prefix="/update", tags=["update"])


@router.post("/index")
async def update_index(
    _request: Empty,
    bgmtv_client: BGMTVClient = Depends(get_bgmtv_client),
    db_client: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
) -> UpdateResponse:
    success = []
    failed = []
    for season_id, index_id in DATA.items():
        subject_ids = await bgmtv_client.get_index_subject_ids(index_id)
        match subject_ids:
            case Failure(e):
                logger.error(f"获取 {season_id} 季度条目 ID 失败: {e}")
                failed.append(season_id)
                continue
            case Success(subject_ids):
                logger.info(f"获取 {season_id} 季度条目 ID 成功: {subject_ids}")
                result = await db_client.upsert_index(season_id, index_id, subject_ids)
                match result:
                    case Failure(e):
                        logger.error(f"更新 {season_id} 季度条目失败: {e}")
                        failed.append(season_id)
                    case Success():
                        success.append(season_id)
    return UpdateResponse(success=success, failed=failed)


async def update_subject(
    season_id: int,
    subject_id: int,
    updated_at: datetime,
    bgmtv_client: BGMTVClient,
    db_client: DBClient,
) -> bool:
    year = season_id // 100
    month = season_id % 100
    days = (datetime.now() - datetime(year, month, 1)).days // 90
    if updated_at >= datetime.now() - timedelta(days=days):
        logger.info(f"条目 {subject_id} 已是最新")
        return True

    wrapped_subject = await bgmtv_client.get_subject_details(subject_id)
    match wrapped_subject:
        case Failure(e):
            logger.error(f"获取条目 {subject_id} 失败: {e}")
            return False
        case Success(subject):
            if subject.id != subject_id:  # redirect
                subject.id = subject_id
            result = await db_client.upsert_subject(subject)
            match result:
                case Failure(e):
                    logger.error(f"更新条目 {subject_id} 失败: {e}")
                    return False
                case Success():
                    logger.info(f"更新条目 {subject_id} 成功")
                    return True
    return False


async def update_season(
    season_id: int,
    subject_ids: list[int],
    bgmtv_client: BGMTVClient,
    db_client: DBClient,
) -> UpdateResponse:
    logger.info(f"开始更新 {season_id} 季度条目")
    success = []
    failed = []
    for subject_id in subject_ids:
        exsit_subject = await db_client.get_subject(subject_id)
        match exsit_subject:
            case Failure(_):
                updated_at = datetime(2010, 1, 1)
            case Success(subject):
                updated_at = subject.updated_at
        if await update_subject(
            season_id, subject_id, updated_at, bgmtv_client, db_client
        ):
            success.append(subject_id)
        else:
            failed.append(subject_id)
    logger.info(
        f"更新 {season_id} 季度条目完成: {len(success)} 成功, {len(failed)} 失败"
    )
    return UpdateResponse(success=success, failed=failed)


async def update_all(
    bgmtv_client: BGMTVClient,
    db_client: DBClient,
) -> UpdateResponse:
    start_time = datetime.now()
    success = []
    failed = []
    wrapped_index_subject_ids = await db_client.get_all_subjects()
    match wrapped_index_subject_ids:
        case Failure(e):
            logger.error(f"获取所有条目 ID 失败: {e}")
            return UpdateResponse(success=[], failed=[])
        case Success(_index_subject_ids):
            for season_id, subject_ids in _index_subject_ids.items():
                result = await update_season(
                    season_id, subject_ids, bgmtv_client, db_client
                )
                success.extend(result.success)
                failed.extend(result.failed)
    end_time = datetime.now()
    logger.info(f"全量更新任务完成，耗时 {end_time - start_time}")
    return UpdateResponse(success=success, failed=failed)


@router.post("/subjects")
async def update_subjects(
    _request: Empty,
    background_tasks: BackgroundTasks,
    bgmtv_client: BGMTVClient = Depends(get_bgmtv_client),
    db_client: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
) -> UpdateResponse:
    background_tasks.add_task(update_all, bgmtv_client, db_client)
    return UpdateResponse(success=[], failed=[])


async def scheduled_update_all_subjects(app: FastAPI) -> None:
    logger.info("开始执行全量更新任务")
    start_time = datetime.now()
    try:
        bgmtv_client = app.state.bgmtv_client
        db_client = app.state.db_client

        await update_all(bgmtv_client, db_client)

        end_time = datetime.now()
        logger.info(f"全量更新任务完成，耗时 {end_time - start_time}")
        await trigger_deploy_hooks()
    except Exception as e:
        logger.error(f"定时任务：更新所有条目失败: {e}")
