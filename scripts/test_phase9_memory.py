"""
Teste e Validação da Fase 1: Memória Hierárquica Autônoma (Padrão MemGPT / Letta).
Valida Core Memory (in-context), Archival Memory (FTS5 BM25 + Projeção Vetorial 64d)
e Recall Memory (diálogo retrospectivo) no nó piDots (Raspberry Pi 4B).
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.memory_manager import MemoryManager, compute_compact_embedding, cosine_similarity
from pidots.tools.registry import registry
from pidots.core.agent import DotAgent


class MockMemoryAgentProvider:
    """Mock Provider para simular o Dot utilizando suas ferramentas de auto-edição de memória."""

    def __init__(self):
        self.call_count = 0

    async def chat_completion(self, messages, tools=None, model="default", temperature=0.2):
        self.call_count += 1
        # Primeira iteração: o modelo decide atualizar a Core Memory chamando core_memory_append
        if self.call_count == 1:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_mem_append_1",
                            "type": "function",
                            "function": {
                                "name": "core_memory_append",
                                "arguments": json.dumps({
                                    "section": "human",
                                    "content": "Operador prefere logs detalhados e respostas em pt-BR."
                                })
                            }
                        }]
                    }
                }]
            }
        # Segunda iteração: responde confirmando a atualização de memória
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Entendido. Registrei suas preferências na minha Core Memory permanente.",
                    "tool_calls": None
                }
            }]
        }


async def run_phase9_memory_tests():
    print("=== [piDots] Teste e Validação da Fase 1: Memória Hierárquica Autônoma ===")

    # 1. Inicialização do banco e tabelas FTS5
    print("[1/6] Inicializando banco SQLite WAL e migrações de memória FTS5...")
    await init_edge_database()

    test_dot_id = f"dot-mem-tester-{uuid.uuid4().hex[:6]}"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (test_dot_id, "Memory Tester", "Engenheiro Cognitivo", "Você é um assistente com auto-gestão de memória.", "qwen3.8-27b", "/tmp", "general")
        )
        await db.commit()
    print(f"      Dot de teste cadastrado: '{test_dot_id}'.")

    # 2. Testando Core Memory (Inicialização e Leitura)
    print("[2/6] Testando Core Memory: inicialização atômica e formatação XML...")
    blocks = await MemoryManager.get_core_memory_blocks(test_dot_id)
    assert "persona" in blocks, "Bloco 'persona' não encontrado."
    assert "human" in blocks, "Bloco 'human' não encontrado."
    assert "active_context" in blocks, "Bloco 'active_context' não encontrado."

    xml_prompt = await MemoryManager.format_core_memory_prompt(test_dot_id)
    assert "<core_memory>" in xml_prompt, "Tag <core_memory> ausente no prompt formatado."
    assert "<persona>" in xml_prompt and "</persona>" in xml_prompt
    assert "<human>" in xml_prompt and "</human>" in xml_prompt
    assert "<active_context>" in xml_prompt and "</active_context>" in xml_prompt
    print("      Blocos XML de Core Memory gerados com sucesso.")

    # 3. Testando Auto-Edição de Core Memory (Append e Replace)
    print("[3/6] Testando ferramentas de auto-edição de Core Memory (Append, Replace e Teto)...")
    res_app = await registry.execute_tool(
        name="core_memory_append",
        arguments={"section": "human", "content": "Preferência: Sempre usar tipagem estrita em Python."},
        dot_id=test_dot_id
    )
    assert res_app.get("success") is True, f"Falha ao executar core_memory_append: {res_app}"
    assert "Sempre usar tipagem estrita" in res_app.get("content", "")

    # Testando substituição (Replace)
    res_rep = await registry.execute_tool(
        name="core_memory_replace",
        arguments={
            "section": "human",
            "old_content": "Sempre usar tipagem estrita em Python.",
            "new_content": "Sempre usar tipagem estrita em Python e Rust."
        },
        dot_id=test_dot_id
    )
    assert res_rep.get("success") is True, f"Falha ao executar core_memory_replace: {res_rep}"
    assert "Python e Rust" in res_rep.get("content", "")

    # Testando proteção contra overflow de caracteres (> 2000 chars)
    overflow_text = "A" * 2500
    res_overflow = await registry.execute_tool(
        name="core_memory_append",
        arguments={"section": "human", "content": overflow_text},
        dot_id=test_dot_id
    )
    assert res_overflow.get("success") is False, "O sistema deveria ter bloqueado o overflow de caracteres."
    assert "Limite de capacidade atingido" in res_overflow.get("error", "")
    print("      Proteção de teto de caracteres validada: overflow bloqueado com sucesso.")

    # 4. Testando Projeção Vetorial 64d e Archival Memory (FTS5 BM25)
    print("[4/6] Testando Archival Memory duradoura (FTS5 BM25 + Projeção Vetorial 64d)...")
    v1 = compute_compact_embedding("O Raspberry Pi 4B possui 4GB de RAM e processador Cortex-A72.")
    v2 = compute_compact_embedding("Hardware de borda ARM64 com memória LPDDR4.")
    v3 = compute_compact_embedding("Receita culinária de bolo de chocolate com morango.")
    assert len(v1) == 64, f"Esperado vetor de 64 dimensões, obtido {len(v1)}"
    sim_tech = cosine_similarity(v1, v2)
    sim_diff = cosine_similarity(v1, v3)
    assert sim_tech > sim_diff, f"Similaridade semântica falhou: {sim_tech} vs {sim_diff}"

    # Inserindo memórias na Archival Memory
    doc1 = "Documentação técnica de calibração do barramento I/O para evitar desgaste prematuro do cartão MicroSD."
    doc2 = "Diretrizes de arquitetura monólito modular em Python uvloop com SQLite em modo WAL."
    doc3 = "Configuração do túnel Cloudflare Zero Trust para exposição segura da porta 8000."

    res_ins1 = await registry.execute_tool(name="archival_memory_insert", arguments={"content": doc1, "tags": ["hardware", "microsd"]}, dot_id=test_dot_id)
    res_ins2 = await registry.execute_tool(name="archival_memory_insert", arguments={"content": doc2, "tags": ["software", "sqlite"]}, dot_id=test_dot_id)
    res_ins3 = await registry.execute_tool(name="archival_memory_insert", arguments={"content": doc3, "tags": ["rede", "cloudflare"]}, dot_id=test_dot_id)
    assert res_ins1.get("success") is True and res_ins2.get("success") is True and res_ins3.get("success") is True

    # Busca híbrida FTS5 BM25
    search_res = await registry.execute_tool(name="archival_memory_search", arguments={"query": "desgaste do cartão MicroSD"}, dot_id=test_dot_id)
    assert search_res.get("count", 0) > 0, "Nenhuma memória encontrada na busca híbrida FTS5."
    top_hit = search_res["results"][0]
    assert "MicroSD" in top_hit["content"]
    assert top_hit["relevance_score"] > 0.0
    print(f"      Busca híbrida FTS5 validada com sucesso! Top hit (Score: {top_hit['relevance_score']}): '{top_hit['content'][:60]}...'")

    # 5. Testando Recall Memory (Diálogo Retrospectivo)
    print("[5/6] Testando Recall Memory (Busca retrospectiva de mensagens na thread)...")
    test_thread = f"thread-mem-{uuid.uuid4().hex[:6]}"
    async with get_db() as db:
        await db.execute("INSERT INTO threads (id, dot_id, title) VALUES (?, ?, ?)", (test_thread, test_dot_id, "Sessão de Memória"))
        await db.execute("INSERT INTO messages (id, thread_id, role, content, actor_id) VALUES (?, ?, 'user', 'Instalei o pacote uvloop no ambiente virtual.', 'user')", (str(uuid.uuid4()), test_thread))
        await db.execute("INSERT INTO messages (id, thread_id, role, content, actor_id) VALUES (?, ?, 'assistant', 'Excelente. O uvloop garante menor latência em operações assíncronas.', 'assistant')", (str(uuid.uuid4()), test_thread))
        await db.commit()

    recall_res = await registry.execute_tool(name="recall_memory_search", arguments={"query": "uvloop"}, thread_id=test_thread)
    assert recall_res.get("count", 0) == 2, f"Esperado 2 mensagens com 'uvloop', obtido {recall_res.get('count')}"
    print("      Recall Memory validada com sucesso no histórico da thread.")

    # 6. Testando Loop Cognitivo do DotAgent com Auto-Edição de Memória
    print("[6/6] Testando Loop do DotAgent executando auto-edição de memória via Function Calling...")
    mock_provider = MockMemoryAgentProvider()
    agent = DotAgent(dot_id=test_dot_id, provider=mock_provider)

    events = []
    async for event in agent.run_thread(thread_id=test_thread, user_message="Por favor, lembre-se que gosto de logs detalhados."):
        events.append(event)

    # Verifica se os eventos AG-UI foram emitidos
    event_types = [e["event"] for e in events]
    assert "run:started" in event_types
    assert "tool:called" in event_types
    assert "tool:result" in event_types
    assert "run:finished" in event_types

    # Checa se o bloco 'human' na Core Memory foi atualizado pelo Dot
    blocks_after = await MemoryManager.get_core_memory_blocks(test_dot_id)
    assert "Operador prefere logs detalhados" in blocks_after["human"], "O Dot não atualizou sua Core Memory durante o loop."
    print("      Loop do DotAgent validado: o Dot atualizou sua Core Memory de forma 100% autônoma!")

    print("\n=== [SUCESSO TOTAL] Fase 1 (Memória Hierárquica Autônoma) Homologada com 100% de Êxito! ===")


if __name__ == "__main__":
    asyncio.run(run_phase9_memory_tests())
