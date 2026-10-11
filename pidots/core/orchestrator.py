"""
Orquestrador de Chat Multi-Bot e Colaboração Inter-Agente para piDots.
Suporta roteamento de menções (@dot), topologias Supervisor-Worker,
Debate Dialético com teto de turnos e Handoffs dinâmicos.
"""

import re
import uuid
import json
import logging
from typing import AsyncGenerator, Any
from datetime import datetime, timezone

from ..storage.db import get_db
from ..providers.openai_client import OpenAIUniversalProvider
from .state import AGUIEvent

logger = logging.getLogger("pidots.orchestrator")


class ThreadRouter:
    """Roteia mensagens e resolve interlocutores em conversas multi-bot."""

    @staticmethod
    def parse_mentions(content: str) -> list[str]:
        """Extrai identificadores de Dots mencionados na mensagem com a sintaxe @nome_do_dot."""
        if not content:
            return []
        matches = re.findall(r"@([a-zA-Z0-9_\-]+)", content)
        # Remove duplicatas preservando a ordem
        seen = set()
        result = []
        for m in matches:
            clean = m.lower()
            if clean not in seen and clean != "all":
                seen.add(clean)
                result.append(clean)
        return result

    @classmethod
    async def resolve_target_dots(cls, thread_id: str, content: str, default_dot_id: str) -> tuple[str, list[str]]:
        """
        Determina o Dot primário que responderá e a lista de Dots citados.
        Se houver menções explícitas, valida no banco SQLite se existem.
        """
        mentions = cls.parse_mentions(content)
        if not mentions:
            return default_dot_id, []

        valid_dots: list[str] = []
        async with get_db() as db:
            for dot_cand in mentions:
                cursor = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_cand,))
                row = await cursor.fetchone()
                if row:
                    valid_dots.append(row["id"])

        if valid_dots:
            # O primeiro dot mencionado torna-se o destinatário primário
            primary = valid_dots[0]
            others = valid_dots[1:]
            return primary, others

        return default_dot_id, []


class MultiBotOrchestrator:
    """Motor de execução de colaboração multi-agente in-process para hardware restrito."""

    @classmethod
    async def record_participant(cls, thread_id: str, dot_id: str) -> None:
        """Registra a participação de um Dot em uma thread se ainda não estiver associado."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO thread_participants (thread_id, dot_id, is_speaker, turn_order)
                VALUES (?, ?, 1, 0)
                """,
                (thread_id, dot_id)
            )
            await db.commit()

    @classmethod
    async def record_message(
        cls,
        thread_id: str,
        actor_id: str,
        actor_type: str,
        content: str,
        role: str = "assistant",
        target_dot_id: str | None = None,
        visibility: str = "public",
        thought_log: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        parent_message_id: str | None = None
    ) -> str:
        """Persiste uma mensagem no SQLite WAL com rastreamento completo de ator e visibilidade."""
        msg_id = str(uuid.uuid4())
        tool_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO messages (
                    id, thread_id, actor_id, actor_type, target_dot_id,
                    visibility, role, content, thought_log, tool_calls_json, parent_message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id, thread_id, actor_id, actor_type, target_dot_id,
                    visibility, role, content, thought_log, tool_json, parent_message_id
                )
            )
            await db.commit()
        return msg_id

    @classmethod
    async def delegate_subtask(
        cls,
        thread_id: str,
        source_dot_id: str,
        target_dot_id: str,
        task_goal: str,
        context_snippet: str | None,
        provider: OpenAIUniversalProvider
    ) -> dict[str, Any]:
        """
        Topologia Supervisor-Worker:
        Executa subtarefa isolada em um Dot especialista sem poluir o histórico público da thread pai.
        Retorna a síntese técnica como resultado da ferramenta.
        """
        logger.info(
            "Delegação inter-agente: [%s] delegou para [%s] na thread %s",
            source_dot_id, target_dot_id, thread_id
        )

        handoff_id = str(uuid.uuid4())
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO agent_handoffs (
                    id, thread_id, source_dot_id, target_dot_id, task_goal,
                    handoff_type, status
                ) VALUES (?, ?, ?, ?, ?, 'delegate_subtask', 'RUNNING')
                """,
                (handoff_id, thread_id, source_dot_id, target_dot_id, task_goal)
            )
            await db.commit()

        # Garante que o worker esteja registrado na thread
        await cls.record_participant(thread_id, target_dot_id)

        # Registra a solicitação como Fita de Carbono (mensagem interna)
        internal_prompt = f"[DELEGAÇÃO DE SUBTAREFA DE @{source_dot_id}]: {task_goal}"
        if context_snippet:
            internal_prompt += f"\n\nContexto Fornecido:\n{context_snippet}"

        await cls.record_message(
            thread_id=thread_id,
            actor_id=source_dot_id,
            actor_type="dot",
            target_dot_id=target_dot_id,
            visibility="internal",
            role="assistant",
            content=internal_prompt
        )

        # Executa o loop do worker em isolamento
        from .agent import DotAgent
        worker_agent = DotAgent(dot_id=target_dot_id, provider=provider)
        worker_response = ""

        # Thread de trabalho isolada para o worker para não interferir no histórico pai
        isolated_thread_id = f"subtask-{handoff_id[:8]}"
        async with get_db() as db:
            await db.execute(
                "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'running')",
                (isolated_thread_id, target_dot_id, f"Subtarefa de {source_dot_id}: {task_goal[:30]}")
            )
            await db.commit()

        try:
            async for event in worker_agent.run_thread(
                thread_id=isolated_thread_id,
                user_message=internal_prompt
            ):
                if event["event"] == "run:finished":
                    # Recupera última mensagem do assistente gerada
                    pass

            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT content FROM messages WHERE thread_id = ? AND role = 'assistant' ORDER BY created_at DESC LIMIT 1",
                    (isolated_thread_id,)
                )
                row = await cursor.fetchone()
                if row:
                    worker_response = row["content"]

            if not worker_response:
                worker_response = "Subtarefa concluída sem saída textual."

            # Atualiza o status do handoff
            async with get_db() as db:
                await db.execute(
                    """
                    UPDATE agent_handoffs
                    SET status = 'COMPLETED',
                        result_summary = ?,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (worker_response[:500], handoff_id)
                )
                await db.commit()

            # Registra o resultado do worker como fita de carbono na thread principal
            await cls.record_message(
                thread_id=thread_id,
                actor_id=target_dot_id,
                actor_type="dot",
                target_dot_id=source_dot_id,
                visibility="internal",
                role="assistant",
                content=f"[RESULTADO DE @{target_dot_id}]:\n{worker_response}"
            )

            return {
                "success": True,
                "worker_dot_id": target_dot_id,
                "handoff_id": handoff_id,
                "output": worker_response
            }

        except Exception as e:
            logger.error("Falha ao executar subtarefa delegada para %s: %s", target_dot_id, str(e), exc_info=True)
            async with get_db() as db:
                await db.execute(
                    "UPDATE agent_handoffs SET status = 'FAILED', result_summary = ? WHERE id = ?",
                    (f"Erro: {str(e)}", handoff_id)
                )
                await db.commit()
            return {"success": False, "error": str(e), "worker_dot_id": target_dot_id}

    @classmethod
    async def handoff_lead(
        cls,
        thread_id: str,
        source_dot_id: str,
        target_dot_id: str,
        reason: str
    ) -> dict[str, Any]:
        """
        Topologia Handoff:
        Transfere a liderança operacional da thread para outro Dot especialista.
        """
        logger.info("Transferência de liderança (Handoff): %s -> %s na thread %s", source_dot_id, target_dot_id, thread_id)
        async with get_db() as db:
            # Atualiza dot_id da thread para o novo líder
            await db.execute(
                "UPDATE threads SET dot_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (target_dot_id, thread_id)
            )
            handoff_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO agent_handoffs (
                    id, thread_id, source_dot_id, target_dot_id, task_goal,
                    handoff_type, status, completed_at
                ) VALUES (?, ?, ?, ?, ?, 'transfer_lead', 'COMPLETED', CURRENT_TIMESTAMP)
                """,
                (handoff_id, thread_id, source_dot_id, target_dot_id, reason)
            )
            await db.commit()

        await cls.record_participant(thread_id, target_dot_id)

        # Registra nota técnica de transferência
        await cls.record_message(
            thread_id=thread_id,
            actor_id=source_dot_id,
            actor_type="dot",
            target_dot_id=target_dot_id,
            visibility="public",
            role="assistant",
            content=f"[TRANSFERÊNCIA DE COMANDO] Liderança transferida para @{target_dot_id}. Motivo: {reason}"
        )

        return {"success": True, "new_lead": target_dot_id, "handoff_id": handoff_id}
