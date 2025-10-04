from database import engine, Base, update_database, SessionLocal

# Create tables
Base.metadata.create_all(bind=engine)

# Populate database
db = SessionLocal()
try:
    update_database(db)
    print("Database populated successfully!")
except Exception as e:
    print(f"Error populating database: {e}")
finally:
    db.close()