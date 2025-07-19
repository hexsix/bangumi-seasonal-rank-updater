from fastapi import APIRouter, Depends, HTTPException

from app.api.v0.utils import verify_password
from app.services.db.client import db_client

router = APIRouter(prefix="/subject", tags=["subject"])


@router.get("/{subject_id}")
async def get_subject(
    subject_id: int,
    _: bool = Depends(verify_password),
):
    subject = db_client.get_subject(subject_id)
    if subject:
        return subject  # subject已经是字典
    else:
        raise HTTPException(status_code=404, detail="Subject not found")
