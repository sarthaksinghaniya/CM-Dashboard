import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.complaint import Complaint, ComplaintStatus, PriorityEnum
from app.models.feedback import Feedback

@pytest.mark.asyncio
async def test_submit_feedback_success(async_client: AsyncClient, db_session: AsyncSession, create_test_user):
    # 1. Create a resolved complaint
    user = await create_test_user(email="feedback_citizen@example.com")
    complaint = Complaint(
        ticket_id="DL-2026-FDBK01",
        citizen_name="John Citizen",
        citizen_email="feedback_citizen@example.com",
        citizen_phone="9876543210",
        title="Sanitation Issue",
        description="Clean street 5",
        category="SANITATION",
        department="MCD",
        district="West Delhi",
        priority=PriorityEnum.LOW,
        status=ComplaintStatus.RESOLVED
    )
    db_session.add(complaint)
    await db_session.commit()
    await db_session.refresh(complaint)

    # 2. Submit high rating (5 stars -> reward +1.0)
    payload = {
        "ticket_id": "DL-2026-FDBK01",
        "rating": 5,
        "remarks": "Cleaned up perfectly!"
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["reward"] == 1.0
    assert res_data["message"] == "Thank you"

    # Verify DB entry
    db_res = await db_session.execute(
        select(Feedback).filter(Feedback.complaint_id == complaint.id)
    )
    feedback_rec = db_res.scalars().first()
    assert feedback_rec is not None
    assert feedback_rec.rating == 5
    assert feedback_rec.note == "Cleaned up perfectly!"
    assert feedback_rec.citizen_id == user.id

@pytest.mark.asyncio
async def test_submit_feedback_low_rating_negative_reward(async_client: AsyncClient, db_session: AsyncSession):
    # Create resolved complaint
    complaint = Complaint(
        ticket_id="DL-2026-FDBK02",
        citizen_name="John Citizen",
        citizen_email="no_user@example.com",
        citizen_phone="9876543210",
        title="Power Line Issue",
        description="Sparks flying",
        category="ELECTRICITY",
        department="DISCOM",
        district="North Delhi",
        priority=PriorityEnum.HIGH,
        status=ComplaintStatus.RESOLVED
    )
    db_session.add(complaint)
    await db_session.commit()

    # Submit low rating (1 star -> reward -2.0)
    payload = {
        "ticket_id": "DL-2026-FDBK02",
        "rating": 1,
        "remarks": "Worst experience ever."
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 201
    assert response.json()["reward"] == -2.0

@pytest.mark.asyncio
async def test_submit_feedback_unresolved_complaint(async_client: AsyncClient, db_session: AsyncSession):
    # Complaint is only ASSIGNED, not resolved
    complaint = Complaint(
        ticket_id="DL-2026-FDBK03",
        citizen_name="John",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Road repairs",
        description="Potholes",
        category="ROAD",
        department="PWD",
        district="South Delhi",
        priority=PriorityEnum.MEDIUM,
        status=ComplaintStatus.ASSIGNED
    )
    db_session.add(complaint)
    await db_session.commit()

    payload = {
        "ticket_id": "DL-2026-FDBK03",
        "rating": 4
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 400
    assert "only be submitted for RESOLVED complaints" in response.json()["detail"]

@pytest.mark.asyncio
async def test_submit_feedback_duplicate(async_client: AsyncClient, db_session: AsyncSession):
    complaint = Complaint(
        ticket_id="DL-2026-FDBK04",
        citizen_name="John",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Road repairs",
        description="Potholes",
        category="ROAD",
        department="PWD",
        district="South Delhi",
        priority=PriorityEnum.MEDIUM,
        status=ComplaintStatus.RESOLVED
    )
    db_session.add(complaint)
    await db_session.commit()

    payload = {
        "ticket_id": "DL-2026-FDBK04",
        "rating": 4
    }
    # First submit
    res1 = await async_client.post("/api/v1/feedback/", json=payload)
    assert res1.status_code == 201

    # Second submit (should fail)
    res2 = await async_client.post("/api/v1/feedback/", json=payload)
    assert res2.status_code == 400
    assert "Feedback has already been submitted" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_submit_feedback_invalid_rating(async_client: AsyncClient):
    # Rating must be 1-5 (validated by Pydantic)
    payload = {
        "ticket_id": "DL-2026-FDBK01",
        "rating": 6
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 422

    payload = {
        "ticket_id": "DL-2026-FDBK01",
        "rating": 0
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_submit_feedback_invalid_ticket(async_client: AsyncClient):
    payload = {
        "ticket_id": "random-text",
        "rating": 5
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 400
    assert "Invalid ticket format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_submit_feedback_soft_deleted(async_client: AsyncClient, db_session: AsyncSession):
    complaint = Complaint(
        ticket_id="DL-2026-FDBK05",
        citizen_name="John",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Road repairs",
        description="Potholes",
        category="ROAD",
        department="PWD",
        district="South Delhi",
        priority=PriorityEnum.MEDIUM,
        status=ComplaintStatus.RESOLVED,
        is_deleted=True
    )
    db_session.add(complaint)
    await db_session.commit()

    payload = {
        "ticket_id": "DL-2026-FDBK05",
        "rating": 5
    }
    response = await async_client.post("/api/v1/feedback/", json=payload)
    assert response.status_code == 404
