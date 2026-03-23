from sqlmodel import SQLModel, create_engine, Field, Session, select
from typing import Optional, List
import datetime
import os

# Database configurations
DB_FILE = "antigravity.db"
sqlite_url = f"sqlite:///{DB_FILE}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    repo_url: str
    status: str = "pending"  # pending, cloning, analyzing, completed, failed
    coverage: str = "0%"
    test_code: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
