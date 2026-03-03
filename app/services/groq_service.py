"""Service d'intégration avec l'API GROQ (OpenAI-compatible)."""

import httpx
from app.config import get_settings

SYSTEM_PROMPT_FR = """You are an intelligent and patient French teacher. Your role is to help the user learn and practice French in a supportive way.

Guidelines:
- Always answer in French.
- Adapt your level (vocabulary and speed of explanation) to the user's level.
- Correct mistakes gently and suggest better formulations.
- Encourage conversation and short exercises (questions, fill-in-the-blanks, or simple role-play) when appropriate.
- Be concise but complete; avoid overwhelming the user with too much information at once."""

SYSTEM_PROMPT_EN = """You are an intelligent and patient English teacher. Your role is to help the user learn and practice English in a supportive way.

Guidelines:
- Always answer in English.
- Adapt your level (vocabulary and speed of explanation) to the user's level.
- Correct mistakes gently and suggest better formulations.
- Encourage conversation and short exercises (questions, fill-in-the-blanks, or simple role-play) when appropriate.
- Be concise but complete; avoid overwhelming the user with too much information at once."""


class GroqServiceError(Exception):
    """Erreur lors de l'appel à l'API GROQ."""

    pass


class GroqService:
    """Client pour l'API GROQ (chat completions)."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _get_system_prompt(self, target_language: str) -> str:
        if target_language == "en":
            return SYSTEM_PROMPT_EN
        return SYSTEM_PROMPT_FR

    def _build_messages(
        self, history: list[dict[str, str]], target_language: str = "fr"
    ) -> list[dict[str, str]]:
        """Construit la liste des messages pour l'API (system + history)."""
        messages = [{"role": "system", "content": self._get_system_prompt(target_language)}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        return messages

    async def chat(self, messages: list[dict[str, str]], target_language: str = "fr") -> str:
        """
        Envoie la conversation à GROQ et retourne le contenu de la réponse assistant.

        Args:
            messages: Liste de dicts avec 'role' et 'content' (sans le system, ajouté ici).

        Returns:
            Contenu textuel de la réponse de l'assistant.

        Raises:
            GroqServiceError: Si l'API renvoie une erreur ou réponse invalide.
        """
        if not self._settings.GROQ_API_KEY:
            raise GroqServiceError("GROQ_API_KEY is not set")

        payload = {
            "model": self._settings.GROQ_MODEL,
            "messages": self._build_messages(messages, target_language=target_language),
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._settings.GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self._settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code != 200:
            raise GroqServiceError(
                f"GROQ API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise GroqServiceError("Invalid GROQ response: no choices")

        first = choices[0]
        message = first.get("message")
        if not message or "content" not in message:
            raise GroqServiceError("Invalid GROQ response: no message content")

        return (message.get("content") or "").strip()
