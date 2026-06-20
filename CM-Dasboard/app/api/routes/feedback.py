import re
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.engines.faiss_rag import get_memory_service
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger("cm_dashboard.api.routes.feedback")
router = APIRouter()

TICKET_REGEX = r"^DL-\d{4}-[A-Z0-9]{6}$"

async def send_feedback_email_safely(email_to: str, ticket_id: str, rating: int, remarks: str):
    try:
        from app.services.email.smtp import async_send_feedback_acknowledgement_email
        await async_send_feedback_acknowledgement_email(
            email_to=email_to,
            ticket_id=ticket_id,
            rating=rating,
            remarks=remarks
        )
    except Exception as e:
        logger.error(f"Failed to send feedback acknowledgement email to {email_to}: {e}", exc_info=True)

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_citizen_feedback(
    payload: FeedbackCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback rating and remarks for a resolved complaint.
    Returns the calculated reinforcement learning reward and a thank you message.
    """
    # 1. Enforce rate limiting: 10 requests per minute per IP
    await check_rate_limit(request, "feedback", limit=10, window_seconds=60)

    # 2. Validate ticket format
    ticket_id = payload.ticket_id.upper().strip()
    if not re.match(TICKET_REGEX, ticket_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ticket format. Expected format: DL-YYYY-XXXXXX"
        )

    # 3. Fetch complaint with feedbacks preloaded
    stmt = (
        select(Complaint)
        .where(Complaint.ticket_id == ticket_id)
        .options(selectinload(Complaint.feedbacks))
    )
    result = await db.execute(stmt)
    complaint = result.scalars().first()

    # Handle nonexistent or soft-deleted complaint
    if not complaint or complaint.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ticket ID '{ticket_id}' not found."
        )

    # 4. Validation: Complaint must be RESOLVED
    if complaint.status != ComplaintStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted for RESOLVED complaints."
        )

    # 5. Validation: Citizen can submit feedback only once per complaint
    if complaint.feedbacks and len(complaint.feedbacks) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback has already been submitted for this complaint."
        )

    # 6. Resolve citizen User ID if exists
    citizen_id = None
    if complaint.citizen_email:
        user_stmt = select(User).where(User.email == complaint.citizen_email)
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()
        if user:
            citizen_id = user.id

    # 7. Create and save feedback
    feedback = Feedback(
        complaint_id=complaint.id,
        citizen_id=citizen_id,
        rating=payload.rating,
        note=payload.remarks
    )
    db.add(feedback)

    # 8. Apply RL Reward to FAISS Memory & record in ledger
    try:
        from app.services.rl.feedback_manager import FeedbackManager
        feedback_manager = FeedbackManager()
        reward = feedback_manager.record_citizen_rating(
            ticket_id=ticket_id,
            rating=payload.rating,
            remarks=payload.remarks
        )
    except Exception as e:
        logger.error(f"Failed to record rating reward in ledger: {e}")
        rating_map = {5: 1.0, 4: 0.5, 3: 0.0, 2: -1.0, 1: -2.0}
        reward = rating_map.get(payload.rating, 0.0)

    try:
        memory_service = get_memory_service()
        # Feed context to RAG search reinforcement
        await memory_service.async_apply_rl_reward(
            text=complaint.description or complaint.title,
            reward=reward,
            metadata={
                "ticket_id": complaint.ticket_id,
                "category": complaint.category,
                "assigned_officer_id": str(complaint.assigned_to) if complaint.assigned_to else None
            }
        )
    except Exception as rl_err:
        # Non-blocking failure for RL memory update
        logger.warning(f"Failed to apply RL reward to FAISS store: {rl_err}")

    # Commit feedback transaction
    await db.commit()

    # Async background task to send acknowledgement email (if email present)
    if complaint.citizen_email:
        background_tasks.add_task(
            send_feedback_email_safely,
            email_to=complaint.citizen_email,
            ticket_id=ticket_id,
            rating=payload.rating,
            remarks=payload.remarks
        )

    return FeedbackResponse(
        reward=reward,
        message="Thank you"
    )
