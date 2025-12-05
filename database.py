from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base # Import the declarative Base class from models.py

# This is the connection URL for the database.
# "sqlite:///./sql_app.db" specifies that SQLite is used, and the database file 
# (sql_app.db) will be located in the current directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# The engine is the main entry point to the database, responsible for managing connections.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # check_same_thread=False is required only for SQLite; it allows multiple threads
    # to interact with the database, which is common in web frameworks like FastAPI.
    connect_args={"check_same_thread": False}
)

# SessionLocal is a configured class used to create a database session (the 'conversation' 
# with the database).
SessionLocal = sessionmaker(
    autocommit=False, # We commit transactions explicitly (db.commit()).
    autoflush=False,  # Don't auto-flush data to the database until needed.
    bind=engine       # Binds the session to the created database engine.
)

# Function used by FastAPI's Dependency Injection system.
# It ensures that a new, independent database session is created for each API request.
def get_db():
    db = SessionLocal() # Create a new session.
    try:
        yield db # Provide the session to the calling endpoint function.
    finally:
        db.close() # Close the session after the request is finished (whether successful or failed).