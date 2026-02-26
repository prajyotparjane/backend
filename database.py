import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get DATABASE_URL from Render environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Safety check (important)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base model class
Base = declarative_base()