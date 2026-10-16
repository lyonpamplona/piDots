"""
Módulo de Manutenção Noturna Autônoma e Saúde do MicroSD para piDots.
Executa compactação atômica, truncamento síncrono de WAL, otimização do planejador
de consultas e consolidação de mensagens históricas em memórias episódicas estruturadas.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite
from .db import get_db
from ..config import settings


logger = logging.getLogger("pidots.maintenance")


class EdgeMaintenanceManager:
    """Gerenciador de rotinas de preservação e compactação do SQLite em hardware Edge."""

    @staticmethod
    def _get_file_size_safe(path: str) -> int:
        """Retorna o tamanho do arquivo em bytes de forma segura."""
        try:
            if os.path.exists(path):
                return os.path.getsize(path)
        except Exception as size_err:
            logger.debug("Falha ao obter tamanho do arquivo %s: %s", path, size_err)
        return 0

    @classmethod
    async def checkpoint_wal(cls, mode: str = "TRUNCATE") -> dict[str, Any]:
        """
        Executa checkpoint síncrono do arquivo WAL (Write-Ahead Log) do SQLite.
        O modo TRUNCATE esvazia fisicamente o arquivo -wal, prevenindo inchaço no MicroSD.
        """
        valid_modes = {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
        selected_mode = mode.upper() if mode.upper() in valid_modes else "TRUNCATE"

        async with get_db() as db:
            cursor = await db.execute(f"PRAGMA wal_checkpoint({selected_mode});")
            row = await cursor.fetchone()
            busy = row[0] if row else 0
            log_pages = row[1] if row else 0
            checkpointed_pages = row[2] if row else 0

        logger.info(
            "WAL Checkpoint (%s) concluído: busy=%s, log_pages=%s, checkpointed=%s",
            selected_mode, busy, log_pages, checkpointed_pages
        )

        return {
            "mode": selected_mode,
            "busy": bool(busy),
            "log_pages": log_pages,
            "checkpointed_pages": checkpointed_pages,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    async def backup_vacuum_into(cls, destination_path: str) -> dict[str, Any]:
        """
        Cria snapshot atômico do banco de dados utilizando VACUUM INTO sem travar
        leituras ou escritas ativas.
        """
        dest = Path(destination_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            dest.unlink()

        safe_path_str = str(dest).replace("'", "''")
        async with aiosqlite.connect(settings.sqlite_db_path, isolation_level=None, timeout=5.0) as db:
            cur_p = await db.execute("PRAGMA busy_timeout = 5000;")
            await cur_p.close()
            cur = await db.execute(f"VACUUM INTO '{safe_path_str}';")
            await cur.close()

        size_bytes = cls._get_file_size_safe(str(dest))
        size_mb = round(size_bytes / (1024 * 1024), 2)


        logger.info("Backup atômico VACUUM INTO gerado em '%s' (%s MB).", str(dest), size_mb)

        return {
            "success": True,
            "backup_path": str(dest),
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    async def optimize_database(cls) -> dict[str, Any]:
        """Executa PRAGMA optimize para atualizar seletivamente estatísticas do query planner e podar tool_runs antigas."""
        deleted_tool_runs = 0
        async with get_db() as db:
            # Poda registros de auditoria de ferramentas com mais de 30 dias para poupar MicroSD
            try:
                cur = await db.execute("DELETE FROM tool_runs WHERE created_at <= datetime('now', '-30 days');")
                deleted_tool_runs = cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else 0
            except Exception as e:
                logger.debug("Poda de tool_runs ignorada: %s", e)

            # PRAGMA optimize executa ANALYZE internamente apenas nas tabelas necessárias, evitando desgaste cego do flash
            await db.execute("PRAGMA optimize;")
            await db.commit()

        logger.info("Otimização de índices e estatísticas SQLite concluída com sucesso. Tool runs podadas: %d", deleted_tool_runs)
        return {
            "success": True,
            "pruned_tool_runs": deleted_tool_runs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    async def consolidate_old_episodes(
        cls,
        days_threshold: int = 7,
        dot_id: str | None = None
    ) -> dict[str, Any]:
        """
        Consolida mensagens brutas antigas (> days_threshold dias) em registros compactos
        na tabela episodic_memories e remove com segurança as mensagens brutas podadas,
        poupando espaço em blocos flash do MicroSD.
        """
        days_threshold = max(1, int(days_threshold))
        async with get_db() as db:
            # 1. Busca mensagens antigas agrupadas por thread
            if dot_id:
                cursor = await db.execute(
                    """
                    SELECT m.id, m.thread_id, m.role, m.content, m.created_at, t.dot_id, t.title
                    FROM messages m
                    JOIN threads t ON m.thread_id = t.id
                    WHERE m.created_at <= datetime('now', '-' || ? || ' days')
                      AND t.dot_id = ?
                    ORDER BY m.thread_id, m.created_at ASC
                    """,
                    (str(days_threshold), dot_id)
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT m.id, m.thread_id, m.role, m.content, m.created_at, t.dot_id, t.title
                    FROM messages m
                    JOIN threads t ON m.thread_id = t.id
                    WHERE m.created_at <= datetime('now', '-' || ? || ' days')
                    ORDER BY m.thread_id, m.created_at ASC
                    """,
                    (str(days_threshold),)
                )
            rows = await cursor.fetchall()

            if not rows:
                return {
                    "threads_consolidated": 0,
                    "messages_pruned": 0,
                    "episodic_records_created": 0,
                    "details": []
                }

            # Agrupa mensagens por thread
            threads_map: dict[str, list[dict[str, Any]]] = {}
            for r in rows:
                t_id = r["thread_id"]
                if t_id not in threads_map:
                    threads_map[t_id] = []
                threads_map[t_id].append(dict(r))

            consolidated_details = []
            total_messages_pruned = 0

            for t_id, msgs in threads_map.items():
                first_msg = msgs[0]
                t_dot_id = first_msg["dot_id"]
                t_title = first_msg["title"] or f"Thread {t_id}"
                msgs_count = len(msgs)

                # Gera resumo analítico sintetizado da thread
                first_user_content = next((m["content"] for m in msgs if m["role"] == "user"), "Interação geral")
                last_assistant_content = next((m["content"] for m in reversed(msgs) if m["role"] == "assistant"), "Concluída")

                summary_text = (
                    f"Consolidação episódica de '{t_title}' ({msgs_count} mensagens). "
                    f"Objetivo inicial: {first_user_content[:200]}... "
                    f"Desfecho: {last_assistant_content[:200]}..."
                )
                key_decisions = f"Consolidado após {days_threshold} dias de inatividade. Total de turnos: {msgs_count}."
                modified_artifacts = f"thread_id={t_id}"

                episodic_id = f"ep-{uuid.uuid4().hex[:12]}"

                # Grava o resumo na memória episódica
                await db.execute(
                    """
                    INSERT INTO episodic_memories (
                        id, dot_id, thread_id, summary, key_decisions, modified_artifacts
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (episodic_id, t_dot_id, t_id, summary_text, key_decisions, modified_artifacts)
                )

                # Remove as mensagens brutas da thread até o corte
                delete_cursor = await db.execute(
                    """
                    DELETE FROM messages
                    WHERE thread_id = ?
                      AND created_at <= datetime('now', '-' || ? || ' days')
                    """,
                    (t_id, str(days_threshold))
                )
                deleted_count = delete_cursor.rowcount
                total_messages_pruned += deleted_count

                consolidated_details.append({
                    "thread_id": t_id,
                    "dot_id": t_dot_id,
                    "messages_pruned": deleted_count,
                    "episodic_memory_id": episodic_id
                })

            await db.commit()

        logger.info(
            "Consolidação episódica concluída: %d threads consolidadas, %d mensagens podadas.",
            len(consolidated_details), total_messages_pruned
        )

        return {
            "threads_consolidated": len(consolidated_details),
            "messages_pruned": total_messages_pruned,
            "episodic_records_created": len(consolidated_details),
            "details": consolidated_details
        }

    @classmethod
    async def run_full_maintenance(
        cls,
        backup_dir: str | None = None,
        days_threshold: int = 7,
        dot_id: str | None = None
    ) -> dict[str, Any]:
        """
        Executa a suíte completa de manutenção e compactação noturna do piDots:
        1. Medição inicial de footprint no disco.
        2. Checkpoint WAL TRUNCATE.
        3. Consolidação e poda episódica de mensagens antigas.
        4. Backup atômico opcional com VACUUM INTO.
        5. Atualização de estatísticas do planejador SQLite.
        6. Checkpoint final e cálculo de bytes economizados.
        """
        db_path = settings.sqlite_db_path
        wal_path = f"{db_path}-wal"

        size_db_before = cls._get_file_size_safe(db_path)
        size_wal_before = cls._get_file_size_safe(wal_path)
        total_before = size_db_before + size_wal_before

        start_time = datetime.now(timezone.utc)

        # 1. Checkpoint WAL inicial
        chk_init = await cls.checkpoint_wal(mode="TRUNCATE")

        # 2. Consolidação episódica
        consolidation = await cls.consolidate_old_episodes(
            days_threshold=days_threshold,
            dot_id=dot_id
        )

        # 3. Backup atômico seguro se solicitado
        backup_result = None
        if backup_dir:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_file = Path(backup_dir) / f"pidots_backup_{ts}.db"
            backup_result = await cls.backup_vacuum_into(str(backup_file))

        # 4. Otimização estatística
        opt_result = await cls.optimize_database()

        # 5. Checkpoint WAL final pós-limpeza
        chk_final = await cls.checkpoint_wal(mode="TRUNCATE")

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        size_db_after = cls._get_file_size_safe(db_path)
        size_wal_after = cls._get_file_size_safe(wal_path)
        total_after = size_db_after + size_wal_after
        bytes_saved = max(0, total_before - total_after)

        report = {
            "status": "COMPLETED",
            "device": "Linux Edge Node (Ref: RPi4 ARM64)",
            "duration_ms": duration_ms,
            "metrics_before": {
                "db_bytes": size_db_before,
                "wal_bytes": size_wal_before,
                "total_bytes": total_before
            },
            "metrics_after": {
                "db_bytes": size_db_after,
                "wal_bytes": size_wal_after,
                "total_bytes": total_after
            },
            "bytes_saved": bytes_saved,
            "wal_checkpoint_initial": chk_init,
            "wal_checkpoint_final": chk_final,
            "consolidation": consolidation,
            "backup": backup_result,
            "optimization": opt_result,
            "timestamp": end_time.isoformat()
        }

        logger.info(
            "Manutenção noturna executada com sucesso em %d ms. Bytes salvos: %d",
            duration_ms, bytes_saved
        )
        return report
