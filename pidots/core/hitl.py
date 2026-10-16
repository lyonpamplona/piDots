"""
Gerenciador de Governança e Human-in-the-Loop (HITL) para o piDots.
Aplica política Deny-by-Default em ações potencialmente destrutivas.
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone
from ..config import settings
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

        if action_type in ("shell_exec", "execute_shell_command", "execute_and_verify"):
            cmd_text = payload
            try:
                data = json.loads(payload)
                if isinstance(data, dict) and "command" in data:
                    cmd_text = data["command"]
            except Exception as parse_err:
                logger.debug("Payload não é JSON ou falhou ao extrair campo command: %s", parse_err)

            for pattern in DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, cmd_text, re.IGNORECASE):
                    return True, "CRITICAL"
            # Remove redirecionamentos inofensivos (/dev/null, 2>&1) e setas (->, =>) antes de verificar redirecionamento de arquivo
            sanitized_cmd = re.sub(r"(?:[12]?>|&>)\s*/dev/null|2>&1|->|=>", "", cmd_text)
            if re.search(r"(?:>>|>|\|\s*tee\b)", sanitized_cmd):
                return True, "MEDIUM"

        return False, "LOW"

    @staticmethod
    async def has_prior_approval(
        dot_id: str,
        thread_id: str | None,
        action_type: str,
        payload: str
    ) -> bool:
        """Verifica se a mesma ação já foi homologada pelo operador humano para este Dot/Thread."""
        async with get_db() as db:
            if thread_id:
                cursor = await db.execute(
                    """
                    SELECT id FROM hitl_approvals
                    WHERE dot_id = ? AND thread_id = ? AND action_type = ? AND payload = ? AND status = 'APPROVED'
                    LIMIT 1
                    """,
                    (dot_id, thread_id, action_type, payload)
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT id FROM hitl_approvals
                    WHERE dot_id = ? AND action_type = ? AND payload = ? AND status = 'APPROVED'
                    LIMIT 1
                    """,
                    (dot_id, action_type, payload)
                )
            row = await cursor.fetchone()
            return row is not None

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
                INSERT OR IGNORE INTO dots (
                    id, name, role, system_prompt, model, workspace_path
                ) VALUES (?, ?, 'AI Coworker', 'Assistente técnico.', ?, ?)
                """,
                (dot_id, dot_id, settings.ai_model, f"{settings.workspaces_root}/{dot_id}")
            )
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
        """Resolve uma solicitação HITL, aprovando-a ou rejeitando-a, e registra o evento na thread."""
        new_status = "APPROVED" if approved else "REJECTED"
        now = datetime.now(timezone.utc).isoformat()
        async with get_db() as db:
            cur_info = await db.execute(
                "SELECT dot_id, thread_id, action_type, payload FROM hitl_approvals WHERE id = ? AND status = 'PENDING'",
                (approval_id,)
            )
            approval_row = await cur_info.fetchone()
            if not approval_row:
                return False

            cursor = await db.execute(
                """
                UPDATE hitl_approvals
                SET status = ?, reviewer_notes = ?, resolved_at = ?
                WHERE id = ? AND status = 'PENDING'
                """,
                (new_status, notes, now, approval_id)
            )
            updated = cursor.rowcount > 0

            # Se houver thread_id vinculada, registra aviso de resolução para continuidade do agente
            t_id = approval_row["thread_id"]
            d_id = approval_row["dot_id"]
            act_type = approval_row["action_type"]
            if updated and t_id:
                cur_th = await db.execute("SELECT id FROM threads WHERE id = ?", (t_id,))
                if await cur_th.fetchone():
                    verdict_label = "HOMOLOGADA (APPROVED)" if approved else "REJEITADA (REJECTED)"
                    note_txt = f" Notas: {notes}" if notes else ""
                    resolution_msg = (
                        f"[GOVERNANCA HITL // ACAO {verdict_label}]\n"
                        f"Solicitacao '{approval_id}' para '{act_type}' foi resolvida pelo operador humano.{note_txt}"
                    )
                    await db.execute(
                        """
                        INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                        VALUES (?, ?, 'system', ?, ?, 'system', 'public')
                        """,
                        (str(uuid.uuid4()), t_id, resolution_msg, d_id)
                    )
                    await db.execute(
                        "UPDATE threads SET status = 'idle', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (t_id,)
                    )

            await db.commit()
            return updated
