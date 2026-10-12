"""
Módulo de Agendamento Proativo e Heartbeat (Always-On) para piDots.
Executa rotinas de verificação em background in-process com persistência SQLite WAL.
Implementa o padrão Dot Heartbeat com diretriz de silêncio HEARTBEAT_OK.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from croniter import croniter

from ..storage.db import get_db
from ..providers.openai_client import OpenAIUniversalProvider
from .agent import DotAgent

logger = logging.getLogger("pidots.scheduler")


class EdgeScheduler:
    """Gerenciador de tarefas agendadas e rotinas proativas de Dots."""

    _running_tasks: set[str] = set()

    @classmethod
    def is_running(cls, task_id: str) -> bool:
        """Verifica se a tarefa já está em execução no loop atual."""
        return task_id in cls._running_tasks

    @classmethod
    def mark_running(cls, task_id: str) -> None:
        """Marca a tarefa como em execução ativa."""
        cls._running_tasks.add(task_id)

    @classmethod
    def mark_stopped(cls, task_id: str) -> None:
        """Remove a tarefa da lista de ativas em execução."""
        cls._running_tasks.discard(task_id)

    @staticmethod
    def calculate_next_run(cron_expr: str, base_time: datetime | None = None) -> datetime:
        """Calcula a data e hora da próxima execução com base na expressão cron."""
        now = base_time or datetime.now(timezone.utc)
        iterator = croniter(cron_expr, now)
        next_timestamp = iterator.get_next(float)
        return datetime.fromtimestamp(next_timestamp, tz=timezone.utc)

    @classmethod
    async def register_task(
        cls,
        dot_id: str,
        task_name: str,
        cron_expr: str,
        action_prompt: str,
        target_channel_type: str = "internal",
        target_channel_id: str | None = None
    ) -> str:
        """Registra uma nova tarefa cron proativa para um Dot no SQLite WAL."""
        if not croniter.is_valid(cron_expr):
            raise ValueError(f"Expressão cron inválida: '{cron_expr}'")

        task_id = str(uuid.uuid4())
        next_run = cls.calculate_next_run(cron_expr)

        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO scheduled_tasks (
                    id, dot_id, task_name, cron_expr, action_prompt,
                    target_channel_type, target_channel_id, next_run_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    task_id,
                    dot_id,
                    task_name,
                    cron_expr,
                    action_prompt,
                    target_channel_type,
                    target_channel_id,
                    next_run.isoformat()
                )
            )
            await db.commit()

        logger.info(
            "Tarefa proativa agendada: [%s] '%s' para Dot '%s'. Próxima execução: %s",
            task_id, task_name, dot_id, next_run.isoformat()
        )
        return task_id

    @classmethod
    async def get_due_tasks(cls) -> list[dict[str, Any]]:
        """Recupera tarefas ativas cuja data de execução seja devida, respeitando janelas de backoff e exclusão mútua."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id, dot_id, task_name, cron_expr, action_prompt,
                       target_channel_type, target_channel_id, next_run_at,
                       consecutive_failures, backoff_until
                FROM scheduled_tasks
                WHERE is_active = 1
                  AND next_run_at <= ?
                  AND (backoff_until IS NULL OR backoff_until <= ?)
                ORDER BY next_run_at ASC
                """,
                (now_iso, now_iso)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows if row["id"] not in cls._running_tasks]

    @classmethod
    async def mark_task_finished(
        cls,
        task_id: str,
        cron_expr: str,
        status: str,
        summary: str
    ) -> None:
        """Atualiza o resultado da execução, calcula backoff exponencial se houver falhas e recalcula a próxima data de disparo."""
        now = datetime.now(timezone.utc)
        next_run = cls.calculate_next_run(cron_expr, now)

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT consecutive_failures FROM scheduled_tasks WHERE id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            current_failures = (row["consecutive_failures"] or 0) if row else 0

            if status == "FAILED":
                new_failures = current_failures + 1
                # Backoff exponencial: 30s, 60s, 120s, 240s, 480s (máximo 1h)
                backoff_delay = min(3600, 30 * (2 ** (new_failures - 1)))
                backoff_until = (now + timedelta(seconds=backoff_delay)).isoformat()

                if new_failures >= 5:
                    new_status = "CIRCUIT_OPEN"
                    is_active = 0
                    logger.warning(
                        "Circuit breaker ativado para a tarefa proativa '%s'. Desativando após %d falhas consecutivas.",
                        task_id, new_failures
                    )
                else:
                    new_status = status
                    is_active = 1

                await db.execute(
                    """
                    UPDATE scheduled_tasks
                    SET last_run_at = ?,
                        next_run_at = ?,
                        last_status = ?,
                        last_result_summary = ?,
                        consecutive_failures = ?,
                        backoff_until = ?,
                        is_active = ?
                    WHERE id = ?
                    """,
                    (
                        now.isoformat(),
                        next_run.isoformat(),
                        new_status,
                        summary[:500],
                        new_failures,
                        backoff_until,
                        is_active,
                        task_id
                    )
                )
            elif status == "AUTH_REQUIRED":
                # Backoff fixo de 10 minutos para dar tempo ao operador configurar a chave sem poluir o loop
                backoff_until = (now + timedelta(minutes=10)).isoformat()
                await db.execute(
                    """
                    UPDATE scheduled_tasks
                    SET last_run_at = ?,
                        next_run_at = ?,
                        last_status = ?,
                        last_result_summary = ?,
                        backoff_until = ?
                    WHERE id = ?
                    """,
                    (
                        now.isoformat(),
                        next_run.isoformat(),
                        status,
                        summary[:500],
                        backoff_until,
                        task_id
                    )
                )
            else:
                # Sucesso ou silêncio operacional: reseta falhas e zera backoff
                await db.execute(
                    """
                    UPDATE scheduled_tasks
                    SET last_run_at = ?,
                        next_run_at = ?,
                        last_status = ?,
                        last_result_summary = ?,
                        consecutive_failures = 0,
                        backoff_until = NULL
                    WHERE id = ?
                    """,
                    (
                        now.isoformat(),
                        next_run.isoformat(),
                        status,
                        summary[:500],
                        task_id
                    )
                )
            await db.commit()


async def execute_proactive_task(
    task: dict[str, Any],
    ai_provider: OpenAIUniversalProvider
) -> None:
    """Executa um ciclo autônomo individual de uma tarefa proativa agendada com exclusão mútua."""
    task_id = task["id"]
    dot_id = task["dot_id"]
    prompt = task["action_prompt"]
    cron_expr = task["cron_expr"]

    if EdgeScheduler.is_running(task_id):
        logger.debug("Tarefa proativa '%s' já em execução. Ignorando disparo duplicado.", task_id)
        return

    # Sanity check preventivo apenas se for provedor real remoto com chave placeholder
    if isinstance(ai_provider, OpenAIUniversalProvider) and ai_provider.api_key in ("", "sua_chave_aqui", "placeholder"):
        logger.warning(
            "Tarefa proativa '%s' pausada: AI_API_KEY não configurada ou com valor placeholder. Configure sua chave no .env.",
            task["task_name"]
        )
        await EdgeScheduler.mark_task_finished(
            task_id=task_id,
            cron_expr=cron_expr,
            status="AUTH_REQUIRED",
            summary="Pausada preventivamente: AI_API_KEY com valor placeholder ou vazia."
        )
        return

    EdgeScheduler.mark_running(task_id)
    logger.info("Executando tarefa proativa '%s' para Dot '%s'", task["task_name"], dot_id)

    proactive_thread_id = f"heartbeat-{task_id[:8]}"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO threads (id, dot_id, title, status)
            VALUES (?, ?, ?, 'proactive')
            """,
            (proactive_thread_id, dot_id, f"Heartbeat: {task['task_name']}")
        )
        await db.execute(
            "UPDATE scheduled_tasks SET last_status = 'RUNNING' WHERE id = ?",
            (task_id,)
        )
        await db.commit()

    agent = DotAgent(dot_id=dot_id, provider=ai_provider)
    final_response = ""
    status = "COMPLETED"
    finish_status = "completed"
    error_msg = ""

    try:
        # Diretriz de silêncio para conter ruído e poupar tokens de notificação
        heartbeat_instruction = (
            f"{prompt}\n\n"
            "DIRETRIZ DE SILÊNCIO OPERACIONAL: Se após inspecionar o sistema ou dados você verificar que "
            "tudo está em normalidade e nenhuma ação corretiva for necessária, responda estritamente 'HEARTBEAT_OK'. "
            "Caso detecte uma anomalia ou necessidade de intervenção, forneça o diagnóstico técnico sucinto."
        )

        async for event in agent.run_thread(thread_id=proactive_thread_id, user_message=heartbeat_instruction):
            if event["event"] == "run:finished":
                event_data = event.get("data", {})
                finish_status = event_data.get("status", "completed")
                final_response = event_data.get("final_response", "")
                error_msg = event_data.get("error", "")

        # Avaliação de resultado
        if finish_status == "failed":
            status = "FAILED"
            summary = f"Falha no ciclo do agente: {error_msg}" if error_msg else "Falha na inferência do agente."
            logger.warning("Tarefa proativa '%s' falhou no ciclo cognitivo: %s", task["task_name"], summary)
        elif "HEARTBEAT_OK" in final_response.strip():
            status = "SILENT"
            summary = "Condição operacional normal. Nenhuma notificação emitida."
            logger.info("Tarefa proativa '%s' concluída com status SILENT (HEARTBEAT_OK).", task["task_name"])
        else:
            status = "COMPLETED"
            summary = final_response[:400] if final_response else "Execução concluída sem texto."
            logger.info("Tarefa proativa '%s' detectou evento e emitiu conclusão.", task["task_name"])

            # Despacho externo se canal configurado
            channel_type = task.get("target_channel_type")
            channel_id = task.get("target_channel_id")
            if channel_type and channel_type in ("webhook", "telegram") and channel_id:
                from .notifier import HITLNotifier
                await HITLNotifier.notify_approval_requested(
                    approval_id=f"heartbeat-{task_id[:8]}",
                    dot_id=dot_id,
                    action_type="proactive_alert",
                    risk_level="MEDIUM",
                    payload=f"Tarefa: {task['task_name']} | Relatório: {final_response}"
                )

    except Exception as e:
        status = "FAILED"
        summary = f"Erro no ciclo proativo: {str(e)}"
        logger.error("Falha ao executar tarefa proativa '%s': %s", task_id, str(e), exc_info=True)
    finally:
        EdgeScheduler.mark_stopped(task_id)

    await EdgeScheduler.mark_task_finished(
        task_id=task_id,
        cron_expr=cron_expr,
        status=status,
        summary=summary
    )


async def heartbeat_worker_loop(
    ai_provider: OpenAIUniversalProvider,
    check_interval_seconds: int = 15
) -> None:
    """
    Loop assíncrono perpétuo de background do scheduler.
    Varre tarefas devidas a cada N segundos e as executa concorrentemente sem duplicações,
    além de monitorar periodicamente limites térmicos e de disco do Raspberry Pi 4B.
    """
    logger.info("Scheduler Proativo (Dot Heartbeat) iniciado (intervalo: %ds).", check_interval_seconds)
    hardware_check_ticks = 0

    while True:
        try:
            due_tasks = await EdgeScheduler.get_due_tasks()
            for task in due_tasks:
                if not EdgeScheduler.is_running(task["id"]):
                    asyncio.create_task(execute_proactive_task(task, ai_provider))

            # Monitoramento proativo de triggers de hardware a cada ~60 segundos
            hardware_check_ticks += 1
            if hardware_check_ticks >= max(1, 60 // check_interval_seconds):
                hardware_check_ticks = 0
                try:
                    from .edge_triggers import EdgeHardwareTriggers
                    await EdgeHardwareTriggers.evaluate_and_alert(notify_hitl=True)
                except Exception as hw_err:
                    logger.debug("Falha na checagem de triggers de hardware no heartbeat: %s", str(hw_err))

            await asyncio.sleep(check_interval_seconds)
        except asyncio.CancelledError:
            logger.info("Scheduler Proativo encerrado.")
            break
        except Exception as e:
            logger.error("Erro inesperado no loop do Heartbeat: %s", str(e), exc_info=True)
            await asyncio.sleep(check_interval_seconds)

