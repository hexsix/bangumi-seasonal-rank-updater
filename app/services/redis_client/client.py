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


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    async def main():
        redis_client = RedisClient()
        print(await redis_client.ping())
        await redis_client.close()

    import asyncio

    asyncio.run(main())
