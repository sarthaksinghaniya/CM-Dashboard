import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta

from app.models.complaint import Complaint, ComplaintStatus, PriorityEnum
from app.models.complaint_update import ComplaintUpdate
from app.models.attachment import Attachment

@pytest.mark.asyncio
async def test_track_complaint_success(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create a complaint in the database
    complaint = Complaint(
        ticket_id="DL-2026-A1B2C3",
        citizen_name="John Citizen",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Pothole Issue",
        description="Pothole near street 5",
        category="ROAD",
        department="PWD",
        district="South Delhi",
        priority=PriorityEnum.MEDIUM,
        status=ComplaintStatus.SUBMITTED
    )
    db_session.add(complaint)
    await db_session.commit()
    await db_session.refresh(complaint)

    # 2. Add an attachment
    attachment = Attachment(
        complaint_id=complaint.id,
        file_url="/static/uploads/pothole.jpg",
        mime_type="image/jpeg"
    )
    db_session.add(attachment)

    # 3. Add status updates with explicit timezone info to prevent timezone mismatch under SQLite/PG
    t0 = datetime.now(timezone.utc) - timedelta(minutes=10)
    t1 = datetime.now(timezone.utc) - timedelta(minutes=5)

    update1 = ComplaintUpdate(
        complaint_id=complaint.id,
        status="SUBMITTED",
        note="Initial submission",
        created_at=t0
    )
    update2 = ComplaintUpdate(
        complaint_id=complaint.id,
        status="ASSIGNED",
        note="Assigned to PWD Officer",
        created_at=t1
    )
    db_session.add(update1)
    db_session.add(update2)
    await db_session.commit()

    # 4. Fetch tracking data via public endpoint
    response = await async_client.get("/api/v1/complaints/track/DL-2026-A1B2C3")
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["ticket_id"] == "DL-2026-A1B2C3"
    assert res_data["status"] == ComplaintStatus.SUBMITTED.value
    assert len(res_data["attachments"]) == 1
    assert res_data["attachments"][0]["file_url"] == "/static/uploads/pothole.jpg"
    
    # Timeline should have 2 updates sorted ascending
    assert len(res_data["timeline"]) == 2
    assert res_data["timeline"][0]["status"] == "SUBMITTED"
    assert res_data["timeline"][1]["status"] == "ASSIGNED"

@pytest.mark.asyncio
async def test_track_complaint_invalid_format(async_client: AsyncClient):
    response = await async_client.get("/api/v1/complaints/track/DL-202-A1B2")
    assert response.status_code == 400
    assert "Invalid ticket format" in response.json()["detail"]

    response = await async_client.get("/api/v1/complaints/track/random-text")
    assert response.status_code == 400
    assert "Invalid ticket format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_track_complaint_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/complaints/track/DL-2026-999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_track_complaint_soft_deleted(async_client: AsyncClient, db_session: AsyncSession):
    complaint = Complaint(
        ticket_id="DL-2026-DELETD",
        citizen_name="John Citizen",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Trash Issue",
        description="Trash not collected",
        category="SANITATION",
        department="MCD",
        district="West Delhi",
        priority=PriorityEnum.LOW,
        status=ComplaintStatus.SUBMITTED,
        is_deleted=True
    )
    db_session.add(complaint)
    await db_session.commit()

    response = await async_client.get("/api/v1/complaints/track/DL-2026-DELETD")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_track_complaint_no_updates_fallback(async_client: AsyncClient, db_session: AsyncSession):
    complaint = Complaint(
        ticket_id="DL-2026-NOUPDT",
        citizen_name="John Citizen",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Water Issue",
        description="Low water pressure",
        category="WATER",
        department="DJB",
        district="East Delhi",
        priority=PriorityEnum.LOW,
        status=ComplaintStatus.SUBMITTED
    )
    db_session.add(complaint)
    await db_session.commit()
    await db_session.refresh(complaint)

    response = await async_client.get("/api/v1/complaints/track/DL-2026-NOUPDT")
    assert response.status_code == 200
    res_data = response.json()

    # Timeline fallback: should contain 1 'SUBMITTED' entry mapped from complaint's created_at
    assert len(res_data["timeline"]) == 1
    assert res_data["timeline"][0]["status"] == "SUBMITTED"
    assert res_data["timeline"][0]["note"] == "Complaint submitted."

@pytest.mark.asyncio
async def test_track_complaint_multiple_escalations(async_client: AsyncClient, db_session: AsyncSession):
    complaint = Complaint(
        ticket_id="DL-2026-ESCAL8",
        citizen_name="John Citizen",
        citizen_email="john@example.com",
        citizen_phone="9876543210",
        title="Power Outage",
        description="No power for 24h",
        category="ELECTRICITY",
        department="DISCOM",
        district="North Delhi",
        priority=PriorityEnum.CRITICAL,
        status=ComplaintStatus.ESCALATED
    )
    db_session.add(complaint)
    await db_session.commit()
    await db_session.refresh(complaint)

    # Adding updates that simulate multiple escalations
    t0 = datetime.now(timezone.utc) - timedelta(hours=3)
    t1 = datetime.now(timezone.utc) - timedelta(hours=2)
    t2 = datetime.now(timezone.utc) - timedelta(hours=1)

    update1 = ComplaintUpdate(complaint_id=complaint.id, status="SUBMITTED", note="Sub", created_at=t0)
    update2 = ComplaintUpdate(complaint_id=complaint.id, status="ESCALATED", note="First escalation", created_at=t1)
    update3 = ComplaintUpdate(complaint_id=complaint.id, status="ESCALATED", note="Re-escalation to super-head", created_at=t2)

    db_session.add_all([update1, update2, update3])
    await db_session.commit()

    response = await async_client.get("/api/v1/complaints/track/DL-2026-ESCAL8")
    assert response.status_code == 200
    res_data = response.json()

    assert len(res_data["timeline"]) == 3
    assert res_data["timeline"][0]["status"] == "SUBMITTED"
    assert res_data["timeline"][1]["status"] == "ESCALATED"
    assert res_data["timeline"][1]["note"] == "First escalation"
    assert res_data["timeline"][2]["status"] == "ESCALATED"
    assert res_data["timeline"][2]["note"] == "Re-escalation to super-head"
