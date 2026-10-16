"""
Módulo de Planejamento em Duas Etapas (Two-Stage Planning) para piDots.
Permite decompor objetivos complexos em metas (Goals) e marcos auditáveis (Milestones),
garantindo execução guiada com checkpoints e evidências técnicas no SQLite WAL.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from ..config import settings
from ..storage.db import get_db

logger = logging.getLogger("pidots.planner")

VALID_MILESTONE_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED")
VALID_GOAL_STATUSES = ("IN_PROGRESS", "COMPLETED", "FAILED", "PAUSED")


class TwoStagePlanner:
    """Gerenciador de planos cognitivos com checkpoints persistentes."""

    @classmethod
    async def create_plan(
        cls,
        dot_id: str,
        title: str,
        milestones: list[dict[str, str]],
        thread_id: str | None = None,
        description: str = "",
        priority: int = 1
    ) -> dict[str, Any]:
        """
        Cria um plano persistente (Goal) decomposto em passos auditáveis (Milestones).
        """
        if not title.strip():
            return {"success": False, "error": "Título do plano não pode ser vazio."}
        if not milestones:
            return {"success": False, "error": "O plano deve conter ao menos um marco (milestone)."}

        goal_id = str(uuid.uuid4())
        created_milestones = []

        async with get_db() as db:
            # 1. Garante existência do Dot e resolve thread_id para conformidade de Foreign Key
            await db.execute(
                """
                INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
                VALUES (?, ?, 'Coworker', 'Agente executor de planos.', ?, ?)
                """,
                (dot_id, dot_id, settings.ai_model, f"{settings.workspaces_root}/{dot_id}")
            )
            valid_thread_id = None
            if thread_id:
                cursor = await db.execute("SELECT id FROM threads WHERE id = ?", (thread_id,))
                if await cursor.fetchone():
                    valid_thread_id = thread_id
                else:
                    await db.execute(
                        "INSERT OR IGNORE INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'idle')",
                        (thread_id, dot_id, f"Plano: {title.strip()[:30]}")
                    )
                    valid_thread_id = thread_id

            # 2. Registra meta principal
            await db.execute(
                """
                INSERT INTO goals (id, dot_id, thread_id, title, description, status, priority)
                VALUES (?, ?, ?, ?, ?, 'IN_PROGRESS', ?)
                """,
                (goal_id, dot_id, valid_thread_id, title.strip(), description.strip(), priority)
            )

            # 3. Registra marcos sequenciais
            for idx, m in enumerate(milestones, start=1):
                m_id = str(uuid.uuid4())
                m_title = m.get("title", f"Passo {idx}").strip()
                m_criteria = m.get("acceptance_criteria", "Critério técnico verificado").strip()

                await db.execute(
                    """
                    INSERT INTO milestones (id, goal_id, order_index, title, acceptance_criteria, status)
                    VALUES (?, ?, ?, ?, ?, 'PENDING')
                    """,
                    (m_id, goal_id, idx, m_title, m_criteria)
                )
                created_milestones.append({
                    "id": m_id,
                    "order_index": idx,
                    "title": m_title,
                    "acceptance_criteria": m_criteria,
                    "status": "PENDING"
                })

            await db.commit()

        logger.info("Plano criado com sucesso: ID %s ('%s') com %d marcos para Dot '%s'.", goal_id, title, len(milestones), dot_id)
        return {
            "success": True,
            "goal_id": goal_id,
            "title": title,
            "milestones_count": len(created_milestones),
            "milestones": created_milestones
        }

    @classmethod
    async def get_plan_status(
        cls,
        goal_id: str | None = None,
        thread_id: str | None = None,
        dot_id: str | None = None
    ) -> dict[str, Any]:
        """
        Recupera o status do plano especificado ou do plano ativo na thread.
        Calcula percentual de conclusão e próximo passo pendente.
        """
        async with get_db() as db:
            target_goal = None
            if goal_id:
                cursor = await db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
                target_goal = await cursor.fetchone()
            elif thread_id:
                cursor = await db.execute(
                    "SELECT * FROM goals WHERE thread_id = ? AND status = 'IN_PROGRESS' ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (thread_id,)
                )
                target_goal = await cursor.fetchone()
                if not target_goal:
                    cursor = await db.execute(
                        "SELECT * FROM goals WHERE thread_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                        (thread_id,)
                    )
                    target_goal = await cursor.fetchone()
            elif dot_id:
                cursor = await db.execute(
                    "SELECT * FROM goals WHERE dot_id = ? AND status = 'IN_PROGRESS' ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (dot_id,)
                )
                target_goal = await cursor.fetchone()
                if not target_goal:
                    cursor = await db.execute(
                        "SELECT * FROM goals WHERE dot_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                        (dot_id,)
                    )
                    target_goal = await cursor.fetchone()

            if not target_goal:
                return {"found": False, "message": "Nenhum plano ativo encontrado para os parâmetros informados."}

            g_data = dict(target_goal)
            g_id = g_data["id"]

            # Busca marcos ordenados
            cursor = await db.execute(
                "SELECT * FROM milestones WHERE goal_id = ? ORDER BY order_index ASC",
                (g_id,)
            )
            rows = await cursor.fetchall()
            milestones = [dict(r) for r in rows]

        total = len(milestones)
        completed = sum(1 for m in milestones if m["status"] == "COMPLETED")
        progress_pct = round((completed / total * 100), 1) if total > 0 else 0.0

        current_step = next((m for m in milestones if m["status"] in ("IN_PROGRESS", "PENDING")), None)

        return {
            "found": True,
            "goal_id": g_id,
            "title": g_data["title"],
            "description": g_data.get("description", ""),
            "status": g_data["status"],
            "progress_pct": progress_pct,
            "total_milestones": total,
            "completed_milestones": completed,
            "current_milestone": current_step,
            "milestones": milestones
        }

    @classmethod
    async def update_milestone(
        cls,
        milestone_id: str,
        status: str,
        evidence_summary: str = ""
    ) -> dict[str, Any]:
        """
        Atualiza o status de um marco com evidência técnica de conclusão.
        Se todos os marcos forem concluídos, marca a meta como COMPLETED.
        """
        st_clean = status.strip().upper()
        if st_clean not in VALID_MILESTONE_STATUSES:
            return {
                "success": False,
                "error": f"Status inválido '{status}'. Valores permitidos: {', '.join(VALID_MILESTONE_STATUSES)}."
            }

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,))
            m_row = await cursor.fetchone()
            if not m_row:
                return {"success": False, "error": f"Marco '{milestone_id}' não encontrado."}

            goal_id = m_row["goal_id"]
            completed_at = datetime.now(timezone.utc).isoformat() if st_clean in ("COMPLETED", "FAILED") else None

            await db.execute(
                """
                UPDATE milestones
                SET status = ?, evidence_summary = ?, completed_at = ?
                WHERE id = ?
                """,
                (st_clean, evidence_summary.strip(), completed_at, milestone_id)
            )

            # Verifica se todos os marcos deste goal foram concluídos
            cursor = await db.execute("SELECT status FROM milestones WHERE goal_id = ?", (goal_id,))
            all_m = await cursor.fetchall()
            statuses = [r["status"] for r in all_m]

            goal_completed = len(statuses) > 0 and all(s == "COMPLETED" for s in statuses)
            goal_failed = any(s == "FAILED" for s in statuses)

            if goal_completed:
                await db.execute(
                    "UPDATE goals SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (goal_id,)
                )
            elif goal_failed and all(s in ("COMPLETED", "FAILED") for s in statuses):
                await db.execute(
                    "UPDATE goals SET status = 'FAILED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (goal_id,)
                )

            await db.commit()

        logger.info("Marco '%s' atualizado para status '%s' no Goal '%s'.", milestone_id, st_clean, goal_id)
        return {
            "success": True,
            "milestone_id": milestone_id,
            "goal_id": goal_id,
            "new_status": st_clean,
            "goal_completed": goal_completed,
            "evidence_summary": evidence_summary
        }

    @classmethod
    async def format_plan_prompt(cls, thread_id: str | None, dot_id: str) -> str:
        """
        Formata o plano ativo em bloco estruturado XML para injeção in-context no DotAgent.
        """
        plan = await cls.get_plan_status(thread_id=thread_id, dot_id=dot_id)
        if not plan.get("found"):
            return ""

        lines = [
            "<execution_plan>",
            f"  <goal id=\"{plan['goal_id']}\" title=\"{plan['title']}\" progress=\"{plan['progress_pct']}%\">",
            "    <milestones>"
        ]
        for m in plan.get("milestones", []):
            evid = f" evidence=\"{m['evidence_summary']}\"" if m.get("evidence_summary") else ""
            lines.append(
                f"      <step order=\"{m['order_index']}\" id=\"{m['id']}\" status=\"{m['status']}\"{evid}>{m['title']} (Critério: {m['acceptance_criteria']})</step>"
            )
        lines.append("    </milestones>")
        lines.append("  </goal>")
        lines.append("  <guideline>")
        lines.append("    Execute as tarefas de forma faseada conforme os passos do plano. Atualize cada passo com 'plan_update_step' assim que atingir os critérios de aceitação.")
        lines.append("  </guideline>")
        lines.append("</execution_plan>")
        return "\n".join(lines)
