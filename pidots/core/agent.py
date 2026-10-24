"""
Motor de Agência Autônoma e Loop de Execução de Dot (piDots Agent Engine).
Implementa streaming de eventos do protocolo AG-UI e integração com o barramento HITL.
"""

import json
import uuid
import logging
from typing import AsyncGenerator, Any
from datetime import datetime, timezone

from ..config import settings
from ..storage.db import get_db
from ..storage.memory_manager import MemoryManager
from ..storage.shared_space import SharedSpaceManager
from ..providers.openai_client import OpenAIUniversalProvider, ProviderAuthError, ProviderEndpointError
from ..tools.registry import registry as default_tool_registry, ToolRegistry
from .hitl import HITLManager
from .planner import TwoStagePlanner

logger = logging.getLogger("pidots.agent")


class DotAgent:
    """Motor operacional autônomo associado a um Dot."""

    def __init__(
        self,
        dot_id: str,
        provider: OpenAIUniversalProvider | None = None,
        tool_registry: ToolRegistry | None = None
    ) -> None:
        self.dot_id = dot_id
        if provider is None:
            from ..providers.openai_client import OpenAIUniversalProvider
            self.provider = OpenAIUniversalProvider()
        else:
            self.provider = provider
        self.tools = tool_registry or default_tool_registry
        self.max_iterations = settings.max_iterations_per_goal

    @staticmethod
    async def _update_thread_status(thread_id: str, status: str) -> None:
        """Atualiza o estado de ciclo de vida da thread no SQLite."""
        try:
            async with get_db() as db:
                await db.execute(
                    "UPDATE threads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, thread_id)
                )
                await db.commit()
        except Exception as e:
            logger.debug("Falha ao atualizar status da thread %s para %s: %s", thread_id, status, e)

    async def run_thread(
        self,
        thread_id: str,
        user_message: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Executa o loop de raciocínio autônomo do Dot para uma thread.
        Emite eventos AG-UI via streaming assíncrono.
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Garante idempotência da thread antes de atualizar status
        try:
            async with get_db() as db:
                await db.execute(
                    """
                    INSERT OR IGNORE INTO threads (id, dot_id, title, status)
                    VALUES (?, ?, ?, 'running')
                    """,
                    (thread_id, self.dot_id, f"Thread {thread_id[:16]}")
                )
                await db.commit()
        except Exception as th_err:
            logger.debug("Falha ao garantir thread antes do run: %s", th_err)

        # Atualiza a thread para running no SQLite
        await self._update_thread_status(thread_id, "running")

        yield {
            "event": "run:started",
            "data": {
                "run_id": run_id,
                "thread_id": thread_id,
                "dot_id": self.dot_id,
                "timestamp": start_time.isoformat()
            }
        }

        is_hitl = False
        try:
            # 1. Carrega dados do Dot e histórico do SQLite
            dot_info, messages = await self._load_context(thread_id, user_message)
            if not dot_info:
                yield {
                    "event": "run:finished",
                    "data": {
                        "run_id": run_id,
                        "status": "failed",
                        "final_response": "",
                        "error": f"Dot '{self.dot_id}' não encontrado."
                    }
                }
                return

            # Poda Dinâmica de Ferramentas (Dynamic Tool Pruning)
            allowed_tools_raw = dot_info.get("allowed_tools_json")
            allowed_tools = None
            if allowed_tools_raw:
                try:
                    allowed_tools = json.loads(allowed_tools_raw) if isinstance(allowed_tools_raw, str) else allowed_tools_raw
                except Exception:
                    allowed_tools = None

            tool_defs = self.tools.get_tool_definitions(allowed_tools if allowed_tools else None)
            iteration = 0
            final_response_text = ""

            # 2. Loop de raciocínio multi-turn (teto estrito de iterações)
            while iteration < self.max_iterations:
                iteration += 1
                yield {
                    "event": "thought:delta",
                    "data": {
                        "run_id": run_id,
                        "iteration": iteration,
                        "thought": f"Analisando contexto e formulando resposta (Passo {iteration}/{self.max_iterations})..."
                    }
                }

                # Modelo a utilizar: se o Dot estiver com modelo mock ou nulo, usa o default_model do provedor
                model_to_use = dot_info.get("model")
                if not model_to_use or model_to_use in ("mock-model", "test-model"):
                    model_to_use = self.provider.default_model

                try:
                    # Chamada com Circuit Breaker ao provedor OpenAI-compativel
                    response = await self.provider.chat_completion(
                        messages=messages,
                        tools=tool_defs if tool_defs else None,
                        model=model_to_use
                    )
                except ProviderEndpointError as endp_err:
                    # Auto-Healing: se o modelo do Dot falhou com 404 e era diferente do default_model,
                    # retenta automaticamente com o default_model do provedor e persiste a correcao
                    if model_to_use != self.provider.default_model:
                        logger.warning(
                            "Modelo '%s' falhou no endpoint. Aplicando Auto-Healing para o modelo padrao '%s'...",
                            model_to_use, self.provider.default_model
                        )
                        try:
                            response = await self.provider.chat_completion(
                                messages=messages,
                                tools=tool_defs if tool_defs else None,
                                model=self.provider.default_model
                            )
                            # Atualiza o modelo do Dot no SQLite WAL para persistir a auto-cura
                            async with get_db() as db:
                                await db.execute(
                                    "UPDATE dots SET model = ? WHERE id = ?",
                                    (self.provider.default_model, self.dot_id)
                                )
                                await db.commit()
                            dot_info["model"] = self.provider.default_model
                        except Exception:
                            # Se mesmo com default_model falhar, segue para tratamento normal
                            err_msg = str(endp_err)
                            logger.error("Falha de endpoint/modelo com provedor de IA: %s", err_msg)

                            diag_msg_id = str(uuid.uuid4())
                            async with get_db() as db:
                                await db.execute(
                                    """
                                    INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log)
                                    VALUES (?, ?, 'assistant', ?, ?, 'dot', 'internal', ?)
                                    """,
                                    (diag_msg_id, thread_id, f"[FALHA DE ENDPOINT]: {err_msg}", self.dot_id, err_msg)
                                )
                                await db.commit()

                            yield {
                                "event": "thought:delta",
                                "data": {"run_id": run_id, "error": err_msg}
                            }
                            yield {
                                "event": "run:finished",
                                "data": {
                                    "run_id": run_id,
                                    "status": "failed",
                                    "final_response": "",
                                    "error": err_msg,
                                    "error_type": "endpoint_error"
                                }
                            }
                            return
                    else:
                        err_msg = str(endp_err)
                        logger.error("Falha de endpoint/modelo com provedor de IA: %s", err_msg)

                        diag_msg_id = str(uuid.uuid4())
                        async with get_db() as db:
                            await db.execute(
                                """
                                INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log)
                                VALUES (?, ?, 'assistant', ?, ?, 'dot', 'internal', ?)
                                """,
                                (diag_msg_id, thread_id, f"[FALHA DE ENDPOINT]: {err_msg}", self.dot_id, err_msg)
                            )
                            await db.commit()

                        yield {
                            "event": "thought:delta",
                            "data": {"run_id": run_id, "error": err_msg}
                        }
                        yield {
                            "event": "run:finished",
                            "data": {
                                "run_id": run_id,
                                "status": "failed",
                                "final_response": "",
                                "error": err_msg,
                                "error_type": "endpoint_error"
                            }
                        }
                        return
                except ProviderAuthError as auth_err:
                    err_msg = str(auth_err)
                    logger.error("Falha de autenticação com provedor de IA: %s", err_msg)
                    
                    # Persiste mensagem interna de diagnóstico no SQLite WAL
                    diag_msg_id = str(uuid.uuid4())
                    async with get_db() as db:
                        await db.execute(
                            """
                            INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log)
                            VALUES (?, ?, 'assistant', ?, ?, 'dot', 'internal', ?)
                            """,
                            (diag_msg_id, thread_id, f"[FALHA DE AUTENTICAÇÃO]: {err_msg}", self.dot_id, err_msg)
                        )
                        await db.commit()

                    yield {
                        "event": "thought:delta",
                        "data": {"run_id": run_id, "error": err_msg}
                    }
                    yield {
                        "event": "run:finished",
                        "data": {
                            "run_id": run_id,
                            "status": "failed",
                            "final_response": "",
                            "error": err_msg,
                            "error_type": "auth_error"
                        }
                    }
                    return
                except Exception as e:
                    err_msg = str(e)
                    logger.error("Erro na chamada de inferência: %s", err_msg)
                    
                    # Persiste mensagem interna de diagnóstico no SQLite WAL
                    diag_msg_id = str(uuid.uuid4())
                    async with get_db() as db:
                        await db.execute(
                            """
                            INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log)
                            VALUES (?, ?, 'assistant', ?, ?, 'dot', 'internal', ?)
                            """,
                            (diag_msg_id, thread_id, f"[FALHA DE INFERÊNCIA]: {err_msg}", self.dot_id, err_msg)
                        )
                        await db.commit()

                    yield {
                        "event": "thought:delta",
                        "data": {"run_id": run_id, "error": f"Falha de conexão com provedor: {err_msg}"}
                    }
                    yield {
                        "event": "run:finished",
                        "data": {
                            "run_id": run_id,
                            "status": "failed",
                            "final_response": "",
                            "error": err_msg,
                            "error_type": "transient_error"
                        }
                    }
                    return

                choice = response.get("choices", [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                tool_calls = msg.get("tool_calls", [])

                if content:
                    final_response_text += content
                    yield {
                        "event": "thought:delta",
                        "data": {"run_id": run_id, "content_chunk": content}
                    }

                # Caso 1: O modelo requisitou chamadas de ferramentas
                if tool_calls:
                    # Adiciona mensagem do assistente contendo as chamadas de ferramenta
                    messages.append(msg)

                    # Persiste a mensagem do assistente com tool_calls no SQLite WAL
                    try:
                        assistant_call_msg_id = str(uuid.uuid4())
                        async with get_db() as db:
                            await db.execute(
                                """
                                INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log, tool_calls_json)
                                VALUES (?, ?, 'assistant', ?, ?, 'dot', 'internal', ?, ?)
                                """,
                                (assistant_call_msg_id, thread_id, content or "", self.dot_id, content or "", json.dumps(tool_calls, ensure_ascii=False))
                            )
                            await db.commit()
                    except Exception as save_err:
                        logger.debug("Falha ao salvar chamada de ferramenta do assistente: %s", save_err)

                    for call in tool_calls:
                        call_id = call.get("id", str(uuid.uuid4()))
                        func = call.get("function", {})
                        fn_name = func.get("name")
                        try:
                            args = json.loads(func.get("arguments", "{}"))
                        except Exception:
                            args = {}

                        # Validação de Governança Human-in-the-Loop
                        serialized_args = json.dumps(args)
                        requires_hitl, risk = HITLManager.requires_approval(fn_name, serialized_args)
                        if requires_hitl and not await HITLManager.has_prior_approval(
                            dot_id=self.dot_id,
                            thread_id=thread_id,
                            action_type=fn_name,
                            payload=serialized_args
                        ):
                            approval_id = await HITLManager.create_approval_request(
                                dot_id=self.dot_id,
                                thread_id=thread_id,
                                action_type=fn_name,
                                payload=serialized_args,
                                risk_level=risk
                            )
                            yield {
                                "event": "hitl:pending_approval",
                                "data": {
                                    "run_id": run_id,
                                    "approval_id": approval_id,
                                    "tool_name": fn_name,
                                    "arguments": args,
                                    "risk_level": risk,
                                    "ttl_minutes": 30
                                }
                            }
                            yield {
                                "event": "hitl:approval_required",
                                "data": {
                                    "run_id": run_id,
                                    "approval_id": approval_id,
                                    "tool_name": fn_name,
                                    "arguments": args,
                                    "risk_level": risk
                                }
                            }
                            # Persiste aviso transparente no chat para evitar silêncio aparente
                            hitl_notice = (
                                f"[GOVERNANCA HITL // ACAO RETIDA]\n"
                                f"O agente '{self.dot_id}' solicitou a acao '{fn_name}' (Risco: {risk}), "
                                f"que requer autorizacao expressa do operador humano.\n"
                                f"ID de Aprovacao: {approval_id}\n"
                                f"Instrucao: Homologue a execucao na aba de governanca HITL ou via comando /hitl."
                            )
                            async with get_db() as db:
                                await db.execute(
                                    """
                                    INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility, thought_log)
                                    VALUES (?, ?, 'assistant', ?, ?, 'dot', 'public', ?)
                                    """,
                                    (str(uuid.uuid4()), thread_id, hitl_notice, self.dot_id, hitl_notice)
                                )
                                await db.commit()

                            # Interrompe o run retendo status awaiting_hitl
                            is_hitl = True
                            await self._update_thread_status(thread_id, "awaiting_hitl")
                            yield {
                                "event": "run:finished",
                                "data": {"run_id": run_id, "status": "awaiting_hitl"}
                            }
                            return

                        # Execução segura da ferramenta
                        yield {
                            "event": "tool:called",
                            "data": {"run_id": run_id, "call_id": call_id, "name": fn_name, "arguments": args}
                        }

                        t_start = datetime.now(timezone.utc)
                        tool_result = await self.tools.execute_tool(
                            fn_name,
                            args,
                            dot_id=self.dot_id,
                            thread_id=thread_id,
                            provider=self.provider
                        )
                        t_duration = int((datetime.now(timezone.utc) - t_start).total_seconds() * 1000)

                        # Persiste auditoria em tool_runs para ferramentas gerais (terminal possui gravação própria)
                        if fn_name != "execute_shell_command":
                            try:
                                async with get_db() as db:
                                    res_str = json.dumps(tool_result, ensure_ascii=False) if isinstance(tool_result, (dict, list)) else str(tool_result)
                                    err_str = str(tool_result.get("error", "")) if isinstance(tool_result, dict) else ""
                                    await db.execute(
                                        """
                                        INSERT INTO tool_runs (id, dot_id, tool_name, arguments_json, exit_code, stdout_text, stderr_text, duration_ms)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            call_id,
                                            self.dot_id,
                                            fn_name,
                                            json.dumps(args, ensure_ascii=False),
                                            1 if err_str else 0,
                                            res_str[:10000],
                                            err_str[:10000],
                                            t_duration
                                        )
                                    )
                                    await db.commit()
                            except Exception as audit_err:
                                logger.debug("Falha ao registrar auditoria em tool_runs para %s: %s", fn_name, audit_err)

                        yield {
                            "event": "tool:result",
                            "data": {
                                "run_id": run_id,
                                "call_id": call_id,
                                "name": fn_name,
                                "result": tool_result,
                                "duration_ms": t_duration
                            }
                        }

                        # Emissão de Eventos AG-UI / CoAgents Shared State Sync
                        if fn_name == "workspace_write_file" and isinstance(tool_result, dict) and not tool_result.get("error"):
                            written_file = args.get("filename") or args.get("filepath") or "artifact.md"
                            written_content = args.get("content", "")
                            yield {
                                "event": "artifact:updated",
                                "data": {
                                    "run_id": run_id,
                                    "dot_id": self.dot_id,
                                    "filename": written_file,
                                    "space_id": tool_result.get("space_id") or written_file,
                                    "version": tool_result.get("version", 1),
                                    "content": written_content,
                                    "canvas_patch": written_content
                                }
                            }
                            yield {
                                "event": "canvas:patch",
                                "data": {
                                    "run_id": run_id,
                                    "dot_id": self.dot_id,
                                    "filename": written_file,
                                    "content": written_content,
                                    "canvas_patch": written_content
                                }
                            }
                        elif fn_name in ("plan_create", "plan_update_step", "plan_get_status"):
                            yield {
                                "event": "state:sync",
                                "data": {
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "dot_id": self.dot_id,
                                    "sync_type": "plan",
                                    "state_data": tool_result
                                }
                            }
                        elif fn_name in ("core_memory_append", "core_memory_replace", "archival_memory_insert"):
                            yield {
                                "event": "state:sync",
                                "data": {
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "dot_id": self.dot_id,
                                    "sync_type": "memory",
                                    "state_data": tool_result
                                }
                            }
                        elif fn_name == "shared_space_write":
                            yield {
                                "event": "state:sync",
                                "data": {
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "dot_id": self.dot_id,
                                    "sync_type": "shared_space",
                                    "state_data": tool_result
                                }
                            }
                        elif fn_name in ("delegate_task", "handoff_to_dot", "run_council_debate"):
                            yield {
                                "event": "state:sync",
                                "data": {
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "dot_id": self.dot_id,
                                    "sync_type": fn_name,
                                    "state_data": tool_result
                                }
                            }

                        # Se a ferramenta acionou Self-Healing Harness, emite evento de diagnóstico
                        if isinstance(tool_result, dict) and tool_result.get("self_healing_details"):
                            healing_info = tool_result["self_healing_details"]
                            yield {
                                "event": "self_healing:triggered",
                                "data": {
                                    "run_id": run_id,
                                    "call_id": call_id,
                                    "tool_name": fn_name,
                                    "attempt": healing_info.get("attempt", 1),
                                    "max_attempts": healing_info.get("max_attempts", 2),
                                    "max_attempts_exceeded": healing_info.get("max_attempts_exceeded", False),
                                    "escalate_to": healing_info.get("escalate_to"),
                                    "error_type": healing_info.get("error_type"),
                                    "target_file": healing_info.get("target_file"),
                                    "target_line": healing_info.get("target_line"),
                                    "diagnosis": healing_info.get("diagnosis")
                                }
                            }
                            if healing_info.get("max_attempts_exceeded"):
                                yield {
                                    "event": "self_healing:max_attempts_exceeded",
                                    "data": {
                                        "run_id": run_id,
                                        "tool_name": fn_name,
                                        "escalate_to": healing_info.get("escalate_to"),
                                        "diagnosis": healing_info.get("diagnosis")
                                    }
                                }

                        # Registra resultado no contexto
                        tool_content_str = json.dumps(tool_result, ensure_ascii=False) if isinstance(tool_result, (dict, list)) else str(tool_result)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": fn_name,
                            "content": tool_content_str
                        })

                        # Persiste o retorno da ferramenta no SQLite WAL
                        try:
                            tool_msg_id = str(uuid.uuid4())
                            async with get_db() as db:
                                await db.execute(
                                    """
                                    INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                                    VALUES (?, ?, 'tool', ?, ?, 'dot', 'internal')
                                    """,
                                    (tool_msg_id, thread_id, tool_content_str, self.dot_id)
                                )
                                await db.commit()
                        except Exception as save_err:
                            logger.debug("Falha ao salvar retorno de ferramenta no SQLite: %s", save_err)

                    # Continua o loop para a próxima iteração com os resultados das ferramentas
                    continue

                # Caso 2: Resposta finalizada sem ferramentas
                break

            # 3. Salva resposta final do assistente no banco SQLite WAL
            if final_response_text:
                msg_id = str(uuid.uuid4())
                async with get_db() as db:
                    await db.execute(
                        """
                        INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                        VALUES (?, ?, 'assistant', ?, ?, 'dot', 'public')
                        """,
                        (msg_id, thread_id, final_response_text, self.dot_id)
                    )
                    await db.commit()

            yield {
                "event": "run:finished",
                "data": {
                    "run_id": run_id,
                    "status": "completed",
                    "iterations": iteration,
                    "duration_seconds": round((datetime.now(timezone.utc) - start_time).total_seconds(), 2),
                    "final_response": final_response_text,
                    "error": None
                }
            }
        finally:
            if not is_hitl:
                await self._update_thread_status(thread_id, "idle")

    async def _load_context(
        self,
        thread_id: str,
        user_message: str | None
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Carrega persona do Dot e mensagens anteriores com suporte a multi-ator."""
        async with get_db() as db:
            # Obtém Dot
            cursor = await db.execute("SELECT * FROM dots WHERE id = ?", (self.dot_id,))
            dot_row = await cursor.fetchone()
            if not dot_row:
                return None, []
            dot_info = dict(dot_row)

            # Garante que a thread exista antes de inserir mensagem para evitar IntegrityError
            await db.execute(
                """
                INSERT OR IGNORE INTO threads (id, dot_id, title, status)
                VALUES (?, ?, ?, 'idle')
                """,
                (thread_id, self.dot_id, f"Thread {thread_id[:16]}")
            )

            # Se houver nova mensagem do usuário, salva no SQLite
            if user_message:
                u_msg_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO messages (id, thread_id, role, content, actor_id, actor_type, visibility)
                    VALUES (?, ?, 'user', ?, 'user', 'user', 'public')
                    """,
                    (u_msg_id, thread_id, user_message)
                )
                await db.commit()

            # Obtém histórico da thread (filtrando mensagens públicas ou direcionadas a este Dot)
            cursor = await db.execute(
                """
                SELECT role, content, actor_id, actor_type, tool_calls_json FROM (
                    SELECT rowid AS rid, role, content, actor_id, actor_type, tool_calls_json, created_at FROM messages
                    WHERE thread_id = ? AND (visibility = 'public' OR target_dot_id = ? OR actor_id = ?)
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT 20
                ) ORDER BY created_at ASC, rid ASC
                """,
                (thread_id, self.dot_id, self.dot_id)
            )
            rows = await cursor.fetchall()

        # Injeção de Core Memory estruturada (Padrão MemGPT / Letta)
        core_memory_xml = await MemoryManager.format_core_memory_prompt(
            dot_id=self.dot_id,
            default_persona=dot_info["system_prompt"]
        )

        # Injeção de Plano Ativo (Two-Stage Planning com Checkpoints)
        plan_xml = await TwoStagePlanner.format_plan_prompt(thread_id, self.dot_id)
        plan_section = f"\n\n{plan_xml}" if plan_xml else ""

        # Injeção de Espaço de Conhecimento Compartilhado (Shared Knowledge Space)
        shared_space_xml = await SharedSpaceManager.format_shared_space_prompt(thread_id)
        shared_space_section = f"\n\n{shared_space_xml}" if shared_space_xml else ""

        system_content = (
            f"{dot_info['system_prompt']}\n\n"
            f"{core_memory_xml}"
            f"{plan_section}"
            f"{shared_space_section}\n\n"
            "DIRETRIZES OPERACIONAIS COGNITIVAS:\n"
            "1. GESTÃO DE MEMÓRIA: Sua memória primária está no bloco <core_memory>. Use 'core_memory_append' ou 'core_memory_replace' para gravar preferências do operador (<human>), atualizações de persona (<persona>) ou contexto ativo (<active_context>). Use 'archival_memory_insert'/'archival_memory_search' para conhecimentos duradouros.\n"
            "2. PLANEJAMENTO EM DUAS ETAPAS (Two-Stage Planning): Para tarefas complexas ou com múltiplos passos, utilize a ferramenta 'plan_create' para decompor a meta em marcos ordenados. Conforme concluir cada marco, invoque 'plan_update_step' registrando a evidência técnica comprovada.\n"
            "3. AUTO-CORREÇÃO (Self-Healing Harness): Se a execução de comandos ou validações resultar em falha técnica ('needs_healing': True), não entregue a resposta com erro ao operador. Examine o diagnóstico em 'self_healing_advice', inspecione o código via 'workspace_read_file', aplique a correção com 'workspace_write_file' e reexecute a verificação com 'execute_and_verify' ou 'execute_shell_command' até a resolução definitiva.\n"
            "4. CONSELHO CONSULTIVO (Dialética Multi-Bot): Para deliberações de arquitetura sensíveis ou consenso entre especialistas, utilize a ferramenta 'run_council_debate' para promover uma rodada formal de debate entre o Propositor (@coder), Auditor Crítico (@auditor) e Supervisor (@supervisor).\n"
            "5. ESPAÇO DE CONHECIMENTO COMPARTILHADO (Shared Knowledge Space): Utilize 'shared_space_write' para registrar notas, contratos ou decisões que outros Dots devam consultar nesta thread, e 'shared_space_read' para ler notas do espaço comum."
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_content}
        ]
        for r in rows:
            entry: dict[str, Any] = {"role": r["role"], "content": r["content"]}
            if r["tool_calls_json"]:
                try:
                    entry["tool_calls"] = json.loads(r["tool_calls_json"])
                except Exception:
                    pass
            actor = r["actor_id"] if "actor_id" in r.keys() else None
            if actor and r["role"] not in ("tool", "system"):
                entry["name"] = actor.replace("-", "_")[:64]
            messages.append(entry)

        return dot_info, messages
