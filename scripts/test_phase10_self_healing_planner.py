"""
Teste e Validação da Fase 2: Self-Healing Harness e Two-Stage Planning.
Homologa os mecanismos de auto-correção iterativa de erros (SWE-agent / OpenHands)
e planejamento guiado por metas e marcos (Goals & Milestones) no nó piDots (Raspberry Pi 4B).
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timezone


import sys
from pathlib import Path

# Adiciona o diretorio raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.self_healing import SelfHealingHarness
from pidots.core.planner import TwoStagePlanner
from pidots.tools.registry import registry
from pidots.core.agent import DotAgent


class MockSelfHealingAgentProvider:
    """Mock Provider para simular o Dot acionando auto-correção após falha em execução."""

    def __init__(self):
        self.step = 0

    async def chat_completion(self, messages, tools=None, model="default", temperature=0.2):
        self.step += 1

        # Iteração 1: O modelo tenta rodar um comando que resulta em erro
        if self.step == 1:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_exec_fail_1",
                            "type": "function",
                            "function": {
                                "name": "execute_and_verify",
                                "arguments": json.dumps({"command": "python3 -c 'raise ValueError(\"Parametro invalido\")'"})
                            }
                        }]
                    }
                }]
            }

        # Iteração 2: O modelo recebe o diagnóstico de auto-correção e reexecuta com o parâmetro correto
        if self.step == 2:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_exec_ok_2",
                            "type": "function",
                            "function": {
                                "name": "execute_and_verify",
                                "arguments": json.dumps({"command": "python3 -c 'print(\"Validacao concluida com sucesso\")'"})
                            }
                        }]
                    }
                }]
            }

        # Iteração 3: Resposta final após validação bem-sucedida
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Falha de parâmetro detectada e auto-corrigida com sucesso. Verificação técnica aprovada.",
                    "tool_calls": None
                }
            }]
        }


async def run_phase10_tests():
    print("=== [piDots] Teste e Validação da Fase 2: Self-Healing Harness & Two-Stage Planning ===")

    # 1. Inicialização do SQLite WAL
    print("[1/5] Inicializando banco SQLite WAL e verificando esquemas...")
    await init_edge_database()

    test_dot_id = f"dot-healer-{uuid.uuid4().hex[:6]}"
    test_thread_id = f"thread-plan-{uuid.uuid4().hex[:6]}"

    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (test_dot_id, "Self-Healing Dot", "Engenheiro de Resiliência", "Você é um assistente autônomo com auto-correção.", "test-model", "/tmp", "grok")
        )
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, ?)",
            (test_thread_id, test_dot_id, "Sessão de Planejamento")
        )
        await db.commit()
    print(f"      Dot de teste registrado: '{test_dot_id}'. Thread: '{test_thread_id}'.")

    # 2. Testando Analisador de Falhas do Self-Healing Harness
    print("[2/5] Testando analisador sintático de tracebacks e diagnóstico cirúrgico...")
    sample_traceback = (
        'Traceback (most recent call last):\n'
        '  File "/app/workspaces/app.py", line 42, in process_data\n'
        '    result = 10 / divisor\n'
        'ZeroDivisionError: division by zero\n'
    )
    analysis = SelfHealingHarness.analyze_failure(sample_traceback, exit_code=1)
    assert analysis["needs_healing"] is True, "Self-Healing não ativado para traceback."
    assert analysis["error_type"] == "ZeroDivisionError", f"Tipo de erro incorreto: {analysis['error_type']}"
    assert analysis["target_file"] == "/app/workspaces/app.py", f"Arquivo alvo incorreto: {analysis['target_file']}"
    assert analysis["target_line"] == 42, f"Linha alvo incorreta: {analysis['target_line']}"
    assert "division by zero" in analysis["error_message"]
    assert "DIRETRIZ DE AUTO-CORREÇÃO" in analysis["diagnosis"]
    print(f"      Diagnóstico extraído com precisão: {analysis['error_type']} na linha {analysis['target_line']} de '{analysis['target_file']}'.")

    # 3. Testando Ferramenta execute_and_verify com Self-Healing
    print("[3/5] Testando ferramenta 'execute_and_verify' com detecção e auto-cura...")
    # Execução com falha
    res_fail = await registry.execute_tool(
        name="execute_and_verify",
        arguments={"command": "python3 -c 'raise KeyError(\"Chave de configuracao ausente\")'"},
        dot_id=test_dot_id
    )
    assert res_fail.get("verified") is False, "Comando deveria ter sido reprovado na verificação."
    assert "self_healing_advice" in res_fail, "Conselho de auto-correção ausente no resultado da ferramenta."
    assert res_fail["self_healing_details"]["error_type"] == "KeyError"
    print("      Reprovação e conselho de auto-correção gerados com sucesso.")

    # Execução bem-sucedida
    res_ok = await registry.execute_tool(
        name="execute_and_verify",
        arguments={"command": "python3 -c 'print(\"Integridade 100%\")'"},
        dot_id=test_dot_id
    )
    assert res_ok.get("verified") is True, "Comando válido deveria ter sido aprovado."
    assert "Integridade 100%" in res_ok.get("stdout", "")
    print("      Execução aprovada na verificação com sucesso.")

    # 4. Testando Two-Stage Planning (Metas e Marcos no SQLite WAL)
    print("[4/5] Testando Two-Stage Planning (Goals, Milestones e Checkpoints no SQLite WAL)...")
    plan_milestones = [
        {"title": "Mapear schema do banco", "acceptance_criteria": "Tabelas criadas com índices"},
        {"title": "Implementar módulo de cálculo", "acceptance_criteria": "Funções passam nos testes unitários"},
        {"title": "Homologar em contêiner", "acceptance_criteria": "Build concluído e health check OK"}
    ]
    plan_res = await registry.execute_tool(
        name="plan_create",
        arguments={
            "title": "Migração de Arquitetura Edge",
            "description": "Decomposição técnica faseada para o Pi 4B.",
            "milestones": plan_milestones
        },
        dot_id=test_dot_id,
        thread_id=test_thread_id
    )
    assert plan_res.get("success") is True, f"Falha ao criar plano: {plan_res}"
    goal_id = plan_res["goal_id"]
    m_list = plan_res["milestones"]
    assert len(m_list) == 3

    # Consulta de status inicial (0.0% de progresso)
    status_0 = await registry.execute_tool(name="plan_get_status", arguments={"goal_id": goal_id})
    assert status_0["found"] is True
    assert status_0["progress_pct"] == 0.0
    assert status_0["current_milestone"]["title"] == "Mapear schema do banco"

    # Atualizando marco 1 para COMPLETED
    m1_id = m_list[0]["id"]
    upd_1 = await registry.execute_tool(
        name="plan_update_step",
        arguments={
            "milestone_id": m1_id,
            "status": "COMPLETED",
            "evidence_summary": "Schema SQLite WAL validado via sqlite3 cli."
        }
    )
    assert upd_1.get("success") is True
    assert upd_1.get("goal_completed") is False

    # Consulta de status após marco 1 (33.3% de progresso)
    status_1 = await registry.execute_tool(name="plan_get_status", arguments={"goal_id": goal_id})
    assert status_1["progress_pct"] == 33.3
    assert status_1["completed_milestones"] == 1

    # Atualizando marcos 2 e 3
    m2_id = m_list[1]["id"]
    m3_id = m_list[2]["id"]
    await registry.execute_tool(name="plan_update_step", arguments={"milestone_id": m2_id, "status": "COMPLETED", "evidence_summary": "Testes unitários 100% aprovados."})
    upd_3 = await registry.execute_tool(name="plan_update_step", arguments={"milestone_id": m3_id, "status": "COMPLETED", "evidence_summary": "Health check respondendo HTTP 200."})
    assert upd_3.get("goal_completed") is True, "Meta principal deveria ter sido marcada como concluída."

    # Status final (100.0% de progresso)
    status_final = await registry.execute_tool(name="plan_get_status", arguments={"goal_id": goal_id})
    assert status_final["progress_pct"] == 100.0
    assert status_final["status"] == "COMPLETED"
    print(f"      Plano concluído com 100% de progresso! Todos os {status_final['total_milestones']} marcos homologados.")

    # Validação do formato XML in-context
    xml_prompt = await TwoStagePlanner.format_plan_prompt(test_thread_id, test_dot_id)
    assert "<execution_plan>" in xml_prompt
    assert "<milestones>" in xml_prompt
    print("      Bloco XML de planejamento formatado corretamente para injeção in-context.")

    # 5. Testando Loop do DotAgent com Evento AG-UI 'self_healing:triggered'
    print("[5/5] Testando Loop do DotAgent com disparo de evento 'self_healing:triggered'...")
    mock_provider = MockSelfHealingAgentProvider()
    agent = DotAgent(dot_id=test_dot_id, provider=mock_provider)

    events = []
    async for ev in agent.run_thread(thread_id=test_thread_id, user_message="Execute a validação técnica de integridade."):
        events.append(ev)

    event_types = [e["event"] for e in events]
    assert "run:started" in event_types
    assert "tool:called" in event_types
    assert "tool:result" in event_types
    assert "self_healing:triggered" in event_types, "Evento 'self_healing:triggered' não foi emitido durante a falha."
    assert "run:finished" in event_types

    healing_event = next(e for e in events if e["event"] == "self_healing:triggered")
    assert healing_event["data"]["error_type"] == "ValueError"
    print(f"      Evento AG-UI 'self_healing:triggered' validado com sucesso! (Erro detectado: {healing_event['data']['error_type']}).")

    finished_event = next(e for e in events if e["event"] == "run:finished")
    assert finished_event["data"]["status"] == "completed"
    assert "auto-corrigida com sucesso" in finished_event["data"]["final_response"]
    print("      Loop de auto-correção do DotAgent concluído com sucesso e resposta final satisfatória.")

    print("\n=== [SUCESSO TOTAL] Fase 2 (Self-Healing Harness & Two-Stage Planning) Homologada com 100% de Êxito! ===")


if __name__ == "__main__":
    asyncio.run(run_phase10_tests())
