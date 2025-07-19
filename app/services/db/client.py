import json

from loguru import logger
from sqlalchemy import create_engine

from app.config import config
from app.services.db.schemas import Index, Subject, YucWiki
from app.services.db.session import with_db_session


class DBClient:
    def __init__(self, db_url: str):
        # 移除长期会话，使用会话管理器
        self.engine = create_engine(db_url, echo=False)
        # 保留session属性用于装饰器访问，但不再长期持有
        self.session = None

    @with_db_session
    def insert_index(self, index: Index) -> int | None:
        self.session.add(index)
        return index.season_id

    @with_db_session
    def insert_subject(self, subject: Subject) -> int | None:
        self.session.add(subject)
        return subject.id

    @with_db_session
    def insert_yucwiki(self, yucwiki: YucWiki) -> int | None:
        self.session.add(yucwiki)
        return yucwiki.id

    @with_db_session
    def get_index(self, season_id: int) -> Index | None:
        return self.session.query(Index).filter(Index.season_id == season_id).first()

    @with_db_session
    def get_subject(self, id: int) -> Subject | None:
        return self.session.query(Subject).filter(Subject.id == id).first()

    @with_db_session
    def get_yucwiki(self, jp_title: str) -> YucWiki | None:
        return self.session.query(YucWiki).filter(YucWiki.jp_title == jp_title).first()

    @with_db_session
    def get_all_index(self) -> list[Index]:
        return self.session.query(Index).all()

    @with_db_session
    def upgrade_index(self, index: Index) -> None:
        old_index = self.get_index(index.season_id)
        if old_index is None:
            self.insert_index(index)
            return
        old_index.subject_ids = index.subject_ids if index.subject_ids else "[]"
        old_index.index_id = index.index_id
        self.session.merge(old_index)
        return None

    @with_db_session
    def upgrade_subject(self, subject: Subject) -> None:
        self.session.merge(subject)
        return None

    @with_db_session
    def upgrade_yucwiki(self, yucwiki: YucWiki) -> None:
        old_yucwiki = self.get_yucwiki(yucwiki.jp_title)
        if old_yucwiki is None:
            self.insert_yucwiki(yucwiki)
            return
        old_yucwiki.subject_id = yucwiki.subject_id
        self.session.merge(old_yucwiki)
        return None

    # Section: 业务
    @with_db_session
    def get_available_seasons(self) -> list[int]:
        season_ids = self.session.query(Index.season_id).distinct().all()
        return [season_id[0] for season_id in season_ids]

    @with_db_session
    def get_season_subjects(self, season_id: int) -> list[Subject]:
        index = self.get_index(season_id)
        if index is None:
            return []
        subject_ids = json.loads(index.subject_ids) if index.subject_ids else []
        subjects = self.session.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        return subjects

    def close(self) -> None:
        # 由于使用会话管理器，只需要处理引擎
        if hasattr(self, "engine"):
            self.engine.dispose()
            logger.info("数据库引擎已关闭")


db_client = DBClient(config.db_url)


if __name__ == "__main__":
    import asyncio

    from app.api.v0.utils import get_subject_detail

    async def main():
        if db_client is not None:
            subject_id = 398951
            subject_data = await get_subject_detail(subject_id)
            db_client.upgrade_subject(subject_data)

            subject = db_client.get_subject(subject_id)
            logger.info(subject)

            db_client.close()
            logger.info("数据库连接已关闭")

    asyncio.run(main())
