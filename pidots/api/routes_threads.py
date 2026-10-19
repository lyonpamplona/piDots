"""
Rotas REST e Streaming SSE para Gerenciamento de Threads, Estado CoAgents e Execuções dos Dots.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..storage.db import get_db
from ..storage.spaces_manager import SpacesManager
from ..storage.shared_space import SharedSpaceManager
from ..core.agent import DotAgent
from ..core.orchestrator import ThreadRouter, MultiBotOrchestrator
from ..core.planner import TwoStagePlanner
from ..core.council import CouncilOrchestrator
from .deps import get_ai_provider

router = APIRouter(tags=["Threads"])


class CreateThreadPayload(BaseModel):
    dot_id: str
    title: str = "Nova Sessão"


class RunPayload(BaseModel):
    message: str | None = None
    source_url: str | None = None


class SaveAsSpacePayload(BaseModel):
    title: str | None = None
    filename: str | None = None
    dot_id: str | None = None


class CouncilTriggerPayload(BaseModel):
    topic: str | None = None
    prompt: str | None = None
    proponent_dot_id: str = "dev-assistant"
    proposer_id: str | None = None
    critic_dot_id: str = "dot-auditor"
    critic_id: str | None = None
    supervisor_dot_id: str = "dot-supervisor"
    supervisor_id: str | None = None
    rounds: int = 1


class HandoffTriggerPayload(BaseModel):
    target_dot_id: str
    reason: str = "Transferência operacional solicitada pelo operador no console."


@router.get("/api/threads")
async def list_threads(dot_id: str | None = None, limit: int = 40):
    """Lista conversas (threads) recentes persistidas no SQLite WAL, excluindo subthreads efêmeras."""
    safe_limit = max(1, min(limit, 100))
    async with get_db() as db:
        if dot_id:
            cursor = await db.execute(
                """
                SELECT t.id, t.dot_id, COALESCE(t.primary_dot_id, t.dot_id) AS primary_dot_id,
                       t.title, t.status, t.created_at, t.updated_at,
                       d.name AS dot_name, d.avatar_stamp AS dot_stamp,
                       (SELECT COUNT(*) FROM messages m WHERE m.thread_id = t.id AND m.visibility = 'public') AS message_count
                FROM threads t
                LEFT JOIN dots d ON d.id = COALESCE(t.primary_dot_id, t.dot_id)
                WHERE (t.dot_id = ? OR t.primary_dot_id = ?)
                  AND t.id NOT LIKE 'subtask-%'
                  AND t.id NOT LIKE 'council-%'
                ORDER BY t.updated_at DESC, t.created_at DESC
                LIMIT ?
                """,
                (dot_id, dot_id, safe_limit)
            )
        else:
            cursor = await db.execute(
                """
                SELECT t.id, t.dot_id, COALESCE(t.primary_dot_id, t.dot_id) AS primary_dot_id,
                       t.title, t.status, t.created_at, t.updated_at,
                       d.name AS dot_name, d.avatar_stamp AS dot_stamp,
                       (SELECT COUNT(*) FROM messages m WHERE m.thread_id = t.id AND m.visibility = 'public') AS message_count
                FROM threads t
                LEFT JOIN dots d ON d.id = COALESCE(t.primary_dot_id, t.dot_id)
                WHERE t.id NOT LIKE 'subtask-%'
                  AND t.id NOT LIKE 'council-%'
                ORDER BY t.updated_at DESC, t.created_at DESC
                LIMIT ?
                """,
                (safe_limit,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/api/threads")
async def create_thread(payload: CreateThreadPayload):
    """Cria uma nova thread de conversação durável."""
    thread_id = str(uuid.uuid4())
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM dots WHERE id = ?", (payload.dot_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{payload.dot_id}' não encontrado.")
        await db.execute(
            "INSERT INTO threads (id, dot_id, primary_dot_id, title) VALUES (?, ?, ?, ?)",
            (thread_id, payload.dot_id, payload.dot_id, payload.title)
        )
        await db.commit()
    return {"id": thread_id, "dot_id": payload.dot_id, "title": payload.title}


@router.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Remove uma thread e todas as suas mensagens associadas do SQLite WAL."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM threads WHERE id = ?", (thread_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        await db.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM thread_shared_notes WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM agent_handoffs WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        await db.commit()
    return {"status": "deleted", "thread_id": thread_id}


@router.get("/api/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """Obtém as mensagens registradas em uma thread com metadados multi-ator e chamadas de ferramenta."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, role, content, actor_id, actor_type, visibility, thought_log, tool_calls_json, created_at
            FROM messages WHERE thread_id = ? ORDER BY created_at ASC, rowid ASC
            """,
            (thread_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.get("/api/threads/{thread_id}/state")
async def get_thread_coagent_state(thread_id: str):
    """
    Retorna o Shared State CoAgents consolidado de uma thread:
    - Metadados da thread e Dot líder;
    - Plano de execução ativo (Goals & Milestones do TwoStagePlanner);
    - Notas do Quadro Negro Compartilhado (SharedSpaceManager);
    - Histórico de Handoffs e Rodadas do Conselho (agent_handoffs);
    - Fitas de carbono internas e últimas execuções de ferramentas (tool_runs).
    """
    async with get_db() as db:
        cur_th = await db.execute(
            "SELECT id, dot_id, COALESCE(primary_dot_id, dot_id) AS active_dot_id, title, status, created_at, updated_at FROM threads WHERE id = ?",
            (thread_id,)
        )
        th_row = await cur_th.fetchone()
        if not th_row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        thread_info = dict(th_row)
        active_dot_id = thread_info["active_dot_id"]

        cur_handoffs = await db.execute(
            """
            SELECT id, source_dot_id, target_dot_id, task_goal, handoff_type, status, result_summary, created_at, completed_at
            FROM agent_handoffs WHERE thread_id = ? ORDER BY created_at DESC LIMIT 20
            """,
            (thread_id,)
        )
        handoffs = [dict(r) for r in await cur_handoffs.fetchall()]

        cur_tools = await db.execute(
            """
            SELECT id, dot_id, tool_name, arguments_json, exit_code, stdout_text, stderr_text, duration_ms, created_at
            FROM tool_runs WHERE dot_id = ? ORDER BY created_at DESC LIMIT 20
            """,
            (active_dot_id,)
        )
        recent_tool_runs = [dict(r) for r in await cur_tools.fetchall()]

        cur_carbon = await db.execute(
            """
            SELECT id, actor_id, target_dot_id, role, content, created_at
            FROM messages WHERE thread_id = ? AND visibility = 'internal' AND role = 'assistant'
            ORDER BY created_at DESC, rowid DESC LIMIT 15
            """,
            (thread_id,)
        )
        carbon_slips = [dict(r) for r in await cur_carbon.fetchall()]

        cur_hitl = await db.execute(
            """
            SELECT id, dot_id, thread_id, action_type, payload, risk_level, status, requested_at, expires_at
            FROM hitl_approvals WHERE thread_id = ? AND status = 'PENDING'
            ORDER BY requested_at DESC
            """,
            (thread_id,)
        )
        pending_hitl = [dict(r) for r in await cur_hitl.fetchall()]

    active_plan = await TwoStagePlanner.get_plan_status(thread_id=thread_id, dot_id=active_dot_id)
    shared_notes = await SharedSpaceManager.list_notes(thread_id=thread_id)

    return {
        "thread": thread_info,
        "active_plan": active_plan if active_plan.get("found") else None,
        "shared_notes": shared_notes,
        "handoffs": handoffs,
        "pending_hitl": pending_hitl,
        "recent_tool_runs": recent_tool_runs,
        "carbon_slips": carbon_slips
    }


@router.post("/api/threads/{thread_id}/save-as-space")
async def save_thread_as_space_page(thread_id: str, payload: SaveAsSpacePayload | None = None):
    """
    Padrão OpenDots 'Save conversation as page':
    Converte as mensagens de uma thread em um documento Markdown estruturado e salva em Spaces.
    """
    p = payload or SaveAsSpacePayload()
    async with get_db() as db:
        cur_th = await db.execute(
            "SELECT id, dot_id, COALESCE(primary_dot_id, dot_id) AS active_dot_id, title FROM threads WHERE id = ?",
            (thread_id,)
        )
        th_row = await cur_th.fetchone()
        if not th_row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")

        dot_id = p.dot_id or th_row["active_dot_id"]
        thread_title = p.title or th_row["title"] or f"Conversa {thread_id[:8]}"

        cur_msgs = await db.execute(
            """
            SELECT role, content, actor_id, visibility, created_at
            FROM messages WHERE thread_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (thread_id,)
        )
        msgs = [dict(r) for r in await cur_msgs.fetchall()]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md_lines = [
        f"# {thread_title}",
        "",
        f"- **Origem:** Thread `{thread_id}`",
        f"- **Especialista Titular:** `{dot_id}`",
        f"- **Exportado em:** {now_iso}",
        "",
        "---",
        ""
    ]
    if not msgs:
        md_lines.append("_Sessão registrada sem mensagens de diálogo até o momento da exportação._")
        md_lines.append("")
    else:
        for m in msgs:
            speaker = "Operador" if m["role"] == "user" else f"@{m.get('actor_id') or dot_id}"
            ts = m.get("created_at") or ""
            md_lines.append(f"## {speaker} ({ts})")
            md_lines.append("")
            md_lines.append((m.get("content") or "").strip())
            md_lines.append("")

    markdown_body = "\n".join(md_lines)
    slug = re.sub(r"[^a-z0-9\-_]+", "_", thread_title.lower()).strip("_")[:40] or f"conversa_{thread_id[:8]}"
    filename = p.filename or f"{slug}.md"
    if not filename.endswith(".md"):
        filename += ".md"

    saved_doc = await SpacesManager.save_document(
        dot_id=dot_id,
        filename=filename,
        content=markdown_body,
        title=thread_title
    )
    return {
        "status": "saved",
        "thread_id": thread_id,
        "space": saved_doc,
        **saved_doc
    }


@router.post("/api/threads/{thread_id}/council")
async def trigger_thread_council(thread_id: str, payload: CouncilTriggerPayload, request: Request):
    """Aciona uma sessão real do CouncilOrchestrator (Debate Multi-Bot) vinculada à thread."""
    effective_topic = (payload.topic or payload.prompt or "Análise de Arquitetura").strip()
    ai_provider = get_ai_provider(request)
    result = await CouncilOrchestrator.run_debate(
        thread_id=thread_id,
        topic=effective_topic,
        proponent_dot_id=payload.proposer_id or payload.proponent_dot_id,
        critic_dot_id=payload.critic_id or payload.critic_dot_id,
        supervisor_dot_id=payload.supervisor_id or payload.supervisor_dot_id,
        rounds=max(1, min(payload.rounds, 3)),
        provider=ai_provider
    )
    return result


@router.post("/api/threads/{thread_id}/handoff")
async def trigger_thread_handoff(thread_id: str, payload: HandoffTriggerPayload):
    """Transfere a titularidade operacional da thread para outro Dot especialista."""
    async with get_db() as db:
        cur_th = await db.execute(
            "SELECT dot_id, COALESCE(primary_dot_id, dot_id) AS active_dot_id FROM threads WHERE id = ?",
            (thread_id,)
        )
        row = await cur_th.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        source_dot_id = row["active_dot_id"]

    result = await MultiBotOrchestrator.handoff_lead(
        thread_id=thread_id,
        source_dot_id=source_dot_id,
        target_dot_id=payload.target_dot_id,
        reason=payload.reason
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao transferir liderança da thread."))
    return result


@router.post("/api/threads/{thread_id}/runs")
async def run_thread_stream(thread_id: str, payload: RunPayload, request: Request):
    """
    Inicia um ciclo autônomo do Dot e transmite eventos via Server-Sent Events (SSE).
    Implementa o protocolo AG-UI v1.0 com suporte a roteamento multi-bot e multi-menção encadeada.
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT dot_id, primary_dot_id, title FROM threads WHERE id = ?", (thread_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        default_dot_id = row["primary_dot_id"] or row["dot_id"]
        current_title = row["title"] or ""

        # Atualiza título da thread automaticamente se ainda estiver com nome genérico
        if payload.message and current_title in ("Nova Sessão", "Sessão Inicial de Comando", "") or current_title.startswith("Thread "):
            clean_title = re.sub(r"\s+", " ", (payload.message or "").strip())[:52]
            if clean_title:
                await db.execute("UPDATE threads SET title = ? WHERE id = ?", (clean_title, thread_id))
                await db.commit()

    effective_message = payload.message or ""
    if payload.source_url and payload.source_url.strip():
        src_url = payload.source_url.strip()
        effective_message = f"[FONTE DE REFERÊNCIA ANEXADA: {src_url}]\n{effective_message}".strip()

    # Roteamento dinâmico de menções (@dot) incluindo Dots secundários em multi-menção
    target_dot_id, secondary_dots = await ThreadRouter.resolve_target_dots(
        thread_id=thread_id,
        content=effective_message,
        default_dot_id=default_dot_id
    )

    dots_sequence = [target_dot_id] + [d for d in secondary_dots[:2] if d != target_dot_id]
    for d_id in dots_sequence:
        await MultiBotOrchestrator.record_participant(thread_id, d_id)

    ai_provider = get_ai_provider(request)

    async def event_generator():
        for idx, active_dot in enumerate(dots_sequence):
            agent = DotAgent(dot_id=active_dot, provider=ai_provider)
            # Apenas o primeiro Dot grava a user_message no banco; os seguintes leem do histórico da thread
            msg_for_turn = effective_message if idx == 0 else None
            if idx > 0:
                chain_ev = {
                    "event": "thought:delta",
                    "run_id": f"chain-{idx}",
                    "dot_id": active_dot,
                    "thought": f"Encadeamento multi-bot ativo: acionando especialista @{active_dot}..."
                }
                yield f"event: thought:delta\ndata: {json.dumps(chain_ev, ensure_ascii=False)}\n\n"

            async for event in agent.run_thread(thread_id=thread_id, user_message=msg_for_turn):
                ev_name = event["event"]
                merged_data = {"event": ev_name, "dot_id": active_dot, **(event.get("data") or {})}
                ev_data = json.dumps(merged_data, ensure_ascii=False)
                yield f"event: {ev_name}\ndata: {ev_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

