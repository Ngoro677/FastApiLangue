# Backend French Voice Learning API

API FastAPI asynchrone pour l'application d'apprentissage du français (voix + chat).

## Prérequis

- Python 3.11+
- PostgreSQL
- Clé API [GROQ](https://console.groq.com/)

## Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` en `.env` et renseigner :

- `DATABASE_URL` : PostgreSQL avec pilote async (`postgresql+asyncpg://user:password@host:5432/dbname`)
- `GROQ_API_KEY` : clé API GROQ

## Base de données

Créer la base PostgreSQL, puis lancer l’app : **les tables sont créées automatiquement au démarrage** via `init_db()` (aucune commande de migration à lancer).

## Lancement

Depuis le dossier `backend` :

```bash
uvicorn app.main:app --reload
```

API : http://127.0.0.1:8000  
Docs : http://127.0.0.1:8000/docs

## Endpoints

- `GET /health` — Santé de l'API
- `POST /api/users` — Créer un utilisateur (body: `{"email": "..."}`)
- `POST /api/chat` — Envoyer un message (body: `user_id`, `message`, optionnel `conversation_id`)

## Exemple d'utilisation

1. Créer un utilisateur : `POST /api/users` avec `{"email": "user@example.com"}`
2. Chat (nouvelle conversation) : `POST /api/chat` avec `{"user_id": 1, "message": "Bonjour !"}`
3. Réponse contient `conversation_id` ; pour enchaîner : `POST /api/chat` avec `{"user_id": 1, "conversation_id": 1, "message": "Comment dit-on 'thank you' ?"}`
