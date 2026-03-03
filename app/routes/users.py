"""Route utilisateurs : création pour pouvoir utiliser le chat."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter()


@router.post("", response_model=UserResponse)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Crée un utilisateur (email unique)."""
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)
