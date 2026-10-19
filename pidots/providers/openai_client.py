"""
Cliente HTTP Universal compatível com a API e SDK da OpenAI.
Funciona com qualquer provedor compatível (OpenAI, OpenRouter, Groq, DeepSeek, LiteLLM, llama-server local).
Implementa Gateway Multi-Provedor com Circuit Breaker de 3 estados (CLOSED, OPEN, HALF_OPEN),
retentativas com backoff exponencial e failover secundário transparente e configurável.
"""

import asyncio
import logging
import random
import time
from typing import Any
import httpx

from ..config import settings

logger = logging.getLogger("pidots.provider")

CIRCUIT_STATE_CLOSED = "CLOSED"
CIRCUIT_STATE_OPEN = "OPEN"
CIRCUIT_STATE_HALF_OPEN = "HALF_OPEN"


class ProviderAuthError(RuntimeError):
    """Erro irrecuperável de autenticação ou credencial no provedor de IA (HTTP 401/403)."""
    pass


class ProviderEndpointError(RuntimeError):
    """Erro de rota ou parâmetros inválidos no provedor de IA (HTTP 400/404)."""
    pass


class ProviderTransientError(RuntimeError):
    """Falha temporária ou esgotamento de retentativas no provedor de IA (HTTP 503/429/timeout)."""
    pass


class OpenAIUniversalProvider:
    """
    Cliente de inferência assíncrono universal com suporte a failover secundário
    e máquina de estados de Circuit Breaker para ambientes de borda.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        fallback_url: str | None = None,
        fallback_api_key: str | None = None,
        fallback_model: str | None = None,
        circuit_breaker_threshold: int | None = None,
        circuit_breaker_cooldown: float | None = None
    ) -> None:
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")
        self.api_key = api_key or settings.ai_api_key
        self.default_model = default_model or settings.ai_model
        self.max_retries = settings.ai_max_retries
        self.timeout = settings.ai_timeout_seconds
        self._external_client = http_client
        self._internal_client: httpx.AsyncClient | None = None

        # Parâmetros de failover secundário opcional
        raw_fallback_url = fallback_url or settings.ai_fallback_url
        self.fallback_url = raw_fallback_url.rstrip("/") if raw_fallback_url else None
        self.fallback_api_key = fallback_api_key or settings.ai_fallback_api_key
        self.fallback_model = fallback_model or settings.ai_fallback_model

        # Máquina de estados do Circuit Breaker para o provedor primário
        self.circuit_breaker_threshold = (
            circuit_breaker_threshold or settings.ai_circuit_breaker_consecutive_failures
        )
        self.circuit_breaker_cooldown = (
            circuit_breaker_cooldown or settings.ai_circuit_breaker_cooldown_seconds
        )
        self.circuit_state = CIRCUIT_STATE_CLOSED
        self.consecutive_failures = 0
        self.circuit_opened_at: float | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client:
            return self._external_client
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

    def check_circuit_state(self) -> str:
        """Avalia a janela de tempo do Circuit Breaker e transiciona OPEN -> HALF_OPEN se o cooldown expirou."""
        if self.circuit_state == CIRCUIT_STATE_OPEN and self.circuit_opened_at is not None:
            elapsed = time.time() - self.circuit_opened_at
            if elapsed >= self.circuit_breaker_cooldown:
                self.circuit_state = CIRCUIT_STATE_HALF_OPEN
                logger.info(
                    "Janela de cooldown do Circuit Breaker expirada (%.1fs >= %.1fs). "
                    "Transicionando para HALF_OPEN (teste canário).",
                    elapsed, self.circuit_breaker_cooldown
                )
        return self.circuit_state

    def reset_circuit(self) -> None:
        """Restaura manualmente o circuito primário para o estado nominal CLOSED."""
        self.circuit_state = CIRCUIT_STATE_CLOSED
        self.consecutive_failures = 0
        self.circuit_opened_at = None

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> dict[str, Any]:
        """
        Executa requisição /chat/completions com retentativa exponencial, failover e circuit breaker.
        """
        current_state = self.check_circuit_state()

        # Se o circuito do primário estiver OPEN e houver fallback configurado, desvia imediatamente sem timeout
        if current_state == CIRCUIT_STATE_OPEN and self.fallback_url:
            logger.warning(
                "Circuit Breaker primário OPEN (%d falhas consecutivas). "
                "Despachando requisição diretamente para o provedor secundário de failover: %s",
                self.consecutive_failures, self.fallback_url
            )
            return await self._execute_fallback(
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

        # Tenta executar no provedor primário
        primary_exception: Exception | None = None
        try:
            result = await self._execute_primary(
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Sucesso no primário
            if current_state == CIRCUIT_STATE_HALF_OPEN:
                logger.info("Requisição canário bem-sucedida! Provedor primário restabelecido. Fechando Circuit Breaker.")
                self.reset_circuit()
            else:
                self.consecutive_failures = 0

            return result

        except (ProviderTransientError, httpx.TransportError, httpx.TimeoutException) as transient_err:
            primary_exception = transient_err
            self.consecutive_failures += 1

            if self.consecutive_failures >= self.circuit_breaker_threshold:
                self.circuit_state = CIRCUIT_STATE_OPEN
                self.circuit_opened_at = time.time()
                logger.warning(
                    "Provedor primário atingiu %d falhas consecutivas. "
                    "Circuit Breaker transicionou para OPEN (cooldown de %.1fs).",
                    self.consecutive_failures, self.circuit_breaker_cooldown
                )

            # Se houver fallback configurado, executa o failover transparente
            if self.fallback_url:
                logger.warning(
                    "Falha no provedor primário (%s). Acionando failover secundário transparente em %s...",
                    str(transient_err), self.fallback_url
                )
                try:
                    return await self._execute_fallback(
                        messages=messages,
                        tools=tools,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                except Exception as fallback_err:
                    logger.error("Falha também no provedor secundário de failover: %s", str(fallback_err))
                    raise ProviderTransientError(
                        f"Falha de inferência em ambos os provedores. "
                        f"Primário ({self.base_url}): {primary_exception} | "
                        f"Secundário ({self.fallback_url}): {fallback_err}"
                    ) from fallback_err

            # Caso não haja fallback configurado, repassa a exceção normalmente
            raise primary_exception

    async def _execute_primary(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> dict[str, Any]:
        """Executa a requisição no endpoint primário com retentativa exponencial e jitter."""
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
                logger.debug("Enviando requisição primária para %s (Tentativa %d/%d)", endpoint, attempt + 1, self.max_retries)
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

                # Códigos passíveis de retry (500, 502, 503, 504, 429)
                if response.status_code in (500, 502, 503, 504, 429):
                    if attempt == self.max_retries - 1:
                        err_text = response.text[:400]
                        logger.error("Esgotadas as %d tentativas com o provedor primário (HTTP %d): %s", self.max_retries, response.status_code, err_text)
                        raise ProviderTransientError(f"Provedor primário retornou HTTP {response.status_code} após {self.max_retries} tentativas: {err_text}")
                    jitter = random.uniform(0.1, 0.5)
                    wait_time = delays[min(attempt, len(delays) - 1)] + jitter
                    logger.warning(
                        "Alerta de Provedor Primário (HTTP %d). Aguardando %.2fs antes de retentar...",
                        response.status_code, wait_time
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Falhas de rota inexistente ou requisição rejeitada (400, 404)
                if response.status_code in (400, 404):
                    err_msg = (
                        f"Endpoint ou modelo não encontrado no gateway primário (HTTP {response.status_code}): "
                        f"verifique AI_BASE_URL ({self.base_url}) e AI_MODEL ({target_model}). "
                        f"Resposta do gateway: {response.text[:200]}"
                    )
                    logger.error("%s", err_msg)
                    raise ProviderEndpointError(err_msg)

                logger.error("Erro retornado pelo provedor primário: HTTP %d - %s", response.status_code, response.text[:200])
                response.raise_for_status()

            except (httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError) as net_err:
                if attempt == self.max_retries - 1:
                    logger.error("Esgotadas as tentativas de conexão primária com %s: %s", endpoint, str(net_err))
                    raise ProviderTransientError(f"Falha de conexão com {endpoint}: {str(net_err)}") from net_err
                jitter = random.uniform(0.2, 0.6)
                wait_time = delays[min(attempt, len(delays) - 1)] + jitter
                logger.warning("Falha temporária de rede primária (%s). Aguardando %.2fs...", type(net_err).__name__, wait_time)
                await asyncio.sleep(wait_time)

        raise ProviderTransientError(f"Falha de inferência primária com {endpoint} após {self.max_retries} tentativas com backoff.")

    async def _execute_fallback(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> dict[str, Any]:
        """Executa a requisição no endpoint secundário de failover."""
        if not self.fallback_url:
            raise ProviderTransientError("Nenhum provedor secundário de failover configurado.")

        target_model = self.fallback_model or model or self.default_model
        fallback_key = self.fallback_api_key or self.api_key
        endpoint = f"{self.fallback_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {fallback_key}",
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

        # Failover tenta com até 2 tentativas rápidas
        fallback_retries = 2
        for attempt in range(fallback_retries):
            try:
                logger.info(
                    "Despachando para provedor secundário de failover: %s (Tentativa %d/%d, Modelo: %s)",
                    endpoint, attempt + 1, fallback_retries, target_model
                )
                response = await client.post(endpoint, headers=headers, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    # Marca metadado indicando que a resposta foi processada via failover
                    if isinstance(data, dict):
                        data["_served_by_fallback"] = True
                    logger.info("Requisição atendida com êxito pelo provedor secundário de failover.")
                    return data

                if response.status_code in (401, 403):
                    raise ProviderAuthError(f"Autenticação recusada no provedor de failover (HTTP {response.status_code})")

                if attempt == fallback_retries - 1:
                    raise ProviderTransientError(f"Provedor de failover retornou HTTP {response.status_code}: {response.text[:200]}")

                await asyncio.sleep(1.0)

            except (httpx.TransportError, httpx.TimeoutException) as net_err:
                if attempt == fallback_retries - 1:
                    raise ProviderTransientError(f"Falha de conexão com provedor de failover {endpoint}: {net_err}") from net_err
                await asyncio.sleep(1.0)

        raise ProviderTransientError(f"Provedor secundário de failover indisponível em {endpoint}.")
