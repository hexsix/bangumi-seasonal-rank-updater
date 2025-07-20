from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel


class Index(SQLModel, table=True):
    season_id: int = Field(primary_key=True)
    index_id: int = Field(primary_key=True)
    subject_ids: Optional[List[int]] = Field(
        default=None, sa_column=Column(ARRAY(Integer))
    )

    def __repr__(self) -> str:
        return f"Index(season_id={self.season_id}, index_id={self.index_id}, subject_ids={self.subject_ids})"


class Subject(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: Optional[str] = None
    name_cn: Optional[str] = None
    images_grid: Optional[str] = None
    images_large: Optional[str] = None
    rank: Optional[int] = None
    score: Optional[float] = None
    collection_total: Optional[int] = None
    average_comment: Optional[float] = None
    drop_rate: Optional[float] = None
    air_weekday: Optional[str] = None
    meta_tags: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    updated_at: datetime = Field(nullable=False)

    def __repr__(self) -> str:
        return f"Subject(id={self.id}, name={self.name}, name_cn={self.name_cn}, images_grid={self.images_grid}, images_large={self.images_large}, rank={self.rank}, score={self.score}, collection_total={self.collection_total}, average_comment={self.average_comment}, drop_rate={self.drop_rate}, air_weekday={self.air_weekday}, meta_tags={self.meta_tags}, updated_at={self.updated_at})"
