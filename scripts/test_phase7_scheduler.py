"""
Teste e Validação da Fase 7: Scheduler Proativo e Padrão Dot Heartbeat.
Valida agendamento in-process, cálculo croniter, diretriz HEARTBEAT_OK e persistência no SQLite WAL.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path


import sys
from pathlib import Path

# Adiciona o diretorio raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.scheduler import EdgeScheduler, execute_proactive_task


class MockHeartbeatProvider:
    """Simula respostas do Dot para ciclos de Heartbeat."""

    def __init__(self) -> None:
        pass

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str = "default",
        temperature: float = 0.2
    ) -> dict:
        prompt_content = messages[-1].get("content", "")
        # Se for checagem normal
        if "Checagem Rotineira Normal" in prompt_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "HEARTBEAT_OK",
                        "tool_calls": None
                    }
                }]
            }
        # Se for detecção de anomalia
        elif "Verificar Alerta de Disco" in prompt_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "ALERTA DETECTADO: Espaço em disco flash do MicroSD atingiu 82% de ocupação. Sugerido purgar caches.",
                        "tool_calls": None
                    }
                }]
            }
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "HEARTBEAT_OK",
                    "tool_calls": None
                }
            }]
        }


async def run_phase7_tests():
    print("=== [piDots] Teste e Validação da Fase 7: Dot Heartbeat e Scheduler Proativo ===")
    await init_edge_database()

    dot_id = "dot-auditor"

    # 1. Garantir que o Dot exista no banco
    print("[1/4] Registrando Dot para rotinas proativas...")
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dot_id, "Auditor Proativo", "Auditor",
                "Você é um auditor proativo de integridade de sistema.",
                "mock-model",
                str(Path(settings.workspaces_root) / dot_id)
            )
        )
        await db.commit()

    # 2. Registrando tarefas proativas no SQLite WAL via EdgeScheduler
    print("[2/4] Registrando tarefas proativas com sintaxe croniter...")
    task_normal_id = await EdgeScheduler.register_task(
        dot_id=dot_id,
        task_name="Monitoramento Rotineiro",
        cron_expr="*/10 * * * *",
        action_prompt="Checagem Rotineira Normal: verificar temperatura e sockets."
    )
    task_alert_id = await EdgeScheduler.register_task(
        dot_id=dot_id,
        task_name="Auditoria de Espaço Flash",
        cron_expr="0 * * * *",
        action_prompt="Verificar Alerta de Disco: auditar partição /var/log."
    )
    print(f"      Tarefas registradas no SQLite WAL: [{task_normal_id[:8]}] e [{task_alert_id[:8]}]")

    # 3. Forçando data retroativa para simular tarefas devidas
    print("[3/4] Testando consulta e disparo de tarefas devidas...")
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    async with get_db() as db:
        await db.execute(
            "UPDATE scheduled_tasks SET next_run_at = ? WHERE id IN (?, ?)",
            (past_iso, task_normal_id, task_alert_id)
        )
        await db.commit()

    due_tasks = await EdgeScheduler.get_due_tasks()
    assert len(due_tasks) >= 2, f"Esperado pelo menos 2 tarefas devidas, obtido: {len(due_tasks)}"
    print(f"      Tarefas devidas recuperadas do SQLite WAL: {len(due_tasks)} tarefa(s).")

    # 4. Executando as tarefas com o MockHeartbeatProvider
    print("[4/4] Executando tarefas proativas e testando filtro de silêncio HEARTBEAT_OK...")
    mock_provider = MockHeartbeatProvider()

    # Executa a tarefa normal
    t_normal = [t for t in due_tasks if t["id"] == task_normal_id][0]
    await execute_proactive_task(t_normal, mock_provider)

    # Executa a tarefa com alerta
    t_alert = [t for t in due_tasks if t["id"] == task_alert_id][0]
    await execute_proactive_task(t_alert, mock_provider)

    # Validando resultados no SQLite WAL
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, task_name, last_status, last_result_summary FROM scheduled_tasks WHERE id IN (?, ?)",
            (task_normal_id, task_alert_id)
        )
        results = {r["id"]: dict(r) for r in await cursor.fetchall()}

    res_norm = results[task_normal_id]
    res_alert = results[task_alert_id]

    print(f"      Tarefa 1: '{res_norm['task_name']}' -> Status: {res_norm['last_status']} | Resumo: '{res_norm['last_result_summary']}'")
    assert res_norm["last_status"] == "SILENT", f"Esperado status SILENT para HEARTBEAT_OK, obtido: {res_norm['last_status']}"

    print(f"      Tarefa 2: '{res_alert['task_name']}' -> Status: {res_alert['last_status']} | Resumo: '{res_alert['last_result_summary'][:60]}...'")
    assert res_alert["last_status"] == "COMPLETED", f"Esperado status COMPLETED para alerta, obtido: {res_alert['last_status']}"
    assert "ALERTA DETECTADO" in res_alert["last_result_summary"]

    print("\n=== [SUCESSO] Fase 3 validada com 100% de êxito! Dot Heartbeat Operacional! ===")


if __name__ == "__main__":
    asyncio.run(run_phase7_tests())
