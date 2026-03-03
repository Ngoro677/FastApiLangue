"""Service de transcription audio via GROQ (Whisper-compatible)."""

import io
import httpx
from app.config import get_settings


class SpeechServiceError(Exception):
    """Erreur lors de la transcription."""

    pass


class SpeechService:
    """Transcription audio via l'API GROQ (Whisper)."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def transcribe(self, audio_content: bytes, filename: str = "audio.m4a") -> str:
        """
        Transcrit l'audio en texte.

        Args:
            audio_content: Contenu binaire du fichier audio.
            filename: Nom du fichier (extension utilisée pour le format).

        Returns:
            Texte transcrit.

        Raises:
            SpeechServiceError: Si la clé API est absente ou l'API échoue.
        """
        if not self._settings.GROQ_API_KEY:
            raise SpeechServiceError("GROQ_API_KEY is not set")

        file = io.BytesIO(audio_content)
        file.name = filename

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={
                        "Authorization": f"Bearer {self._settings.GROQ_API_KEY}",
                    },
                    files={"file": (filename, file, "audio/m4a")},
                    data={
                        "model": self._settings.GROQ_WHISPER_MODEL,
                        "language": "fr",
                    },
                )
        except Exception as e:
            raise SpeechServiceError(str(e)) from e

        if response.status_code != 200:
            raise SpeechServiceError(
                f"GROQ Whisper API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        text = (data.get("text") or "").strip()
        if not text:
            raise SpeechServiceError("Empty transcription")
        return text
