from datetime import datetime

from fastapi import APIRouter, Depends, FastAPI
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


@router.post("/subjects")
async def update_subjects(
    _request: Empty,
    bgmtv_client: BGMTVClient = Depends(get_bgmtv_client),
    db_client: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
) -> UpdateResponse:
    success = []
    failed = []
    wrapped_subject_ids = await db_client.get_all_subjects()
    match wrapped_subject_ids:
        case Failure(e):
            logger.error(f"获取所有条目 ID 失败: {e}")
            return UpdateResponse(success=[], failed=[])
        case Success(_subject_ids):
            subject_ids = sorted(_subject_ids, reverse=True)
            for subject_id in subject_ids:
                wrapped_subject = await bgmtv_client.get_subject_details(subject_id)
                match wrapped_subject:
                    case Failure(e):
                        logger.error(f"获取条目 {subject_id} 失败: {e}")
                        failed.append(subject_id)
                        continue
                    case Success(subject):
                        result = await db_client.upsert_subject(subject)
                        match result:
                            case Failure(e):
                                logger.error(f"更新条目 {subject_id} 失败: {e}")
                                failed.append(subject_id)
                                continue
                            case Success():
                                success.append(subject_id)
    return UpdateResponse(success=success, failed=failed)


async def scheduled_update_all_subjects(app: FastAPI) -> None:
    logger.info("开始执行全量更新任务")
    start_time = datetime.now()
    try:
        # 直接从应用状态获取客户端实例
        bgmtv_client = app.state.bgmtv_client
        db_client = app.state.db_client

        # 执行更新逻辑
        success = []
        failed = []
        wrapped_subject_ids = await db_client.get_all_subjects()
        match wrapped_subject_ids:
            case Failure(e):
                logger.error(f"获取所有条目 ID 失败: {e}")
                return
            case Success(_subject_ids):
                subject_ids = sorted(_subject_ids, reverse=True)
                for subject_id in subject_ids:
                    wrapped_subject = await bgmtv_client.get_subject_details(subject_id)
                    match wrapped_subject:
                        case Failure(e):
                            logger.error(f"获取条目 {subject_id} 失败: {e}")
                            failed.append(subject_id)
                            continue
                        case Success(subject):
                            result = await db_client.upsert_subject(subject)
                            match result:
                                case Failure(e):
                                    logger.error(f"更新条目 {subject_id} 失败: {e}")
                                    failed.append(subject_id)
                                    continue
                                case Success():
                                    success.append(subject_id)

        end_time = datetime.now()
        logger.info(f"全量更新任务完成，耗时 {end_time - start_time}")
        await trigger_deploy_hooks()
    except Exception as e:
        logger.error(f"定时任务：更新所有条目失败: {e}")
