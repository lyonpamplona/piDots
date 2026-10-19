"""
Suíte de Validação e Homologação da Fase 1:
Saneamento de Backend, Contratos AG-UI e API Operacional Completa (OpenDots + CopilotKit Paradigm).
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from pidots.main import app
from pidots.storage.vector_store import VectorStore
from pidots.storage.memory_manager import compute_compact_embedding, cosine_similarity
from pidots.core.hitl import HITLManager


def run_phase1_opendots_agui_tests() -> None:
    print("=" * 80)
    print(" [piDots] Homologacao Automatizada - Fase 1 (Backend OpenDots & AG-UI Protocol)")
    print("=" * 80)

    # 1. Validar unificação do motor de embedding 64D
    print("\n--- [1/7] Validando Unificacao do Motor de Embedding 64D ---")
    sample_text = "Arquitetura de agentes autonomos em Raspberry Pi 4B com Bubblewrap"
    vec_vs = VectorStore._compute_embedding(sample_text)
    vec_mm = compute_compact_embedding(sample_text)
    assert vec_vs == vec_mm, "Divergencia entre VectorStore._compute_embedding e compute_compact_embedding!"
    assert len(vec_vs) == 64, f"Dimensao incorreta: esperado 64, obtido {len(vec_vs)}"
    sim = VectorStore.cosine_similarity(vec_vs, vec_mm)
    assert abs(sim - 1.0) < 1e-5, f"Similaridade de cosseno incorreta: {sim}"
    print("     [OK] Motor de embedding 64D unificado entre VectorStore e MemoryManager (100% identico).")

    with TestClient(app) as client:
        # 2. Validar Telemetria de Processo RSS e Rotas de Edge / Dot's Computer
        print("\n--- [2/7] Validando Telemetria RSS Real (process_rss_mb) e Dot's Computer ---")
        res_health = client.get("/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert "process_rss_mb" in health_data["memory"], "Campo process_rss_mb ausente em /health!"
        rss_val = health_data["memory"]["process_rss_mb"]
        assert isinstance(rss_val, (int, float)) and rss_val > 0
        print(f"     [OK] /health reportando RSS real do processo Python: {rss_val} MB.")

        res_trig = client.get("/api/edge/triggers")
        assert res_trig.status_code == 200
        assert "process_rss_mb" in res_trig.json()

        # Testar escrita e leitura de arquivo no Dot's Computer
        res_write = client.post("/api/edge/computer/files", json={
            "dot_id": "dot-coder",
            "filename": "fase1_computer_test.txt",
            "content": "Validacao de escrita no Computador de Borda (Takeover Mode).\nLinha 2.",
            "sync_space": True
        })
        assert res_write.status_code == 200, f"Erro em POST /api/edge/computer/files: {res_write.text}"
        write_data = res_write.json()
        assert write_data["status"] == "success"
        space_id_created = write_data.get("space_id")

        res_read = client.get("/api/edge/computer/files", params={"dot_id": "dot-coder", "filename": "fase1_computer_test.txt"})
        assert res_read.status_code == 200
        assert "Takeover Mode" in res_read.json()["content"]

        # Testar execucao no Dot's Computer
        res_exec = client.post("/api/edge/computer/exec", json={
            "dot_id": "dot-coder",
            "command": "echo 'DOT_COMPUTER_TAKEOVER_OK'",
            "timeout_seconds": 10.0
        })
        assert res_exec.status_code == 200
        assert "DOT_COMPUTER_TAKEOVER_OK" in res_exec.json().get("stdout", "")

        # Testar listagem de tool_runs e catalogo /api/tools
        res_runs = client.get("/api/edge/tool-runs", params={"dot_id": "dot-coder", "limit": 5})
        assert res_runs.status_code == 200
        assert len(res_runs.json()) >= 1

        res_tools = client.get("/api/tools")
        assert res_tools.status_code == 200
        tools_data = res_tools.json()
        assert tools_data["total"] >= 20
        print(f"     [OK] Dot's Computer (files + exec + tool-runs) e Catalogo /api/tools ({tools_data['total']} tools) validados.")

        # 3. Validar Execução Real Pós-Aprovação HITL
        print("\n--- [3/7] Validando Execucao Real Pos-Aprovacao HITL ---")
        loop = asyncio.new_event_loop()
        approval_id = loop.run_until_complete(
            HITLManager.create_approval_request(
                dot_id="dot-coder",
                thread_id="thread-hitl-exec-test",
                action_type="execute_shell_command",
                payload=json.dumps({
                    "tool": "execute_shell_command",
                    "arguments": {"command": "echo 'HITL_APPROVED_EXECUTION_SUCCESS'"}
                }),
                risk_level="HIGH"
            )
        )
        loop.close()

        res_hitl_detail = client.get(f"/api/hitl/{approval_id}")
        assert res_hitl_detail.status_code == 200
        assert res_hitl_detail.json()["status"] == "PENDING"

        res_resolve = client.post(f"/api/hitl/{approval_id}/resolve", json={
            "approved": True,
            "reviewer_notes": "Homologado no teste automatizado da Fase 1",
            "execute_action": True
        })
        assert res_resolve.status_code == 200, f"Falha ao resolver HITL: {res_resolve.text}"
        resolve_json = res_resolve.json()
        assert resolve_json["decision"] == "APPROVED"
        assert resolve_json["execution_result"] is not None
        assert resolve_json["execution_result"]["status"] == "executed"
        assert "HITL_APPROVED_EXECUTION_SUCCESS" in resolve_json["execution_result"]["result"].get("stdout", "")

        res_hitl_hist = client.get("/api/hitl/history", params={"limit": 10})
        assert res_hitl_hist.status_code == 200
        assert any(item["id"] == approval_id for item in res_hitl_hist.json())
        print("     [OK] Aprovacao HITL executou comando real no Sandbox e gravou recibo auditavel.")

        # 4. Validar CRUD Completo de Dots + Memória Core e Arquival
        print("\n--- [4/7] Validando CRUD Completo de Dots e Inspecao de Memoria ---")
        client.delete("/api/dots/dot-qa-specialist")
        res_create_dot = client.post("/api/dots", json={
            "id": "dot-qa-specialist",
            "name": "Dot QA Specialist",
            "role": "Engenheiro de Qualidade e Testes Automatizados",
            "system_prompt": "Voce e um especialista em QA e auditoria de testes.",
            "model_override": None,
            "temperature": 0.2,
            "allowed_tools": ["workspace_read_file", "workspace_list_files", "execute_shell_command"]
        })
        assert res_create_dot.status_code == 200, f"Erro ao criar Dot: {res_create_dot.text}"
        assert res_create_dot.json()["id"] == "dot-qa-specialist"

        res_get_dot = client.get("/api/dots/dot-qa-specialist")
        assert res_get_dot.status_code == 200
        assert res_get_dot.json()["name"] == "Dot QA Specialist"

        res_upd_dot = client.put("/api/dots/dot-qa-specialist", json={
            "role": "Arquiteto Senior de QA",
            "temperature": 0.1
        })
        assert res_upd_dot.status_code == 200
        assert res_upd_dot.json()["role"] == "Arquiteto Senior de QA"

        # Testar memoria Core e Archival do Dot
        res_mem_put = client.put("/api/dots/dot-qa-specialist/memory/persona", json={
            "content": "Especialista em testes deterministas para ARM64."
        })
        assert res_mem_put.status_code == 200

        res_arch_post = client.post("/api/dots/dot-qa-specialist/memory/archival", json={
            "content": "Fato arquival: Sempre validar consumo de RAM abaixo de 50MB no Raspberry Pi 4B.",
            "tags": ["qa", "arm64"]
        })
        assert res_arch_post.status_code == 200

        res_mem_get = client.get("/api/dots/dot-qa-specialist/memory")
        assert res_mem_get.status_code == 200
        mem_payload = res_mem_get.json()
        assert "ARM64" in mem_payload["core_memory"].get("persona", "")
        assert len(mem_payload["archival_memories"]) >= 1
        arch_id = mem_payload["archival_memories"][0]["id"]

        res_mem_search = client.get("/api/dots/dot-qa-specialist/memory/search", params={"query": "consumo de RAM Raspberry"})
        assert res_mem_search.status_code == 200
        search_items = res_mem_search.json()
        if isinstance(search_items, dict):
            search_items = search_items.get("results", [])
        assert len(search_items) >= 1

        res_arch_del = client.delete(f"/api/dots/dot-qa-specialist/memory/archival/{arch_id}")
        assert res_arch_del.status_code == 200

        # Protecao contra delecao de Dot core
        res_del_core = client.delete("/api/dots/dot-supervisor")
        assert res_del_core.status_code == 400

        # Delecao de Dot customizado
        res_del_custom = client.delete("/api/dots/dot-qa-specialist")
        assert res_del_custom.status_code == 200
        print("     [OK] CRUD de Dots, protecao de core Dots e gerenciamento de memoria Core/Archival validados.")

        # 5. Validar Threads, CoAgents Shared State e Save Conversation as Space
        print("\n--- [5/7] Validando Threads, CoAgents Shared State e Save-as-Space ---")
        res_th = client.post("/api/threads", json={
            "dot_id": "dot-coder",
            "title": "Sessao de Arquitetura OpenDots"
        })
        assert res_th.status_code == 200
        th_id = res_th.json()["id"]

        res_th_list = client.get("/api/threads", params={"dot_id": "dot-coder"})
        assert res_th_list.status_code == 200
        assert any(t["id"] == th_id for t in res_th_list.json())

        # Handoff na thread
        res_handoff = client.post(f"/api/threads/{th_id}/handoff", json={
            "target_dot_id": "dot-auditor",
            "reason": "Revisao de topologia de microsservicos",
            "context_summary": "Definicao inicial de contratos REST concluida."
        })
        assert res_handoff.status_code == 200, f"Erro no handoff: {res_handoff.text}"

        # Estado consolidado CoAgents
        res_state = client.get(f"/api/threads/{th_id}/state")
        assert res_state.status_code == 200
        state_data = res_state.json()
        assert state_data["thread"]["id"] == th_id
        assert state_data["thread"]["active_dot_id"] == "dot-auditor"
        assert "pending_hitl" in state_data
        assert "recent_tool_runs" in state_data

        # Save conversation as Space
        res_save_space = client.post(f"/api/threads/{th_id}/save-as-space", json={
            "title": "Ata de Arquitetura OpenDots",
            "filename": "ata_arquitetura_opendots.md"
        })
        assert res_save_space.status_code == 200
        saved_space_id = res_save_space.json()["space"]["space_id"]

        # Limpeza da thread e dos spaces de teste
        res_del_th = client.delete(f"/api/threads/{th_id}")
        assert res_del_th.status_code == 200
        if saved_space_id:
            client.delete(f"/api/spaces/{saved_space_id}")
        if space_id_created:
            client.delete(f"/api/spaces/{space_id_created}")
        print("     [OK] Ciclo de Threads, Handoff, CoAgents Shared State (/state) e Save-as-Space homologados.")

        # 6. Validar Tasks Agendadas (Create, Patch, Run Now, Delete)
        print("\n--- [6/7] Validando Ciclo Completo de Tasks Agendadas ---")
        res_task_create = client.post("/api/tasks", json={
            "dot_id": "dot-supervisor",
            "task_name": "Verificacao Termica de Teste",
            "cron_expr": "*/30 * * * *",
            "action_prompt": "Verifique a temperatura do SoC."
        })
        assert res_task_create.status_code == 200, f"Erro em POST /api/tasks: {res_task_create.text}"
        task_id = res_task_create.json()["id"]

        res_task_patch = client.patch(f"/api/tasks/{task_id}", json={
            "is_active": False,
            "cron_expr": "0 * * * *"
        })
        assert res_task_patch.status_code == 200
        assert res_task_patch.json()["is_active"] is False

        res_task_del = client.delete(f"/api/tasks/{task_id}")
        assert res_task_del.status_code == 200
        assert res_task_del.json()["status"] == "deleted"
        print("     [OK] Criacao, atualizacao/pausa (PATCH) e exclusao (DELETE) de Tasks validados.")

        # 7. Validar Rotas MCP e Diagnóstico de Provedor
        print("\n--- [7/7] Validando Endpoints MCP Servers e Diagnostico de Provedor ---")
        res_mcp = client.get("/api/mcp/servers")
        assert res_mcp.status_code == 200
        assert "servers" in res_mcp.json()

        res_test_prov = client.post("/api/edge/settings/test-provider")
        assert res_test_prov.status_code == 200
        assert "circuit_state" in res_test_prov.json()
        print("     [OK] Endpoints /api/mcp/servers e /api/edge/settings/test-provider validados.")

    print("\n" + "=" * 80)
    print(" [SUCESSO TOTAL] Fase 1 concluida e homologada com 100% de exito!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase1_opendots_agui_tests()
