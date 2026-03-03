"""Route de chat : envoi de message (texte ou voix), historique, GROQ, persistance."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Conversation, Message, MessageRole
from app.schemas import ChatRequest, ChatResponse, MessageResponse, ConversationResponse
from app.services.groq_service import GroqService, GroqServiceError
from app.services.speech_service import SpeechService, SpeechServiceError

router = APIRouter()


def get_groq_service() -> GroqService:
    """Injection de dépendance pour le service GROQ."""
    return GroqService()


def get_speech_service() -> SpeechService:
    """Injection de dépendance pour la transcription audio."""
    return SpeechService()


async def _process_chat(
    db: AsyncSession,
    groq: GroqService,
    user_id: int,
    conversation_id: int | None,
    message: str,
    target_language: str = "fr",
) -> ChatResponse:
    """Logique partagée : récupère/crée conversation, appelle GROQ, persiste, retourne réponse."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if conversation_id:
        conv_result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        await db.flush()

    # Charger explicitement les messages (pas de lazy-load avec AsyncSession)
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    messages = list(msg_result.scalars().all())

    history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]
    history.append({"role": "user", "content": message})

    try:
        assistant_content = await groq.chat(history, target_language=target_language)
    except GroqServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=message,
    )
    db.add(user_message)
    await db.flush()

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=assistant_content,
    )
    db.add(assistant_message)
    await db.flush()

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        role="assistant",
        content=assistant_content,
        created_at=assistant_message.created_at,
    )


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    groq: GroqService = Depends(get_groq_service),
) -> ChatResponse:
    """
    1. Reçoit le message utilisateur (texte).
    2. Récupère ou crée la conversation et l'historique.
    3. Envoie la conversation complète à GROQ.
    4. Enregistre le message utilisateur et la réponse IA.
    5. Retourne la réponse IA.
    """
    return await _process_chat(
        db,
        groq,
        body.user_id,
        body.conversation_id,
        body.message,
        body.target_language,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retourne les messages d'une conversation (vérifie user_id)."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return [MessageResponse.model_validate(m) for m in msg_result.scalars().all()]


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Liste les conversations d'un utilisateur (ordre antéchronologique)."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = list(result.scalars().all())
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("/voice", response_model=ChatResponse)
async def chat_voice(
    user_id: int = Form(..., gt=0),
    conversation_id: int | None = Form(None, gt=0),
    target_language: str = Form("fr"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    groq: GroqService = Depends(get_groq_service),
    speech: SpeechService = Depends(get_speech_service),
) -> ChatResponse:
    """
    Reçoit un fichier audio, le transcrit (Whisper), puis exécute le même flux de chat.
    """
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an audio type (e.g. audio/mpeg, audio/m4a, audio/wav)",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file")
    if target_language not in ("fr", "en"):
        raise HTTPException(status_code=400, detail="Invalid target_language")
    try:
        text = await speech.transcribe(content, filename=file.filename or "audio.m4a")
    except SpeechServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = await _process_chat(db, groq, user_id, conversation_id, text, target_language)
    data = result.model_dump()
    data["transcribed_text"] = text
    return ChatResponse(**data)
