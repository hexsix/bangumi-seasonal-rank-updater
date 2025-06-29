from datetime import datetime

from loguru import logger

from app.services import redis_client
from app.services.bgmtv import get_episodes, get_subject


async def get_subject_detail(subject_id: int) -> redis_client.Subject:
    """获取条目详情"""
    subject = await get_subject(subject_id)

    if subject.images:
        grid = subject.images.grid
        large = subject.images.large

    if subject.rating:
        rank = subject.rating.rank
        if subject.rating.count and subject.rating.total:
            total_score = 0
            for key, value in subject.rating.count.items():
                total_score += key * value
            score = total_score / subject.rating.total
        else:
            score = subject.rating.score
    else:
        rank = None
        score = None

    if subject.collection:
        total = (
            subject.collection.collect
            + subject.collection.wish
            + subject.collection.doing
            + subject.collection.on_hold
            + subject.collection.dropped
        )
        drop_rate = subject.collection.dropped / total
    else:
        total = None
        drop_rate = None

    # 处理infobox字段，仅保留"放送星期"
    air_weekday = None
    if subject.infobox:
        for item in subject.infobox:
            if item.key == "放送星期":
                air_weekday = item.value

    episodes = await get_episodes(subject_id, 0, 100, 0)
    if not episodes or not episodes.data:
        average_comment = 0
    else:
        current_date = datetime.now().date()
        aired_episodes = []
        total_comments = 0

        for episode in episodes.data:
            # 检查是否有播出日期
            if episode.airdate:
                try:
                    airdate = datetime.strptime(episode.airdate, "%Y-%m-%d").date()
                    # 只统计已播出的集数
                    if airdate <= current_date:
                        episode_info = {
                            "ep": episode.ep,
                            "comments": episode.comment,
                        }
                        aired_episodes.append(episode_info)
                        if episode.comment:
                            total_comments += episode.comment
                except ValueError:
                    logger.warning(f"无效的播出日期格式: {episode.airdate}")

        if aired_episodes:
            average_comment = total_comments / len(aired_episodes)
        else:
            average_comment = 0

    redis_subject = redis_client.Subject(
        id=subject.id,
        name=subject.name,
        name_cn=subject.name_cn,
        images_grid=grid,
        images_large=large,
        rank=rank,
        score=score,
        collection_total=total,
        average_comment=average_comment,
        drop_rate=drop_rate,
        air_weekday=air_weekday,
        meta_tags=subject.meta_tags,
        updated_at=datetime.now(),
    )
    return redis_subject


if __name__ == "__main__":
    import asyncio

    async def main():
        subject_id = 486347
        subject_data = await get_subject_detail(subject_id)
        print(subject_data)

    asyncio.run(main())
