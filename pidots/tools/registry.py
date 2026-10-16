"""
Registro central de ferramentas operacionais do piDots.
Formatação compatível com a especificação da OpenAI API (Function Calling).
Inclui terminal isolado (Bubblewrap/Subprocess), extrator web semântico e gerenciamento de arquivos.
"""

import inspect
import logging
from typing import Callable, Any, Awaitable
from datetime import datetime, timezone

from .terminal import TerminalSandbox
from .web_reader import WebReader
from .file_ops import FileManager
from ..storage.memory_manager import MemoryManager

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

    async def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        dot_id: str = "default",
        thread_id: str | None = None,
        provider: Any = None
    ) -> dict[str, Any]:
        """Executa o handler de uma ferramenta registrada injetando dot_id, thread_id e provider se aplicável."""
        if name not in self._handlers:
            return {"error": f"Ferramenta '{name}' não encontrada no registro."}
        try:
            handler = self._handlers[name]
            # Assegura que arguments seja sempre um dicionário válido
            if arguments is None:
                arguments = {}
            else:
                arguments = dict(arguments)

            # Injeta argumentos contextuais conforme a ferramenta
            if name in (
                "execute_shell_command", "execute_and_verify", "workspace_read_file", "workspace_write_file", "workspace_list_files",
                "core_memory_append", "core_memory_replace", "archival_memory_insert", "archival_memory_search"
            ):
                if "dot_id" not in arguments:
                    arguments["dot_id"] = dot_id
            elif name == "recall_memory_search":
                if "thread_id" not in arguments and thread_id:
                    arguments["thread_id"] = thread_id
            elif name in ("plan_get_status", "plan_create", "shared_space_write", "shared_space_read"):
                if "dot_id" not in arguments:
                    arguments["dot_id"] = dot_id
                if "thread_id" not in arguments and thread_id:
                    arguments["thread_id"] = thread_id
            elif name == "delegate_task":
                arguments["source_dot_id"] = dot_id
                if "thread_id" not in arguments and thread_id:
                    arguments["thread_id"] = thread_id
                if "provider" not in arguments and provider:
                    arguments["provider"] = provider
            elif name == "run_council_debate":
                if "thread_id" not in arguments and thread_id:
                    arguments["thread_id"] = thread_id
                if "provider" not in arguments and provider:
                    arguments["provider"] = provider
            elif name == "handoff_to_dot":
                arguments["source_dot_id"] = dot_id
                if "thread_id" not in arguments and thread_id:
                    arguments["thread_id"] = thread_id
            elif name == "edge_maintenance_run":
                if "dot_id" not in arguments:
                    arguments["dot_id"] = dot_id

            # Filtra argumentos alucinados se a função não aceitar **kwargs arbitrários
            sig = inspect.signature(handler)
            has_var_keyword = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
            if not has_var_keyword:
                arguments = {k: v for k, v in arguments.items() if k in sig.parameters}

            return await handler(**arguments)
        except TypeError as te:
            logger.warning("Argumentos incompletos ou inválidos para a ferramenta %s: %s", name, str(te))
            return {"error": f"Argumentos incompletos para a ferramenta '{name}': {str(te)}"}
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

        # 8. Delegação de Subtarefa Inter-Agente (Supervisor-Worker)
        self.register(
            name="delegate_task",
            schema={
                "type": "function",
                "function": {
                    "name": "delegate_task",
                    "description": "Delega uma subtarefa técnica para outro Dot especialista (ex: dot-coder, dot-auditor) em contexto isolado e aguarda a conclusão sintetizada.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_dot_id": {
                                "type": "string",
                                "description": "ID do Dot especialista destinatário que executará a subtarefa."
                            },
                            "task_goal": {
                                "type": "string",
                                "description": "Descrição clara do objetivo e da entrega esperada da subtarefa."
                            },
                            "context_snippet": {
                                "type": "string",
                                "description": "Trecho opcional de código, comandos ou contexto necessário para a execução."
                            }
                        },
                        "required": ["target_dot_id", "task_goal"]
                    }
                }
            },
            handler=self._tool_delegate_task
        )

        # 9. Transferência de Liderança (Handoff)
        self.register(
            name="handoff_to_dot",
            schema={
                "type": "function",
                "function": {
                    "name": "handoff_to_dot",
                    "description": "Transfere formalmente a liderança da conversa para outro Dot especialista quando o objetivo ultrapassar sua área de domínio.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_dot_id": {
                                "type": "string",
                                "description": "ID do Dot que assumirá o comando da thread."
                            },
                            "reason": {
                                "type": "string",
                                "description": "Justificativa operacional e técnica para a transferência de titularidade."
                            }
                        },
                        "required": ["target_dot_id", "reason"]
                    }
                }
            },
            handler=self._tool_handoff_to_dot
        )

        # 10. Auto-Edição de Memória Primária (Append)
        self.register(
            name="core_memory_append",
            schema={
                "type": "function",
                "function": {
                    "name": "core_memory_append",
                    "description": "Anexa uma nova informação ao final de uma seção da sua memória de trabalho primária (Core Memory).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {
                                "type": "string",
                                "enum": ["persona", "human", "active_context"],
                                "description": "Seção alvo da Core Memory ('human' para preferências do operador, 'persona' para fatos sobre si, 'active_context' para metas ativas)."
                            },
                            "content": {
                                "type": "string",
                                "description": "Texto a ser anexado à seção."
                            }
                        },
                        "required": ["section", "content"]
                    }
                }
            },
            handler=self._tool_core_memory_append
        )

        # 11. Auto-Edição de Memória Primária (Replace)
        self.register(
            name="core_memory_replace",
            schema={
                "type": "function",
                "function": {
                    "name": "core_memory_replace",
                    "description": "Substitui um trecho específico de informação na sua memória primária (Core Memory), eliminando dados obsoletos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {
                                "type": "string",
                                "enum": ["persona", "human", "active_context"],
                                "description": "Seção alvo da Core Memory ('human', 'persona', 'active_context')."
                            },
                            "old_content": {
                                "type": "string",
                                "description": "Trecho exato do texto atual que deve ser substituído."
                            },
                            "new_content": {
                                "type": "string",
                                "description": "Novo texto que substituirá o trecho antigo."
                            }
                        },
                        "required": ["section", "old_content", "new_content"]
                    }
                }
            },
            handler=self._tool_core_memory_replace
        )

        # 12. Gravação em Memória Arquivística Duradoura
        self.register(
            name="archival_memory_insert",
            schema={
                "type": "function",
                "function": {
                    "name": "archival_memory_insert",
                    "description": "Grava um fato duradouro, lição aprendida ou resumo técnico na memória permanente arquivística com indexação BM25 e vetorial.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Conteúdo factual ou técnico a ser arquivado permanentemente."
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista opcional de tags temáticas para indexação."
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            handler=self._tool_archival_memory_insert
        )

        # 13. Busca Híbrida em Memória Arquivística
        self.register(
            name="archival_memory_search",
            schema={
                "type": "function",
                "function": {
                    "name": "archival_memory_search",
                    "description": "Pesquisa na memória permanente arquivística usando busca híbrida (FTS5 BM25 + Projeção Vetorial 64d).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Termo de busca ou pergunta para localizar memórias relevantes."
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de memórias a recuperar (padrão: 5)."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            handler=self._tool_archival_memory_search
        )

        # 14. Busca Retrospectiva no Diálogo (Recall Memory)
        self.register(
            name="recall_memory_search",
            schema={
                "type": "function",
                "function": {
                    "name": "recall_memory_search",
                    "description": "Pesquisa retrospectiva no histórico de mensagens arquivadas da thread atual.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Palavra-chave ou trecho a ser pesquisado nas mensagens passadas."
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de mensagens a recuperar (padrão: 5)."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            handler=self._tool_recall_memory_search
        )

        # 15. Execução com Verificação e Self-Healing Harness
        self.register(
            name="execute_and_verify",
            schema={
                "type": "function",
                "function": {
                    "name": "execute_and_verify",
                    "description": "Executa comando bash isolado de teste/validação e aciona o Self-Healing Harness em caso de falha ou traceback.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando de teste ou verificação a ser executado (ex: 'python3 -m unittest test_app.py', 'pytest', 'python3 script.py')."
                            },
                            "timeout_seconds": {
                                "type": "number",
                                "description": "Timeout em segundos antes de abortar o processo (padrão: 30)."
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            handler=self._tool_execute_and_verify
        )

        # 16. Planejamento em Duas Etapas (Criação de Metas e Marcos)
        self.register(
            name="plan_create",
            schema={
                "type": "function",
                "function": {
                    "name": "plan_create",
                    "description": "Cria um plano de execução estruturado (Goal) decomposto em marcos sequenciais (Milestones) para guiar a tarefa fase a fase.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Título claro do plano ou objetivo principal."
                            },
                            "description": {
                                "type": "string",
                                "description": "Descrição detalhada do escopo e requisitos da meta."
                            },
                            "milestones": {
                                "type": "array",
                                "description": "Lista de marcos ordenados a serem cumpridos com critérios de aceitação.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Título do marco (ex: 'Fase 1: Implementar módulo de persistência')."
                                        },
                                        "acceptance_criteria": {
                                            "type": "string",
                                            "description": "Critério objetivo de validação e sucesso deste marco."
                                        }
                                    },
                                    "required": ["title", "acceptance_criteria"]
                                }
                            }
                        },
                        "required": ["title", "milestones"]
                    }
                }
            },
            handler=self._tool_plan_create
        )

        # 17. Atualização de Marco do Plano (Checkpoint e Evidência)
        self.register(
            name="plan_update_step",
            schema={
                "type": "function",
                "function": {
                    "name": "plan_update_step",
                    "description": "Atualiza o status de um marco do plano de execução registrando evidência técnica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "milestone_id": {
                                "type": "string",
                                "description": "Identificador único do marco a ser atualizado."
                            },
                            "status": {
                                "type": "string",
                                "enum": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"],
                                "description": "Novo status do marco ('IN_PROGRESS', 'COMPLETED', 'FAILED')."
                            },
                            "evidence_summary": {
                                "type": "string",
                                "description": "Resumo técnico da evidência comprovando a conclusão ou falha do critério."
                            }
                        },
                        "required": ["milestone_id", "status"]
                    }
                }
            },
            handler=self._tool_plan_update_step
        )

        # 18. Consulta de Status do Plano Ativo
        self.register(
            name="plan_get_status",
            schema={
                "type": "function",
                "function": {
                    "name": "plan_get_status",
                    "description": "Consulta o progresso percentual, marcos pendentes e concluídos do plano de execução ativo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_id": {
                                "type": "string",
                                "description": "ID específico do plano (opcional; se omitido, busca o plano ativo da thread)."
                            }
                        },
                        "required": []
                    }
                }
            },
            handler=self._tool_plan_get_status
        )

        # 19. Conselho Consultivo e Debate Dialético Multi-Bot
        self.register(
            name="run_council_debate",
            schema={
                "type": "function",
                "function": {
                    "name": "run_council_debate",
                    "description": "Convoca uma rodada formal de deliberação do Conselho Consultivo entre Propositor (@coder), Auditor Crítico (@auditor) e Supervisor (@supervisor).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Tópico técnico, problema de arquitetura ou proposta de código a ser deliberada."
                            },
                            "proponent_dot_id": {
                                "type": "string",
                                "description": "ID do Dot que formulará a proposta (padrão: 'dot-coder')."
                            },
                            "critic_dot_id": {
                                "type": "string",
                                "description": "ID do Dot que realizará a auditoria crítica (padrão: 'dot-auditor')."
                            },
                            "supervisor_dot_id": {
                                "type": "string",
                                "description": "ID do Dot supervisor que mediará e emitirá o veredito final (padrão: 'dot-supervisor')."
                            },
                            "rounds": {
                                "type": "integer",
                                "description": "Número de rodadas de debate/réplica (padrão: 1, máx: 3)."
                            }
                        },
                        "required": ["topic"]
                    }
                }
            },
            handler=self._tool_run_council_debate
        )

        # 20. Escrita no Espaço de Conhecimento Compartilhado (Shared Knowledge Space)
        self.register(
            name="shared_space_write",
            schema={
                "type": "function",
                "function": {
                    "name": "shared_space_write",
                    "description": "Grava ou atualiza uma nota técnica compartilhada no quadro de conhecimento comum da thread, visível a todos os Dots participantes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic_key": {
                                "type": "string",
                                "description": "Identificador do tópico compartilhado (ex: 'arquitetura_banco', 'analise_vulnerabilidades', 'endpoints_api')."
                            },
                            "content": {
                                "type": "string",
                                "description": "Conteúdo factual, código, diagrama ou especificação técnica a ser compartilhado."
                            }
                        },
                        "required": ["topic_key", "content"]
                    }
                }
            },
            handler=self._tool_shared_space_write
        )

        # 21. Leitura no Espaço de Conhecimento Compartilhado
        self.register(
            name="shared_space_read",
            schema={
                "type": "function",
                "function": {
                    "name": "shared_space_read",
                    "description": "Lê uma nota técnica específica ou lista todos os tópicos disponíveis no espaço de conhecimento compartilhado da thread.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic_key": {
                                "type": "string",
                                "description": "Identificador do tópico a ser lido (opcional; se omitido, retorna a lista de todos os tópicos da thread)."
                            }
                        },
                        "required": []
                    }
                }
            },
            handler=self._tool_shared_space_read
        )

        # 22. Verificação de Triggers de Hardware Edge
        self.register(
            name="hardware_trigger_check",
            schema={
                "type": "function",
                "function": {
                    "name": "hardware_trigger_check",
                    "description": "Avalia em tempo real os limites operacionais de hardware do Raspberry Pi 4B (temperatura do SoC Broadcom, espaço livre no cartão MicroSD e memória RAM), reportando anomalias ou violações de limiares.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thermal_limit_celsius": {
                                "type": "number",
                                "description": "Teto customizado de temperatura em °C para avaliação (opcional, padrão do sistema: 72.0°C)."
                            },
                            "disk_min_free_percent": {
                                "type": "number",
                                "description": "Percentual mínimo customizado de espaço livre em disco antes de alerta (opcional, padrão: 10.0%)."
                            }
                        },
                        "required": []
                    }
                }
            },
            handler=self._tool_hardware_trigger_check
        )

        # 23. Rotina de Manutenção Noturna Autônoma e Preservação de MicroSD
        self.register(
            name="edge_maintenance_run",
            schema={
                "type": "function",
                "function": {
                    "name": "edge_maintenance_run",
                    "description": "Executa a suíte de manutenção autônoma do piDots: checkpoint WAL TRUNCATE, consolidação de mensagens históricas em memórias episódicas, backup atômico opcional com VACUUM INTO e otimização de índices SQLite.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_threshold": {
                                "type": "integer",
                                "description": "Limiar em dias para consolidação e poda de mensagens antigas da tabela de histórico (padrão: 7 dias)."
                            },
                            "create_backup": {
                                "type": "boolean",
                                "description": "Se verdadeiro, gera cópia atômica consistente do banco SQLite em data/backups via VACUUM INTO (padrão: false)."
                            }
                        },
                        "required": []
                    }
                }
            },
            handler=self._tool_edge_maintenance_run
        )

    # Implementações dos Handlers

    async def _tool_execute_shell(self, command: str, timeout_seconds: float = 30.0, dot_id: str = "default") -> dict[str, Any]:
        result = await TerminalSandbox.execute(dot_id=dot_id, command=command, timeout_seconds=timeout_seconds)
        healing = self._get_self_healing().inspect_execution_result("execute_shell_command", {"command": command}, result)
        if healing:
            result["self_healing_advice"] = healing["diagnosis"]
            result["self_healing_details"] = healing
        return result

    async def _tool_read_web_page(self, url: str) -> dict[str, Any]:
        return await WebReader.read_url(url=url)

    async def _tool_read_workspace_file(self, filename: str, dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.read_file(dot_id=dot_id, filename=filename)

    async def _tool_write_workspace_file(self, filename: str, content: str, dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.write_file(dot_id=dot_id, filename=filename, content=content, sync_space=True)

    async def _tool_list_workspace_files(self, subdirectory: str = "", dot_id: str = "default") -> dict[str, Any]:
        return await FileManager.list_files(dot_id=dot_id, subdirectory=subdirectory)

    async def _tool_current_time(self) -> dict[str, Any]:
        return {"current_time": datetime.now(timezone.utc).isoformat()}

    async def _tool_edge_telemetry(self) -> dict[str, Any]:
        hw = self._get_hardware_triggers()
        temp = hw.get_soc_temperature()
        mem = hw.get_memory_metrics()
        return {
            "soc_temperature_celsius": temp,
            "memory": mem,
            "arch": "aarch64",
            "device": "Raspberry Pi 4B"
        }

    @staticmethod
    def _get_orchestrator():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..core.orchestrator import MultiBotOrchestrator
        return MultiBotOrchestrator

    @staticmethod
    def _get_self_healing():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..core.self_healing import SelfHealingHarness
        return SelfHealingHarness

    @staticmethod
    def _get_planner():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..core.planner import TwoStagePlanner
        return TwoStagePlanner

    @staticmethod
    def _get_council():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..core.council import CouncilOrchestrator
        return CouncilOrchestrator

    @staticmethod
    def _get_shared_space():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..storage.shared_space import SharedSpaceManager
        return SharedSpaceManager

    @staticmethod
    def _get_hardware_triggers():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..core.edge_triggers import EdgeHardwareTriggers
        return EdgeHardwareTriggers

    @staticmethod
    def _get_maintenance_manager():
        """Importador sob demanda para desacoplar dependências circulares em tempo de import."""
        from ..storage.maintenance import EdgeMaintenanceManager
        return EdgeMaintenanceManager


    async def _tool_delegate_task(
        self,
        target_dot_id: str,
        task_goal: str,
        context_snippet: str | None = None,
        source_dot_id: str = "default",
        thread_id: str | None = None,
        provider: Any = None
    ) -> dict[str, Any]:
        if provider is None:
            from ..providers.openai_client import OpenAIUniversalProvider
            provider = OpenAIUniversalProvider()
        orchestrator = self._get_orchestrator()
        t_id = thread_id or "default-thread"
        return await orchestrator.delegate_subtask(
            thread_id=t_id,
            source_dot_id=source_dot_id,
            target_dot_id=target_dot_id,
            task_goal=task_goal,
            context_snippet=context_snippet,
            provider=provider
        )

    async def _tool_handoff_to_dot(
        self,
        target_dot_id: str,
        reason: str,
        source_dot_id: str = "default",
        thread_id: str | None = None
    ) -> dict[str, Any]:
        orchestrator = self._get_orchestrator()
        t_id = thread_id or "default-thread"
        return await orchestrator.handoff_lead(
            thread_id=t_id,
            source_dot_id=source_dot_id,
            target_dot_id=target_dot_id,
            reason=reason
        )

    async def _tool_core_memory_append(self, section: str, content: str, dot_id: str = "default") -> dict[str, Any]:
        return await MemoryManager.append_core_memory(dot_id=dot_id, section=section, content=content)

    async def _tool_core_memory_replace(self, section: str, old_content: str, new_content: str, dot_id: str = "default") -> dict[str, Any]:
        return await MemoryManager.replace_core_memory(dot_id=dot_id, section=section, old_content=old_content, new_content=new_content)

    async def _tool_archival_memory_insert(self, content: str, tags: list[str] | None = None, dot_id: str = "default") -> dict[str, Any]:
        return await MemoryManager.insert_archival_memory(dot_id=dot_id, content=content, tags=tags)

    async def _tool_archival_memory_search(self, query: str, limit: int = 5, dot_id: str = "default") -> dict[str, Any]:
        results = await MemoryManager.search_archival_memory(dot_id=dot_id, query=query, limit=limit)
        return {"results": results, "count": len(results)}

    async def _tool_recall_memory_search(self, query: str, limit: int = 5, thread_id: str | None = None) -> dict[str, Any]:
        t_id = thread_id or "default-thread"
        results = await MemoryManager.search_recall_memory(thread_id=t_id, query=query, limit=limit)
        return {"results": results, "count": len(results)}

    async def _tool_execute_and_verify(
        self,
        command: str,
        timeout_seconds: float = 30.0,
        dot_id: str = "default"
    ) -> dict[str, Any]:
        """Executa comando de validação/teste e diagnostica falhas para auto-correção via Self-Healing."""
        result = await TerminalSandbox.execute(dot_id=dot_id, command=command, timeout_seconds=timeout_seconds)
        healing = self._get_self_healing().inspect_execution_result("execute_and_verify", {"command": command}, result)
        if healing:
            result["verified"] = False
            result["self_healing_advice"] = healing["diagnosis"]
            result["self_healing_details"] = healing
        else:
            result["verified"] = True
            result["verification_message"] = "Comando executado com sucesso e verificação técnica aprovada."
        return result

    async def _tool_plan_create(
        self,
        title: str,
        milestones: list[dict[str, str]],
        description: str = "",
        dot_id: str = "default",
        thread_id: str | None = None
    ) -> dict[str, Any]:
        return await self._get_planner().create_plan(
            dot_id=dot_id,
            thread_id=thread_id,
            title=title,
            milestones=milestones,
            description=description
        )

    async def _tool_plan_update_step(
        self,
        milestone_id: str,
        status: str,
        evidence_summary: str = ""
    ) -> dict[str, Any]:
        return await self._get_planner().update_milestone(
            milestone_id=milestone_id,
            status=status,
            evidence_summary=evidence_summary
        )

    async def _tool_plan_get_status(
        self,
        goal_id: str | None = None,
        dot_id: str = "default",
        thread_id: str | None = None
    ) -> dict[str, Any]:
        return await self._get_planner().get_plan_status(
            goal_id=goal_id,
            thread_id=thread_id,
            dot_id=dot_id
        )

    async def _tool_run_council_debate(
        self,
        topic: str,
        proponent_dot_id: str = "dot-coder",
        critic_dot_id: str = "dot-auditor",
        supervisor_dot_id: str = "dot-supervisor",
        rounds: int = 1,
        thread_id: str | None = None,
        provider: Any = None
    ) -> dict[str, Any]:
        """Executa deliberação formal entre Propositor, Crítico e Supervisor."""
        t_id = thread_id or "default-thread"
        return await self._get_council().run_debate(
            thread_id=t_id,
            topic=topic,
            proponent_dot_id=proponent_dot_id,
            critic_dot_id=critic_dot_id,
            supervisor_dot_id=supervisor_dot_id,
            rounds=rounds,
            provider=provider
        )

    async def _tool_shared_space_write(
        self,
        topic_key: str,
        content: str,
        dot_id: str = "default",
        thread_id: str | None = None
    ) -> dict[str, Any]:
        """Grava ou atualiza nota no espaço compartilhado da thread."""
        t_id = thread_id or "default-thread"
        return await self._get_shared_space().write_note(
            thread_id=t_id,
            dot_id=dot_id,
            topic_key=topic_key,
            content=content
        )

    async def _tool_shared_space_read(
        self,
        topic_key: str | None = None,
        dot_id: str = "default",
        thread_id: str | None = None
    ) -> dict[str, Any]:
        """Lê nota específica ou lista todas as notas do espaço compartilhado da thread."""
        t_id = thread_id or "default-thread"
        if topic_key:
            return await self._get_shared_space().read_note(
                thread_id=t_id,
                topic_key=topic_key
            )
        notes = await self._get_shared_space().list_notes(thread_id=t_id)
        return {"notes": notes, "count": len(notes)}

    async def _tool_hardware_trigger_check(
        self,
        thermal_limit_celsius: float | None = None,
        disk_min_free_percent: float | None = None
    ) -> dict[str, Any]:
        """Avalia telemetria e limites de hardware do nó Raspberry Pi."""
        return self._get_hardware_triggers().check_triggers(
            thermal_limit=thermal_limit_celsius,
            disk_min_free_percent=disk_min_free_percent
        )

    async def _tool_edge_maintenance_run(
        self,
        days_threshold: int = 7,
        create_backup: bool = False,
        dot_id: str = "default"
    ) -> dict[str, Any]:
        """Executa suíte de manutenção autônoma e compactação no SQLite."""
        backup_dir = None
        if create_backup:
            from pathlib import Path
            from ..config import settings
            backup_dir = str(Path(settings.sqlite_db_path).parent / "backups")

        return await self._get_maintenance_manager().run_full_maintenance(
            backup_dir=backup_dir,
            days_threshold=days_threshold,
            dot_id=dot_id if dot_id != "default" else None
        )


registry = ToolRegistry()

