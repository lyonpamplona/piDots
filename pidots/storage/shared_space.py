"""
Módulo de Espaço de Conhecimento Compartilhado entre Bots (Shared Knowledge Space) para piDots.
Inspirado em padrões OpenDots, permite que múltiplos Dots compartilhem notas técnicas,
descobertas e dados estruturados na mesma thread com persistência atômica no SQLite WAL.
"""

import uuid
import re
import logging
from typing import Any

from .db import get_db

logger = logging.getLogger("pidots.shared_space")


class SharedSpaceManager:
    """Gerencia notas e quadro de conhecimento compartilhado entre bots."""

    @classmethod
    async def write_note(
        cls,
        thread_id: str,
        dot_id: str,
        topic_key: str,
        content: str
    ) -> dict[str, Any]:
        """
        Escreve ou atualiza atomicamente uma nota compartilhada para a thread.
        Se o tópico já existir, atualiza o conteúdo e o autor.
        """
        clean_key = re.sub(r"[^\w\-_.]", "_", topic_key.strip().lower())
        if not clean_key:
            return {"success": False, "error": "Chave de tópico inválida ou vazia."}
        if not content.strip():
            return {"success": False, "error": "Conteúdo da nota compartilhada não pode ser vazio."}

        note_id = str(uuid.uuid4())
        async with get_db() as db:
            # Garante que o Dot e a Thread existam de forma idempotente para cumprir FK
            await db.execute(
                """
                INSERT OR IGNORE INTO dots (
                    id, name, role, system_prompt, model, workspace_path
                ) VALUES (?, ?, 'AI Coworker', 'Assistente técnico.', 'qwen3.8-27b', ?)
                """,
                (dot_id, dot_id, f"workspaces/{dot_id}")
            )
            await db.execute(
                """
                INSERT OR IGNORE INTO threads (id, dot_id, title, status)
                VALUES (?, ?, ?, 'idle')
                """,
                (thread_id, dot_id, f"Thread {thread_id[:16]}")
            )

            await db.execute(
                """
                INSERT INTO thread_shared_notes (id, thread_id, dot_id, topic_key, content, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(thread_id, topic_key) DO UPDATE SET
                    dot_id = excluded.dot_id,
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (note_id, thread_id, dot_id, clean_key, content.strip())
            )
            await db.commit()

        logger.info("Nota compartilhada gravada na thread '%s' por @%s: tópico '%s' (%d chars).", thread_id, dot_id, clean_key, len(content))
        return {
            "success": True,
            "thread_id": thread_id,
            "dot_id": dot_id,
            "topic_key": clean_key,
            "content_length": len(content.strip())
        }

    @classmethod
    async def read_note(
        cls,
        thread_id: str,
        topic_key: str
    ) -> dict[str, Any]:
        """Lê o conteúdo de uma nota compartilhada específica na thread."""
        clean_key = re.sub(r"[^\w\-_.]", "_", topic_key.strip().lower())
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM thread_shared_notes WHERE thread_id = ? AND topic_key = ?",
                (thread_id, clean_key)
            )
            row = await cursor.fetchone()

        if not row:
            return {
                "found": False,
                "error": f"Nenhuma nota compartilhada encontrada para o tópico '{clean_key}' nesta thread."
            }

        return {
            "found": True,
            "id": row["id"],
            "thread_id": row["thread_id"],
            "author_dot_id": row["dot_id"],
            "topic_key": row["topic_key"],
            "content": row["content"],
            "updated_at": row["updated_at"]
        }

    @classmethod
    async def list_notes(
        cls,
        thread_id: str
    ) -> list[dict[str, Any]]:
        """Lista todos os tópicos disponíveis no espaço compartilhado da thread."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, dot_id, topic_key, content, updated_at FROM thread_shared_notes WHERE thread_id = ? ORDER BY updated_at DESC",
                (thread_id,)
            )
            rows = await cursor.fetchall()

        return [
            {
                "id": r["id"],
                "author_dot_id": r["dot_id"],
                "topic_key": r["topic_key"],
                "preview": r["content"][:120] + ("..." if len(r["content"]) > 120 else ""),
                "updated_at": r["updated_at"]
            }
            for r in rows
        ]

    @classmethod
    async def format_shared_space_prompt(
        cls,
        thread_id: str | None
    ) -> str:
        """
        Formata as notas compartilhadas da thread em tags XML estruturadas para injeção in-context.
        """
        if not thread_id:
            return ""

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT dot_id, topic_key, content, updated_at FROM thread_shared_notes WHERE thread_id = ? ORDER BY updated_at ASC LIMIT 10",
                (thread_id,)
            )
            rows = await cursor.fetchall()

        if not rows:
            return ""

        lines = [
            "<shared_knowledge_space>",
            "  <description>Notas técnicas e descobertas compartilhadas entre múltiplos Dots nesta thread:</description>"
        ]
        for r in rows:
            lines.append(f"  <topic key=\"{r['topic_key']}\" author=\"@{r['dot_id']}\" updated_at=\"{r['updated_at']}\">")
            lines.append(f"    {r['content']}")
            lines.append("  </topic>")
        lines.append("</shared_knowledge_space>")

        return "\n".join(lines)
