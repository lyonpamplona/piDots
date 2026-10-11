"""
Cliente HTTP Universal compatível com a API e SDK da OpenAI.
Funciona com qualquer provedor compatível (OpenAI, OpenRouter, Groq, DeepSeek, LiteLLM, llama-server local).
Implementa Circuit Breaker com Backoff Exponencial e Jitter contra erros 503, 429 e quedas de rede.
"""

import httpx
import asyncio
import random
import logging
from typing import Any, AsyncGenerator
from ..config import settings

logger = logging.getLogger("pidots.provider")


class ProviderAuthError(RuntimeError):
    """Erro irrecuperável de autenticação ou credencial no provedor de IA (HTTP 401/403)."""
    pass


class ProviderTransientError(RuntimeError):
    """Falha temporária ou esgotamento de retentativas no provedor de IA (HTTP 503/429/timeout)."""
    pass


class OpenAIUniversalProvider:
    """
    Cliente de inferência leve e assíncrono para qualquer API OpenAI-compatível.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        http_client: httpx.AsyncClient | None = None
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.default_model = default_model or settings.ai_model
        self.max_retries = settings.ai_max_retries
        self.timeout = settings.ai_timeout_seconds
        self._external_client = http_client
        self._internal_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client:
            return self._external_client
        # Cliente fallback local reutilizável caso não seja injetado via Lifespan
        if self._internal_client is None or self._internal_client.is_closed:
            self._internal_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=15)
            )
        return self._internal_client

    async def aclose(self) -> None:
        """Encerra com segurança o cliente interno caso tenha sido criado."""
        if self._internal_client and not self._internal_client.is_closed:
            await self._internal_client.aclose()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> dict[str, Any]:
        """
        Executa requisição /chat/completions com retentativa exponencial e circuit breaker.
        """
        target_model = model or self.default_model
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        client = await self._get_client()
        delays = [1.5, 3.5, 7.0]

        for attempt in range(self.max_retries):
            try:
                logger.debug("Enviando requisição para %s (Tentativa %d/%d)", endpoint, attempt + 1, self.max_retries)
                response = await client.post(endpoint, headers=headers, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    return response.json()

                # Falhas irrecuperáveis de autenticação / credencial (401 Unauthorized, 403 Forbidden)
                if response.status_code in (401, 403):
                    err_msg = (
                        f"Autenticação recusada pelo provedor (HTTP {response.status_code}): "
                        f"verifique AI_API_KEY e AI_BASE_URL. Resposta: {response.text[:200]}"
                    )
                    logger.error("%s", err_msg)
                    raise ProviderAuthError(err_msg)

                # Códigos passíveis de retry (503 Service Unavailable, 429 Rate Limit, 502 Bad Gateway, 504 Gateway Timeout)
                if response.status_code in (503, 429, 502, 504):
                    jitter = random.uniform(0.1, 0.5)
                    wait_time = delays[min(attempt, len(delays) - 1)] + jitter
                    logger.warning(
                        "Alerta de Provedor (HTTP %d). Acionando Circuit Breaker. Aguardando %.2fs antes de retentar...",
                        response.status_code, wait_time
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Demais erros HTTP inesperados (400, 404, etc.)
                logger.error("Erro retornado pelo provedor: HTTP %d - %s", response.status_code, response.text[:200])
                response.raise_for_status()

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as net_err:
                if attempt == self.max_retries - 1:
                    logger.error("Esgotadas as tentativas de conexão com %s: %s", endpoint, str(net_err))
                    raise ProviderTransientError(f"Falha de conexão com {endpoint}: {str(net_err)}") from net_err
                jitter = random.uniform(0.2, 0.6)
                wait_time = delays[min(attempt, len(delays) - 1)] + jitter
                logger.warning("Falha temporária de rede (%s). Aguardando %.2fs...", type(net_err).__name__, wait_time)
                await asyncio.sleep(wait_time)

        raise ProviderTransientError(f"Falha de inferência com {endpoint} após {self.max_retries} tentativas com backoff.")
