from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4
from enum import Enum as PyEnum

class UserRole(str, PyEnum):
    COMPLIANCE_OFFICER = "compliance_officer"
    COMPLIANCE_SUPERVISOR = "compliance_supervisor"
    ADMIN = "admin"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    role: UserRole
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)