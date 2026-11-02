"""
Script de Validação e Homologação Técnica da Fase 1:
Fast-Path Conversacional, Poda Dinâmica Real de Ferramentas e Sanitização OpenAI.
"""

import asyncio
import json
import os
import sys

# Ajuste de path para importação do pacote pidots
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pidots.core.agent import DotAgent, ARCHETYPE_DOMAINS, DOT_ID_TO_ARCHETYPE
from pidots.tools.registry import registry
from pidots.storage.db import init_edge_database, get_db


async def main():
    print("=== [piDots] Teste e Validação da Fase 1: Fast-Path e Poda de Ferramentas ===")

    # 1. Teste de Fast-Path Conversacional
    print("[1/3] Validando heurística do Fast-Path Conversacional...")
    conversational_samples = [
        "oi",
        "olá!",
        "Olá, tudo bem?",
        "Bom dia",
        "Boa tarde equipe",
        "quem é você?",
        "O que vocês fazem?",
        "qual o seu papel aqui?",
        "Apresente-se por favor",
        "por onde começo?",
        "ajuda",
        "E aí, tudo bom?"
    ]
    for sample in conversational_samples:
        is_fast = DotAgent.is_conversational_fast_path(sample)
        assert is_fast is True, f"Falha: '{sample}' deveria ser classificado como Fast-Path."
    print("      Sucesso: Todas as 12 saudações e apresentações ativaram Fast-Path.")

    technical_samples = [
        "execute python3 script.py",
        "crie o arquivo index.html no workspace",
        "leia a url https://exemplo.com",
        "qual a temperatura da cpu e telemetria da placa?",
        "crie um plano de migracao para o banco",
        "escreva as notas no shared space",
        "rode o comando ls -la no terminal",
        "salve esta preferencia na memoria central",
        "mostre os oito processos ativos",
        "analise o log de ontem a noite",
        "verifique duas coisas no sistema",
        "preciso de apoio no deploy",
        "liste os containers em execucao"
    ]
    for sample in technical_samples:
        is_fast = DotAgent.is_conversational_fast_path(sample)
        assert is_fast is False, f"Falha: '{sample}' NÃO deveria ser classificado como Fast-Path."
    print("      Sucesso: Todos os comandos técnicos desativaram o Fast-Path para carregar ferramentas.")

    # 2. Teste da Poda Dinâmica de Ferramentas (Dynamic Tool Pruning)
    print("[2/3] Validando poda dinâmica real sem estouro de ferramentas...")
    total_system_tools = len(registry.get_tool_definitions(None))
    assert total_system_tools >= 20, f"Registro deveria conter pelo menos 20 ferramentas, encontrado {total_system_tools}."

    # Simulação dos dots principais
    test_dots = ["dot-supervisor", "dot-coder", "dot-auditor", "dot-muse", "dev-assistant"]
    for d_id in test_dots:
        arch = DOT_ID_TO_ARCHETYPE.get(d_id, "general")
        expected_tools = ARCHETYPE_DOMAINS[arch]
        tool_defs = registry.get_tool_definitions(expected_tools)
        
        # Garante que não foram injetadas todas as ferramentas
        assert len(tool_defs) < total_system_tools, f"Dot {d_id} não deveria receber todas as ferramentas."
        assert len(tool_defs) == len(expected_tools), f"Dot {d_id} deveria ter {len(expected_tools)} ferramentas."
        print(f"      Dot '@{d_id}' (arquétipo: {arch}): {len(tool_defs)} ferramentas carregadas (economia de {total_system_tools - len(tool_defs)} ferramentas).")

    # 3. Teste de Sanitização de Mensagens (Remoção de 'name' e injeção de prefixo)
    print("[3/3] Validando sanitização de mensagens para compatibilidade OpenAI...")
    await init_edge_database()
    
    agent = DotAgent(dot_id="dot-supervisor")
    thread_id = "test-phase1-sanitization"
    
    async with get_db() as db:
        # Cria thread de teste
        await db.execute(
            "INSERT OR REPLACE INTO threads (id, dot_id, title, status) VALUES (?, 'dot-supervisor', 'Teste Sanitizacao', 'idle')",
            (thread_id,)
        )
        # Limpa mensagens anteriores da thread de teste
        await db.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        # Insere mensagem de outro Dot (@dot-coder) e mensagem do usuário
        await db.execute(
            """
            INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
            VALUES ('msg-1', ?, 'assistant', 'Código refatorado com sucesso no ARM64.', 'dot-coder', 'dot', 'public')
            """,
            (thread_id,)
        )
        await db.execute(
            """
            INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
            VALUES ('msg-2', ?, 'user', 'Como ficou o resultado final?', 'user', 'user', 'public')
            """,
            (thread_id,)
        )
        await db.commit()

    dot_info, messages = await agent._load_context(thread_id, None)
    assert dot_info is not None, "dot_info não pode ser None."
    
    # Verifica que NENHUMA mensagem possui a chave 'name'
    for msg in messages:
        assert "name" not in msg, f"Mensagem não deve conter o campo 'name': {msg}"
    
    # Verifica que a mensagem de outro Dot foi prefixada com [@dot-coder]:
    coder_msg = next((m for m in messages if "Código refatorado" in m["content"]), None)
    assert coder_msg is not None, "Mensagem do @dot-coder deveria estar presente."
    assert coder_msg["content"].startswith("[@dot-coder]: "), f"Conteúdo deveria começar com prefixo [@dot-coder]: {coder_msg['content']}"

    # Limpa thread de teste
    async with get_db() as db:
        await db.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        await db.commit()

    print("      Sucesso: Todas as mensagens sanitizadas sem chave 'name' e com prefixo textual inter-agentes.")
    print("\n=== [SUCESSO] Fase 1 validada com 100% de êxito! Fast-Path e Poda Ativos! ===")


if __name__ == "__main__":
    asyncio.run(main())
