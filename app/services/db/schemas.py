import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Index(Base):
    __tablename__ = "index"
    season_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_ids: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"Index(season_id={self.season_id}, index_id={self.index_id}, subject_ids={self.subject_ids})"

    @classmethod
    def from_dict(cls, data: dict) -> "Index":
        return cls(
            season_id=data["season_id"],
            index_id=data["index_id"],
            subject_ids=json.dumps(data["subject_ids"]),
        )

    def to_dict(self) -> dict:
        return {
            "season_id": self.season_id,
            "index_id": self.index_id,
            "subject_ids": json.loads(self.subject_ids) if self.subject_ids else [],
        }


class Subject(Base):
    __tablename__ = "subject"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_cn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    images_grid: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    images_large: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    collection_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_comment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    drop_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    air_weekday: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    meta_tags: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"Subject(id={self.id}, name={self.name}, name_cn={self.name_cn}, images_grid={self.images_grid}, images_large={self.images_large}, rank={self.rank}, score={self.score}, collection_total={self.collection_total}, average_comment={self.average_comment}, drop_rate={self.drop_rate}, air_weekday={self.air_weekday}, meta_tags={self.meta_tags}, updated_at={self.updated_at})"

    @classmethod
    def from_dict(cls, data: dict) -> "Subject":
        return cls(
            id=data["id"],
            name=data["name"],
            name_cn=data["name_cn"],
            images_grid=data["images_grid"],
            images_large=data["images_large"],
            rank=data["rank"],
            score=data["score"],
            collection_total=data["collection_total"],
            average_comment=data["average_comment"],
            drop_rate=data["drop_rate"],
            air_weekday=data["air_weekday"],
            meta_tags=json.dumps(data["meta_tags"]),
            updated_at=data["updated_at"].isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_cn": self.name_cn,
            "images_grid": self.images_grid,
            "images_large": self.images_large,
            "rank": self.rank,
            "score": self.score,
            "collection_total": self.collection_total,
            "average_comment": self.average_comment,
            "drop_rate": self.drop_rate,
            "air_weekday": self.air_weekday,
            "meta_tags": json.loads(self.meta_tags) if self.meta_tags else [],
            "updated_at": datetime.fromisoformat(self.updated_at),
        }


class YucWiki(Base):
    __tablename__ = "yucwiki"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jp_title: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self):
        return f"YucWiki(id={self.id}, jp_title={self.jp_title}, subject_id={self.subject_id})"

    @classmethod
    def from_dict(cls, data: dict) -> "YucWiki":
        return cls(
            jp_title=data["jp_title"],
            subject_id=data["subject_id"],
        )

    def to_dict(self) -> dict:
        return {
            "jp_title": self.jp_title,
            "subject_id": self.subject_id,
        }
