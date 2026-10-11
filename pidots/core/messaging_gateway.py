"""
Gateway de Mensageria Unificada e Barramento de Canais Temáticos para piDots.
Recebe webhooks de Telegram, WhatsApp (Evolution API), Discord e Slack,
e orquestra salas temáticas colaborativas com prevenção de loops infinitos.
"""

import asyncio
import hmac
import hashlib
import json
import logging
import uuid
from typing import Any
from datetime import datetime, timezone
from pydantic import BaseModel
import httpx

from ..config import settings
from ..storage.db import get_db
from .agent import DotAgent
from ..providers.openai_client import OpenAIUniversalProvider

logger = logging.getLogger("pidots.messaging")


class UnifiedIncomingMessage(BaseModel):
    """Modelo canônico unificado para mensagens recebidas de qualquer plataforma."""
    platform: str
    sender_id: str
    sender_name: str
    text: str
    reply_target_id: str
    channel_id: str | None = None


class MessagingGateway:
    """Núcleo de recepção, normalização e despacho de mensagens externas."""

    @classmethod
    async def get_or_create_external_thread(
        cls,
        dot_id: str,
        platform: str,
        sender_id: str,
        sender_name: str
    ) -> str:
        """Localiza ou cria uma thread persistente para a conversa externa no SQLite WAL."""
        thread_title = f"{platform.capitalize()}: {sender_name} ({sender_id})"
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id FROM threads 
                WHERE dot_id = ? AND title = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (dot_id, thread_title)
            )
            row = await cursor.fetchone()
            if row:
                return row["id"]

            new_thread_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'idle')",
                (new_thread_id, dot_id, thread_title)
            )
            await db.commit()
            return new_thread_id

    @classmethod
    async def process_and_respond(
        cls,
        dot_id: str,
        msg: UnifiedIncomingMessage,
        ai_provider: OpenAIUniversalProvider,
        http_client: httpx.AsyncClient | None = None
    ) -> str:
        """Processa a mensagem pelo loop do Dot e despacha a resposta de volta ao canal."""
        thread_id = await cls.get_or_create_external_thread(
            dot_id=dot_id,
            platform=msg.platform,
            sender_id=msg.sender_id,
            sender_name=msg.sender_name
        )

        agent = DotAgent(dot_id=dot_id, provider=ai_provider)
        final_response_text = ""

        async for event in agent.run_thread(thread_id=thread_id, user_message=msg.text):
            if event["event"] == "run:finished":
                final_response_text = event.get("data", {}).get("final_response", "")

        if not final_response_text:
            final_response_text = "Comando recebido e processado com sucesso pelo agente."

        # Despacho da resposta de volta
        await cls.dispatch_outgoing_message(
            channel_type=msg.platform,
            target_id=msg.reply_target_id,
            text=final_response_text,
            http_client=http_client
        )

        return final_response_text

    @classmethod
    async def dispatch_outgoing_message(
        cls,
        channel_type: str,
        target_id: str,
        text: str,
        http_client: httpx.AsyncClient | None = None
    ) -> bool:
        """Despacha uma mensagem textual para uma plataforma externa específica."""
        client = http_client or httpx.AsyncClient(timeout=10.0)
        should_close = http_client is None

        try:
            if channel_type == "telegram":
                token = settings.telegram_bot_token
                if not token:
                    logger.debug("Tentativa de envio Telegram sem token configurado.")
                    return False
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {"chat_id": target_id, "text": text}
                resp = await client.post(url, json=payload)
                return resp.status_code == 200

            elif channel_type == "whatsapp":
                evo_url = getattr(settings, "evolution_api_url", "http://host.docker.internal:8080")
                evo_token = getattr(settings, "evolution_api_key", "")
                url = f"{evo_url.rstrip('/')}/message/sendText"
                headers = {"apikey": evo_token} if evo_token else {}
                payload = {
                    "number": target_id,
                    "options": {"delay": 1000, "presence": "composing"},
                    "textMessage": {"text": text}
                }
                resp = await client.post(url, json=payload, headers=headers)
                return resp.status_code in (200, 201)

            elif channel_type == "discord":
                if target_id.startswith("https://discord.com/api/webhooks/"):
                    payload = {"content": text}
                    resp = await client.post(target_id, json=payload)
                    return resp.status_code in (200, 204)
                return False

            elif channel_type == "slack":
                if target_id.startswith("https://hooks.slack.com/"):
                    payload = {"text": text}
                    resp = await client.post(target_id, json=payload)
                    return resp.status_code == 200

        except Exception as e:
            logger.error("Erro ao despachar mensagem para %s (%s): %s", channel_type, target_id, str(e))
            return False
        finally:
            if should_close:
                await client.aclose()
        return False


class ChannelOrchestrator:
    """Gerenciador de colaboração e roteamento em salas temáticas (#canais)."""

    MAX_HOPS = 3

    @classmethod
    async def post_message_to_channel(
        cls,
        channel_id: str,
        author_type: str,
        author_id: str,
        content: str,
        hop_count: int,
        ai_provider: OpenAIUniversalProvider
    ) -> str:
        """Grava a mensagem no canal e despacha para os Dots ouvintes com trava anti-recursão."""
        if hop_count > cls.MAX_HOPS:
            logger.warning(
                "Limite de saltos excedido (hop_count=%d) no canal %s. Bloqueando propagação em loop.",
                hop_count, channel_id
            )
            return "Recursion limit reached"

        msg_id = str(uuid.uuid4())
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO channel_messages (id, channel_id, author_type, author_id, content, hop_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, channel_id, author_type, author_id, content, hop_count)
            )
            await db.commit()

        # Identifica os Dots membros do canal
        dots_to_trigger: list[str] = []
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT member_id FROM channel_members WHERE channel_id = ? AND member_type = 'dot'",
                (channel_id,)
            )
            members = await cursor.fetchall()
            dot_ids = [row["member_id"] for row in members]

        # Se não houver tabela de membros preenchida, considera todos os dots ativos
        if not dot_ids:
            async with get_db() as db:
                cursor = await db.execute("SELECT id FROM dots WHERE is_active = 1")
                dot_ids = [row["id"] for row in await cursor.fetchall()]

        # Regras de disparo inteligente
        for d_id in dot_ids:
            if d_id == author_id:
                continue

            if author_type in ("user", "webhook"):
                if f"@{d_id}" in content or "@all" in content or len(dot_ids) == 1:
                    dots_to_trigger.append(d_id)
            elif author_type == "dot":
                # Bot só responde a outro bot se houver menção explícita
                if f"@{d_id}" in content:
                    dots_to_trigger.append(d_id)

        # Dispara os agentes de forma assíncrona desacoplada
        for target_dot in dots_to_trigger:
            asyncio.create_task(
                cls._run_dot_in_channel(
                    channel_id=channel_id,
                    dot_id=target_dot,
                    trigger_msg=content,
                    hop_count=hop_count + 1,
                    ai_provider=ai_provider
                )
            )

        return msg_id

    @classmethod
    async def _run_dot_in_channel(
        cls,
        channel_id: str,
        dot_id: str,
        trigger_msg: str,
        hop_count: int,
        ai_provider: OpenAIUniversalProvider
    ) -> None:
        """Executa o ciclo do Dot no contexto da sala temática."""
        logger.info("Executando Dot '%s' no canal '%s' (Salto %d)", dot_id, channel_id, hop_count)

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT author_type, author_id, content FROM channel_messages
                WHERE channel_id = ?
                ORDER BY created_at DESC LIMIT 8
                """,
                (channel_id,)
            )
            history_rows = await cursor.fetchall()

        history_context = "\n".join(
            [f"[{r['author_type'].upper()} - {r['author_id']}]: {r['content']}" for r in reversed(history_rows)]
        )

        prompt_with_context = (
            f"Você está colaborando na sala temática #{channel_id}.\n"
            f"Histórico recente da conversa:\n{history_context}\n\n"
            f"Mensagem recebida:\n{trigger_msg}\n\n"
            "DIRETRIZES DE RESPOSTA:\n"
            "1. Responda de forma direta e técnica.\n"
            "2. Se você precisar que outro Dot atue na sequência, mencione-o explicitamente no formato @nome_do_dot.\n"
            "3. Se você não tiver nada relevante a acrescentar, responda estritamente 'NO_ACTION'."
        )

        channel_thread_id = f"channel-{channel_id}-{dot_id}"
        async with get_db() as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO threads (id, dot_id, title, status)
                VALUES (?, ?, ?, 'idle')
                """,
                (channel_thread_id, dot_id, f"Canal #{channel_id}")
            )
            await db.commit()

        agent = DotAgent(dot_id=dot_id, provider=ai_provider)
        final_answer = ""

        try:
            async for event in agent.run_thread(thread_id=channel_thread_id, user_message=prompt_with_context):
                if event["event"] == "run:finished":
                    final_answer = event.get("data", {}).get("final_response", "")

            if final_answer and "NO_ACTION" not in final_answer.strip():
                await cls.post_message_to_channel(
                    channel_id=channel_id,
                    author_type="dot",
                    author_id=dot_id,
                    content=final_answer,
                    hop_count=hop_count,
                    ai_provider=ai_provider
                )
        except Exception as e:
            logger.error("Erro no processamento do Dot %s no canal %s: %s", dot_id, channel_id, str(e), exc_info=True)
