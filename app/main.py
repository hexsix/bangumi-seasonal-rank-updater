import os
import socket
import sys
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v0.routers import routers as v0_routers
from app.api.v0.update.endpoints import scheduled_update_all_subjects
from app.config import config
from app.services.db.client import db_client

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.remove()
    logger.add(sys.stdout, level=config.log_level)
    log_filename = os.path.join(
        os.path.dirname(__file__), "logs", f"{socket.gethostname()}_{{time}}.log"
    )
    logger.add(
        log_filename,
        level=config.log_level,
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )
    logger.info("Starting up...")

    scheduler.add_job(
        scheduled_update_all_subjects,
        "interval",
        hours=4,
        id="update_all_subjects",
        name="每4小时更新所有条目",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("调度器已启动，每4小时执行一次全量更新任务")

    yield

    logger.info("Shutting down...")
    scheduler.shutdown()
    logger.info("调度器已停止")
    db_client.close()
    logger.stop()
    logger.complete()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rinshankaiho.fun",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
for v0_router in v0_routers:
    api_router.include_router(v0_router, prefix="/v0")
app.include_router(api_router)
