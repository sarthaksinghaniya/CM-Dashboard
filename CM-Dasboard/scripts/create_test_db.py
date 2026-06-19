import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user='postgres', password='anubhav2004', host='localhost', database='postgres')
    try:
        await conn.execute("CREATE DATABASE cm_dashboard_test")
        print("Database created successfully.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database already exists.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
