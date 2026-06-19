import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)

replace_in_file('tests/conftest.py', [
    ('async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:', 'async def async_client() -> AsyncGenerator[AsyncClient, None]:'),
    ('yield db_session', 'async with TestingSessionLocal() as session:\n            yield session')
])

replace_in_file('tests/test_auth.py', [
    ('"/auth/', '"/api/v1/auth/')
])

replace_in_file('tests/test_complaints.py', [
    ('"/complaints/', '"/api/v1/complaints/')
])

replace_in_file('tests/test_notifications.py', [
    ('"/notifications/', '"/api/v1/notifications/'),
    ('f"/notifications/', 'f"/api/v1/notifications/')
])

replace_in_file('tests/test_load.py', [
    ('"/complaints/', '"/api/v1/complaints/')
])
