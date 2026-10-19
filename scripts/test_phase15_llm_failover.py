"""
Teste e Homologação da Fase 15: Gateway Multi-Provedor de IA com Circuit Breaker e Failover.
Valida a operação padrão inócua sem fallback (conforme a diretriz do usuário),
a transição transparente para o provedor secundário em caso de falhas HTTP 5xx/timeout,
a máquina de estados do Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED) e a
atualização a quente via endpoint REST /api/settings/ai.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from pidots.config import settings
from pidots.main import app
from pidots.providers.openai_client import (
    OpenAIUniversalProvider,
    ProviderAuthError,
    ProviderTransientError,
    CIRCUIT_STATE_CLOSED,
    CIRCUIT_STATE_OPEN,
    CIRCUIT_STATE_HALF_OPEN
)


async def test_standard_operation_without_fallback():
    """Valida que sem fallback configurado o comportamento permanece 100% idêntico ao original."""
    print("\n--- [1/5] Testando Operação Nominal sem Fallback (Regra do Usuário) ---")

    provider = OpenAIUniversalProvider(
        base_url="https://mock-primary.ai/v1",
        api_key="mock-key",
        default_model="gpt-4o-mini",
        fallback_url=None
    )

    # 1. Sucesso no primário
    mock_resp_200 = httpx.Response(
        status_code=200,
        json={"id": "chat-1", "choices": [{"message": {"role": "assistant", "content": "Olá piDots"}}]},
        request=httpx.Request("POST", "https://mock-primary.ai/v1/chat/completions")
    )

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_resp_200
    provider._external_client = mock_client

    res = await provider.chat_completion(messages=[{"role": "user", "content": "Teste"}])
    assert res["choices"][0]["message"]["content"] == "Olá piDots"
    assert provider.circuit_state == CIRCUIT_STATE_CLOSED
    assert provider.consecutive_failures == 0
    print("     [OK] Inferência primária executada com sucesso (circuito CLOSED, 0 falhas).")

    # 2. Falha 503 repetida sem fallback -> deve lançar ProviderTransientError sem mascaramento
    mock_resp_503 = httpx.Response(
        status_code=503,
        text="Service Temporarily Unavailable",
        request=httpx.Request("POST", "https://mock-primary.ai/v1/chat/completions")
    )
    mock_client.post.return_value = mock_resp_503
    provider.max_retries = 1  # 1 tentativa para teste rápido

    caught = False
    try:
        await provider.chat_completion(messages=[{"role": "user", "content": "Teste Falha"}])
    except ProviderTransientError as exc:
        caught = True
        assert "503" in str(exc)
        print("     [OK] ProviderTransientError lançado corretamente sem tentar fallback inexistente.")

    assert caught, "Deveria ter lançado ProviderTransientError quando o primário falha sem fallback"
    assert provider.consecutive_failures == 1


async def test_transparent_failover_to_secondary():
    """Valida chaveamento transparente para o provedor secundário quando o primário retorna 503."""
    print("\n--- [2/5] Testando Failover Transparente para Provedor Secundário ---")

    provider = OpenAIUniversalProvider(
        base_url="https://primary.ai/v1",
        api_key="key-prim",
        default_model="gpt-4o-mini",
        fallback_url="https://secondary-failover.ai/v1",
        fallback_api_key="key-sec",
        fallback_model="meta-llama/llama-3.1-8b-instruct",
        circuit_breaker_threshold=3
    )
    provider.max_retries = 1

    async def mock_post(url, *args, **kwargs):
        if "primary.ai" in str(url):
            return httpx.Response(
                status_code=503,
                text="Primary 503 Overloaded",
                request=httpx.Request("POST", str(url))
            )
        elif "secondary-failover.ai" in str(url):
            return httpx.Response(
                status_code=200,
                json={
                    "id": "chat-fallback-1",
                    "choices": [{"message": {"role": "assistant", "content": "Resposta servida via Failover Secundário"}}]
                },
                request=httpx.Request("POST", str(url))
            )
        raise ValueError(f"URL desconhecida: {url}")

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = mock_post
    provider._external_client = mock_client

    res = await provider.chat_completion(messages=[{"role": "user", "content": "Pergunta"}])
    assert res["choices"][0]["message"]["content"] == "Resposta servida via Failover Secundário"
    assert res.get("_served_by_fallback") is True
    assert provider.consecutive_failures == 1
    assert provider.circuit_state == CIRCUIT_STATE_CLOSED
    print("     [OK] Failover executado com sucesso e marcado com metadado _served_by_fallback: True.")


async def test_circuit_breaker_state_transitions():
    """Valida as transições de estado do Circuit Breaker: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    print("\n--- [3/5] Testando Máquina de Estados do Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED) ---")

    cooldown_seconds = 0.25  # Cooldown curto para teste rápido
    provider = OpenAIUniversalProvider(
        base_url="https://primary.ai/v1",
        api_key="key-prim",
        default_model="gpt-4o-mini",
        fallback_url="https://secondary-failover.ai/v1",
        fallback_api_key="key-sec",
        circuit_breaker_threshold=2,  # Abre circuito após 2 falhas consecutivas
        circuit_breaker_cooldown=cooldown_seconds
    )
    provider.max_retries = 1

    primary_calls = 0
    fallback_calls = 0

    async def mock_post_cb(url, *args, **kwargs):
        nonlocal primary_calls, fallback_calls
        if "primary.ai" in str(url):
            primary_calls += 1
            if primary_calls <= 2:
                # Primeiras 2 chamadas falham com 502
                return httpx.Response(status_code=502, text="Bad Gateway", request=httpx.Request("POST", str(url)))
            else:
                # Chamada canário restabelecida com 200 OK
                return httpx.Response(
                    status_code=200,
                    json={"choices": [{"message": {"role": "assistant", "content": "Primário Restabelecido"}}]},
                    request=httpx.Request("POST", str(url))
                )
        elif "secondary-failover.ai" in str(url):
            fallback_calls += 1
            return httpx.Response(
                status_code=200,
                json={"choices": [{"message": {"role": "assistant", "content": "Fallback Ativo"}}]},
                request=httpx.Request("POST", str(url))
            )
        raise ValueError(f"URL: {url}")

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = mock_post_cb
    provider._external_client = mock_client

    # 1. Primeira falha do primário -> Failover (consecutive_failures = 1, CLOSED)
    await provider.chat_completion(messages=[{"role": "user", "content": "Chamada 1"}])
    assert provider.circuit_state == CIRCUIT_STATE_CLOSED
    assert provider.consecutive_failures == 1

    # 2. Segunda falha do primário -> Threshold de 2 atingido -> Transiciona para OPEN!
    await provider.chat_completion(messages=[{"role": "user", "content": "Chamada 2"}])
    assert provider.circuit_state == CIRCUIT_STATE_OPEN
    assert provider.consecutive_failures == 2
    print("     [OK] Circuito transicionou para OPEN após atingir o threshold de falhas consecutivas.")

    # 3. Terceira chamada: com circuito OPEN, deve ir direto para o fallback SEM chamar o primário
    initial_primary_calls = primary_calls
    res3 = await provider.chat_completion(messages=[{"role": "user", "content": "Chamada 3 com CB OPEN"}])
    assert primary_calls == initial_primary_calls, "Circuito OPEN não deveria ter tentado o primário"
    assert res3["choices"][0]["message"]["content"] == "Fallback Ativo"
    print("     [OK] Circuito OPEN desviou chamada diretamente para o fallback sem latência do primário.")

    # 4. Aguarda expiração do cooldown (0.25s) -> Transição para HALF_OPEN
    await asyncio.sleep(cooldown_seconds + 0.05)
    state = provider.check_circuit_state()
    assert state == CIRCUIT_STATE_HALF_OPEN, f"Esperado HALF_OPEN, obtido {state}"
    print("     [OK] Janela de cooldown expirada: transição para HALF_OPEN confirmada.")

    # 5. Quarta chamada (Canário): tenta o primário, que agora responde 200 OK -> Circuito fecha (CLOSED)
    res4 = await provider.chat_completion(messages=[{"role": "user", "content": "Chamada 4 Canário"}])
    assert res4["choices"][0]["message"]["content"] == "Primário Restabelecido"
    assert provider.circuit_state == CIRCUIT_STATE_CLOSED
    assert provider.consecutive_failures == 0
    print("     [OK] Requisição canário recuperou o primário e fechou o Circuit Breaker (CLOSED).")


async def test_both_providers_failure():
    """Valida o diagnóstico consolidado quando ambos os provedores falham simultaneamente."""
    print("\n--- [4/5] Testando Diagnóstico Consolidado em Queda Total de Ambos os Provedores ---")

    provider = OpenAIUniversalProvider(
        base_url="https://broken-primary.ai/v1",
        api_key="k1",
        default_model="m1",
        fallback_url="https://broken-secondary.ai/v1",
        fallback_api_key="k2"
    )
    provider.max_retries = 1

    async def mock_post_all_fail(url, *args, **kwargs):
        if "broken-primary.ai" in str(url):
            return httpx.Response(status_code=504, text="Primary Gateway Timeout", request=httpx.Request("POST", str(url)))
        return httpx.Response(status_code=503, text="Secondary Overloaded", request=httpx.Request("POST", str(url)))

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = mock_post_all_fail
    provider._external_client = mock_client

    caught = False
    try:
        await provider.chat_completion(messages=[{"role": "user", "content": "Queda Total"}])
    except ProviderTransientError as exc:
        caught = True
        err_msg = str(exc)
        assert "broken-primary.ai" in err_msg
        assert "broken-secondary.ai" in err_msg
        print(f"     [OK] Exceção consolidada reportou ambos os provedores: {err_msg[:90]}...")

    assert caught


async def test_hot_reload_api_and_settings_endpoint():
    """Valida a atualização a quente dos parâmetros de failover via API REST."""
    print("\n--- [5/5] Testando Atualização a Quente via POST /api/settings/ai e Telemetria GET /api/settings ---")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Consulta inicial de settings
        r_init = await client.get("/api/settings")
        assert r_init.status_code == 200
        ai_data = r_init.json()["ai"]
        assert "circuit_breaker" in ai_data
        assert ai_data["circuit_breaker"]["state"] in ("CLOSED", "OPEN", "HALF_OPEN")
        print(f"     [OK] Telemetria inicial do Circuit Breaker: estado={ai_data['circuit_breaker']['state']}.")

        # 2. Atualiza a quente configurando um fallback temporário
        payload_update = {
            "fallback_url": "https://test-hotreload.fallback.ai/v1",
            "fallback_api_key": "sec-secret-key-12345",
            "fallback_model": "test-fallback-model",
            "circuit_breaker_consecutive_failures": 4,
            "circuit_breaker_cooldown_seconds": 45.0
        }
        r_post = await client.post("/api/settings/ai", json=payload_update)
        assert r_post.status_code == 200
        assert r_post.json()["status"] == "success"

        # 3. Consulta de validação: parâmetros devem refletir a nova configuração
        r_check = await client.get("/api/settings")
        assert r_check.status_code == 200
        ai_updated = r_check.json()["ai"]
        assert ai_updated["fallback_configured"] is True
        assert ai_updated["fallback_url"] == "https://test-hotreload.fallback.ai/v1"
        assert "sec-" in ai_updated["fallback_api_key_masked"]
        assert "345" in ai_updated["fallback_api_key_masked"]
        assert ai_updated["circuit_breaker"]["threshold"] == 4
        assert ai_updated["circuit_breaker"]["cooldown_seconds"] == 45.0
        print("     [OK] Hot-Reload de parâmetros de failover e Circuit Breaker validado com sucesso via API.")

        # 4. Restaura estado original (limpando o fallback de teste)
        restore_payload = {
            "fallback_url": "",
            "fallback_api_key": "",
            "fallback_model": ""
        }
        r_restore = await client.post("/api/settings/ai", json=restore_payload)
        assert r_restore.status_code == 200

        r_final = await client.get("/api/settings")
        assert r_final.json()["ai"]["fallback_configured"] is False
        print("     [OK] Configuração original limpa e restaurada.")


async def main():
    print("================================================================================")
    print(" [piDots] Teste e Homologação Automatizada - Fase 15 (Gateway Multi-Provedor)")
    print(" Versão: 1.5.2 | Componente: Circuit Breaker de 3 Estados & Failover Opcional")
    print("================================================================================")

    await test_standard_operation_without_fallback()
    await test_transparent_failover_to_secondary()
    await test_circuit_breaker_state_transitions()
    await test_both_providers_failure()
    await test_hot_reload_api_and_settings_endpoint()

    print("\n================================================================================")
    print(" [SUCESSO TOTAL] Todos os testes da Fase 15 foram homologados com 100% de êxito.")
    print("================================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
