from fastapi import APIRouter, HTTPException

from app.services.db.client import db_client

router = APIRouter(prefix="/subject", tags=["subject"])


@router.get("/{subject_id}")
async def get_subject(
    subject_id: int,
):
    subject = db_client.get_subject(subject_id)
    if subject:
        return subject.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Subject not found")
