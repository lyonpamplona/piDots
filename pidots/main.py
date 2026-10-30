"""
piDots Core Application (FastAPI + uvloop).
Servidor assíncrono em worker único calibrado para Raspberry Pi 4B (ARM64).
Serve a API REST modular, streaming de eventos AG-UI e o console SPA via EdgeAssetManager.
"""

import asyncio
import gzip
import hashlib
import httpx
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .config import settings
from .core.edge_triggers import EdgeHardwareTriggers
from .providers.openai_client import OpenAIUniversalProvider
from .storage.db import get_db, init_edge_database

logger = logging.getLogger("pidots.main")

APP_VERSION = "1.5.5"


HTML_404_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>piDots // 404 Não Encontrado</title>
<style>
  :root { --bg: #0c0d0e; --ink: #c9cbcf; --green: #33ff66; --amber: #f59e0b; --border: #26292d; }
  body { background: var(--bg); color: var(--ink); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; margin: 0; padding: 24px; display: flex; align-items: center; justify-content: center; min-height: 100vh; box-sizing: border-box; }
  .box { max-width: 520px; width: 100%; border: 1px solid var(--border); padding: 24px; background: #121316; }
  .tag { color: var(--amber); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
  h1 { font-size: 18px; margin: 0 0 12px 0; color: #fff; font-weight: 600; }
  p { font-size: 13px; line-height: 1.5; color: var(--ink); margin: 0 0 16px 0; }
  ul { list-style: none; padding: 0; margin: 0 0 16px 0; font-size: 12px; }
  li { padding: 4px 0; }
  a { color: var(--green); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .foot { font-size: 11px; color: #6b7280; border-top: 1px dashed var(--border); padding-top: 12px; }
</style>
</head>
<body>
<div class="box">
  <div class="tag">[erro 404 // recurso inexistente]</div>
  <h1>Página não encontrada</h1>
  <p>O arquivo ou rota solicitada não existe neste nó de borda.</p>
  <ul>
    <li>-> <a href="/">/ (Apresentação do piDots)</a></li>
    <li>-> <a href="/app">/app (Console Operacional)</a></li>
    <li>-> <a href="/docs">/docs (Manual Técnico)</a></li>
    <li>-> <a href="/relatorio">/relatorio (Auditoria Técnica)</a></li>
  </ul>
  <div class="foot">piDots Edge Core // Nó ARM64</div>
</div>
</body>
</html>"""


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
                    content=HTML_404_PAGE,
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
    app.state.page_manager = page_manager

    # Sanity check preventivo de credenciais de inferência no arranque do nó Edge
    if settings.ai_api_key in ("", "sua_chave_aqui", "placeholder"):
        logger.warning(
            "AI_API_KEY vazia ou placeholder ('%s'). O nó subiu em modo offline: inferências remotas falharão até você definir a chave no .env ou no painel /settings.",
            settings.ai_api_key
        )
    else:
        logger.info("motor de inferência pronto -> modelo '%s'", settings.ai_model)

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


app = FastAPI(
    title="piDots Edge Core",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)
app.state.page_manager = page_manager

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

# Registro Central do Roteador Modular
app.include_router(api_router)
