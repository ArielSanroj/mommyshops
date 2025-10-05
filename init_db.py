import asyncio
from database import engine, Base, update_database, SessionLocal

# Create tables
Base.metadata.create_all(bind=engine)

# Populate database
async def populate_db():
    db = SessionLocal()
    try:
        await update_database(db)
        print("Database populated successfully!")
    except Exception as e:
        print(f"Error populating database: {e}")
    finally:
        db.close()

# Run the async function
asyncio.run(populate_db())