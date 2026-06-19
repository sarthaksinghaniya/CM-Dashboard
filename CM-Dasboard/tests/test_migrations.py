import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

@pytest.mark.asyncio
async def test_district_column_migration(db_session: AsyncSession):
    # Retrieve the sync connection underlying the async session to use inspector
    sync_conn = await db_session.connection()
    
    def get_columns(conn):
        inspector = inspect(conn)
        return inspector.get_columns('users')
        
    columns = await sync_conn.run_sync(get_columns)
    column_names = [col['name'] for col in columns]
    
    # Verify the migration added the 'district' column
    assert 'district' in column_names, "District column missing from users table"
    assert 'department' in column_names, "Department column missing from users table"
