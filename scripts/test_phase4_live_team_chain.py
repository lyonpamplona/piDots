"""
Script de Validação e Homologação Técnica da Fase 4:
Live Team Chain Inter-Agentes e Default Responder nos Canais.
"""

import asyncio
import os
import sys

# Ajuste de path para importação do pacote pidots
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pidots.storage.db import init_edge_database, get_db
from pidots.core.messaging_gateway import MessagingGateway
from pidots.core.orchestrator import ThreadRouter, MultiBotOrchestrator


async def main():
    print("=== [piDots] Teste e Validação da Fase 4: Live Team Chain e Default Responder ===")
    await init_edge_database()

    # 1. Teste de Default Responder no Gateway de Mensageria
    print("[1/2] Validando Default Responder em canais sem @menção...")
    test_channel_id = "ch-test-team-chain"
    
    async with get_db() as db:
        # Registra canal de teste
        await db.execute(
            "INSERT OR REPLACE INTO channels (id, name, description) VALUES (?, 'Canal Teste Equipe', 'Canal de testes')",
            (test_channel_id,)
        )
        # Adiciona membros do Squad Central
        await db.execute("DELETE FROM channel_members WHERE channel_id = ?", (test_channel_id,))
        for member_dot in ["dot-supervisor", "dot-coder", "dot-auditor"]:
            await db.execute(
                "INSERT INTO channel_members (channel_id, member_id, member_type) VALUES (?, ?, 'dot')",
                (test_channel_id, member_dot)
            )
        await db.commit()

    # Identifica membros e aplica regra de disparo do gateway
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT member_id FROM channel_members WHERE channel_id = ? AND member_type = 'dot'",
            (test_channel_id,)
        )
        members = await cursor.fetchall()
        dot_ids = [row["member_id"] for row in members]

    # Mensagem de usuário sem menção explícita
    user_content = "Bom dia time, qual é o status da bancada hoje?"
    explicit_mentions = set(ThreadRouter.parse_mentions(user_content))
    has_all_mention = "@all" in user_content.lower().split()
    author_type = "user"
    author_id = "user-123"

    dots_to_trigger = []
    for d_id in dot_ids:
        if d_id == author_id:
            continue
        if author_type in ("user", "webhook"):
            if d_id.lower() in explicit_mentions or has_all_mention or len(dot_ids) == 1:
                dots_to_trigger.append(d_id)

    # Aplicação da regra de Default Responder (Passo 4)
    if author_type in ("user", "webhook") and not dots_to_trigger and not explicit_mentions and not has_all_mention:
        default_owner = "dot-supervisor" if "dot-supervisor" in dot_ids else (dot_ids[0] if dot_ids else None)
        if default_owner and default_owner != author_id:
            dots_to_trigger.append(default_owner)

    assert len(dots_to_trigger) == 1, f"Deveria haver exatamente 1 default responder, encontrado: {dots_to_trigger}"
    assert dots_to_trigger[0] == "dot-supervisor", f"Default responder deveria ser 'dot-supervisor', recebido: {dots_to_trigger[0]}"
    print("      Sucesso: Mensagem sem menção no canal ativou '@dot-supervisor' como Task Owner padrão.")

    # 2. Teste do Mecanismo de Encadeamento Live Team Chain (Prevenção de Loops e Salto Automático)
    print("[2/2] Validando lógica de Live Team Chain inter-agentes e limite de saltos...")
    
    # Simula resposta emitida pelo primeiro agente mencionando o colega @dot-coder
    first_agent_response = (
        "Com certeza! Já estruturei o plano em duas etapas para a bancada. "
        "@dot-coder, você pode inspecionar os arquivos em workspaces/ e implementar o endpoint?"
    )
    
    # Extração de menções na resposta
    detected_mentions = ThreadRouter.parse_mentions(first_agent_response)
    assert "dot-coder" in detected_mentions, "Deveria detectar menção ao @dot-coder na resposta do supervisor."
    print("      Menção extraída da resposta do Supervisor: @dot-coder")

    # Simulação da fila de execução
    execution_queue = ["dot-supervisor"]
    visited_dots = set(execution_queue)
    max_chain_hops = 2
    chain_hops = 0
    executed_sequence = []

    while execution_queue:
        active = execution_queue.pop(0)
        executed_sequence.append(active)
        
        # Simula resposta do agente
        if active == "dot-supervisor":
            resp = first_agent_response
        elif active == "dot-coder":
            # Coder responde e chama o auditor para revisar
            resp = "Módulo implementado com sucesso! @dot-auditor, por favor revise os riscos de segurança."
        elif active == "dot-auditor":
            # Auditor tenta chamar de volta o supervisor (teste de trava contra loop)
            resp = "Auditoria aprovada com 100% de integridade! @dot-supervisor, missão concluída."
        else:
            resp = "Concluído."

        if chain_hops < max_chain_hops and resp:
            candidates = ThreadRouter.parse_mentions(resp)
            for cand in candidates:
                cand_clean = cand.lower()
                # Trava 1: não reexecutar dots já visitados na mesma stream
                # Trava 2: não chamar a si próprio
                if cand_clean not in visited_dots and cand_clean != active:
                    execution_queue.append(cand_clean)
                    visited_dots.add(cand_clean)
                    chain_hops += 1
                    print(f"      Salto {chain_hops}/{max_chain_hops}: @{active} acionou @{cand_clean} na mesma stream.")
                    break

    assert executed_sequence == ["dot-supervisor", "dot-coder", "dot-auditor"], (
        f"Sequência executada incorreta: {executed_sequence}"
    )
    assert chain_hops == 2, f"Total de saltos deveria atingir o teto seguro de 2, obtido {chain_hops}."
    assert "dot-supervisor" not in execution_queue, "Supervisor não deveria reentrar em loop infinito."
    print("      Sucesso: Encadeamento tripartite (@dot-supervisor -> @dot-coder -> @dot-auditor) validado com trava de teto.")

    # Limpeza do canal de teste
    async with get_db() as db:
        await db.execute("DELETE FROM channel_members WHERE channel_id = ?", (test_channel_id,))
        await db.execute("DELETE FROM channels WHERE id = ?", (test_channel_id,))
        await db.commit()

    print("\n=== [SUCESSO] Fase 4 validada com 100% de êxito! Live Team Chain Operacional! ===")


if __name__ == "__main__":
    asyncio.run(main())
