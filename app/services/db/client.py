import json

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import config
from app.services.db.schemas import Index, Subject, YucWiki


class DBClient:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, echo=False)
        self.session = Session(self.engine)

    def insert_index(self, index: Index) -> int | None:
        self.session.add(index)
        self.session.commit()
        return index.season_id

    def insert_subject(self, subject: Subject) -> int | None:
        self.session.add(subject)
        self.session.commit()
        return subject.id

    def insert_yucwiki(self, yucwiki: YucWiki) -> int | None:
        self.session.add(yucwiki)
        self.session.commit()
        return yucwiki.id

    def get_index(self, season_id: int) -> Index | None:
        return self.session.query(Index).filter(Index.season_id == season_id).first()

    def get_subject(self, id: int) -> Subject | None:
        return self.session.query(Subject).filter(Subject.id == id).first()

    def get_yucwiki(self, jp_title: str) -> YucWiki | None:
        return self.session.query(YucWiki).filter(YucWiki.jp_title == jp_title).first()

    def get_all_index(self) -> list[Index]:
        return self.session.query(Index).all()

    def upgrade_index(self, index: Index) -> None:
        old_index = self.get_index(index.season_id)
        if old_index is None:
            self.insert_index(index)
            return
        old_index.subject_ids = index.subject_ids if index.subject_ids else "[]"
        old_index.index_id = index.index_id
        self.session.merge(old_index)
        self.session.commit()
        return None

    def upgrade_subject(self, subject: Subject) -> None:
        self.session.merge(subject)
        self.session.commit()
        return None

    def upgrade_yucwiki(self, yucwiki: YucWiki) -> None:
        old_yucwiki = self.get_yucwiki(yucwiki.jp_title)
        if old_yucwiki is None:
            self.insert_yucwiki(yucwiki)
            return
        old_yucwiki.subject_id = yucwiki.subject_id
        self.session.merge(old_yucwiki)
        self.session.commit()
        return None

    # Section: 业务
    def get_available_seasons(self) -> list[int]:
        season_ids = self.session.query(Index.season_id).distinct().all()
        return [season_id[0] for season_id in season_ids]

    def get_season_subjects(self, season_id: int) -> list[Subject]:
        index = self.get_index(season_id)
        if index is None:
            return []
        subject_ids = json.loads(index.subject_ids) if index.subject_ids else []
        subjects = self.session.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        return subjects

    def close(self) -> None:
        self.session.close()
        self.engine.dispose()


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
