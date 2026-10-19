"""
Script de Homologação Automatizada - Fase 3 do Roadmap piDots
Ajustes e Melhorias em Módulos Existentes (Enhancements):
1. Governança HITL com Expiração (TTL de 30 min) e Push Instantâneo
2. Teto de Tentativas no Self-Healing (MAX_HEAL_ATTEMPTS = 2) e Escalonamento para @dot-auditor
3. Saída Antecipada por Consenso no Conselho (Early Consensus Exit)
4. Deduplicação Semântica na Memória Arquival (FTS5 BM25 + Projeção Vetorial 64d)
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Garante import do pacote pidots
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.hitl import HITLManager
from pidots.core.self_healing import SelfHealingHarness, MAX_HEAL_ATTEMPTS
from pidots.core.council import CouncilOrchestrator
from pidots.storage.memory_manager import MemoryManager


class MockConsensusProvider:
    """Provedor mock calibrado para testar Early Consensus Exit no Conselho tripartite."""
    def __init__(self):
        self.call_count = 0

    async def chat_completion(self, messages, tools=None, model=None):
        self.call_count += 1
        prompt_content = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                prompt_content = m.get("content", "")
                break

        if "SOLICITAÇÃO DE PROPOSTA" in prompt_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Proposta Técnica: Implementar cache L1 em memória RAM com expiração LRU de 64 entradas."
                    }
                }]
            }
        elif "AUDITORIA CRÍTICA" in prompt_content and "TRÉPLICA" not in prompt_content:
            # Primeira rodada: aponta pequenas ressalvas
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Auditoria: Proposta interessante, porém requer atenção ao footprint no Raspberry Pi 4B. RISK_HIGH / NEEDS_CHANGES."
                    }
                }]
            }
        elif "RÉPLICA DO PROPOSITOR" in prompt_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Réplica: Adicionado teto de 8MB para o cache L1 garantindo segurança em hardware restrito."
                    }
                }]
            }
        elif "TRÉPLICA DO AUDITOR CRÍTICO" in prompt_content:
            # Segunda rodada: aprova com RISK_LOW / APPROVED
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Tréplica de Auditoria: Os ajustes atendem plenamente aos critérios de borda. Parecer final: RISK_LOW / APPROVED."
                    }
                }]
            }
        elif "DELIBERAÇÃO FINAL" in prompt_content:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Resolução do Supervisor: Proposta aprovada por consenso antecipado entre Coder e Auditor."
                    }
                }]
            }
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Deliberação nominal concluída."
                }
            }]
        }


async def test_hitl_ttl_and_expiration():
    print("\n--- [TESTE 1] Governança HITL: TTL de 30 min e Expiração Automática ---")
    
    thread_id = f"test-thread-hitl-{uuid.uuid4().hex[:8]}"
    dot_id = "dot-auditor"

    async with get_db() as db:
        await db.execute(
            "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, 'Thread Teste HITL', 'awaiting_hitl')",
            (thread_id, dot_id)
        )
        await db.commit()

    # 1. Cria solicitação HITL com TTL
    approval_id = await HITLManager.create_approval_request(
        dot_id=dot_id,
        thread_id=thread_id,
        action_type="shell_exec",
        payload='{"command": "rm -rf /tmp/test"}',
        risk_level="CRITICAL",
        ttl_minutes=30
    )
    assert approval_id, "Falha ao criar solicitação HITL"

    # Verifica se expires_at foi persistido
    async with get_db() as db:
        cursor = await db.execute("SELECT expires_at, status FROM hitl_approvals WHERE id = ?", (approval_id,))
        row = await cursor.fetchone()
        assert row is not None, "Registro HITL não encontrado"
        assert row["expires_at"] is not None, "Campo expires_at está nulo"
        assert row["status"] == "PENDING", f"Status inicial incorreto: {row['status']}"
        print(f"OK: Solicitação criada [{approval_id[:8]}...] com expires_at: {row['expires_at']}")

    # 2. Simula passagem do tempo (força expires_at para 10 minutos no passado)
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    async with get_db() as db:
        await db.execute("UPDATE hitl_approvals SET expires_at = ? WHERE id = ?", (past_iso, approval_id))
        await db.commit()

    # 3. Executa varredura de expiração
    expired_ids = await HITLManager.expire_stale_approvals()
    assert approval_id in expired_ids, f"Solicitação {approval_id} deveria ter expirado"

    # 4. Verifica status final no SQLite WAL
    async with get_db() as db:
        cursor = await db.execute("SELECT status, reviewer_notes, resolved_at FROM hitl_approvals WHERE id = ?", (approval_id,))
        row = await cursor.fetchone()
        assert row["status"] == "EXPIRED", f"Status deveria ser EXPIRED, obtido: {row['status']}"
        assert "30 minutos" in row["reviewer_notes"], "Nota de expiração não registrada"
        assert row["resolved_at"] is not None, "resolved_at não preenchido na expiração"

        # Verifica se thread foi liberada para idle
        cursor_th = await db.execute("SELECT status FROM threads WHERE id = ?", (thread_id,))
        th_row = await cursor_th.fetchone()
        assert th_row["status"] == "idle", f"Status da thread deveria voltar para idle, obtido: {th_row['status']}"

        # Verifica mensagem de auditoria gravada
        cursor_msg = await db.execute("SELECT content FROM messages WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1", (thread_id,))
        msg_row = await cursor_msg.fetchone()
        assert msg_row and "ACAO EXPIRADA" in msg_row["content"], "Mensagem de expiração não persistida na thread"

    print("OK: Expiração HITL validada com liberação da thread e trilha de auditoria.")


async def test_self_healing_ceiling():
    print("\n--- [TESTE 2] Self-Healing: Teto Estrito de Tentativas (MAX_HEAL_ATTEMPTS = 2) ---")
    
    assert MAX_HEAL_ATTEMPTS == 2, f"MAX_HEAL_ATTEMPTS deveria ser 2, encontrado: {MAX_HEAL_ATTEMPTS}"

    SelfHealingHarness.reset_attempts()

    fail_output = {
        "exit_code": 1,
        "stdout": "",
        "stderr": 'Traceback (most recent call last):\n  File "worker.py", line 42, in process\nZeroDivisionError: division by zero'
    }

    # Tentativa 1
    t1 = SelfHealingHarness.inspect_execution_result(
        tool_name="execute_and_verify",
        tool_args={"command": "python3 worker.py"},
        tool_result=fail_output,
        context_key="test-ctx-step1"
    )
    assert t1 is not None, "Diagnóstico da tentativa 1 deveria existir"
    assert t1["needs_healing"] is True
    assert t1["attempt"] == 1
    assert t1["max_attempts_exceeded"] is False
    assert t1["escalate_to"] is None
    assert "Tentativa 1/2" in t1["diagnosis"]
    print(f"OK: Tentativa 1 diagnosticada: attempt={t1['attempt']}, max_exceeded={t1['max_attempts_exceeded']}")

    # Tentativa 2
    t2 = SelfHealingHarness.inspect_execution_result(
        tool_name="execute_and_verify",
        tool_args={"command": "python3 worker.py"},
        tool_result=fail_output,
        context_key="test-ctx-step1"
    )
    assert t2 is not None, "Diagnóstico da tentativa 2 deveria existir"
    assert t2["attempt"] == 2
    assert t2["max_attempts_exceeded"] is True, "max_attempts_exceeded deveria ser True na 2ª tentativa"
    assert t2["escalate_to"] == "@dot-auditor", f"Escalonamento esperado para @dot-auditor, obtido: {t2['escalate_to']}"
    assert "TETO DE AUTO-CURA ATINGIDO" in t2["diagnosis"], "Aviso de teto atingido ausente no diagnóstico"
    print(f"OK: Tentativa 2 bloqueada no teto: attempt={t2['attempt']}, max_exceeded={t2['max_attempts_exceeded']}, escalate_to={t2['escalate_to']}")

    # Tentativa 3 (se chamada novamente, mantém bloqueio)
    t3 = SelfHealingHarness.inspect_execution_result(
        tool_name="execute_and_verify",
        tool_args={"command": "python3 worker.py"},
        tool_result=fail_output,
        context_key="test-ctx-step1"
    )
    assert t3["max_attempts_exceeded"] is True
    print("OK: Teto de reparo impediu loop infinito e escalou para @dot-auditor.")


async def test_council_early_consensus_exit():
    print("\n--- [TESTE 3] Conselho Consultivo: Early Consensus Exit na Rodada 2 ---")
    
    mock_provider = MockConsensusProvider()
    thread_id = f"test-council-early-{uuid.uuid4().hex[:8]}"

    # Solicita 3 rodadas no debate, mas com aprovação na rodada 2 deve sair antecipadamente
    result = await CouncilOrchestrator.run_debate(
        thread_id=thread_id,
        topic="Arquitetura de Cache L1 para Single Board Computer",
        proponent_dot_id="dot-coder",
        critic_dot_id="dot-auditor",
        supervisor_dot_id="dot-supervisor",
        rounds=3,
        provider=mock_provider
    )

    assert result["success"] is True, f"Conselho falhou: {result.get('error')}"
    assert result["early_consensus"] is True, "early_consensus deveria ser True"
    assert result["rounds_executed"] == 2, f"Deveria ter executado 2 rodadas, executou: {result['rounds_executed']}"
    assert "consenso antecipado" in result["supervisor_verdict"].lower() or "resolução" in result["public_resolution"].lower()
    print(f"OK: Conselho finalizado com Early Consensus Exit: rounds={result['rounds_executed']}/3, early_consensus={result['early_consensus']}")


async def test_archival_semantic_deduplication():
    print("\n--- [TESTE 4] Memória Arquival: Deduplicação Semântica (> 0.92) ---")
    
    dot_id = f"test-dot-dedup-{uuid.uuid4().hex[:6]}"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
            VALUES (?, 'Dot Dedup', 'Tester', 'Prompt de teste', 'test-model', 'workspaces/test')
            """,
            (dot_id,)
        )
        await db.commit()

    fact_text = "O Raspberry Pi 4B possui processador Broadcom BCM2711 quad-core Cortex-A72 ARMv8 de 64 bits operando a 1.5GHz."
    
    # 1. Inserção inicial
    res1 = await MemoryManager.insert_archival_memory(
        dot_id=dot_id,
        content=fact_text,
        tags=["hardware", "cpu", "arm64"]
    )
    assert res1["success"] is True
    assert res1["deduplicated"] is False
    mem_id = res1["id"]
    print(f"OK: Memória base inserida: ID {mem_id[:8]}... (tags={res1['tags']})")

    # 2. Inserção de memória quase idêntica com tags complementares
    equivalent_fact = "O Raspberry Pi 4B possui processador Broadcom BCM2711 quad-core Cortex-A72 ARMv8 de 64 bits operando em 1.5GHz com hardware de borda."
    res2 = await MemoryManager.insert_archival_memory(
        dot_id=dot_id,
        content=equivalent_fact,
        tags=["raspberry_pi", "bcm2711", "edge"]
    )
    assert res2["success"] is True
    assert res2["deduplicated"] is True, "Deveria ter identificado alta similaridade semântica e deduplicado"
    assert res2["id"] == mem_id, f"ID deveria ser o mesmo registro unificado ({mem_id}), obtido: {res2['id']}"
    assert "hardware" in res2["tags"] and "bcm2711" in res2["tags"], "Tags deveriam ter sido mescladas"
    print(f"OK: Deduplicação semântica executou merge/update (Similaridade: {res2.get('similarity')}, Tags unificadas: {res2['tags']})")

    # 3. Valida no SQLite WAL que existe APENAS 1 registro na tabela e no FTS5
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as total FROM archival_memories WHERE dot_id = ?", (dot_id,))
        count_row = await cursor.fetchone()
        assert count_row["total"] == 1, f"Tabela archival_memories deveria ter exatamente 1 registro, tem: {count_row['total']}"

        # Valida que busca FTS5 encontra o conteúdo atualizado
        search_results = await MemoryManager.search_archival_memory(
            dot_id=dot_id,
            query="Broadcom BCM2711 Cortex-A72"
        )
        assert len(search_results) == 1, f"Busca deveria retornar 1 registro, retornou: {len(search_results)}"
        assert search_results[0]["id"] == mem_id
        print(f"OK: Integridade relacional comprovada no SQLite WAL e índice FTS5 (1 linha única).")


async def main():
    print("================================================================================")
    print("INICIANDO SUÍTE DE HOMOLOGAÇÃO: FASE 3 ROADMAP (ENHANCEMENTS & RESILIENCE)")
    print("================================================================================")
    
    await init_edge_database()

    await test_hitl_ttl_and_expiration()
    await test_self_healing_ceiling()
    await test_council_early_consensus_exit()
    await test_archival_semantic_deduplication()

    print("\n================================================================================")
    print("HOMOLOGAÇÃO DA FASE 3 CONCLUÍDA COM 100% DE ÊXITO: TODOS OS 4 TESTES APROVADOS")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(main())
