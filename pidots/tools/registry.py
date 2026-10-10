"""
Registro central de ferramentas operacionais do piDots.
Formatação compatível com a especificação da OpenAI API (Function Calling).
Inclui terminal isolado (Bubblewrap/Subprocess), extrator web semântico e gerenciamento de arquivos.
"""

import json
import logging
from typing import Callable, Any, Awaitable
from datetime import datetime
import os

from .terminal import TerminalSandbox
from .web_reader import WebReader
from .file_ops import FileManager

logger = logging.getLogger("pidots.tools")

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    """Gerencia ferramentas disponíveis para os Dots com suporte a Dynamic Tool Pruning."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._register_default_tools()

    def register(self, name: str, schema: dict[str, Any], handler: ToolHandler) -> None:
        """Registra uma ferramenta e seu respectivo handler assíncrono."""
        self._tools[name] = schema
        self._handlers[name] = handler

    def get_tool_definitions(self, tool_names: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Retorna as definições das ferramentas no formato da OpenAI API.
        Aplica poda dinâmica (Dynamic Tool Pruning) quando especificado.
        """
        if tool_names is None:
            return list(self._tools.values())
        return [self._tools[name] for name in tool_names if name in self._tools]

    async def execute_tool(self, name: str, arguments: dict[str, Any], dot_id: str = "default") -> dict[str, Any]:
        """Executa o handler de uma ferramenta registrada injetando dot_id se aplicável."""
        if name not in self._handlers:
            return {"error": f"Ferramenta '{name}' não encontrada no registro."}
        try:
            handler = self._handlers[name]
            # Se a ferramenta aceitar dot_id em seus parâmetros e não tiver sido passado, injeta
            if name in ("execute_shell_command", "workspace_read_file", "workspace_write_file", "workspace_list_files"):
                if "dot_id" not in arguments:
                    arguments["dot_id"] = dot_id
            return await handler(**arguments)
        except Exception as e:
            logger.error("Erro ao executar ferramenta %s: %s", name, str(e), exc_info=True)
            return {"error": f"Exceção durante a execução de {name}: {str(e)}"}

    def _register_default_tools(self) -> None:
        """Registra todas as ferramentas operacionais da Fase 3."""

        # 1. Execução de comandos no Terminal Sandbox
        self.register(
            name="execute_shell_command",
            schema={
                "type": "function",
                "function": {
                    "name": "execute_shell_command",
                    "description": "Executa um comando bash isolado no workspace do Dot com limites de tempo e memória.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando bash a ser executado (ex: 'python3 script.py', 'ls -la', 'cat data.json')."
                            },
                            "timeout_seconds": {
                                "type": "number",
                                "description": "Timeout em segundos antes de abortar o processo (default: 30)."
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            handler=self._tool_execute_shell
        )

        # 2. Navegador e Leitor Web Semântico (Camada 1)
        self.register(
            name="read_web_page",
            schema={
                "type": "function",
                "function": {
                    "name": "read_web_page",
                    "description": "Lê uma URL da web e extrai seu conteúdo textual limpo em formato Markdown estruturado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Endereço HTTP ou HTTPS completo da página a ser lida."
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            handler=self._tool_read_web_page
        )

        # 3. Leitura Segura de Arquivos no Workspace
        self.register(
            name="workspace_read_file",
            schema={
                "type": "function",
                "function": {
                    "name": "workspace_read_file",
                    "description": "Lê o conteúdo de um arquivo de texto no workspace do Dot com proteção contra path traversal.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Nome relativo do arquivo a ser lido (ex: 'main.py', 'docs/plan.md')."
                            }
                        },
                        "required": ["filename"]
                    }
                }
            },
            handler=self._tool_read_workspace_file
        )

        # 4. Escrita Atômica de Arquivos no Workspace
        self.register(
            name="workspace_write_file",
            schema={
                "type": "function",
                "function": {
                    "name": "workspace_write_file",
                    "description": "Cria ou substitui atomicamente um arquivo no workspace do Dot e sincroniza em Spaces.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Nome relativo do arquivo a ser gravado (ex: 'script.py', 'notes.md')."
                            },
                            "content": {
                                "type": "string",
                                "description": "Conteúdo textual completo a ser escrito no arquivo."
                            }
                        },
                        "required": ["filename", "content"]
                    }
                }
            },
            handler=self._tool_write_workspace_file
        )

        # 5. Listagem de Arquivos no Workspace
        self.register(
            name="workspace_list_files",
            schema={
                "type": "function",
                "function": {
                    "name": "workspace_list_files",
                    "description": "Lista os arquivos e tamanhos presentes dentro do workspace do Dot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subdirectory": {
                                "type": "string",
                                "description": "Subdiretório opcional para listar (default: raiz do workspace)."
                            }
                        },
                        "required": []
                    }
                }
            },
            handler=self._tool_list_workspace_files
        )

        # 6. Informações de Data e Hora
        self.register(
            name="get_current_time",
            schema={
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Retorna o horário atual do sistema do Raspberry Pi 4B (UTC).",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            handler=self._tool_current_time
        )

        # 7. Telemetria do Raspberry Pi 4B
        self.register(
            name="get_edge_telemetry",
            schema={
                "type": "function",
                "function": {
                    "name": "get_edge_telemetry",
                    "description": "Retorna a telemetria do Raspberry Pi 4B (temperatura do SoC Broadcom e memória).",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            handler=self._tool_edge_telemetry
        )

    # Implementações dos Handlers
    async def _tool_execute_shell(self, command: str, timeout_seconds: float = 30.0, dot_id: str = "default") -> dict[str, Any]:
        return await TerminalSandbox.execute(dot_id=dot_id, command=command, timeout_seconds=timeout_seconds)

    async def _tool_read_web_page(self, url: str) -> dict[str, Any]:
        return await WebReader.read_url(url=url)

    async def _tool_read_workspace_file(self, filename: str, dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.read_file(dot_id=dot_id, filename=filename)

    async def _tool_write_workspace_file(self, filename: str, content: str, dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.write_file(dot_id=dot_id, filename=filename, content=content)

    async def _tool_list_workspace_files(self, subdirectory: str = "", dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.list_files(dot_id=dot_id, subdirectory=subdirectory)

    async def _tool_current_time(self) -> dict[str, Any]:
        return {"current_time": datetime.utcnow().isoformat() + "Z"}

    async def _tool_edge_telemetry(self) -> dict[str, Any]:
        temp = 45.0
        thermal_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal_path):
            try:
                with open(thermal_path, "r") as f:
                    temp = round(float(f.read().strip()) / 1000.0, 1)
            except Exception:
                pass
        return {"soc_temperature_celsius": temp, "arch": "aarch64", "device": "Raspberry Pi 4B"}


registry = ToolRegistry()
