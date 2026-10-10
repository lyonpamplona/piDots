"""
Motor de Agência Autônoma e Loop de Execução de Dot (piDots Agent Engine).
Implementa streaming de eventos do protocolo AG-UI e integração com o barramento HITL.
"""

import json
import uuid
import logging
from typing import AsyncGenerator, Any
from datetime import datetime

from ..config import settings
from ..storage.db import get_db
from ..providers.openai_client import OpenAIUniversalProvider
from ..tools.registry import registry as default_tool_registry, ToolRegistry
from .hitl import HITLManager
from .state import AGUIEvent

logger = logging.getLogger("pidots.agent")


class DotAgent:
    """Motor operacional autônomo associado a um Dot."""

    def __init__(
        self,
        dot_id: str,
        provider: OpenAIUniversalProvider,
        tool_registry: ToolRegistry | None = None
    ) -> None:
        self.dot_id = dot_id
        self.provider = provider
        self.tools = tool_registry or default_tool_registry
        self.max_iterations = settings.max_iterations_per_goal

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
        start_time = datetime.utcnow()

        yield {
            "event": "run:started",
            "data": {
                "run_id": run_id,
                "thread_id": thread_id,
                "dot_id": self.dot_id,
                "timestamp": start_time.isoformat()
            }
        }

        # 1. Carrega dados do Dot e histórico do SQLite
        dot_info, messages = await self._load_context(thread_id, user_message)
        if not dot_info:
            yield {
                "event": "run:finished",
                "data": {"run_id": run_id, "error": f"Dot '{self.dot_id}' não encontrado.", "status": "error"}
            }
            return

        tool_defs = self.tools.get_tool_definitions()
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

            try:
                # Chamada com Circuit Breaker ao provedor OpenAI-compatível
                response = await self.provider.chat_completion(
                    messages=messages,
                    tools=tool_defs if tool_defs else None,
                    model=dot_info["model"]
                )
            except Exception as e:
                logger.error("Erro na chamada de inferência: %s", str(e), exc_info=True)
                yield {
                    "event": "thought:delta",
                    "data": {"run_id": run_id, "error": f"Falha de conexão com provedor: {str(e)}"}
                }
                yield {
                    "event": "run:finished",
                    "data": {"run_id": run_id, "status": "failed", "error": str(e)}
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
                # Adiciona mensagem do assistente contendo as chamadas de ferramentas
                messages.append(msg)

                for call in tool_calls:
                    call_id = call.get("id", str(uuid.uuid4()))
                    func = call.get("function", {})
                    fn_name = func.get("name")
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except Exception:
                        args = {}

                    # Validação de Governança Human-in-the-Loop
                    requires_hitl, risk = HITLManager.requires_approval(fn_name, json.dumps(args))
                    if requires_hitl:
                        approval_id = await HITLManager.create_approval_request(
                            dot_id=self.dot_id,
                            thread_id=thread_id,
                            action_type=fn_name,
                            payload=json.dumps(args),
                            risk_level=risk
                        )
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
                        # Interrompe o run até aprovação humana
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

                    t_start = datetime.utcnow()
                    tool_result = await self.tools.execute_tool(fn_name, args, dot_id=self.dot_id)
                    t_duration = int((datetime.utcnow() - t_start).total_seconds() * 1000)

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

                    # Registra resultado no contexto
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": fn_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

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
                    INSERT INTO messages (id, thread_id, role, content)
                    VALUES (?, ?, 'assistant', ?)
                    """,
                    (msg_id, thread_id, final_response_text)
                )
                await db.commit()

        yield {
            "event": "run:finished",
            "data": {
                "run_id": run_id,
                "status": "completed",
                "iterations": iteration,
                "duration_seconds": round((datetime.utcnow() - start_time).total_seconds(), 2)
            }
        }

    async def _load_context(
        self,
        thread_id: str,
        user_message: str | None
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Carrega persona do Dot e mensagens anteriores."""
        async with get_db() as db:
            # Obtém Dot
            cursor = await db.execute("SELECT * FROM dots WHERE id = ?", (self.dot_id,))
            dot_row = await cursor.fetchone()
            if not dot_row:
                return None, []
            dot_info = dict(dot_row)

            # Se houver nova mensagem do usuário, salva no SQLite
            if user_message:
                u_msg_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO messages (id, thread_id, role, content)
                    VALUES (?, ?, 'user', ?)
                    """,
                    (u_msg_id, thread_id, user_message)
                )
                await db.commit()

            # Obtém histórico da thread (máximo 15 mensagens recentes para manter janela enxuta no edge)
            cursor = await db.execute(
                """
                SELECT role, content FROM messages
                WHERE thread_id = ?
                ORDER BY created_at ASC
                LIMIT 15
                """,
                (thread_id,)
            )
            rows = await cursor.fetchall()

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": dot_info["system_prompt"]}
        ]
        for r in rows:
            messages.append({"role": r["role"], "content": r["content"]})

        return dot_info, messages
