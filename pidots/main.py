"""
piDots Core Application (FastAPI + uvloop).
Servidor assíncrono em worker único calibrado para Raspberry Pi 4B (ARM64).
Serve a API REST, streaming de eventos AG-UI e o console SPA.
"""

import httpx
import os
import uuid
import json
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .storage.db import init_edge_database, get_db
from .storage import SpacesManager, VectorStore
from .core.hitl import HITLManager
from .core.agent import DotAgent
from .providers.openai_client import OpenAIUniversalProvider

logger = logging.getLogger("pidots.main")


def get_soc_temperature() -> float:
    """Lê a temperatura do SoC Broadcom BCM2711 no Raspberry Pi 4B."""
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.exists(thermal_path):
        try:
            with open(thermal_path, "r") as f:
                return round(float(f.read().strip()) / 1000.0, 1)
        except Exception:
            return 45.0
    return 45.0


def get_memory_info() -> dict:
    """Lê memória RAM diretamente de /proc/meminfo sem bibliotecas externas."""
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    meminfo[parts[0].strip()] = parts[1].strip()
        total_kb = int(meminfo.get("MemTotal", "0 kB").split()[0])
        avail_kb = int(meminfo.get("MemAvailable", "0 kB").split()[0])
        used_mb = round((total_kb - avail_kb) / 1024, 1)
        total_mb = round(total_kb / 1024, 1)
        return {"total_mb": total_mb, "used_mb": used_mb, "available_mb": round(avail_kb / 1024, 1)}
    except Exception:
        return {"total_mb": 3700.0, "used_mb": 850.0, "available_mb": 2850.0}


async def periodic_wal_checkpoint(interval_seconds: int = 900):
    """
    Executa checkpoint PASSIVE periódico no SQLite WAL para evitar crescimento
    indefinido do arquivo .db-wal no cartão MicroSD sob operação contínua 24/7.
    """
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            async with get_db() as db:
                await db.execute("PRAGMA wal_checkpoint(PASSIVE);")
            logger.debug("Checkpoint PASSIVE periódico do SQLite WAL executado.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Falha na rotina periódica de checkpoint WAL: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida assíncrono: pooling compartilhado e inicialização do SQLite WAL."""
    settings.ensure_directories()
    await init_edge_database()

    # Pool de cliente HTTP compartilhado com limites rígidos de keep-alive
    limits = httpx.Limits(
        max_keepalive_connections=5,
        max_connections=15,
        keepalive_expiry=30.0
    )
    timeout = httpx.Timeout(settings.ai_timeout_seconds, connect=5.0)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    app.state.ai_provider = OpenAIUniversalProvider(http_client=app.state.http_client)

    # Sanity check preventivo de credenciais de inferência no arranque do nó Edge
    if settings.ai_api_key in ("", "sua_chave_aqui", "placeholder"):
        logger.warning(
            "AVISO DE CONFIGURAÇÃO EDGE: AI_API_KEY não configurada ou com valor placeholder ('%s'). "
            "Chamadas cognitivas que dependem do provedor remoto entrarão em modo protegido até que uma chave válida seja configurada no .env.",
            settings.ai_api_key
        )
    else:
        logger.info("Credencial de inferência carregada com sucesso para o modelo: %s", settings.ai_model)

    # Inicia rotina periódica de proteção contra inchaço do MicroSD (a cada 15 min)
    checkpoint_task = asyncio.create_task(periodic_wal_checkpoint(interval_seconds=900))

    # Inicia motor de agendamento proativo Dot Heartbeat (varredura a cada 15s)
    from .core.scheduler import heartbeat_worker_loop
    heartbeat_task = asyncio.create_task(
        heartbeat_worker_loop(ai_provider=app.state.ai_provider, check_interval_seconds=15)
    )

    yield

    heartbeat_task.cancel()
    checkpoint_task.cancel()
    await app.state.http_client.aclose()


app = FastAPI(
    title="piDots Edge Core",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Injeta cabeçalhos defensivos de segurança calibrados para o console de borda."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response



@app.get("/health")
async def health_check():
    """Retorna o estado de integridade e telemetria do Raspberry Pi 4B."""
    return {
        "status": "healthy",
        "system": "piDots Edge Core",
        "soc_temperature_celsius": get_soc_temperature(),
        "memory": get_memory_info(),
        "ai_provider": {
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "max_retries": settings.ai_max_retries
        },
        "database": {
            "path": settings.sqlite_db_path,
            "mode": "WAL"
        }
    }


@app.get("/api/dots")
async def list_dots():
    """Lista todos os AI coworkers (Dots) registrados."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id, name, role, model, workspace_path, is_active, archetype, avatar_stamp FROM dots")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@app.get("/api/hitl/pending")
async def list_pending_hitl():
    """Lista solicitações de aprovação humana pendentes."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM hitl_approvals WHERE status = 'PENDING'")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


class CreateThreadPayload(BaseModel):
    dot_id: str
    title: str = "Nova Sessão"


@app.post("/api/threads")
async def create_thread(payload: CreateThreadPayload):
    """Cria uma nova thread de conversação durável."""
    thread_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, ?)",
            (thread_id, payload.dot_id, payload.title)
        )
        await db.commit()
    return {"id": thread_id, "dot_id": payload.dot_id, "title": payload.title}


@app.get("/api/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """Obtém as mensagens registradas em uma thread com metadados multi-ator."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, role, content, actor_id, actor_type, visibility, thought_log, created_at
            FROM messages WHERE thread_id = ? ORDER BY created_at ASC
            """,
            (thread_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


class RunPayload(BaseModel):
    message: str | None = None


@app.post("/api/threads/{thread_id}/runs")
async def run_thread_stream(thread_id: str, payload: RunPayload, request: Request):
    """
    Inicia um ciclo autônomo do Dot e transmite eventos via Server-Sent Events (SSE).
    Implementa o protocolo AG-UI v1.0 com suporte a roteamento multi-bot.
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT dot_id FROM threads WHERE id = ?", (thread_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        default_dot_id = row["dot_id"]

    # Roteamento dinâmico de menções (@dot)
    from .core.orchestrator import ThreadRouter, MultiBotOrchestrator
    target_dot_id, _ = await ThreadRouter.resolve_target_dots(
        thread_id=thread_id,
        content=payload.message or "",
        default_dot_id=default_dot_id
    )

    # Registra o participante na thread
    await MultiBotOrchestrator.record_participant(thread_id, target_dot_id)

    agent = DotAgent(
        dot_id=target_dot_id,
        provider=request.app.state.ai_provider
    )

    async def event_generator():
        async for event in agent.run_thread(thread_id=thread_id, user_message=payload.message):
            ev_name = event["event"]
            ev_data = json.dumps(event["data"], ensure_ascii=False)
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


class HITLResolutionPayload(BaseModel):
    approved: bool
    notes: str | None = None


@app.post("/api/hitl/{approval_id}/resolve")
async def resolve_hitl(approval_id: str, payload: HITLResolutionPayload):
    """Resolve (aprova ou rejeita) uma solicitação Human-in-the-Loop."""
    success = await HITLManager.resolve_approval(approval_id, payload.approved, payload.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada ou já resolvida.")
    return {"status": "success", "approval_id": approval_id, "approved": payload.approved}


# =============================================================================
# ENDPOINTS DA FASE 4: SPACES, VERSIONAMENTO E MEMÓRIA VETORIAL
# =============================================================================

@app.get("/api/spaces")
async def list_spaces(dot_id: str | None = None):
    """Lista todos os documentos versionados em Spaces."""
    return await SpacesManager.list_documents(dot_id=dot_id)


@app.get("/api/spaces/search")
async def search_spaces_get(query: str, top_k: int = 3):
    """Executa busca semântica KNN vetorial via GET nos documentos dos Spaces."""
    return await VectorStore.search(query=query, top_k=top_k)


@app.get("/api/spaces/{space_id}")
async def get_space_doc(space_id: str):
    """Retorna os dados completos de um documento em Space."""
    doc = await SpacesManager.get_document(space_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return doc


@app.get("/api/spaces/{space_id}/revisions")
async def get_space_revisions(space_id: str):
    """Retorna o histórico de revisões com diffs de um documento."""
    return await SpacesManager.get_revisions(space_id)


class SaveDocumentPayload(BaseModel):
    dot_id: str
    filename: str
    content: str
    title: str | None = None


@app.post("/api/spaces")
async def save_space_doc(payload: SaveDocumentPayload):
    """Salva ou atualiza um documento com versionamento incremental e cálculo de diff."""
    return await SpacesManager.save_document(
        dot_id=payload.dot_id,
        filename=payload.filename,
        content=payload.content,
        title=payload.title
    )


class VectorSearchPayload(BaseModel):
    query: str
    top_k: int = 3


@app.post("/api/spaces/search")
async def search_spaces(payload: VectorSearchPayload):
    """Executa busca semântica KNN vetorial nos documentos dos Spaces."""
    return await VectorStore.search(query=payload.query, top_k=payload.top_k)


@app.get("/api/spaces/{space_id}/download")
async def download_space_doc(space_id: str):
    """Download individual do documento."""
    doc = await SpacesManager.get_document(space_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    from fastapi.responses import Response
    return Response(
        content=doc["content"],
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{doc['filename']}\""}
    )


class CreateTaskPayload(BaseModel):
    dot_id: str
    task_name: str
    cron_expr: str
    action_prompt: str
    target_channel_type: str = "internal"
    target_channel_id: str | None = None


@app.get("/api/tasks")
async def list_scheduled_tasks():
    """Lista todas as tarefas proativas agendadas (Dot Heartbeats)."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, dot_id, task_name, cron_expr, action_prompt,
                   target_channel_type, target_channel_id, next_run_at,
                   last_run_at, last_status, last_result_summary, is_active
            FROM scheduled_tasks ORDER BY next_run_at ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@app.post("/api/tasks")
async def create_scheduled_task(payload: CreateTaskPayload):
    """Registra uma nova tarefa cron proativa para um Dot no SQLite WAL."""
    from .core.scheduler import EdgeScheduler
    try:
        task_id = await EdgeScheduler.register_task(
            dot_id=payload.dot_id,
            task_name=payload.task_name,
            cron_expr=payload.cron_expr,
            action_prompt=payload.action_prompt,
            target_channel_type=payload.target_channel_type,
            target_channel_id=payload.target_channel_id
        )
        return {"id": task_id, "status": "scheduled", "task_name": payload.task_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/workspaces/{dot_id}/export.zip")
async def export_workspace_zip(dot_id: str):
    """Exporta o workspace completo de um Dot em formato ZIP."""
    zip_bytes = await SpacesManager.export_workspace_zip(dot_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=\"workspace_{dot_id}.zip\""}
    )


# =============================================================================
# ENDPOINTS DA FASE 5: CONFIGURAÇÕES A QUENTE, NOTIFICAÇÕES HITL E PWA
# =============================================================================

class AISettingsUpdatePayload(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_retries: int | None = None
    timeout_seconds: float | None = None


class NotificationSettingsUpdatePayload(BaseModel):
    webhook_url: str | None = None
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    evolution_url: str | None = None
    evolution_key: str | None = None


class WebhookCallbackPayload(BaseModel):
    approval_id: str
    approved: bool
    notes: str | None = None


@app.get("/api/settings")
async def get_system_settings():
    """Retorna o estado operacional e configurações ativas do piDots."""
    masked_key = ""
    if settings.ai_api_key:
        masked_key = settings.ai_api_key[:4] + "..." + settings.ai_api_key[-3:] if len(settings.ai_api_key) > 7 else "***"

    masked_evo_key = ""
    if settings.evolution_api_key:
        masked_evo_key = settings.evolution_api_key[:3] + "..." + settings.evolution_api_key[-3:] if len(settings.evolution_api_key) > 6 else "***"

    return {
        "ai": {
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "api_key_masked": masked_key,
            "max_retries": settings.ai_max_retries,
            "timeout_seconds": settings.ai_timeout_seconds
        },
        "notifications": {
            "webhook_url": settings.webhook_notification_url,
            "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
            "telegram_chat_id": settings.telegram_chat_id,
            "evolution_api_url": settings.evolution_api_url,
            "evolution_api_key_masked": masked_evo_key
        },
        "governance": {
            "max_iterations_per_goal": settings.max_iterations_per_goal,
            "thermal_throttle_enabled": settings.enable_thermal_throttle,
            "thermal_limit_celsius": settings.thermal_limit_celsius
        }
    }


@app.post("/api/settings/ai")
async def update_ai_settings(payload: AISettingsUpdatePayload):
    """Atualiza a quente os parâmetros de IA sem reiniciar o contêiner."""
    settings.update_ai_params(
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
        max_retries=payload.max_retries,
        timeout_seconds=payload.timeout_seconds
    )
    # Atualiza a instância compartilhada do provedor de inferência
    app.state.ai_provider = OpenAIUniversalProvider(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        default_model=settings.ai_model,
        http_client=app.state.http_client
    )
    return {"status": "success", "message": "Parâmetros de IA atualizados a quente."}


@app.post("/api/settings/notifications")
async def update_notification_settings(payload: NotificationSettingsUpdatePayload):
    """Atualiza a quente os canais de notificação e alertas remotos."""
    settings.update_notification_params(
        webhook_url=payload.webhook_url,
        telegram_token=payload.telegram_token,
        telegram_chat_id=payload.telegram_chat_id,
        evolution_url=payload.evolution_url,
        evolution_key=payload.evolution_key
    )
    return {"status": "success", "message": "Canais de notificação atualizados com sucesso."}


@app.post("/api/hitl/webhook-callback")
async def handle_hitl_webhook_callback(payload: WebhookCallbackPayload):
    """Endpoint de retorno para resolução de aprovação HITL via mensageria/webhook."""
    success = await HITLManager.resolve_approval(
        approval_id=payload.approval_id,
        approved=payload.approved,
        notes=payload.notes or "Resolvido via Webhook Callback Remoto"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada ou já resolvida.")
    return {
        "status": "success",
        "approval_id": payload.approval_id,
        "resolved_state": "APPROVED" if payload.approved else "REJECTED"
    }


# =============================================================================
# ENDPOINTS DO GATEWAY DE MENSAGERIA E SALAS TEMÁTICAS (FASE 4)
# =============================================================================

from .core.messaging_gateway import MessagingGateway, ChannelOrchestrator, UnifiedIncomingMessage


class GenericIncomingWebhookPayload(BaseModel):
    text: str
    sender_name: str = "Webhook External"
    sender_id: str = "webhook-user"
    reply_target_id: str | None = None


class CreateChannelPayload(BaseModel):
    name: str
    description: str | None = None


class PostChannelMessagePayload(BaseModel):
    author_type: str = "user"  # 'user', 'dot', 'webhook'
    author_id: str
    content: str


class AddChannelMemberPayload(BaseModel):
    member_type: str = "dot"  # 'dot', 'user'
    member_id: str


@app.post("/api/webhooks/incoming/{dot_id}")
async def handle_generic_incoming_webhook(dot_id: str, payload: GenericIncomingWebhookPayload):
    """Webhook genérico universal para envio de mensagens a um Dot por APIs, scripts ou CI/CD."""
    unified_msg = UnifiedIncomingMessage(
        platform="generic_webhook",
        sender_id=payload.sender_id,
        sender_name=payload.sender_name,
        text=payload.text,
        reply_target_id=payload.reply_target_id or payload.sender_id
    )
    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=app.state.ai_provider,
        http_client=app.state.http_client
    )
    return {
        "status": "success",
        "dot_id": dot_id,
        "response": response_text
    }


@app.post("/api/webhooks/telegram/{dot_id}")
async def handle_telegram_webhook(dot_id: str, request: Request):
    """Recebe webhooks oficiais de mensagens da API de bots do Telegram."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    message_data = body.get("message", {})
    text = message_data.get("text", "")
    if not text:
        return {"status": "ignored", "reason": "Sem mensagem de texto"}

    chat_id = str(message_data.get("chat", {}).get("id", ""))
    from_data = message_data.get("from", {})
    sender_id = str(from_data.get("id", chat_id))
    sender_name = from_data.get("first_name", "Telegram User")

    unified_msg = UnifiedIncomingMessage(
        platform="telegram",
        sender_id=sender_id,
        sender_name=sender_name,
        text=text,
        reply_target_id=chat_id
    )

    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=app.state.ai_provider,
        http_client=app.state.http_client
    )
    return {"status": "success", "dot_id": dot_id, "chat_id": chat_id, "response": response_text}


@app.post("/api/webhooks/whatsapp/{dot_id}")
async def handle_whatsapp_webhook(dot_id: str, request: Request):
    """Recebe webhooks de mensagens da Evolution API ou Baileys (WhatsApp)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    data = body.get("data", {})
    key = data.get("key", {})
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "Mensagem enviada pelo próprio bot"}

    remote_jid = key.get("remoteJid", "")
    push_name = data.get("pushName", "WhatsApp User")

    message_content = data.get("message", {})
    text = (
        message_content.get("conversation")
        or message_content.get("extendedTextMessage", {}).get("text")
        or ""
    )

    if not text:
        return {"status": "ignored", "reason": "Sem conteúdo textual"}

    unified_msg = UnifiedIncomingMessage(
        platform="whatsapp",
        sender_id=remote_jid,
        sender_name=push_name,
        text=text,
        reply_target_id=remote_jid
    )

    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=app.state.ai_provider,
        http_client=app.state.http_client
    )
    return {"status": "success", "dot_id": dot_id, "remote_jid": remote_jid, "response": response_text}


@app.get("/api/channels")
async def list_channels():
    """Lista todas as salas temáticas colaborativas com contagem de mensagens."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT c.id, c.name, c.description, c.created_at,
                   COUNT(m.id) as message_count
            FROM channels c
            LEFT JOIN channel_messages m ON m.channel_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@app.post("/api/channels")
async def create_channel(payload: CreateChannelPayload):
    """Cria uma nova sala temática de equipe no SQLite WAL."""
    channel_id = payload.name.lower().strip().replace(" ", "-").replace("#", "")
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO channels (id, name, description) VALUES (?, ?, ?)",
                (channel_id, payload.name, payload.description)
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Canal já existe ou dados inválidos: {e}")

    return {"id": channel_id, "name": payload.name, "description": payload.description}


@app.get("/api/channels/{channel_id}/messages")
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Retorna as mensagens recentes de uma sala temática."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, channel_id, author_type, author_id, content, hop_count, created_at
            FROM channel_messages
            WHERE channel_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (channel_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@app.post("/api/channels/{channel_id}/messages")
async def post_channel_message(channel_id: str, payload: PostChannelMessagePayload):
    """Envia uma mensagem para a sala temática e dispara a orquestração autônoma."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Canal não encontrado.")

    msg_id = await ChannelOrchestrator.post_message_to_channel(
        channel_id=channel_id,
        author_type=payload.author_type,
        author_id=payload.author_id,
        content=payload.content,
        hop_count=0,
        ai_provider=app.state.ai_provider
    )
    return {"status": "dispatched", "message_id": msg_id, "channel_id": channel_id}


@app.post("/api/channels/{channel_id}/members")
async def add_channel_member(channel_id: str, payload: AddChannelMemberPayload):
    """Adiciona um membro (Dot ou Usuário) à sala temática."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Canal não encontrado.")

        await db.execute(
            """
            INSERT OR REPLACE INTO channel_members (channel_id, member_type, member_id)
            VALUES (?, ?, ?)
            """,
            (channel_id, payload.member_type, payload.member_id)
        )
        await db.commit()
    return {"status": "success", "channel_id": channel_id, "member_id": payload.member_id}



OFFICIAL_SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="16" fill="#07090c"/>
<circle cx="32" cy="50" r="14" fill="#33ff66"/>
<circle cx="68" cy="50" r="14" fill="#38bdf8"/>
<path d="M46 50h8" stroke="#f1f5f9" stroke-width="4" stroke-linecap="round"/>
<circle cx="32" cy="50" r="6" fill="#ffffff"/>
<circle cx="68" cy="50" r="6" fill="#ffffff"/>
</svg>"""


@app.get("/icon.svg")
async def get_app_icon():
    """Serve o ícone oficial vetorial SVG para favicons e instalação PWA."""
    return Response(
        content=OFFICIAL_SVG_ICON.strip(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"}
    )


@app.get("/manifest.json")
async def get_pwa_manifest():
    """Retorna o manifesto oficial PWA para instalação no celular e desktop."""
    manifest = {
        "name": "piDots Edge Console",
        "short_name": "piDots",
        "description": "Console autônomo e persistente de AI coworkers para Raspberry Pi 4B",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#07090c",
        "theme_color": "#07090c",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/icon.svg",
                "sizes": "192x192 512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    return JSONResponse(
        content=manifest,
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache, must-revalidate"}
    )


@app.get("/sw.js")
async def get_service_worker():
    """Retorna o Service Worker para suporte PWA offline-first sem risco de cache imortal."""
    sw_code = """
const CACHE_NAME = 'pidots-cache-v2';
const STATIC_ASSETS = ['/', '/manifest.json', '/icon.svg'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // 1. Chamadas à API ou endpoints de telemetria: bypass total de cache
    if (event.request.url.includes('/api/') || event.request.url.includes('/health')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(JSON.stringify({ error: 'Rede indisponível no modo offline' }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // 2. Navegação de páginas HTML (evita cache imortal via Network-First)
    if (event.request.mode === 'navigate' || event.request.destination === 'document') {
        event.respondWith(
            fetch(event.request).then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => {
                return caches.match(event.request).then((cached) => cached || caches.match('/'));
            })
        );
        return;
    }

    // 3. Demais assets estáticos: Stale-While-Revalidate
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => cachedResponse);

            return cachedResponse || fetchPromise;
        })
    );
});
"""
    return Response(
        content=sw_code.strip(),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


def find_html_file(filename: str) -> Path:
    """Localiza o arquivo HTML seja dentro do container Docker (/app) ou no host."""
    candidates = [
        Path(__file__).resolve().parent.parent / filename,
        Path("/app") / filename,
        Path.cwd() / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


@app.get("/", response_class=HTMLResponse)
async def serve_spa_prototype():
    """Serve o console operacional oficial do piDots em Pixel Paper UI (100% Funcional)."""
    spa_path = find_html_file("pidots_spa_prototype.html")
    if spa_path.exists():
        return spa_path.read_text(encoding="utf-8")
    return "<h1>piDots SPA em desenvolvimento</h1>"


@app.get("/relatorio", response_class=HTMLResponse)
async def serve_study_report():
    """Serve o relatório completo de estudo e viabilidade."""
    report_path = find_html_file("relatorio_estudo_pidots.html")
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    return "<h1>Relatório não encontrado</h1>"


@app.get("/apresentacao", response_class=HTMLResponse)
async def serve_presentation():
    """Serve o protótipo de apresentação do piDots em Pixel Paper UI."""
    pres_path = find_html_file("pidots_apresentacao_pixel_paper.html")
    if pres_path.exists():
        return pres_path.read_text(encoding="utf-8")
    return "<h1>Apresentação não encontrada</h1>"


@app.get("/guia", response_class=HTMLResponse)
async def serve_guide():
    """Serve o guia didático operacional oficial do piDots."""
    guide_path = find_html_file("pidots_guia.html")
    if guide_path.exists():
        return guide_path.read_text(encoding="utf-8")
    return "<h1>Guia operacional não encontrado</h1>"


