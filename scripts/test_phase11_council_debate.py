"""
Teste e Validação da Fase 3: Conselho Consultivo e Debate Multi-Agente (Dialética Multi-Bot).
Homologa a orquestração tripartite entre Propositor (@coder), Auditor Crítico (@auditor)
e Supervisor (@supervisor) com consenso técnico no nó piDots (Raspberry Pi 4B).
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timezone

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.council import CouncilOrchestrator
from pidots.tools.registry import registry
from pidots.core.agent import DotAgent


class MockCouncilProvider:
    """Mock Provider para simular intervenções especializadas no conselho consultivo."""

    def __init__(self):
        self.call_count = 0

    async def chat_completion(self, messages, tools=None, model="default", temperature=0.2):
        self.call_count += 1
        last_content = messages[-1].get("content", "")

        # Resposta do Propositor
        if "SOLICITAÇÃO DE PROPOSTA" in last_content or "RÉPLICA DO PROPOSITOR" in last_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Proponho implementar cache in-memory em dicionário Python com política LRU para até 200 entradas com chave hash SHA-256."
                    }
                }]
            }

        # Resposta do Crítico / Auditor
        if "AUDITORIA CRÍTICA" in last_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "AUDITORIA: Risco de vazamento de memória se as entradas forem grandes. No Raspberry Pi 4B com 4GB, recomendo teto máximo de 50 entradas e validação de tamanho individual < 64KB."
                    }
                }]
            }

        # Resposta do Supervisor / Deliberador
        if "DELIBERAÇÃO FINAL" in last_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "VEREDITO DO CONSELHO: Proposta do @coder aprovada com a incorporação integral das restrições do @auditor (teto de 50 entradas e 64KB por item). O plano de ação está homologado."
                    }
                }]
            }

        # Resposta genérica
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Intervenção registrada com sucesso no conselho."
                }
            }]
        }


def get_rss_memory_mb() -> float:
    """Mede a memória RSS real do processo."""
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
    except Exception:
        return 0.0


async def run_phase11_tests():
    print("=== [piDots] Teste e Validação da Fase 3: Conselho Consultivo Multi-Bot ===")

    # 1. Inicialização do banco e cadastro de arquétipos
    print("[1/5] Inicializando banco SQLite WAL e cadastrando Dots do conselho...")
    await init_edge_database()

    coder_id = f"dot-coder-{uuid.uuid4().hex[:4]}"
    auditor_id = f"dot-auditor-{uuid.uuid4().hex[:4]}"
    supervisor_id = f"dot-supervisor-{uuid.uuid4().hex[:4]}"
    test_thread = f"thread-council-{uuid.uuid4().hex[:6]}"

    async with get_db() as db:
        # Cadastra Propositor (Grok/Coder)
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, 'Dot Coder', 'Engenheiro de Software', 'Você propõe arquiteturas e códigos.', 'mock-model', '/tmp', 'grok')
            """,
            (coder_id,)
        )
        # Cadastra Auditor Crítico
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, 'Dot Auditor', 'Auditor de Segurança e Borda', 'Você busca vulnerabilidades e falhas.', 'mock-model', '/tmp', 'general')
            """,
            (auditor_id,)
        )
        # Cadastra Supervisor Geral
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, 'Dot Supervisor', 'Coordenador Executivo', 'Você delibera e emite sínteses finais.', 'mock-model', '/tmp', 'general')
            """,
            (supervisor_id,)
        )
        # Cria thread de deliberação
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, 'Sessão do Conselho Consultivo')",
            (test_thread, supervisor_id)
        )
        await db.commit()

    print(f"      Dots registrados: @{coder_id} (Propositor), @{auditor_id} (Auditor), @{supervisor_id} (Supervisor).")

    # 2. Testando Execução Direta do Conselho (CouncilOrchestrator.run_debate)
    print("[2/5] Executando ciclo de deliberação tripartite com Mock Provider...")
    mem_before = get_rss_memory_mb()
    mock_provider = MockCouncilProvider()

    debate_res = await CouncilOrchestrator.run_debate(
        thread_id=test_thread,
        topic="Estratégia de Cache em Memória para Redução de Escrita em Disco MicroSD",
        proponent_dot_id=coder_id,
        critic_dot_id=auditor_id,
        supervisor_dot_id=supervisor_id,
        rounds=1,
        provider=mock_provider
    )

    mem_after = get_rss_memory_mb()
    assert debate_res["success"] is True, f"Falha na execução do debate: {debate_res}"
    assert "teto de 50 entradas" in debate_res["supervisor_verdict"]
    assert "LRU" in debate_res["proponent_output"]
    assert "Risco de vazamento" in debate_res["critic_output"]
    print("      Debate concluído: Proposta, Auditoria e Veredito gerados com êxito.")

    # 3. Verificando Isolamento e Persistência no SQLite WAL
    print("[3/5] Verificando isolamento de mensagens (Fitas Internas vs Resolução Pública)...")
    async with get_db() as db:
        # Verifica handoff
        cursor = await db.execute("SELECT * FROM agent_handoffs WHERE id = ?", (debate_res["handoff_id"],))
        h_row = await cursor.fetchone()
        assert h_row is not None, "Registro em agent_handoffs não encontrado."
        assert h_row["handoff_type"] == "council_debate"
        assert h_row["status"] == "COMPLETED"

        # Verifica mensagens na thread principal
        cursor = await db.execute("SELECT role, visibility, actor_id, content FROM messages WHERE thread_id = ? ORDER BY created_at ASC", (test_thread,))
        messages = await cursor.fetchall()

    # Deve haver pelo menos 2 mensagens internas (proposta e crítica) e 1 mensagem pública (resolução do supervisor)
    internal_msgs = [m for m in messages if m["visibility"] == "internal"]
    public_msgs = [m for m in messages if m["visibility"] == "public"]

    assert len(internal_msgs) >= 2, f"Esperado ao menos 2 mensagens internas, obtido {len(internal_msgs)}"
    assert len(public_msgs) >= 1, f"Esperado ao menos 1 mensagem pública, obtido {len(public_msgs)}"

    pub_msg = public_msgs[-1]
    assert "[CONSELHO CONSULTIVO - RESOLUÇÃO FINAL]" in pub_msg["content"]
    assert pub_msg["actor_id"] == supervisor_id
    print(f"      Persistência validada: {len(internal_msgs)} fitas internas e 1 resolução executiva pública persistidas no SQLite WAL.")

    # 4. Testando Invocação via Ferramenta (registry.execute_tool)
    print("[4/5] Testando execução do conselho via ferramenta nativa 'run_council_debate'...")
    tool_res = await registry.execute_tool(
        name="run_council_debate",
        arguments={
            "topic": "Políticas de Checkpoint WAL de SQLite para Preservação de Flash MicroSD",
            "proponent_dot_id": coder_id,
            "critic_dot_id": auditor_id,
            "supervisor_dot_id": supervisor_id,
            "rounds": 1
        },
        thread_id=test_thread,
        provider=mock_provider
    )
    assert tool_res.get("success") is True, f"Falha ao executar ferramenta: {tool_res}"
    assert "public_resolution" in tool_res
    print("      Ferramenta 'run_council_debate' executada e integrada ao ToolRegistry com sucesso.")

    # 5. Testando Trava de Limite de Rodadas e Telemetria de Memória
    print("[5/5] Testando trava de segurança para limite de rodadas (Max Rounds = 3)...")
    tool_res_capped = await registry.execute_tool(
        name="run_council_debate",
        arguments={
            "topic": "Dimensionamento de Threads e uvloop",
            "proponent_dot_id": coder_id,
            "critic_dot_id": auditor_id,
            "supervisor_dot_id": supervisor_id,
            "rounds": 10  # Deve ser limitado a 3
        },
        thread_id=test_thread,
        provider=mock_provider
    )
    assert tool_res_capped.get("rounds_executed") == 3, f"Esperado teto de 3 rodadas, obtido {tool_res_capped.get('rounds_executed')}"
    print(f"      Trava de segurança validada: solicitação de 10 rodadas limitada ao teto seguro de 3 rodadas.")
    print(f"      Aferição de Memória RAM: RSS Final = {mem_after:.2f} MB (Delta: {mem_after - mem_before:.2f} MB).")

    print("\n=== [SUCESSO TOTAL] Fase 3 (Conselho Consultivo Multi-Bot) Homologada com 100% de Êxito! ===")


if __name__ == "__main__":
    asyncio.run(run_phase11_tests())
