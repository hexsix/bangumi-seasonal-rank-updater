import os
import socket
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from loguru import logger

from app.api.v0.routers import routers as v0_routers
from app.config import config

load_dotenv()


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
    logger.debug(config.pretty_print())

    yield

    logger.info("Shutting down...")
    logger.stop()
    logger.complete()


app = FastAPI(lifespan=lifespan)

api_router = APIRouter(prefix="/api")
for v0_router in v0_routers:
    api_router.include_router(v0_router, prefix="/v0")
app.include_router(api_router)
