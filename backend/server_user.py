# gère les routes utilisateur et les conversations
import argparse
import uuid
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from conversation_db import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversations_by_user,
    get_messages,
    make_title,
    rename_conversation,
)
from user_db import create_user, authenticate_user, get_user, request_password_reset, reset_password, smtp_config_status, _send_brevo_reset_email

app = FastAPI(
    title="Multi-Agents Santé — Cas 1 (Utilisateur)",
    description="Serveur dédié aux questions médicales utilisateur et à l'historique des conversations.",
    version="1.1.0",
)


class RegisterBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=80, example="Aymene Bahbah")
    email: str = Field(..., example="aymene@example.com")
    password: str = Field(..., min_length=6, example="123456")


class LoginBody(BaseModel):
    email: str = Field(..., example="aymene@example.com")
    password: str = Field(..., example="123456")


class ForgotPasswordBody(BaseModel):
    email: str = Field(..., example="aymene@example.com")


class ResetPasswordBody(BaseModel):
    email: str = Field(..., example="aymene@example.com")
    token: str = Field(..., example="token-recu-par-email")
    new_password: str = Field(..., min_length=6, example="nouveau123")


class TestEmailBody(BaseModel):
    email: str = Field(..., example="aymene@example.com")


class UserQuestion(BaseModel):
    question: str = Field(..., example="J'ai des maux de tête fréquents, que faire ?")
    user_id: Optional[str] = Field(default="user_001", example="user_001")
    conversation_id: Optional[str] = Field(default=None, example="b2e51c6c-8f3e-4f1d-9d0c-...")


class RenameConversationBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    user_id: Optional[str] = Field(default="user_001")


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Cas 1 — Réponse utilisateur",
        "port": 8001,
        "routes": {
            "POST /ask": "question médicale utilisateur",
            "GET /conversations": "liste des conversations",
            "GET /conversations/{id}/messages": "messages d'une conversation",
        },
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "user"}


@app.post("/auth/register", tags=["Authentification"])
def register(body: RegisterBody):
    try:
        return create_user(body.name, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email.")


@app.post("/auth/login", tags=["Authentification"])
def login(body: LoginBody):
    result = authenticate_user(body.email, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return result


@app.post("/auth/forgot-password", tags=["Authentification"])
def forgot_password(body: ForgotPasswordBody):
    try:
        return request_password_reset(body.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impossible d'envoyer l'email de réinitialisation : {str(e)}")


@app.get("/auth/smtp-status", tags=["Authentification"])
def smtp_status():
    return smtp_config_status()


@app.post("/auth/test-email", tags=["Authentification"])
def test_email(body: TestEmailBody):
    try:
        fake_link = "http://localhost:3000"
        ok = _send_brevo_reset_email(
            to_email=body.email,
            to_name="Utilisateur",
            reset_link=fake_link,
            token="TEST-CODE",
        )
        return {"email_sent": ok, "message": "Email de test envoyé." if ok else "SMTP non configuré."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/reset-password", tags=["Authentification"])
def reset_password_route(body: ResetPasswordBody):
    try:
        return reset_password(body.email, body.token, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation : {str(e)}")


@app.get("/auth/me/{user_id}", tags=["Authentification"])
def me(user_id: str):
    user = get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return {"user": user}


@app.post("/ask", tags=["Cas 1 — Utilisateur"])
def ask_question(body: UserQuestion):
    question = body.question.strip()
    user_id = body.user_id or "user_001"

    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    conversation_id = body.conversation_id or str(uuid.uuid4())
    is_new = body.conversation_id is None

    existing = get_conversation(conversation_id, user_id)
    if existing is None:
        create_conversation(conversation_id, user_id, title=make_title(question))
        is_new = True


    add_message(conversation_id, "user", question)

    from crew import run_health_crew

    try:
        response = run_health_crew(question)
    except Exception as e:

        error_msg = f"Erreur pipeline Cas 1 : {str(e)}"
        add_message(conversation_id, "assistant", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    add_message(conversation_id, "assistant", response)

    return {
        "case": 1,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "is_new_conversation": is_new,
        "question": question,
        "response": response,
    }


@app.get("/conversations", tags=["Historique"])
def list_conversations(
    user_id: str = Query(default="user_001"),
    limit: int = Query(default=50, ge=1, le=200),
):
    return {"user_id": user_id, "conversations": get_conversations_by_user(user_id, limit)}


@app.get("/conversations/{conversation_id}/messages", tags=["Historique"])
def conversation_messages(
    conversation_id: str,
    user_id: str = Query(default="user_001"),
    limit: int = Query(default=100, ge=1, le=500),
):
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    return {
        "conversation": conversation,
        "messages": get_messages(conversation_id, user_id, limit),
    }


@app.patch("/conversations/{conversation_id}", tags=["Historique"])
def update_conversation(conversation_id: str, body: RenameConversationBody):
    user_id = body.user_id or "user_001"
    updated = rename_conversation(conversation_id, user_id, body.title)
    if updated is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return updated


@app.delete("/conversations/{conversation_id}", tags=["Historique"])
def remove_conversation(
    conversation_id: str,
    user_id: str = Query(default="user_001"),
):
    deleted = delete_conversation(conversation_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return {"deleted": True, "conversation_id": conversation_id}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur Cas 1 — Questions utilisateur")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--dev", action="store_true", help="Mode reload (développement)")
    args = parser.parse_args()

    print(f"\n👤  Serveur Cas 1 (Utilisateur) — port {args.port}")
    print("=" * 50)
    uvicorn.run(
        "server_user:app",
        host=args.host,
        port=args.port,
        reload=args.dev,
        workers=1,
    )
