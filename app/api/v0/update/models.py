from pydantic import BaseModel


class Empty(BaseModel):
    pass


class Season2IndexRequest(BaseModel):
    season_id: int
    index_id: int
