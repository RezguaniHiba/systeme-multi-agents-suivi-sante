# gère le stockage local des données
from __future__ import annotations

import os
import sqlite3
import uuid
import hashlib
import secrets
import base64
import json
import smtplib
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
except Exception:

    pass


DB_PATH = os.getenv("CONVERSATION_DB_PATH", "conversations.db")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return salt, digest


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _make_demo_token(user_id: str) -> str:

    payload = json.dumps({"user_id": user_id, "iat": utc_now()}, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def init_users_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            patient_id    TEXT NOT NULL UNIQUE,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            token_hash  TEXT NOT NULL UNIQUE,
            expires_at  TEXT NOT NULL,
            used_at     TEXT,
            created_at  TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def public_user(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "patient_id": row["patient_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_user(name: str, email: str, password: str) -> dict:
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name:
        raise ValueError("Le nom est obligatoire.")
    if not email or "@" not in email:
        raise ValueError("Email invalide.")
    if not password or len(password) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")

    now = utc_now()
    user_id = str(uuid.uuid4())
    patient_id = f"patient_{user_id[:8]}"
    salt, pwd_hash = _hash_password(password)

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (id, name, email, password_salt, password_hash, patient_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, salt, pwd_hash, patient_id, now, now))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    return {"user": public_user(row), "token": _make_demo_token(user_id)}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    email = (email or "").strip().lower()
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        return None
    _, expected = _hash_password(password or "", row["password_salt"])
    if not secrets.compare_digest(expected, row["password_hash"]):
        return None
    return {"user": public_user(row), "token": _make_demo_token(row["id"])}


def get_user(user_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return public_user(row) if row else None


def get_user_by_email(email: str):
    email = (email or "").strip().lower()
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def _is_development() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() != "production"


def smtp_config_status() -> dict:
    smtp_host = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com").strip()
    smtp_port = os.getenv("BREVO_SMTP_PORT", "587").strip()
    smtp_user = os.getenv("BREVO_SMTP_USER", "").strip()
    smtp_key = os.getenv("BREVO_SMTP_KEY", "").strip()
    from_email = os.getenv("BREVO_FROM_EMAIL", "").strip() or smtp_user
    from_name = os.getenv("BREVO_FROM_NAME", "Multi-Agents Santé").strip()

    missing = []
    if not smtp_host:
        missing.append("BREVO_SMTP_HOST")
    if not smtp_port:
        missing.append("BREVO_SMTP_PORT")
    if not smtp_user:
        missing.append("BREVO_SMTP_USER")
    if not smtp_key:
        missing.append("BREVO_SMTP_KEY")
    if not from_email:
        missing.append("BREVO_FROM_EMAIL")

    return {
        "configured": len(missing) == 0,
        "missing": missing,
        "host": smtp_host,
        "port": smtp_port,
        "user": smtp_user,
        "from_email": from_email,
        "from_name": from_name,
        "key_present": bool(smtp_key),
    }


def _send_brevo_reset_email(to_email: str, to_name: str, reset_link: str, token: str) -> bool:
    cfg = smtp_config_status()
    if not cfg["configured"]:
        print(f"[SMTP] Configuration incomplète : {cfg['missing']}")
        return False

    smtp_host = cfg["host"]
    smtp_port = int(cfg["port"])
    smtp_user = cfg["user"]
    smtp_key = os.getenv("BREVO_SMTP_KEY", "").strip()
    from_email = cfg["from_email"]
    from_name = cfg["from_name"]

    msg = EmailMessage()
    msg["Subject"] = "Réinitialisation de votre mot de passe"
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.set_content(
        f"""Bonjour {to_name},

Vous avez demandé la réinitialisation du mot de passe de votre compte Multi-Agents Santé.

Cliquez sur ce lien pour créer un nouveau mot de passe :
{reset_link}

Code de réinitialisation :
{token}

Ce lien expire automatiquement. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

Cordialement,
Multi-Agents Santé
"""
    )

    try:
        print(f"[SMTP] Envoi email reset via {smtp_host}:{smtp_port} — user={smtp_user} — from={from_email} — to={to_email}")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_key)
            server.send_message(msg)
        print(f"[SMTP] Email de réinitialisation envoyé à {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            "Authentification Brevo refusée. Vérifiez BREVO_SMTP_USER et BREVO_SMTP_KEY "
            "(il faut la clé SMTP Brevo, pas le mot de passe du compte)."
        ) from e
    except smtplib.SMTPRecipientsRefused as e:
        raise RuntimeError("Adresse destinataire refusée par Brevo.") from e
    except smtplib.SMTPSenderRefused as e:
        raise RuntimeError(
            "Expéditeur refusé par Brevo. Vérifiez que BREVO_FROM_EMAIL est un expéditeur validé dans Brevo."
        ) from e
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Erreur SMTP Brevo : {e}") from e
    except OSError as e:
        raise RuntimeError(
            f"Impossible de contacter le serveur SMTP Brevo ({smtp_host}:{smtp_port}) : {e}"
        ) from e


def request_password_reset(email: str) -> dict:
    email = (email or "").strip().lower()
    generic_response = {
        "message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."
    }

    if not email or "@" not in email:
        return generic_response

    row = get_user_by_email(email)
    if not row:

        if _is_development():
            result = dict(generic_response)
            result["email_sent"] = False
            result["debug"] = "Aucun compte trouvé avec cet email en base SQLite."
            return result
        return generic_response

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    minutes = int(os.getenv("AUTH_RESET_TOKEN_MINUTES", "30"))
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=minutes)).isoformat()

    conn = get_connection()
    try:

        conn.execute(
            "UPDATE password_reset_tokens SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
            (utc_now(), row["id"]),
        )
        conn.execute("""
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, used_at, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
        """, (str(uuid.uuid4()), row["id"], token_hash, expires_at, utc_now()))
        conn.commit()
    finally:
        conn.close()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    reset_link = f"{frontend_url}/?reset_token={token}&email={email}"

    email_sent = _send_brevo_reset_email(
        to_email=email,
        to_name=row["name"],
        reset_link=reset_link,
        token=token,
    )

    result = dict(generic_response)
    result["email_sent"] = email_sent
    if not email_sent and _is_development():

        result["reset_token_preview"] = token
        result["reset_link_preview"] = reset_link
        result["smtp_status"] = smtp_config_status()
    return result


def reset_password(email: str, token: str, new_password: str) -> dict:
    email = (email or "").strip().lower()
    token = (token or "").strip()
    if not email or "@" not in email:
        raise ValueError("Email invalide.")
    if not token:
        raise ValueError("Token de réinitialisation obligatoire.")
    if not new_password or len(new_password) < 6:
        raise ValueError("Le nouveau mot de passe doit contenir au moins 6 caractères.")

    row = get_user_by_email(email)
    if not row:
        raise ValueError("Lien de réinitialisation invalide ou expiré.")

    token_hash = _hash_token(token)
    now_iso = utc_now()
    now_dt = datetime.now(timezone.utc)

    conn = get_connection()
    try:
        token_row = conn.execute("""
            SELECT * FROM password_reset_tokens
            WHERE user_id = ? AND token_hash = ? AND used_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
        """, (row["id"], token_hash)).fetchone()

        if not token_row:
            raise ValueError("Lien de réinitialisation invalide ou déjà utilisé.")

        expires_at = datetime.fromisoformat(token_row["expires_at"])
        if expires_at < now_dt:
            raise ValueError("Lien de réinitialisation expiré.")

        salt, pwd_hash = _hash_password(new_password)
        conn.execute("""
            UPDATE users
            SET password_salt = ?, password_hash = ?, updated_at = ?
            WHERE id = ?
        """, (salt, pwd_hash, now_iso, row["id"]))
        conn.execute("""
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE id = ?
        """, (now_iso, token_row["id"]))
        conn.commit()

        fresh = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
    finally:
        conn.close()

    return {
        "message": "Mot de passe réinitialisé avec succès.",
        "user": public_user(fresh),
        "token": _make_demo_token(row["id"]),
    }


init_users_db()
