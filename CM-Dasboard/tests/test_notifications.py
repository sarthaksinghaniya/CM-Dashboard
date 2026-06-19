import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.services.notification.service import NotificationService
from app.models.notification import Notification

@pytest.mark.asyncio
async def test_trigger_notification_success(db_session: AsyncSession, create_test_user):
    user = await create_test_user(email="notify@example.com")
    
    with patch("app.services.notification.service.async_send_notification_email", new_callable=AsyncMock) as mock_email:
        background_tasks = AsyncMock()
        
        NotificationService.trigger_notification(
            db=db_session,
            background_tasks=background_tasks,
            user_id=user.id,
            title="Test Alert",
            message="This is a test notification.",
            type="status_changed"
        )
        
        # Verify db record
        res = await db_session.execute(select(Notification).filter(Notification.user_id == user.id))
        notifs = res.scalars().all()
        assert len(notifs) == 1
        assert notifs[0].title == "Test Alert"
        
        # Background task should be called
        assert background_tasks.add_task.called

@pytest.mark.asyncio
async def test_trigger_notification_duplicate_storm_protection(db_session: AsyncSession, create_test_user):
    user = await create_test_user(email="storm@example.com")
    
    background_tasks = AsyncMock()
    
    # Send 1st
    NotificationService.trigger_notification(
        db=db_session,
        background_tasks=background_tasks,
        user_id=user.id,
        title="Duplicate Alert",
        message="This is a test notification.",
        type="status_changed"
    )
    
    # Send 2nd (identical content, should be dropped)
    NotificationService.trigger_notification(
        db=db_session,
        background_tasks=background_tasks,
        user_id=user.id,
        title="Duplicate Alert",
        message="This is a test notification.",
        type="status_changed"
    )
    
    # Verify only 1 db record exists
    res = await db_session.execute(select(Notification).filter(Notification.user_id == user.id))
    notifs = res.scalars().all()
    assert len(notifs) == 1

@pytest.mark.asyncio
async def test_trigger_notification_inactive_user(db_session: AsyncSession, create_test_user):
    user = await create_test_user(email="deleted@example.com")
    user.is_deleted = True
    await db_session.commit()
    
    background_tasks = AsyncMock()
    
    NotificationService.trigger_notification(
        db=db_session,
        background_tasks=background_tasks,
        user_id=user.id,
        title="Should Not Send",
        message="User is deleted.",
        type="status_changed"
    )
    
    # Verify no record created
    res = await db_session.execute(select(Notification).filter(Notification.user_id == user.id))
    notifs = res.scalars().all()
    assert len(notifs) == 0

@pytest.mark.asyncio
async def test_get_notifications_api(async_client: AsyncClient, db_session: AsyncSession, create_test_user, auth_headers):
    user = await create_test_user(email="api_notify@example.com")
    headers = await auth_headers(user=user)
    
    # Create notification
    notif = Notification(
        user_id=user.id,
        title="API Test",
        message="API Message",
        type="status_changed",
        is_read=False
    )
    db_session.add(notif)
    await db_session.commit()
    
    res = await async_client.get("/api/v1/notifications/", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1
    assert res.json()["items"][0]["title"] == "API Test"

@pytest.mark.asyncio
async def test_mark_notification_read(async_client: AsyncClient, db_session: AsyncSession, create_test_user, auth_headers):
    user = await create_test_user(email="read_notify@example.com")
    headers = await auth_headers(user=user)
    
    notif = Notification(
        user_id=user.id,
        title="Mark Read",
        message="Read Me",
        type="status_changed",
        is_read=False
    )
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)
    
    res = await async_client.post(f"/api/v1/notifications/{notif.id}/read", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_read"] is True
    
    # Verify db updated
    await db_session.refresh(notif)
    assert notif.is_read is True
