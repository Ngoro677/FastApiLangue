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
    """Crée un utilisateur ou retourne l'existant si l'email est déjà enregistré (get-or-create)."""
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        return UserResponse.model_validate(existing)
    user = User(email=body.email)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)
