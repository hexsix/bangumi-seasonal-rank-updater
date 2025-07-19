from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v0.utils import verify_password
from app.services import db
from app.services.db.client import db_client

router = APIRouter(prefix="/yucwiki", tags=["yucwiki"])


class YucWikiRequest(BaseModel):
    jp_title: str
    subject_id: Optional[int] = None


@router.post("/get")
async def get_yucwiki(
    request: YucWikiRequest,
    _: bool = Depends(verify_password),
):
    yucwiki = db_client.get_yucwiki(request.jp_title)
    if yucwiki:
        return yucwiki  # yucwiki已经是字典
    else:
        raise HTTPException(status_code=404, detail="YucWiki not found")


@router.post("/update")
async def update_yucwiki(
    request: YucWikiRequest,
    _: bool = Depends(verify_password),
):
    if request.subject_id is None:
        raise HTTPException(status_code=400, detail="Subject ID is required")
    yucwiki = db_client.get_yucwiki(request.jp_title)
    if yucwiki:
        yucwiki.subject_id = request.subject_id
        db_client.upgrade_yucwiki(yucwiki)
        return "updated"
    else:
        db_client.insert_yucwiki(
            db.YucWiki(jp_title=request.jp_title, subject_id=request.subject_id)
        )
        return "created"
