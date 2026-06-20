import asyncio
from app.db.session import engine
from app.models.base import Base

async def go():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(go())
print("DB tables created successfully.")
