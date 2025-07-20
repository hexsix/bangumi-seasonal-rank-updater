from pydantic import BaseModel


class Empty(BaseModel):
    pass


class UpdateResponse(BaseModel):
    success: list[int]
    failed: list[int]
