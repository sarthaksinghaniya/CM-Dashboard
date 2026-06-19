import os
import re
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.db.session import get_db
from app.models.complaint import Complaint, PriorityEnum, ComplaintStatus
from app.models.attachment import Attachment
from app.schemas.complaint import ComplaintSubmissionResponse, CrisisCreate, CrisisUpdate
from app.services.ml.inference import MLInferenceService
from app.services.email.smtp import async_send_complaint_acknowledgement_email

logger = logging.getLogger(__name__)
router = APIRouter()

# Validation regex patterns
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
PHONE_REGEX = r"^\+?[0-9]{10,15}$"

def get_sla_for_priority(priority: PriorityEnum) -> str:
    if priority == PriorityEnum.CRITICAL:
        return "24 Hours"
    elif priority == PriorityEnum.HIGH:
        return "3 Days"
    elif priority == PriorityEnum.MEDIUM:
        return "5 Days"
    else:
        return "7 Days"

def get_department_for_category(category: str) -> str:
    cat = category.strip().upper()
    if not cat or cat == "OTHER":
        return "GENERAL_DEPT"
    if cat.endswith("_DEPT"):
        return cat
    return f"{cat}_DEPT"

@router.post("/", response_model=ComplaintSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    citizen_name: str = Form(...),
    citizen_email: str = Form(...),
    citizen_phone: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    district: str = Form(...),
    category: Optional[str] = Form(None),
    attachments: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db)
):
    # 1. Input Validations
    citizen_email = citizen_email.lower().strip()
    citizen_phone = citizen_phone.strip()
    citizen_name = citizen_name.strip()
    title = title.strip()
    description = description.strip()
    district = district.strip()

    if not citizen_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Citizen name cannot be empty.")
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint title cannot be empty.")
    if not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint description cannot be empty.")
    if not district:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="District cannot be empty.")

    if not re.match(EMAIL_REGEX, citizen_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )

    if not re.match(PHONE_REGEX, citizen_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Expected 10-15 digits optionally starting with '+'."
        )

    if len(attachments) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many files. Maximum 5 attachments allowed."
        )

    # Validate attachments in-memory first before doing any database or disk work
    for file in attachments:
        # Ignore empty dummy uploads if any
        if not file.filename:
            continue
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension: .{ext}. Allowed extensions: pdf, png, jpg, jpeg."
            )
        
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} exceeds the 10 MB size limit."
            )
        
        EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        if EICAR_SIGNATURE in content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Virus detected in file {file.filename}."
            )
        
        # Reset file pointer for writing
        await file.seek(0)

    # 2. Duplicate submission prevention within 5 minutes
    duplicate_query = select(Complaint).filter(
        Complaint.citizen_email == citizen_email,
        Complaint.title == title,
        Complaint.description == description,
        Complaint.created_at >= datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    dup_res = await db.execute(duplicate_query)
    if dup_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate complaint submitted. Please wait 5 minutes before submitting again."
        )

    # 3. Auto-Classification Fallback
    ml_service = MLInferenceService()
    final_category = category
    if not final_category or not final_category.strip():
        # Classify using fine-tuned model
        ml_res = ml_service.predict(description)
        predicted_labels = ml_res.get("category_pred", ["OTHER"])
        final_category = predicted_labels[0] if predicted_labels else "OTHER"
    
    final_category = final_category.strip()

    # Determine severity/priority
    pred_priority_str = ml_service.predict_severity(description)
    final_priority = PriorityEnum[pred_priority_str]

    # Map department
    final_department = get_department_for_category(final_category)

    # 4. Generate Ticket ID sequentially
    current_year = datetime.now().year
    prefix = f"DL-{current_year}-"
    ticket_query = select(Complaint.ticket_id).filter(
        Complaint.ticket_id.like(f"{prefix}%")
    ).order_by(Complaint.ticket_id.desc()).limit(1)
    ticket_res = await db.execute(ticket_query)
    last_ticket = ticket_res.scalars().first()
    
    if last_ticket:
        try:
            last_seq = int(last_ticket.split("-")[-1])
            next_seq = last_seq + 1
        except Exception:
            next_seq = 1
    else:
        next_seq = 1
    ticket_id = f"{prefix}{next_seq:06d}"

    # 5. Database Save & File Storage Transaction
    db_complaint = Complaint(
        ticket_id=ticket_id,
        citizen_name=citizen_name,
        citizen_email=citizen_email,
        citizen_phone=citizen_phone,
        title=title,
        description=description,
        category=final_category,
        department=final_department,
        district=district,
        priority=final_priority,
        status=ComplaintStatus.OPEN
    )

    UPLOAD_DIR = os.path.join("app", "static", "uploads")
    written_files = []

    try:
        db.add(db_complaint)
        await db.flush() # Populate ID

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        for file in attachments:
            if not file.filename:
                continue
            
            content = await file.read()
            unique_name = f"{uuid.uuid4().hex}_{file.filename}"
            dest_path = os.path.join(UPLOAD_DIR, unique_name)
            
            # Write to disk
            with open(dest_path, "wb") as f:
                f.write(content)
            written_files.append(dest_path)
            
            file_url = f"/static/uploads/{unique_name}"
            db_attachment = Attachment(
                complaint_id=db_complaint.id,
                file_url=file_url
            )
            db.add(db_attachment)

        await db.commit()
    except Exception as e:
        # Rollback DB transaction
        await db.rollback()
        # Clean up files written to disk during this request
        for path in written_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as cleanup_err:
                logger.error(f"Failed to delete file {path} during rollback: {cleanup_err}")
        
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to store complaint registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register complaint due to storage or database error."
        )

    # 6. Async Acknowledgement Email (Failure should not rollback complaint)
    estimated_sla = get_sla_for_priority(final_priority)
    try:
        await async_send_complaint_acknowledgement_email(
            email_to=citizen_email,
            citizen_name=citizen_name,
            ticket_id=ticket_id,
            status=ComplaintStatus.OPEN.value,
            estimated_sla=estimated_sla
        )
    except Exception as email_err:
        logger.error(f"Non-blocking email delivery failure for ticket {ticket_id}: {email_err}")

    # 7. Response
    return ComplaintSubmissionResponse(
        ticket_id=ticket_id,
        status=ComplaintStatus.OPEN.value,
        estimated_sla=estimated_sla
    )
