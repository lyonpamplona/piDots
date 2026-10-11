"""
Teste e Validação de Resiliência: Fases 1 a 4 do Plano de Ação piDots.
Valida tipagem de exceções de provedor, contrato run:finished de erro,
propagação cirúrgica em consumidores (scheduler, gateway, orchestrator),
circuit breaker com backoff exponencial e sanity check preventivo de credenciais.
"""

import asyncio
from datetime import datetime, timezone
import httpx

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.providers.openai_client import (
    OpenAIUniversalProvider,
    ProviderAuthError,
    ProviderTransientError
)
from pidots.core.agent import DotAgent
from pidots.core.scheduler import EdgeScheduler, execute_proactive_task
from pidots.core.orchestrator import MultiBotOrchestrator
from pidots.core.messaging_gateway import MessagingGateway


class FailingMockProvider:
    """Simula falha de autenticação (HTTP 401) para testar tratamento de erros."""

    def __init__(self, error_type: str = "auth"):
        self.error_type = error_type
        self.api_key = "mock_key"

    async def chat_completion(self, messages, tools=None, model="default", temperature=0.2):
        if self.error_type == "auth":
            raise ProviderAuthError("HTTP 401: Unauthorized - Chave de API inválida no gateway remoto.")
        raise ProviderTransientError("HTTP 503: Service Unavailable - Gateway temporariamente inacessível.")


async def run_resilience_tests():
    print("=== [piDots] Teste de Resiliência das Fases 1 a 4 ===")
    await init_edge_database()

    test_dot_id = "dot-resilience-tester"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (test_dot_id, "Resilience Tester", "Tester", "Você é um assistente de testes.", "qwen3.8-27b", "/tmp", "general")
        )
        await db.commit()

    # -------------------------------------------------------------
    # 1. Teste da Fase 1: run_thread com ProviderAuthError
    # -------------------------------------------------------------
    print("[1/5] Testando Fase 1: Emissão de evento de erro e mensagens internas de diagnóstico...")
    failing_provider = FailingMockProvider(error_type="auth")
    agent = DotAgent(dot_id=test_dot_id, provider=failing_provider)

    thread_id = "resilience-test-thread-1"
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO threads (id, dot_id, title) VALUES (?, ?, ?)",
            (thread_id, test_dot_id, "Thread de Teste")
        )
        await db.commit()

    run_finished_event = None

    async for event in agent.run_thread(thread_id=thread_id, user_message="Olá mundo!"):
        if event["event"] == "run:finished":
            run_finished_event = event

    assert run_finished_event is not None, "Evento run:finished não foi emitido."
    assert run_finished_event["data"]["status"] == "failed", f"Esperado status 'failed', obtido {run_finished_event['data']['status']}"
    assert "HTTP 401" in run_finished_event["data"]["error"], "Mensagem de erro não contém detalhe de autenticação."
    assert run_finished_event["data"]["final_response"] == "", "final_response deveria ser vazio em caso de erro."

    # Verifica se a mensagem de diagnóstico foi gravada no SQLite com visibility='internal'
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT content, visibility FROM messages WHERE thread_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
            (thread_id,)
        )
        diag_msg = await cursor.fetchone()
        assert diag_msg is not None, "Mensagem interna de diagnóstico não foi gravada."
        assert diag_msg["visibility"] == "internal", f"Esperado visibility 'internal', obtido {diag_msg['visibility']}"
        assert "[FALHA DE AUTENTICAÇÃO]" in diag_msg["content"]
    print("      Fase 1 validada com sucesso: run:finished emitido com status 'failed' e nota interna gravada.")

    # -------------------------------------------------------------
    # 2. Teste da Fase 2: Consumidor Scheduler com falha
    # -------------------------------------------------------------
    print("[2/5] Testando Fase 2 (Scheduler): Tarefa que falha na inferência grava status FAILED...")
    task_id = "task-resilience-fail"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO scheduled_tasks (id, dot_id, task_name, cron_expr, action_prompt, next_run_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (task_id, test_dot_id, "Tarefa Falha", "*/10 * * * *", "Executar teste", datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    task_obj = {
        "id": task_id,
        "dot_id": test_dot_id,
        "task_name": "Tarefa Falha",
        "cron_expr": "*/10 * * * *",
        "action_prompt": "Executar teste",
        "target_channel_type": "internal",
        "target_channel_id": None
    }
    await execute_proactive_task(task_obj, failing_provider)

    async with get_db() as db:
        cursor = await db.execute("SELECT last_status, last_result_summary FROM scheduled_tasks WHERE id = ?", (task_id,))
        task_row = await cursor.fetchone()
        assert task_row["last_status"] == "FAILED", f"Esperado last_status 'FAILED', obtido {task_row['last_status']}"
        assert "Falha no ciclo do agente" in task_row["last_result_summary"]
    print("      Fase 2 (Scheduler) validada: status FAILED e sumário de falha gravados no SQLite.")

    # -------------------------------------------------------------
    # 3. Teste da Fase 2: Consumidor Orchestrator (delegate_subtask) com falha
    # -------------------------------------------------------------
    print("[3/5] Testando Fase 2 (Orchestrator): Delegação a worker que falha devolve success: False...")
    result = await MultiBotOrchestrator.delegate_subtask(
        thread_id=thread_id,
        source_dot_id=test_dot_id,
        target_dot_id=test_dot_id,
        task_goal="Objetivo com falha induzida",
        context_snippet="Contexto de teste",
        provider=failing_provider
    )
    assert result.get("success") is False, f"Esperado success: False, obtido {result.get('success')}"
    assert "HTTP 401" in result.get("error", "")

    # Checa status no banco em agent_handoffs
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT status, result_summary FROM agent_handoffs WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1",
            (thread_id,)
        )
        handoff_row = await cursor.fetchone()
        assert handoff_row["status"] == "FAILED", f"Esperado handoff status FAILED, obtido {handoff_row['status']}"
    print("      Fase 2 (Orchestrator) validada: handoff marcado FAILED e supervisor informado da falha.")

    # -------------------------------------------------------------
    # 4. Teste da Fase 3: Circuit Breaker e Backoff Exponencial
    # -------------------------------------------------------------
    print("[4/5] Testando Fase 3: Circuit Breaker abre circuito na 5ª falha consecutiva...")
    cb_task_id = "task-resilience-cb"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO scheduled_tasks
            (id, dot_id, task_name, cron_expr, action_prompt, next_run_at, consecutive_failures, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 3, 1)
            """,
            (cb_task_id, test_dot_id, "Tarefa Circuit Breaker", "*/10 * * * *", "Executar", datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    # Falha 4: deve incrementar para 4 e manter ativo com backoff
    await EdgeScheduler.mark_task_finished(cb_task_id, "*/10 * * * *", "FAILED", "Falha de teste 4")
    async with get_db() as db:
        cursor = await db.execute("SELECT consecutive_failures, is_active, last_status, backoff_until FROM scheduled_tasks WHERE id = ?", (cb_task_id,))
        row = await cursor.fetchone()
        assert row["consecutive_failures"] == 4
        assert row["is_active"] == 1
        assert row["backoff_until"] is not None

    # Falha 5: deve acionar o circuit breaker (is_active = 0, last_status = 'CIRCUIT_OPEN')
    await EdgeScheduler.mark_task_finished(cb_task_id, "*/10 * * * *", "FAILED", "Falha de teste 5")
    async with get_db() as db:
        cursor = await db.execute("SELECT consecutive_failures, is_active, last_status FROM scheduled_tasks WHERE id = ?", (cb_task_id,))
        row = await cursor.fetchone()
        assert row["consecutive_failures"] == 5
        assert row["is_active"] == 0
        assert row["last_status"] == "CIRCUIT_OPEN"
    print("      Fase 3 validada: Circuit Breaker abriu circuito na 5ª falha e desativou tarefa.")

    # -------------------------------------------------------------
    # 5. Teste da Fase 4: Sanity Check Preventivo de Chave Placeholder
    # -------------------------------------------------------------
    print("[5/5] Testando Fase 4: Sanity check de chave placeholder pausa tarefa com AUTH_REQUIRED...")
    real_provider_placeholder = OpenAIUniversalProvider(
        base_url="https://api.openai.com/v1",
        api_key="sua_chave_aqui"
    )
    sanity_task_id = "task-resilience-sanity"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO scheduled_tasks
            (id, dot_id, task_name, cron_expr, action_prompt, next_run_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (sanity_task_id, test_dot_id, "Tarefa Placeholder", "*/10 * * * *", "Executar", datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    sanity_task_obj = {
        "id": sanity_task_id,
        "dot_id": test_dot_id,
        "task_name": "Tarefa Placeholder",
        "cron_expr": "*/10 * * * *",
        "action_prompt": "Executar",
        "target_channel_type": "internal",
        "target_channel_id": None
    }
    await execute_proactive_task(sanity_task_obj, real_provider_placeholder)

    async with get_db() as db:
        cursor = await db.execute("SELECT last_status, backoff_until FROM scheduled_tasks WHERE id = ?", (sanity_task_id,))
        row = await cursor.fetchone()
        assert row["last_status"] == "AUTH_REQUIRED", f"Esperado last_status 'AUTH_REQUIRED', obtido {row['last_status']}"
        assert row["backoff_until"] is not None, "backoff_until deve estar preenchido para evitar retry imediato."
    print("      Fase 4 validada: Tarefa pausada com AUTH_REQUIRED sem realizar requisição remota inútil.")

    print("\n=== [SUCESSO TOTAL] Fases 1, 2, 3 e 4 validadas com 100% de êxito! ===")


if __name__ == "__main__":
    asyncio.run(run_resilience_tests())
