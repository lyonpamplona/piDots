"""
piDots Core Application (FastAPI + uvloop).
Servidor assíncrono em worker único calibrado para Raspberry Pi 4B (ARM64).
Serve a API REST, streaming de eventos AG-UI e o console SPA.
"""

import io
import httpx
import os
import uuid
import gzip
import hashlib
import json
import asyncio
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from PIL import Image, ImageDraw
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings
from .storage.db import init_edge_database, get_db
from .storage import SpacesManager, VectorStore
from .core.hitl import HITLManager
from .core.agent import DotAgent
from .core.edge_triggers import EdgeHardwareTriggers
from .providers.openai_client import OpenAIUniversalProvider

logger = logging.getLogger("pidots.main")


class StaticPageManager:
    """
    Gerenciador de páginas HTML e assets estáticos residentes em memória RAM.
    Elimina leituras no cartão MicroSD do Raspberry Pi 4B e fornece pré-compressão Gzip
    com suporte completo a ETag (HTTP 304 Not Modified).
    """

    def __init__(self, search_dirs: list[Path]):
        self.search_dirs = search_dirs
        self._raw_cache: Dict[str, bytes] = {}
        self._gzip_cache: Dict[str, bytes] = {}
        self._etags: Dict[str, str] = {}

    def _resolve_file(self, filename: str) -> Optional[Path]:
        for base in self.search_dirs:
            target = base / filename
            if target.is_file():
                return target
        return None

    def preload(self, filename: str, compress_level: int = 6) -> bool:
        """Carrega e pré-comprime o arquivo HTML na memória RAM durante o startup."""
        path = self._resolve_file(filename)
        if not path:
            return False
        try:
            content = path.read_bytes()
            self._raw_cache[filename] = content
            self._gzip_cache[filename] = gzip.compress(content, compresslevel=compress_level)
            self._etags[filename] = f'"{hashlib.sha256(content).hexdigest()[:16]}"'
            logger.info("Página '%s' pré-carregada na RAM (%d bytes, gzipped: %d bytes)", filename, len(content), len(self._gzip_cache[filename]))
            return True
        except Exception as e:
            logger.warning("Falha ao pré-carregar '%s' na RAM: %s", filename, e)
            return False

    def serve(
        self,
        filename: str,
        request: Request,
        cache_control: str = "public, max-age=0, must-revalidate"
    ) -> Response:
        """Entrega o documento HTML com validação ETag e negociação de codificação Gzip."""
        raw_data = self._raw_cache.get(filename)
        if raw_data is None:
            if not self.preload(filename):
                return Response(
                    content=f"<h1>Recurso '{filename}' não encontrado</h1>",
                    status_code=status.HTTP_404_NOT_FOUND,
                    media_type="text/html; charset=utf-8"
                )
            raw_data = self._raw_cache[filename]

        etag = self._etags.get(filename, "")

        # 1. Validação de ETag condicional (HTTP 304 Not Modified)
        client_etag = request.headers.get("if-none-match")
        if client_etag and client_etag.strip() == etag:
            return Response(
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Cache-Control": cache_control
                }
            )

        # 2. Servir buffer pré-comprimido se o cliente aceitar Gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" in accept_encoding and filename in self._gzip_cache:
            content = b"" if request.method == "HEAD" else self._gzip_cache[filename]
            return Response(
                content=content,
                status_code=status.HTTP_200_OK,
                media_type="text/html; charset=utf-8",
                headers={
                    "Content-Encoding": "gzip",
                    "ETag": etag,
                    "Cache-Control": cache_control,
                    "Vary": "Accept-Encoding"
                }
            )

        # 3. Entrega sem compressão
        content = b"" if request.method == "HEAD" else raw_data
        return Response(
            content=content,
            status_code=status.HTTP_200_OK,
            media_type="text/html; charset=utf-8",
            headers={
                "ETag": etag,
                "Cache-Control": cache_control,
                "Vary": "Accept-Encoding"
            }
        )


HTML_SEARCH_DIRS = [
    Path(__file__).resolve().parent.parent / "pages",
    Path(__file__).resolve().parent.parent,
    Path("/app/pages"),
    Path("/app"),
    Path.cwd() / "pages",
    Path.cwd()
]
EdgeAssetManager = StaticPageManager
page_manager = EdgeAssetManager(search_dirs=HTML_SEARCH_DIRS)


def get_soc_temperature() -> float:
    """Delega leitura térmica unificada para EdgeHardwareTriggers."""
    return EdgeHardwareTriggers.get_soc_temperature()


def get_memory_info() -> dict:
    """Delega leitura de memória RAM unificada para EdgeHardwareTriggers."""
    ram = EdgeHardwareTriggers.get_ram_metrics()
    return {
        "total_mb": ram["total_mb"],
        "used_mb": ram["used_mb"],
        "available_mb": ram["available_mb"]
    }


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

    # Pré-carregamento dos documentos HTML em memória RAM para latência ultra-baixa e preservação de I/O MicroSD
    pages_to_preload = (
        "landing.html",
        "app.html",
        "docs.html",
        "relatorio.html"
    )
    for page in pages_to_preload:
        page_manager.preload(page)

    yield

    heartbeat_task.cancel()
    checkpoint_task.cancel()
    from .core.messaging_gateway import MessagingGateway, ChannelOrchestrator
    await MessagingGateway.cancel_pending_tasks()
    await ChannelOrchestrator.cancel_pending_tasks()
    await asyncio.gather(heartbeat_task, checkpoint_task, return_exceptions=True)
    await app.state.http_client.aclose()


APP_VERSION = "1.5.2"

app = FastAPI(
    title="piDots Edge Core",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1024,
    compresslevel=4
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


# Montagem de Assets Estáticos Desacoplados (CSS, JS e Recursos)
static_asset_dir = Path(__file__).resolve().parent.parent / "static"
if not static_asset_dir.exists():
    static_asset_dir = Path.cwd() / "static"
if static_asset_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_asset_dir)), name="static")



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
async def list_dots(core_only: bool = True):
    """Lista AI coworkers (Dots) registrados. Por padrão retorna o Squad Central enxuto."""
    async with get_db() as db:
        if core_only:
            cursor = await db.execute(
                """
                SELECT id, name, role, model, workspace_path, is_active, archetype, avatar_stamp, is_core
                FROM dots
                WHERE is_core = 1
                ORDER BY CASE id
                    WHEN 'dot-supervisor' THEN 1
                    WHEN 'dev-assistant' THEN 2
                    WHEN 'dot-muse' THEN 3
                    WHEN 'dot-auditor' THEN 4
                    ELSE 5
                END
                """
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, name, role, model, workspace_path, is_active, archetype, avatar_stamp, is_core
                FROM dots
                ORDER BY is_core DESC, name ASC
                """
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@app.get("/api/dots/{dot_id}/export-pack")
async def export_dot_pack_endpoint(dot_id: str):
    """Exporta manifesto estruturado DotPack v1.0 com personas, core memory e arquivística."""
    from .core.dot_pack import DotPackManager
    result = await DotPackManager.export_dot_pack(dot_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Dot não encontrado"))
    return JSONResponse(
        content=result["manifest"],
        headers={"Content-Disposition": f"attachment; filename=dotpack_{dot_id}.json"}
    )


class ImportDotPackPayload(BaseModel):
    pack: dict[str, Any]
    override_id: str | None = None


@app.post("/api/dots/import-pack")
async def import_dot_pack_endpoint(payload: ImportDotPackPayload):
    """Importa e instancia um novo Dot no SQLite WAL a partir de manifesto DotPack."""
    from .core.dot_pack import DotPackManager
    result = await DotPackManager.import_dot_pack(pack_data=payload.pack, override_id=payload.override_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao importar DotPack"))
    return result


@app.get("/api/hitl/pending")
async def list_pending_hitl():
    """Lista solicitações de aprovação humana pendentes."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM hitl_approvals WHERE status = 'PENDING' ORDER BY requested_at DESC")
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
        cursor = await db.execute("SELECT id FROM dots WHERE id = ?", (payload.dot_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{payload.dot_id}' não encontrado.")
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
            FROM messages WHERE thread_id = ? ORDER BY created_at ASC, rowid ASC
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
        cursor = await db.execute("SELECT dot_id, primary_dot_id FROM threads WHERE id = ?", (thread_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        default_dot_id = row["primary_dot_id"] or row["dot_id"]

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
    # Atualiza os atributos in-place da instância compartilhada para que background workers (ex: heartbeat_worker_loop)
    # enxerguem as novas credenciais/URL imediatamente sem perder a referência
    provider = getattr(app.state, "ai_provider", None)
    if provider is not None:
        provider.base_url = settings.ai_base_url.rstrip("/")
        provider.api_key = settings.ai_api_key
        provider.default_model = settings.ai_model
        provider.max_retries = settings.ai_max_retries
        provider.timeout = settings.ai_timeout_seconds
    else:
        app.state.ai_provider = OpenAIUniversalProvider(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            default_model=settings.ai_model,
            http_client=getattr(app.state, "http_client", None)
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
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

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
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

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
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    data = body.get("data", {})
    key = data.get("key", {})
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "Mensagem enviada pelo próprio bot"}

    remote_jid = key.get("remoteJid", "")
    if not remote_jid or remote_jid == "status@broadcast":
        return {"status": "ignored", "reason": "Status broadcast ou remoteJid ausente"}

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
    import re
    channel_id = re.sub(r"[^a-z0-9_\-]", "", payload.name.lower().strip().replace(" ", "-"))
    if not channel_id:
        raise HTTPException(status_code=400, detail="Nome de canal inválido.")
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO channels (id, name, description) VALUES (?, ?, ?)",
                (channel_id, payload.name.strip(), payload.description)
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Canal já existe ou dados inválidos: {e}")

    return {"id": channel_id, "name": payload.name.strip(), "description": payload.description}


@app.get("/api/channels/{channel_id}/messages")
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Retorna as mensagens recentes de uma sala temática."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, channel_id, author_type, author_id, content, hop_count, created_at
            FROM channel_messages
            WHERE channel_id = ?
            ORDER BY created_at ASC, rowid ASC
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


class EdgeMaintenancePayload(BaseModel):
    days_threshold: int = 7
    create_backup: bool = False
    dot_id: str | None = None


@app.get("/api/edge/triggers")
async def get_edge_hardware_triggers():
    """Retorna o status em tempo real dos triggers de hardware (SoC Broadcom, MicroSD, RAM)."""
    report = EdgeHardwareTriggers.check_triggers()
    return report


@app.post("/api/edge/maintenance")
async def trigger_edge_maintenance(payload: EdgeMaintenancePayload | None = None):
    """Executa sob demanda a suíte de compactação e saúde do MicroSD."""
    from .storage.maintenance import EdgeMaintenanceManager
    p = payload or EdgeMaintenancePayload()
    backup_dir = None
    if p.create_backup:
        backup_dir = str(Path(settings.sqlite_db_path).parent / "backups")

    report = await EdgeMaintenanceManager.run_full_maintenance(
        backup_dir=backup_dir,
        days_threshold=p.days_threshold,
        dot_id=p.dot_id
    )
    return report


OFFICIAL_SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">

<rect width="100" height="100" rx="16" fill="#07090c"/>
<circle cx="32" cy="50" r="14" fill="#33ff66"/>
<circle cx="68" cy="50" r="14" fill="#38bdf8"/>
<path d="M46 50h8" stroke="#f1f5f9" stroke-width="4" stroke-linecap="round"/>
<circle cx="32" cy="50" r="6" fill="#ffffff"/>
<circle cx="68" cy="50" r="6" fill="#ffffff"/>
</svg>"""


def render_pidots_icon_png(size: int = 192, maskable: bool = False) -> bytes:
    """
    Renderiza o ícone oficial do piDots em buffer PNG rasterizado via Pillow.
    Aplica supersampling 4x e filtro Lanczos para antialiasing de alta precisão.
    Para variantes maskable, ajusta a geometria à Safe Zone de 80% do W3C.
    """
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(canvas_size * 0.1) if maskable else 0
    draw_size = canvas_size - (margin * 2)
    s = draw_size / 100.0

    bg_color = (7, 9, 12, 255)
    if maskable:
        draw.rectangle([0, 0, canvas_size, canvas_size], fill=bg_color)
    else:
        corner_r = int(16 * s)
        draw.rounded_rectangle([0, 0, canvas_size, canvas_size], radius=corner_r, fill=bg_color)

    ox, oy = margin, margin

    # Círculo verde fósforo esquerdo
    cx1, cy1 = ox + 32 * s, oy + 50 * s
    r1 = 14 * s
    draw.ellipse([cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1], fill=(51, 255, 102, 255))

    # Círculo azul blueprint direito
    cx2, cy2 = ox + 68 * s, oy + 50 * s
    r2 = 14 * s
    draw.ellipse([cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2], fill=(56, 189, 248, 255))

    # Traço central de ligação
    x_line1, x_line2 = ox + 46 * s, ox + 54 * s
    y_line = oy + 50 * s
    line_w = max(2, int(4 * s))
    draw.line([(x_line1, y_line), (x_line2, y_line)], fill=(241, 245, 249, 255), width=line_w)

    # Centros brancos crisp
    rc = 6 * s
    draw.ellipse([cx1 - rc, cy1 - rc, cx1 + rc, cy1 + rc], fill=(255, 255, 255, 255))
    draw.ellipse([cx2 - rc, cy2 - rc, cx2 + rc, cy2 + rc], fill=(255, 255, 255, 255))

    img = img.resize((size, size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# Cache de memória preguiçoso (lazy-loaded) para não penalizar o startup da CLI no ARM64
PNG_ICONS_CACHE: Dict[str, bytes] = {}


def get_cached_icon(key: str) -> bytes:
    """Retorna o ícone PNG rasterizado, gerando-o sob demanda na primeira requisição."""
    if key not in PNG_ICONS_CACHE:
        specs = {
            "192": (192, False),
            "512": (512, False),
            "192_maskable": (192, True),
            "512_maskable": (512, True),
        }
        size, maskable = specs.get(key, (192, False))
        PNG_ICONS_CACHE[key] = render_pidots_icon_png(size, maskable=maskable)
    return PNG_ICONS_CACHE[key]


@app.get("/icon.svg")
async def get_app_icon():
    """Serve o ícone oficial vetorial SVG para favicons e navegadores desktop."""
    return Response(
        content=OFFICIAL_SVG_ICON.strip(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@app.get("/icon-192.png")
async def get_app_icon_192():
    """Serve o ícone oficial PNG 192x192 para Android WebAPK e Apple Touch Icon."""
    return Response(
        content=get_cached_icon("192"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@app.get("/icon-512.png")
async def get_app_icon_512():
    """Serve o ícone oficial PNG 512x512 para instalação e splash screen nativa."""
    return Response(
        content=get_cached_icon("512"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@app.get("/icon-maskable-192.png")
async def get_app_icon_maskable_192():
    """Serve o ícone oficial PNG adaptativo com Safe Zone de 80% (192x192)."""
    return Response(
        content=get_cached_icon("192_maskable"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@app.get("/icon-maskable-512.png")
async def get_app_icon_maskable_512():
    """Serve o ícone oficial PNG adaptativo com Safe Zone de 80% (512x512)."""
    return Response(
        content=get_cached_icon("512_maskable"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@app.get("/manifest.json")
async def get_pwa_manifest():
    """Retorna o manifesto oficial PWA 100% compatível com especificação W3C e WebAPK."""
    manifest = {
        "id": "/",
        "name": "piDots Edge Console",
        "short_name": "piDots",
        "description": "Console autônomo e persistente de AI coworkers para hardware de borda",
        "start_url": "/app?source=pwa",
        "scope": "/",
        "display": "standalone",
        "display_override": ["window-controls-overlay", "standalone", "minimal-ui"],
        "background_color": "#07090c",
        "theme_color": "#07090c",
        "orientation": "any",
        "lang": "pt-BR",
        "dir": "ltr",
        "categories": ["productivity", "utilities", "developer-tools"],
        "prefer_related_applications": False,
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/icon-maskable-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable"
            },
            {
                "src": "/icon-maskable-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable"
            },
            {
                "src": "/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any"
            }
        ],
        "shortcuts": [
            {
                "name": "Console Operacional",
                "short_name": "Console",
                "description": "Abrir o workspace e o terminal interativo dos Dots",
                "url": "/app",
                "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}]
            },
            {
                "name": "Documentação Técnica",
                "short_name": "Guia",
                "description": "Abrir o guia didático operacional do piDots",
                "url": "/docs",
                "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}]
            },
            {
                "name": "Apresentação e Visão Geral",
                "short_name": "Visão Geral",
                "description": "Abrir a landing page de onboarding e telemetria",
                "url": "/",
                "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}]
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
    """Retorna o Service Worker com ciclo de vida controlado, cache resiliente e suporte offline."""
    sw_code = """
const CACHE_NAME = 'pidots-cache-v7';
const CORE_STATIC_ASSETS = [
    '/app',
    '/',
    '/docs',
    '/relatorio',
    '/manifest.json',
    '/icon.svg',
    '/icon-192.png',
    '/icon-512.png',
    '/icon-maskable-192.png',
    '/icon-maskable-512.png',
    '/data/locales/pt.json',
    '/data/locales/en.json',
    '/static/css/tokens.css',
    '/static/css/reset.css',
    '/static/css/layout.css',
    '/static/css/components.css',
    '/static/css/mobile.css',
    '/static/css/spa.css',
    '/static/css/landing.css',
    '/static/css/docs.css',
    '/static/css/relatorio.css',
    '/static/js/core/scroll-lock.js',
    '/static/js/core/pixel-system.js',
    '/static/js/core/pidots-i18n.js',
    '/static/js/spa/pidots-api.js',
    '/static/js/spa/slash-commands.js',
    '/static/js/spa/tour-engine.js',
    '/static/js/spa/pidots-ux.js',
    '/static/js/spa/app-init.js',
    '/static/js/landing/landing.js',
    '/static/js/docs/docs.js',
    '/static/js/docs/relatorio.js'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return Promise.allSettled(
                CORE_STATIC_ASSETS.map((asset) => cache.add(asset).catch((err) => {
                    console.warn('[SW] Falha ao pre-armazenar asset:', asset, err);
                }))
            );
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', (event) => {
    // 0. Ignora métodos não-GET (POST/PUT/DELETE não podem ser armazenados na Cache API)
    if (event.request.method !== 'GET') {
        return;
    }

    // 1. Chamadas a API ou endpoints de telemetria e health: bypass total de cache
    if (event.request.url.includes('/api/') || event.request.url.includes('/health')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(
                    JSON.stringify({
                        error: 'Rede indisponivel no modo offline',
                        offline: true,
                        timestamp: Date.now()
                    }),
                    {
                        status: 503,
                        statusText: 'Service Unavailable',
                        headers: { 'Content-Type': 'application/json' }
                    }
                );
            })
        );
        return;
    }

    // 2. Navegacao de paginas HTML (Network-First com fallback para cache local)
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
                return caches.match(event.request).then((cached) => {
                    return cached || caches.match('/app') || caches.match('/') || caches.match('/docs');
                });
            })
        );
        return;
    }

    // 3. Fontes externas (Google Fonts / gstatic) e assets estaticos: Stale-While-Revalidate
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


@app.get("/api/changelog")
async def get_changelog():
    """Retorna as notas de versão e histórico do changelog do piDots."""
    changelog_path = Path(__file__).resolve().parent.parent / "data" / "changelog.json"
    if not changelog_path.exists():
        # Fallback de emergência caso o arquivo não seja encontrado
        return JSONResponse(
            content={
                "system": "piDots",
                "current_version": APP_VERSION,
                "patch_notes": {"version": APP_VERSION, "categories": {}},
                "history": []
            },
            headers={"Cache-Control": "public, max-age=60"}
        )
    try:
        content = json.loads(changelog_path.read_text(encoding="utf-8"))
        return JSONResponse(
            content=content,
            headers={"Cache-Control": "public, max-age=300"}
        )
    except Exception as exc:
        logger.error(f"Erro ao ler data/changelog.json: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar o changelog")


@app.get("/data/locales/{lang}.json")
async def get_locale_dictionary(lang: str):
    """Serve os dicionários de internacionalização (PT/EN) para o frontend com cache de borda."""
    if lang not in ["pt", "en"]:
        raise HTTPException(status_code=404, detail="Locale não suportado")
    locale_path = Path(__file__).resolve().parent.parent / "data" / "locales" / f"{lang}.json"
    if not locale_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de locale não encontrado")
    try:
        content = json.loads(locale_path.read_text(encoding="utf-8"))
        return JSONResponse(
            content=content,
            headers={
                "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
                "Content-Language": "pt-BR" if lang == "pt" else "en-US"
            }
        )
    except Exception as exc:
        logger.error(f"Erro ao carregar locale {lang}: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar dicionário de idioma")


@app.get("/static/pidots-i18n.js")
async def get_i18n_script():
    """Serve o micro-motor Vanilla JS de internacionalização com cache estático (rota de retrocompatibilidade)."""
    script_path = Path(__file__).resolve().parent.parent / "static" / "js" / "core" / "pidots-i18n.js"
    if not script_path.exists():
        script_path = Path(__file__).resolve().parent.parent / "static" / "pidots-i18n.js"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script i18n não encontrado")
    return Response(
        content=script_path.read_text(encoding="utf-8"),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"}
    )


# ==============================================================================
# Rotas Canônicas de Superfície & Redirecionamentos Suaves (RFC 7538)
# ==============================================================================

@app.api_route("/", methods=["GET", "HEAD"], response_class=Response)
async def serve_landing_presentation(request: Request):
    """Serve a Landing Page Oficial de Apresentação e Onboarding do piDots em Pixel Paper UI."""
    return page_manager.serve("landing.html", request)


@app.api_route("/app", methods=["GET", "HEAD"], response_class=Response)
@app.api_route("/workspace", methods=["GET", "HEAD"], response_class=Response)
@app.api_route("/app/{path:path}", methods=["GET", "HEAD"], response_class=Response)
async def serve_spa_console(request: Request, path: str = ""):
    """Serve o Console Operacional SPA dos Agentes (100% Funcional e reativo)."""
    return page_manager.serve("app.html", request)


@app.api_route("/docs", methods=["GET", "HEAD"], response_class=Response)
async def serve_canonical_guide(request: Request):
    """Serve o Guia Didático Operacional e Documentação Oficial em Pixel Paper UI."""
    return page_manager.serve("docs.html", request)


@app.api_route("/relatorio", methods=["GET", "HEAD"], response_class=Response)
async def serve_study_report(request: Request):
    """Serve o relatório completo de estudo e viabilidade."""
    return page_manager.serve("relatorio.html", request)


@app.api_route("/apresentacao", methods=["GET", "HEAD"])
async def redirect_apresentacao():
    """Redireciona a rota legada /apresentacao para a raiz canonica /."""
    return RedirectResponse(url="/", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.api_route("/guia", methods=["GET", "HEAD"])
async def redirect_guia():
    """Redireciona a rota legada /guia para a documentacao canonica /docs."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.api_route("/console", methods=["GET", "HEAD"])
async def redirect_console():
    """Redireciona o alias /console para a aplicacao /app."""
    return RedirectResponse(url="/app", status_code=status.HTTP_308_PERMANENT_REDIRECT)



