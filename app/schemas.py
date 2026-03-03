"""Schémas Pydantic pour validation et sérialisation."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


# ----- User -----


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Conversation -----


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----- Message -----


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=16000)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Chat -----


class ChatRequest(BaseModel):
    """Requête du endpoint chat."""

    user_id: int = Field(..., gt=0, description="ID de l'utilisateur")
    conversation_id: int | None = Field(None, gt=0, description="ID de la conversation (optionnel, crée une nouvelle si absent)")
    message: str = Field(..., min_length=1, max_length=16000, description="Message de l'utilisateur")
    target_language: Literal["fr", "en"] = Field(
        "fr", description="Langue dans laquelle l'assistant doit répondre."
    )


class ChatResponse(BaseModel):
    """Réponse du endpoint chat."""

    conversation_id: int
    message_id: int
    role: str = "assistant"
    content: str
    created_at: datetime
    transcribed_text: str | None = None  # Texte transcrit (endpoint voice uniquement)
