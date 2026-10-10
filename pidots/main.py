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
from fastapi.responses import HTMLResponse, JSONResponse
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

    # Inicia rotina periódica de proteção contra inchaço do MicroSD (a cada 15 min)
    checkpoint_task = asyncio.create_task(periodic_wal_checkpoint(interval_seconds=900))

    yield

    checkpoint_task.cancel()
    await app.state.http_client.aclose()


app = FastAPI(
    title="piDots Edge Core",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        cursor = await db.execute("SELECT id, name, role, model, workspace_path, is_active FROM dots")
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
    """Obtém as mensagens registradas em uma thread."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, role, content, thought_log, created_at FROM messages WHERE thread_id = ? ORDER BY created_at ASC",
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
    Implementa o protocolo AG-UI v1.0.
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT dot_id FROM threads WHERE id = ?", (thread_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thread não encontrada.")
        dot_id = row["dot_id"]

    agent = DotAgent(
        dot_id=dot_id,
        provider=request.app.state.ai_provider
    )

    async def event_generator():
        async for event in agent.run_thread(thread_id=thread_id, user_message=payload.message):
            ev_name = event["event"]
            ev_data = json.dumps(event["data"], ensure_ascii=False)
            yield f"event: {ev_name}\ndata: {ev_data}\n\n"

    from fastapi.responses import StreamingResponse
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


@app.get("/api/workspaces/{dot_id}/export.zip")
async def export_workspace_zip(dot_id: str):
    """Exporta o workspace completo de um Dot em formato ZIP."""
    zip_bytes = await SpacesManager.export_workspace_zip(dot_id)
    from fastapi.responses import Response
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
            "telegram_chat_id": settings.telegram_chat_id
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
        telegram_chat_id=payload.telegram_chat_id
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


@app.get("/manifest.json")
async def get_pwa_manifest():
    """Retorna o manifesto oficial PWA para instalação no celular e desktop."""
    manifest = {
        "name": "piDots Edge Console",
        "short_name": "piDots",
        "description": "Console autônomo e persistente de AI coworkers para Raspberry Pi 4B",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090d13",
        "theme_color": "#0d1117",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%23090d13'/%3E%3Ccircle cx='35' cy='50' r='12' fill='%2322c55e'/%3E%3Ccircle cx='65' cy='50' r='12' fill='%2338bdf8'/%3E%3Cpath d='M35 50h30' stroke='%23f1f5f9' stroke-width='4'/%3E%3C/svg%3E",
                "sizes": "192x192 512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    return JSONResponse(content=manifest, media_type="application/manifest+json")


@app.get("/sw.js")
async def get_service_worker():
    """Retorna o Service Worker para suporte PWA offline-first."""
    sw_code = """
const CACHE_NAME = 'pidots-cache-v1';
const STATIC_ASSETS = ['/', '/manifest.json'];

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
    // Para chamadas à API, estratégia Network-First com bypass de cache
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

    // Para páginas e assets estáticos, estratégia Cache-First com fallback de rede
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request).then((response) => {
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                return response;
            });
        })
    );
});
"""
    from fastapi.responses import Response
    return Response(content=sw_code.strip(), media_type="application/javascript")


def find_html_file(filename: str) -> Path:
    """Localiza o arquivo HTML seja dentro do container Docker (/app) ou no host."""
    candidates = [
        Path(__file__).resolve().parent.parent / filename,
        Path("/app") / filename,
        Path("/mnt/storage/piDots") / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


@app.get("/", response_class=HTMLResponse)
async def serve_spa_prototype():
    """Serve o console interativo SPA do piDots."""
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

