"""
Gerenciador de Governança e Human-in-the-Loop (HITL) para o piDots.
Aplica política Deny-by-Default em ações potencialmente destrutivas.
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
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
        risk_level: str = "HIGH",
        ttl_minutes: int = 30
    ) -> str:
        """Cria e persiste uma solicitação de aprovação pendente no SQLite com TTL configurável."""
        approval_id = str(uuid.uuid4())
        now_dt = datetime.now(timezone.utc)
        expires_dt = now_dt + timedelta(minutes=ttl_minutes)
        expires_at = expires_dt.isoformat()

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
                INSERT INTO hitl_approvals (id, dot_id, thread_id, action_type, payload, risk_level, status, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (approval_id, dot_id, thread_id, action_type, payload, risk_level, expires_at)
            )
            await db.commit()
        logger.info("Solicitação HITL criada [%s] para Dot %s: %s (%s, Expira em: %s)", approval_id, dot_id, action_type, risk_level, expires_at)

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

    @classmethod
    async def expire_stale_approvals(cls) -> list[str]:
        """
        Varre solicitações pendentes cujo expires_at já foi ultrapassado (TTL de 30 min).
        Atualiza o status para 'EXPIRED', libera threads associadas e grava histórico de auditoria.
        Retorna lista com IDs das aprovações expiradas.
        """
        now = datetime.now(timezone.utc).isoformat()
        expired_ids: list[str] = []
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id, dot_id, thread_id, action_type
                FROM hitl_approvals
                WHERE status = 'PENDING' AND expires_at IS NOT NULL AND expires_at <= ?
                """,
                (now,)
            )
            rows = await cursor.fetchall()
            if not rows:
                return []

            for row in rows:
                app_id = row["id"]
                t_id = row["thread_id"]
                d_id = row["dot_id"]
                act_type = row["action_type"]

                await db.execute(
                    """
                    UPDATE hitl_approvals
                    SET status = 'EXPIRED', reviewer_notes = 'Expirado por inatividade (> 30 minutos) pelo guardiao HITL.', resolved_at = ?
                    WHERE id = ? AND status = 'PENDING'
                    """,
                    (now, app_id)
                )

                if t_id:
                    expire_notice = (
                        f"[GOVERNANCA HITL // ACAO EXPIRADA]\n"
                        f"A solicitacao '{app_id}' para '{act_type}' expirou por inatividade (> 30 minutos). "
                        "A execucao foi cancelada e os recursos de processamento foram liberados."
                    )
                    await db.execute(
                        """
                        INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                        VALUES (?, ?, 'system', ?, ?, 'system', 'public')
                        """,
                        (str(uuid.uuid4()), t_id, expire_notice, d_id)
                    )
                    await db.execute(
                        "UPDATE threads SET status = 'idle', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (t_id,)
                    )
                expired_ids.append(app_id)

            await db.commit()

        if expired_ids:
            logger.info("Guardiao HITL expirou %d solicitacoes pendentes: %s", len(expired_ids), expired_ids)
        return expired_ids

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

    @staticmethod
    async def execute_approved_action(approval_id: str, modified_args: dict | str | None = None) -> dict:
        """
        Executa no sandbox isolado do Dot a ferramenta cujos argumentos foram congelados
        e homologados em uma solicitação HITL com status 'APPROVED' (aplicando modified_args se editado pelo operador).
        Registra o recibo de saída na thread associada e em tool_runs.
        """
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, dot_id, thread_id, action_type, payload, status FROM hitl_approvals WHERE id = ?",
                (approval_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return {"executed": False, "error": "Solicitação HITL não encontrada."}
            if row["status"] != "APPROVED":
                return {"executed": False, "error": f"Ação não está aprovada (status atual: {row['status']})."}

            dot_id = row["dot_id"]
            thread_id = row["thread_id"]
            action_type = row["action_type"]
            raw_payload = row["payload"] or "{}"

        try:
            args = json.loads(raw_payload)
            if not isinstance(args, dict):
                args = {"command": str(raw_payload)}
        except Exception:
            args = {"command": str(raw_payload)}

        # Mapeia alias legado shell_exec para execute_shell_command e desempacota envelope {"tool": ..., "arguments": {...}}
        tool_name = "execute_shell_command" if action_type == "shell_exec" else action_type
        if isinstance(args.get("arguments"), dict):
            if isinstance(args.get("tool"), str) and args["tool"].strip():
                tool_name = args["tool"].strip()
            args = args["arguments"]

        # Se o operador humano editou argumentos via modified_args (Padrão CopilotKit Interrupt-Resume), aplica override
        if modified_args is not None:
            if isinstance(modified_args, dict):
                if isinstance(modified_args.get("arguments"), dict):
                    args = modified_args["arguments"]
                else:
                    args = modified_args
            elif isinstance(modified_args, str) and modified_args.strip():
                try:
                    parsed_mod = json.loads(modified_args)
                    if isinstance(parsed_mod, dict):
                        args = parsed_mod.get("arguments") if isinstance(parsed_mod.get("arguments"), dict) else parsed_mod
                    else:
                        args = {"command": modified_args.strip()}
                except Exception:
                    args = {"command": modified_args.strip()}

        from ..tools.registry import registry as default_tool_registry
        if tool_name not in default_tool_registry._handlers:
            return {
                "executed": False,
                "status": "unsupported_tool",
                "tool_name": tool_name,
                "error": f"Ferramenta '{tool_name}' não possui executor automático registrado."
            }

        t_start = datetime.now(timezone.utc)
        result = await default_tool_registry.execute_tool(
            name=tool_name,
            arguments=args,
            dot_id=dot_id,
            thread_id=thread_id
        )
        duration_ms = int((datetime.now(timezone.utc) - t_start).total_seconds() * 1000)

        # Se houver thread associada, persiste o recibo de execução pós-HITL
        if thread_id:
            try:
                out_preview = ""
                if isinstance(result, dict):
                    out_preview = result.get("stdout") or result.get("message") or result.get("error") or json.dumps(result, ensure_ascii=False)
                else:
                    out_preview = str(result)
                receipt_msg = (
                    f"[RECIBO DE EXECUCAO POS-HOMOLOGACAO HITL]\n"
                    f"Ferramenta: {tool_name} | Duracao: {duration_ms}ms\n"
                    f"Resultado: {str(out_preview)[:1200]}"
                )
                async with get_db() as db:
                    cur_th = await db.execute("SELECT id FROM threads WHERE id = ?", (thread_id,))
                    if await cur_th.fetchone():
                        await db.execute(
                            """
                            INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                            VALUES (?, ?, 'system', ?, ?, 'system', 'public')
                            """,
                            (str(uuid.uuid4()), thread_id, receipt_msg, dot_id)
                        )
                        await db.commit()
            except Exception as rec_err:
                logger.debug("Falha ao gravar recibo pós-HITL na thread %s: %s", thread_id, rec_err)

        return {
            "executed": True,
            "status": "executed",
            "approval_id": approval_id,
            "dot_id": dot_id,
            "thread_id": thread_id,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "result": result
        }

