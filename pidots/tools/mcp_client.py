"""
Cliente MCP Lite (Model Context Protocol) para piDots.
Implementação em Python assíncrono puro (< 5MB de overhead de RAM),
sem SDKs de terceiros ou runtime Node.js obrigatório, concebida para
hardware restrito (Raspberry Pi 4B ARM64).

Suporta transportes STDIO e SSE com JSON-RPC 2.0 padrão da especificação MCP.
Permite conexão sob demanda a servidores MCP externos (Git, Home Assistant, SQLite, etc.)
com integração estrita ao Dynamic Tool Pruning (allowed_tools_json).
"""

import os
import json
import asyncio
import logging
from typing import Any, Callable, Awaitable
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("pidots.mcp_client")


class LiteMCPClient:
    """Cliente leve para o protocolo MCP (Model Context Protocol) via STDIO ou SSE/HTTP."""

    def __init__(
        self,
        server_name: str,
        transport: str = "stdio",
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        sse_url: str | None = None,
        http_endpoint: str | None = None,
        timeout_seconds: float = 30.0
    ) -> None:
        self.server_name = server_name
        self.transport = transport.lower()
        self.command = command
        self.args = args or []
        self.env = env
        self.sse_url = sse_url
        self.http_endpoint = http_endpoint or (sse_url.replace("/sse", "/message") if sse_url else None)
        self.timeout_seconds = timeout_seconds

        self._process: asyncio.subprocess.Process | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._request_counter = 0
        self._is_initialized = False
        self._server_capabilities: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    def _next_id(self) -> int:
        self._request_counter += 1
        return self._request_counter

    async def connect(self) -> bool:
        """Estabelece a conexão com o servidor MCP de acordo com o transporte configurado."""
        if self.transport == "stdio":
            if not self.command:
                logger.error("Comando não especificado para transporte STDIO no servidor MCP '%s'.", self.server_name)
                return False

            env_vars = os.environ.copy()
            if self.env:
                env_vars.update(self.env)

            try:
                self._process = await asyncio.create_subprocess_exec(
                    self.command,
                    *self.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env_vars
                )
                logger.info("Servidor MCP STDIO '%s' iniciado (PID: %s).", self.server_name, self._process.pid)
                return True
            except Exception as e:
                logger.error("Falha ao iniciar processo do servidor MCP '%s': %s", self.server_name, str(e))
                return False

        elif self.transport in ("sse", "http"):
            if not self.sse_url and not self.http_endpoint:
                logger.error("URL não especificada para transporte SSE/HTTP no servidor MCP '%s'.", self.server_name)
                return False
            self._http_client = httpx.AsyncClient(timeout=self.timeout_seconds)
            logger.info("Cliente HTTP/SSE para servidor MCP '%s' instanciado.", self.server_name)
            return True

        else:
            logger.error("Transporte desconhecido '%s' para servidor MCP '%s'.", self.transport, self.server_name)
            return False

    async def send_rpc_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Envia uma requisição JSON-RPC 2.0 e aguarda a resposta."""
        req_id = self._next_id()
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        async with self._lock:
            if self.transport == "stdio":
                if not self._process or self._process.returncode is not None:
                    return {"error": {"code": -32000, "message": "Processo MCP STDIO não está ativo."}}

                line = json.dumps(payload, ensure_ascii=False) + "\n"
                assert self._process.stdin is not None
                assert self._process.stdout is not None

                self._process.stdin.write(line.encode("utf-8"))
                await self._process.stdin.drain()

                # Leitura da resposta linha a linha com timeout defensivo
                try:
                    resp_line = await asyncio.wait_for(
                        self._process.stdout.readline(),
                        timeout=self.timeout_seconds
                    )
                    if not resp_line:
                        return {"error": {"code": -32000, "message": "Servidor MCP encerrou stdout inesperadamente."}}
                    return json.loads(resp_line.decode("utf-8").strip())
                except asyncio.TimeoutError:
                    return {"error": {"code": -32000, "message": f"Timeout ({self.timeout_seconds}s) aguardando resposta MCP."}}
                except Exception as e:
                    return {"error": {"code": -32000, "message": f"Erro de desserialização JSON-RPC: {str(e)}"}}

            elif self.transport in ("sse", "http"):
                target_url = self.http_endpoint or self.sse_url
                if not target_url or not self._http_client:
                    return {"error": {"code": -32000, "message": "Cliente HTTP MCP não configurado."}}

                try:
                    resp = await self._http_client.post(
                        target_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    if resp.status_code not in (200, 201, 202):
                        return {"error": {"code": -32000, "message": f"Erro HTTP {resp.status_code}: {resp.text}"}}
                    return resp.json()
                except Exception as e:
                    return {"error": {"code": -32000, "message": f"Falha na comunicação HTTP com MCP: {str(e)}"}}

        return {"error": {"code": -32000, "message": "Transporte não operacional."}}

    async def send_rpc_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Envia uma notificação JSON-RPC 2.0 (sem id e sem espera por resposta)."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        if self.transport == "stdio" and self._process and self._process.returncode is None:
            line = json.dumps(payload, ensure_ascii=False) + "\n"
            assert self._process.stdin is not None
            self._process.stdin.write(line.encode("utf-8"))
            await self._process.stdin.drain()
        elif self.transport in ("sse", "http") and self._http_client:
            target_url = self.http_endpoint or self.sse_url
            if target_url:
                try:
                    await self._http_client.post(target_url, json=payload)
                except Exception as e:
                    logger.debug("Falha no envio de notificação MCP HTTP: %s", str(e))

    async def initialize(self) -> bool:
        """Executa o handshake 'initialize' do protocolo MCP e envia confirmação."""
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "piDots-LiteMCP",
                "version": "1.5.0"
            }
        }

        resp = await self.send_rpc_request("initialize", init_params)
        if "error" in resp:
            logger.error("Falha na inicialização do servidor MCP '%s': %s", self.server_name, resp["error"])
            return False

        result = resp.get("result", {})
        self._server_capabilities = result.get("capabilities", {})
        self._is_initialized = True

        # Notifica o servidor de que a inicialização foi concluída
        await self.send_rpc_notification("notifications/initialized", {})
        logger.info("Servidor MCP '%s' inicializado com sucesso (Protocolo: %s).", self.server_name, result.get("protocolVersion"))
        return True

    async def list_tools(self) -> list[dict[str, Any]]:
        """Recupera a lista de ferramentas disponibilizadas pelo servidor MCP."""
        if not self._is_initialized:
            ok = await self.initialize()
            if not ok:
                return []

        resp = await self.send_rpc_request("tools/list", {})
        if "error" in resp:
            logger.warning("Erro ao listar ferramentas do MCP '%s': %s", self.server_name, resp["error"])
            return []

        result = resp.get("result", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoca uma ferramenta específica no servidor MCP e retorna o resultado estruturado."""
        if not self._is_initialized:
            ok = await self.initialize()
            if not ok:
                return {"error": f"Servidor MCP '{self.server_name}' não inicializado."}

        resp = await self.send_rpc_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        if "error" in resp:
            return {"error": resp["error"].get("message", "Erro retornado pelo servidor MCP.")}

        result = resp.get("result", {})
        # Extrai conteúdo de texto ou estruturado conforme especificação MCP
        content_items = result.get("content", [])
        text_outputs = []
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                text_outputs.append(item.get("text", ""))
            elif isinstance(item, str):
                text_outputs.append(item)

        is_error = result.get("isError", False)
        output_text = "\n".join(text_outputs) if text_outputs else json.dumps(result, ensure_ascii=False)

        if is_error:
            return {"error": output_text, "mcp_server": self.server_name}
        return {"result": output_text, "mcp_server": self.server_name}

    async def close(self) -> None:
        """Encerra graciosamente os recursos do cliente MCP."""
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=3.0)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self._is_initialized = False
        logger.info("Cliente MCP '%s' desconectado.", self.server_name)


def convert_mcp_tool_to_openai_schema(server_name: str, mcp_tool: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Converte uma definição de ferramenta do formato MCP para a especificação da OpenAI API (Function Calling).
    Gera nome padronizado com prefixo: mcp_{server_name}_{mcp_tool_name}.
    """
    mcp_name = mcp_tool.get("name", "unknown")
    standard_name = f"mcp_{server_name}_{mcp_name}"
    description = mcp_tool.get("description", f"Ferramenta MCP do servidor '{server_name}'.")
    input_schema = mcp_tool.get("inputSchema", {})

    parameters = {
        "type": input_schema.get("type", "object"),
        "properties": input_schema.get("properties", {}),
        "required": input_schema.get("required", [])
    }

    openai_schema = {
        "type": "function",
        "function": {
            "name": standard_name,
            "description": f"[MCP: {server_name}] {description}",
            "parameters": parameters
        }
    }
    return standard_name, openai_schema


class MCPRegistryManager:
    """
    Gerenciador global para acoplamento de servidores MCP externos ao ToolRegistry do piDots.
    Garante o respeito estrito ao Dynamic Tool Pruning (allowed_tools_json).
    """

    _active_clients: dict[str, LiteMCPClient] = {}
    _server_tools: dict[str, list[str]] = {}

    @classmethod
    async def register_server(
        cls,
        server_name: str,
        client: LiteMCPClient,
        tool_registry: Any
    ) -> list[str]:
        """
        Conecta o cliente MCP, recupera suas ferramentas e registra os handlers no ToolRegistry.
        Retorna a lista de nomes de ferramentas registradas.
        """
        connected = await client.connect()
        if not connected:
            logger.error("Falha na conexão com o servidor MCP '%s'. Registro abortado.", server_name)
            return []

        initialized = await client.initialize()
        if not initialized:
            logger.error("Falha no handshake inicial com o servidor MCP '%s'.", server_name)
            await client.close()
            return []

        tools = await client.list_tools()
        registered_names: list[str] = []

        for mcp_tool in tools:
            tool_name = mcp_tool.get("name")
            if not tool_name:
                continue

            std_name, schema = convert_mcp_tool_to_openai_schema(server_name, mcp_tool)

            # Handler com encapsulamento de closure correto
            def make_handler(c: LiteMCPClient, t_name: str):
                async def _mcp_handler(**kwargs: Any) -> dict[str, Any]:
                    return await c.call_tool(t_name, kwargs)
                return _mcp_handler

            tool_registry.register(
                name=std_name,
                schema=schema,
                handler=make_handler(client, tool_name)
            )
            registered_names.append(std_name)

        cls._active_clients[server_name] = client
        cls._server_tools[server_name] = registered_names
        logger.info(
            "Servidor MCP '%s' registrado no ToolRegistry com %d ferramentas: %s",
            server_name, len(registered_names), registered_names
        )
        return registered_names

    @classmethod
    async def unregister_server(cls, server_name: str, tool_registry: Any = None) -> bool:
        """Desconecta o servidor MCP e remove suas ferramentas do ToolRegistry."""
        client = cls.get_client(server_name)
        if not client:
            return False

        if tool_registry:
            tool_names = cls._server_tools.get(server_name, [])
            for t_name in tool_names:
                tool_registry.unregister(t_name)

        cls._server_tools.pop(server_name, None)
        cls._active_clients.pop(server_name, None)
        await client.close()
        return True

    @classmethod
    def get_client(cls, server_name: str) -> LiteMCPClient | None:
        """Recupera uma instância de cliente MCP ativo pelo nome."""
        return cls._active_clients.get(server_name)

    @classmethod
    async def disconnect_all(cls) -> None:
        """Desconecta todos os servidores MCP e limpa conexões ativas."""
        for name, client in list(cls._active_clients.items()):
            try:
                await client.close()
            except Exception as e:
                logger.debug("Erro ao fechar cliente MCP %s: %s", name, str(e))
        cls._active_clients.clear()
