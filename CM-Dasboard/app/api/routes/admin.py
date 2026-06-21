from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from pydantic import BaseModel

from app.api.deps import get_db, require_role, Admin
from app.models.complaint import Complaint, ComplaintStatus
from app.models.complaint_update import ComplaintUpdate
from app.services.storage.attachment import AttachmentService
from app.schemas.complaint import Complaint as ComplaintSchema
from app.models.user import User

router = APIRouter()

class StatusUpdateRequest(BaseModel):
    status: str
    note: str = None

@router.get("/complaints", response_model=List[ComplaintSchema])
async def get_all_complaints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Admin))
):
    # Admins can see all complaints
    query = select(Complaint).order_by(Complaint.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/complaints/{ticket_id}")
async def update_complaint_status(
    ticket_id: str,
    payload: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Admin))
):
    try:
        new_status = ComplaintStatus(payload.status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
    result = await db.execute(query)
    complaint = result.scalars().first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = new_status

    db_update = ComplaintUpdate(
        complaint_id=complaint.id,
        status=new_status.value,
        note=payload.note or "Status updated by admin.",
        updated_by=current_user.id
    )
    db.add(db_update)
    await db.commit()

    return {"msg": "Status updated successfully", "status": new_status.value}

@router.post("/complaints/{ticket_id}/proof")
async def upload_proof(
    ticket_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Admin))
):
    query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
    result = await db.execute(query)
    complaint = result.scalars().first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    attach_rec = await AttachmentService.validate_and_upload(
        file=file,
        complaint_id=complaint.id,
        db=db
    )
    await db.commit()

    return {"msg": "Proof uploaded successfully", "file_url": attach_rec.file_url}
