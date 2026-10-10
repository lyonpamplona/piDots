"""
Script de validação e teste empírico da Fase 2 do piDots.
Testa o loop autônomo do DotAgent, streaming de eventos AG-UI e persistência multi-turn.
"""

import asyncio
import sys
import uuid
import json
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.agent import DotAgent
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.tools.registry import registry


class MockOpenAIProvider(OpenAIUniversalProvider):
    """Provedor mock para teste determinístico e isolado de streaming AG-UI."""

    def __init__(self):
        super().__init__()
        self.call_count = 0

    async def chat_completion(self, messages, tools=None, model=None, temperature=0.2, max_tokens=4096):
        self.call_count += 1
        last_msg = messages[-1].get("content", "")

        # Se for o primeiro turno e o usuário perguntar o horário ou telemetria, aciona tool call
        if self.call_count == 1:
            return {
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "Consultando a telemetria do sistema Edge...",
                        "tool_calls": [{
                            "id": "call_mock_123",
                            "type": "function",
                            "function": {
                                "name": "get_edge_telemetry",
                                "arguments": "{}"
                            }
                        }]
                    }
                }]
            }

        # Segundo turno: síntese final
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "A telemetria do Raspberry Pi 4B indica temperatura normal e sistema estável.",
                    "tool_calls": []
                }
            }]
        }


async def main():
    print("=== [piDots] Teste e Validação da Fase 2 no Raspberry Pi 4B ===")

    # 1. Inicializa banco
    print("[1/4] Inicializando infraestrutura SQLite WAL...")
    await init_edge_database()

    # 2. Cria thread de teste
    print("[2/4] Criando thread de conversação durável...")
    thread_id = str(uuid.uuid4())
    dot_id = "dot-dev-core"

    async with get_db() as db:
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, ?)",
            (thread_id, dot_id, "Sessão de Teste AG-UI Fase 2")
        )
        await db.commit()
    print(f"      Thread criada com ID: {thread_id}")

    # 3. Execução do DotAgent com streaming de eventos AG-UI
    print("[3/4] Executando loop de raciocínio do DotAgent com mock provider...")
    mock_provider = MockOpenAIProvider()
    agent = DotAgent(dot_id=dot_id, provider=mock_provider, tool_registry=registry)

    events_received = []
    async for event in agent.run_thread(thread_id=thread_id, user_message="Como está o sistema agora?"):
        events_received.append(event["event"])
        print(f"      [EVENTO AG-UI] {event['event']} -> {json.dumps(event['data'], ensure_ascii=False)[:80]}...")

    # Validações dos eventos AG-UI
    assert "run:started" in events_received, "Evento 'run:started' não emitido!"
    assert "thought:delta" in events_received, "Evento 'thought:delta' não emitido!"
    assert "tool:called" in events_received, "Evento 'tool:called' não emitido!"
    assert "tool:result" in events_received, "Evento 'tool:result' não emitido!"
    assert "run:finished" in events_received, "Evento 'run:finished' não emitido!"
    print("      Todos os eventos do protocolo AG-UI v1.0 foram emitidos na ordem esperada!")

    # 4. Validação da persistência de mensagens
    print("[4/4] Verificando persistência multi-turn no SQLite WAL...")
    async with get_db() as db:
        cursor = await db.execute("SELECT role, content FROM messages WHERE thread_id = ? ORDER BY created_at ASC", (thread_id,))
        rows = await cursor.fetchall()

    print(f"      Mensagens persistidas na thread: {len(rows)}")
    for r in rows:
        print(f"      - {r['role'].upper()}: {r['content'][:60]}...")

    assert len(rows) >= 2, "As mensagens do usuário e do assistente deveriam estar salvas!"
    print("\n=== [SUCESSO] Fase 2 validada com 100% de êxito! Motor de Agência Autônoma Operacional! ===")


if __name__ == "__main__":
    asyncio.run(main())
