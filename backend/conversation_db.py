# gère le stockage local des données

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.getenv("CONVERSATION_DB_PATH", "conversations.db")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content         TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def make_title(question: str, max_len: int = 48) -> str:
    title = " ".join((question or "").strip().split())
    if not title:
        return "Nouvelle conversation"
    return title[: max_len - 1].rstrip() + "…" if len(title) > max_len else title


def create_conversation(conversation_id: str, user_id: str, title: Optional[str] = None) -> dict:
    now = utc_now()
    final_title = title or "Nouvelle conversation"
    conn = get_connection()
    conn.execute("""
        INSERT INTO conversations (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (conversation_id, user_id, final_title, now, now))
    conn.commit()
    conn.close()
    return {"id": conversation_id, "user_id": user_id, "title": final_title, "created_at": now, "updated_at": now}


def ensure_conversation(conversation_id: str, user_id: str, title: Optional[str] = None) -> dict:
    existing = get_conversation(conversation_id, user_id)
    if existing:
        return existing
    return create_conversation(conversation_id, user_id, title=title)


def get_conversation(conversation_id: str, user_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("""
        SELECT id, user_id, title, created_at, updated_at
        FROM conversations
        WHERE id = ? AND user_id = ?
    """, (conversation_id, user_id)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_conversations_by_user(user_id: str, limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, user_id, title, created_at, updated_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_message(conversation_id: str, role: str, content: str) -> dict:
    timestamp = utc_now()
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO conversation_messages (conversation_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (conversation_id, role, content, timestamp))
    conn.execute("""
        UPDATE conversations SET updated_at = ? WHERE id = ?
    """, (timestamp, conversation_id))
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return {"id": message_id, "role": role, "content": content, "timestamp": timestamp}


def get_messages(conversation_id: str, user_id: str, limit: int = 100) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.id, m.role, m.content, m.timestamp
        FROM conversation_messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.conversation_id = ? AND c.user_id = ?
        ORDER BY m.id ASC
        LIMIT ?
    """, (conversation_id, user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rename_conversation(conversation_id: str, user_id: str, title: str) -> Optional[dict]:
    now = utc_now()
    conn = get_connection()
    cursor = conn.execute("""
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (title.strip() or "Nouvelle conversation", now, conversation_id, user_id))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return None
    return get_conversation(conversation_id, user_id)


def delete_conversation(conversation_id: str, user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


init_db()
