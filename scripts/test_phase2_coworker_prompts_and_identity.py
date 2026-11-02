"""
Script de Validação e Homologação Técnica da Fase 2:
Reformulação dos System Prompts para o Padrão Coworker / AI Teammate (OpenBot).
"""

import asyncio
import os
import sys

# Ajuste de path para importação do pacote pidots
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pidots.core.agent import DotAgent
from pidots.storage.db import init_edge_database, get_db


async def main():
    print("=== [piDots] Teste e Validação da Fase 2: Padrão Coworker / AI Teammate ===")

    # 1. Executa inicialização e migrações idempotentes do SQLite
    print("[1/3] Executando inicialização do banco SQLite WAL com novas personas...")
    await init_edge_database()

    # 2. Inspeciona o banco de dados para verificar os Core Dots
    print("[2/3] Validando atualização dos perfis do Core Squad no SQLite...")
    async with get_db() as db:
        cursor = await db.execute("SELECT id, name, role, system_prompt FROM dots WHERE is_core = 1")
        core_dots = {row["id"]: dict(row) for row in await cursor.fetchall()}

    expected_dots = ["dot-supervisor", "dev-assistant", "dot-coder", "dot-muse", "dot-auditor", "dot-dev-core"]
    for d_id in expected_dots:
        assert d_id in core_dots, f"Dot core '{d_id}' não encontrado no banco."
        dot = core_dots[d_id]
        prompt = dot["system_prompt"]
        role = dot["role"]
        assert len(prompt) > 80, f"Prompt do Dot '{d_id}' muito curto ou vazio."
        print(f"      Dot '@{d_id}' ({role}): Prompt validado ({len(prompt)} caracteres).")

    # Validações semânticas específicas
    sup_prompt = core_dots["dot-supervisor"]["system_prompt"]
    assert "Ada" in sup_prompt or "líder de bancada" in sup_prompt, "Prompt do Supervisor deve conter tom de liderança e acolhimento."
    assert "boas-vindas" in sup_prompt, "Prompt do Supervisor deve orientar boas-vindas."

    coder_prompt = core_dots["dot-coder"]["system_prompt"]
    assert "Linus" in coder_prompt or "mão na massa" in coder_prompt, "Prompt do Coder deve refletir persona prática de software."
    assert "@dot-auditor" in coder_prompt, "Prompt do Coder deve incentivar revisão com o auditor."

    auditor_prompt = core_dots["dot-auditor"]["system_prompt"]
    assert "Grace" in auditor_prompt or "saúde de hardware" in auditor_prompt, "Prompt do Auditor deve focar em silício e segurança."

    muse_prompt = core_dots["dot-muse"]["system_prompt"]
    assert "artesão de software" in muse_prompt, "Prompt do Muse deve refletir voz de artesão."

    # 3. Teste da Injeção de Contexto em DotAgent._load_context
    print("[3/3] Validando injeção das Diretrizes de Coworker no contexto do agente...")
    thread_id = "test-phase2-coworker-context"
    agent = DotAgent(dot_id="dot-supervisor")

    dot_info, messages = await agent._load_context(thread_id=thread_id, user_message="Oi equipe!")
    assert dot_info is not None, "dot_info não pode ser nulo."
    assert len(messages) >= 1, "Deve haver pelo menos a mensagem de system no contexto."

    system_msg = messages[0]["content"]
    assert "COMO INTERAGIR COM O OPERADOR E COM A EQUIPE (PADRÃO COWORKER):" in system_msg, "Bloco padrão Coworker ausente no system prompt."
    assert "CONVERSA NATURAL" in system_msg, "Diretriz de Conversa Natural ausente."
    assert "TRABALHO EM EQUIPE VISÍVEL" in system_msg, "Diretriz de Trabalho em Equipe ausente."
    assert "NÃO chame ferramentas de planejamento ('plan_create')" in system_msg, "Diretriz anti-burocracia em saudações ausente."

    # Limpeza da thread de teste
    async with get_db() as db:
        await db.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        await db.commit()

    print("      Sucesso: Todas as diretrizes operacionais de Coworker injetadas com fidelidade.")
    print("\n=== [SUCESSO] Fase 2 validada com 100% de êxito! Personas e Diretrizes Ativas! ===")


if __name__ == "__main__":
    asyncio.run(main())
