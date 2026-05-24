"""
RBAC (Role-Based Access Control) - Phase 3

Provides FastAPI dependencies for role-based access control.
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional
from enum import Enum

class Role(str, Enum):
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


def get_current_role(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> str:
    """
    Extracts the current user's role.
    
    In production, this would come from JWT/session authentication.
    For now, it reads from the X-User-Role header (or defaults to 'officer').
    """
    if x_user_role:
        return x_user_role.lower()
    return "officer"  # Default for development


def require_officer(role: str = Depends(get_current_role)):
    if role not in [Role.OFFICER, Role.SUPERVISOR, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Officer role required")
    return role


def require_supervisor(role: str = Depends(get_current_role)):
    if role not in [Role.SUPERVISOR, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Supervisor role required")
    return role


def require_admin(role: str = Depends(get_current_role)):
    if role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return role
