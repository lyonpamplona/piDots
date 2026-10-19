"""
Script de Validação e Teste da Fase 4: Gateway de Mensageria e Canais Temáticos.
Valida:
1. Normalização de webhooks (Genérico, Telegram, WhatsApp).
2. Criação e membresia de canais temáticos (#devops, #pesquisa).
3. Roteamento colaborativo com trava anti-recursão (hop_count <= 3).
4. Telemetria de memória RAM em Linux ARM64.
Regra estrita: ZERO EMOJIS.
"""

import asyncio
import os
import sys
import uuid
import httpx

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.messaging_gateway import MessagingGateway, ChannelOrchestrator, UnifiedIncomingMessage
from pidots.main import app


class MockMessagingProvider:
    """Provedor mock determinístico para simular respostas em canais e webhooks."""

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str = "default",
        temperature: float = 0.2
    ) -> dict:
        last_msg = messages[-1].get("content", "")

        if "CPU alta" in last_msg:
            answer = "Notificação de CPU alta registrada. Recomendo investigar processos zumbis."
        elif "status da memoria" in last_msg.lower():
            answer = "Memoria RAM utilizada: 78.4 MB de 3.8 GB disponiveis no Raspberry Pi 4B."
        elif "status do sistema" in last_msg.lower():
            answer = "Sistema operacional saudavel. Temperatura do SoC: 44.2C."
        elif "verificar os servicos" in last_msg.lower():
            answer = "Servicos edge inspecionados: SQLite WAL ativo, HTTP worker ok."
        elif "NO_ACTION" in last_msg:
            answer = "NO_ACTION"
        else:
            answer = "Comando processado com sucesso pelo agente."

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": answer,
                    "tool_calls": None
                }
            }]
        }


def get_current_memory_mb() -> float:
    """Mede o consumo real de memória RSS do processo via /proc/self/status."""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return round(float(line.split()[1]) / 1024.0, 2)
    except Exception:
        pass
    return 0.0


async def run_phase8_tests():
    print("[TESTE FASE 4] Iniciando bateria de validacao de Mensageria e Canais...")
    mem_start = get_current_memory_mb()
    print(f"[TELEMETRIA] Memoria RSS inicial do processo: {mem_start} MB")

    # 1. Inicializa o banco de dados e migrações
    await init_edge_database()

    # Configura state da aplicação com o mock provider
    app.state.http_client = httpx.AsyncClient()
    app.state.ai_provider = MockMessagingProvider()

    # Cria Dot de teste
    test_dot_id = "bot_tester_msg"
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, archetype, avatar_stamp, system_prompt, model, workspace_path, is_active)
            VALUES (?, 'Dot Mensageiro', 'Operador de Integracoes', 'general', '[MSG]', 'Voce e um assistente de teste.', 'test-model', 'data/workspaces/bot_tester_msg', 1)
            """,
            (test_dot_id,)
        )
        await db.commit()

    # 2. Testa o cliente HTTP da aplicação FastAPI via httpx.AsyncClient ASGITransport
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # A. Teste do Webhook Genérico Universal
        print("[TESTE 1/6] Disparando webhook generico incoming...")
        payload_generic = {
            "text": "Alerta de CPU alta no servidor edge-01",
            "sender_name": "Prometheus Alerter",
            "sender_id": "prom-edge-01",
            "reply_target_id": "alert-channel"
        }
        resp = await client.post(f"/api/webhooks/incoming/{test_dot_id}", json=payload_generic)
        assert resp.status_code == 200, f"Falha no webhook generico: {resp.text}"
        data = resp.json()
        assert data["status"] == "success"
        assert "response" in data
        assert "CPU alta registrada" in data["response"]
        print(f"[OK] Webhook generico processado: '{data['response'][:60]}...'")

        # B. Teste do Webhook Telegram
        print("[TESTE 2/6] Disparando webhook Telegram normalizado...")
        telegram_payload = {
            "update_id": 99901,
            "message": {
                "message_id": 101,
                "from": {
                    "id": 12345678,
                    "is_bot": False,
                    "first_name": "Carlos",
                    "username": "carlos_dev"
                },
                "chat": {
                    "id": 12345678,
                    "first_name": "Carlos",
                    "type": "private"
                },
                "date": 1728500000,
                "text": "Status da memoria no Raspberry Pi?"
            }
        }
        resp_tg = await client.post(f"/api/webhooks/telegram/{test_dot_id}", json=telegram_payload)
        assert resp_tg.status_code == 200, f"Falha no webhook Telegram: {resp_tg.text}"
        tg_data = resp_tg.json()
        assert tg_data["status"] == "success"
        assert "Memoria RAM utilizada" in tg_data["response"]
        print(f"[OK] Webhook Telegram normalizado e respondido. Chat ID: {tg_data['chat_id']}")

        # C. Teste do Webhook WhatsApp (Evolution API)
        print("[TESTE 3/6] Disparando webhook WhatsApp normalizado...")
        wa_payload = {
            "event": "messages.upsert",
            "instance": "pidots-primary",
            "data": {
                "key": {
                    "remoteJid": "5511999998888@s.whatsapp.net",
                    "fromMe": False,
                    "id": "WA_MSG_001"
                },
                "pushName": "Engenheiro Operacional",
                "message": {
                    "conversation": "Qual e o status do sistema agora?"
                }
            }
        }
        resp_wa = await client.post(f"/api/webhooks/whatsapp/{test_dot_id}", json=wa_payload)
        assert resp_wa.status_code == 200, f"Falha no webhook WhatsApp: {resp_wa.text}"
        wa_data = resp_wa.json()
        assert wa_data["status"] == "success"
        assert "Sistema operacional saudavel" in wa_data["response"]
        print(f"[OK] Webhook WhatsApp normalizado e respondido. Remote JID: {wa_data['remote_jid']}")

        # D. Teste de Criação e Membresia de Canal Temático
        print("[TESTE 4/6] Criando canal tematico e associando membros...")
        resp_ch = await client.post("/api/channels", json={
            "name": "edge-operations",
            "description": "Sala colaborativa para monitoramento e manutencao"
        })
        assert resp_ch.status_code == 200 or "já existe" in resp_ch.text, f"Falha ao criar canal: {resp_ch.text}"
        channel_id = "edge-operations"

        # Adiciona o Dot como membro do canal
        resp_mem = await client.post(f"/api/channels/{channel_id}/members", json={
            "member_type": "dot",
            "member_id": test_dot_id
        })
        assert resp_mem.status_code == 200, f"Falha ao associar membro ao canal: {resp_mem.text}"
        print(f"[OK] Canal '#{channel_id}' configurado com membro '{test_dot_id}'.")

        # E. Postagem de Mensagem no Canal e Leitura
        print("[TESTE 5/6] Postando mensagem do usuario no canal tematico...")
        post_payload = {
            "author_type": "user",
            "author_id": "operador_chefe",
            "content": f"@{test_dot_id} favor verificar os servicos"
        }
        resp_post = await client.post(f"/api/channels/{channel_id}/messages", json=post_payload)
        assert resp_post.status_code == 200, f"Falha ao postar mensagem: {resp_post.text}"
        post_data = resp_post.json()
        assert post_data["status"] == "dispatched"

        # Polling determinístico aguardando a persistência da mensagem
        messages = []
        for _ in range(30):
            resp_msgs = await client.get(f"/api/channels/{channel_id}/messages")
            if resp_msgs.status_code == 200:
                messages = resp_msgs.json()
                if len(messages) >= 1:
                    break
            await asyncio.sleep(0.1)

        assert len(messages) >= 1, "Falha: nenhuma mensagem encontrada no canal após polling!"
        print(f"[OK] Mensagens listadas no canal com sucesso. Total recuperado: {len(messages)}")

        # F. Teste de Trava Anti-Recursão do ChannelOrchestrator
        print("[TESTE 6/6] Validando trava de seguranca contra loops infinitos (hop_count > MAX_HOPS)...")
        res_limit = await ChannelOrchestrator.post_message_to_channel(
            channel_id=channel_id,
            author_type="dot",
            author_id=test_dot_id,
            content="@outro_bot mensagem em loop recursivo",
            hop_count=4,  # Excede MAX_HOPS (3)
            ai_provider=app.state.ai_provider
        )
        assert res_limit == "Recursion limit reached", f"Falha: trava anti-recurao nao disparou: {res_limit}"
        print("[OK] Trava anti-recurao validada com sucesso: loop bloqueado com hop_count=4.")

    await app.state.http_client.aclose()
    mem_end = get_current_memory_mb()
    print(f"[TELEMETRIA] Memoria RSS final: {mem_end} MB (Delta: {round(mem_end - mem_start, 2)} MB)")
    assert mem_end < 300.0, f"Memoria excedeu o teto estrito de 300MB: {mem_end} MB"
    print("[SUCESSO] Todos os testes da Fase 4 (Mensageria e Canais) passaram com perfeicao.")


if __name__ == "__main__":
    asyncio.run(run_phase8_tests())
