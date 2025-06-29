from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from redis.asyncio import Redis

from app.config import config


class RedisClient:
    def __init__(self):
        if not config.redis_password:
            self.client = Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=0,
                decode_responses=True,
            )
        else:
            self.client = Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=0,
                decode_responses=True,
                password=config.redis_password,
            )

    async def get(self, key: str) -> str:
        return await self.client.get(key)

    async def set(self, key: str, value: str) -> None:
        self.client.set(key, value)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def ping(self) -> bool:
        return await self.client.ping()

    async def close(self) -> None:
        await self.client.aclose()


class Subject(BaseModel):
    id: int
    name: Optional[str]
    name_cn: Optional[str]
    images_grid: Optional[str]
    images_large: Optional[str]
    rank: Optional[int]
    score: Optional[float]
    collection_total: Optional[int]
    average_comment: Optional[float]
    drop_rate: Optional[float]
    air_weekday: Optional[str]
    meta_tags: Optional[list[str]]
    updated_at: datetime


async def get_index_id(redis_client: Redis, season_id: int) -> int | None:
    key = f"rank.index:{season_id}"
    index_id = await redis_client.get(key)
    if index_id is None:
        return None
    return int(index_id)


async def create_index(redis_client: Redis, season_id: int, index_id: int) -> None:
    key = f"rank.index:{season_id}"
    await redis_client.set(key, index_id)


async def update_subject(redis_client: Redis, subject: Subject) -> None:
    key = f"rank.subject:{subject.id}"
    await redis_client.set(key, subject.model_dump_json())


async def get_subject(redis_client: Redis, subject_id: int) -> Subject | None:
    key = f"rank.subject:{subject_id}"
    subject = await redis_client.get(key)
    if subject is None:
        return None
    return Subject.model_validate_json(subject)


async def get_available_seasons(redis_client: Redis) -> list[int]:
    key = "rank.index:*"
    keys = await redis_client.keys(key)
    if not keys:
        return []
    return [int(key.split(":")[-1]) for key in keys]


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    async def main():
        redis_client = RedisClient()
        print(await redis_client.ping())
        await redis_client.close()

    import asyncio

    asyncio.run(main())
