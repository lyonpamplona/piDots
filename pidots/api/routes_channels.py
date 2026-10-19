"""
Rotas REST para Gerenciamento de Canais e Salas Temáticas Colaborativas do piDots.
"""

import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..storage.db import get_db
from ..core.messaging_gateway import ChannelOrchestrator
from .deps import get_ai_provider

router = APIRouter(tags=["Channels"])


class CreateChannelPayload(BaseModel):
    name: str
    description: str | None = None


class PostChannelMessagePayload(BaseModel):
    author_type: str = "user"  # 'user', 'dot', 'webhook'
    author_id: str
    content: str


class AddChannelMemberPayload(BaseModel):
    member_type: str = "dot"  # 'dot', 'user'
    member_id: str


@router.get("/api/channels")
async def list_channels():
    """Lista todas as salas temáticas colaborativas com contagem de mensagens."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT c.id, c.name, c.description, c.created_at,
                   COUNT(m.id) as message_count
            FROM channels c
            LEFT JOIN channel_messages m ON m.channel_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/api/channels")
async def create_channel(payload: CreateChannelPayload):
    """Cria uma nova sala temática de equipe no SQLite WAL."""
    channel_id = re.sub(r"[^a-z0-9_\-]", "", payload.name.lower().strip().replace(" ", "-"))
    if not channel_id:
        raise HTTPException(status_code=400, detail="Nome de canal inválido.")
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO channels (id, name, description) VALUES (?, ?, ?)",
                (channel_id, payload.name.strip(), payload.description)
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Canal já existe ou dados inválidos: {e}")

    return {"id": channel_id, "name": payload.name.strip(), "description": payload.description}


@router.get("/api/channels/{channel_id}/messages")
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Retorna as mensagens recentes de uma sala temática."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, channel_id, author_type, author_id, content, hop_count, created_at
            FROM channel_messages
            WHERE channel_id = ?
            ORDER BY created_at ASC, rowid ASC
            LIMIT ?
            """,
            (channel_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/api/channels/{channel_id}/messages")
async def post_channel_message(channel_id: str, payload: PostChannelMessagePayload, request: Request):
    """Envia uma mensagem para a sala temática e dispara a orquestração autônoma."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Canal não encontrado.")

    ai_provider = get_ai_provider(request)
    msg_id = await ChannelOrchestrator.post_message_to_channel(
        channel_id=channel_id,
        author_type=payload.author_type,
        author_id=payload.author_id,
        content=payload.content,
        hop_count=0,
        ai_provider=ai_provider
    )
    return {"status": "dispatched", "message_id": msg_id, "channel_id": channel_id}


@router.post("/api/channels/{channel_id}/members")
async def add_channel_member(channel_id: str, payload: AddChannelMemberPayload):
    """Adiciona um membro (Dot ou Usuário) à sala temática."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Canal não encontrado.")

        await db.execute(
            """
            INSERT OR REPLACE INTO channel_members (channel_id, member_type, member_id)
            VALUES (?, ?, ?)
            """,
            (channel_id, payload.member_type, payload.member_id)
        )
        await db.commit()
    return {"status": "success", "channel_id": channel_id, "member_id": payload.member_id}
