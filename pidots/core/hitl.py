"""
Gerenciador de Governança e Human-in-the-Loop (HITL) para o piDots.
Aplica política Deny-by-Default em ações potencialmente destrutivas.
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Any
from ..storage.db import get_db

logger = logging.getLogger("pidots.hitl")

# Comandos shell que exigem aprovação obrigatória do operador
DANGEROUS_COMMAND_PATTERNS = [
    r"\brm\s+-[rf]+",            # remoção recursiva forçada
    r"\bmkfs\b",                 # formatação de disco
    r"\bdd\s+if=",               # sobrescrita de blocos
    r"\bchmod\s+[0-7]{3,4}\b",   # alteração arbitrária de permissão
    r"\bchown\b",                # mudança de proprietário
    r"\bsudo\b",                 # privilégios de superusuário
    r"\bcurl\b.*\|\s*bash",      # execução direta de script da internet
    r"\bwget\b.*\|\s*bash",
    r"\bkillall\b",              # finalização de processos do sistema
    r"\bshutdown\b|\breboot\b",  # desligamento da máquina
]


class HITLManager:
    """Gerencia a máquina de estados de aprovações humanas."""

    @staticmethod
    def requires_approval(action_type: str, payload: str) -> tuple[bool, str]:
        """
        Verifica se a ação pretendida requer aprovação do operador humano.
        Retorna (necessita_aprovacao, nivel_de_risco).
        """
        if action_type in ("file_delete", "skill_create"):
            return True, "HIGH"

        if action_type in ("shell_exec", "execute_shell_command"):
            cmd_text = payload
            try:
                data = json.loads(payload)
                if isinstance(data, dict) and "command" in data:
                    cmd_text = data["command"]
            except Exception:
                pass

            for pattern in DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, cmd_text, re.IGNORECASE):
                    return True, "CRITICAL"
            # Comandos com escrita ou redirecionamento fora de controle
            if any(token in cmd_text for token in [">", ">>", "tee"]):
                return True, "MEDIUM"

        return False, "LOW"

    @staticmethod
    async def create_approval_request(
        dot_id: str,
        thread_id: str | None,
        action_type: str,
        payload: str,
        risk_level: str = "HIGH"
    ) -> str:
        """Cria e persiste uma solicitação de aprovação pendente no SQLite."""
        approval_id = str(uuid.uuid4())
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO hitl_approvals (id, dot_id, thread_id, action_type, payload, risk_level, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
                """,
                (approval_id, dot_id, thread_id, action_type, payload, risk_level)
            )
            await db.commit()
        logger.info("Solicitação HITL criada [%s] para Dot %s: %s (%s)", approval_id, dot_id, action_type, risk_level)

        # Dispara notificação não-bloqueante para canais remotos (Webhook / Telegram)
        try:
            from .notifier import HITLNotifier
            import asyncio
            asyncio.create_task(
                HITLNotifier.notify_approval_requested(
                    approval_id=approval_id,
                    dot_id=dot_id,
                    action_type=action_type,
                    payload=payload,
                    risk_level=risk_level
                )
            )
        except Exception as e:
            logger.debug("Falha ao agendar tarefa de notificação HITL: %s", e)

        return approval_id

    @staticmethod
    async def resolve_approval(approval_id: str, approved: bool, notes: str | None = None) -> bool:
        """Resolve uma solicitação HITL, aprovando-a ou rejeitando-a."""
        new_status = "APPROVED" if approved else "REJECTED"
        now = datetime.now(timezone.utc).isoformat()
        async with get_db() as db:
            cursor = await db.execute(
                """
                UPDATE hitl_approvals
                SET status = ?, reviewer_notes = ?, resolved_at = ?
                WHERE id = ? AND status = 'PENDING'
                """,
                (new_status, notes, now, approval_id)
            )
            await db.commit()
            return cursor.rowcount > 0
