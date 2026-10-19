"""
Agregador Central de Roteadores da API do piDots.
Consolida e exporta os sub-roteadores desacoplados de dots, threads, tasks, canais,
webhooks, telemetria edge, governança HITL e superfícies PWA.
"""

from fastapi import APIRouter

from .routes_dots import router as dots_router
from .routes_hitl import router as hitl_router
from .routes_threads import router as threads_router
from .routes_tasks import router as tasks_router
from .routes_channels import router as channels_router
from .routes_webhooks import router as webhooks_router
from .routes_edge import router as edge_router
from .routes_pwa import router as pwa_router

api_router = APIRouter()

api_router.include_router(dots_router)
api_router.include_router(hitl_router)
api_router.include_router(threads_router)
api_router.include_router(tasks_router)
api_router.include_router(channels_router)
api_router.include_router(webhooks_router)
api_router.include_router(edge_router)
api_router.include_router(pwa_router)

__all__ = [
    "api_router",
    "dots_router",
    "hitl_router",
    "threads_router",
    "tasks_router",
    "channels_router",
    "webhooks_router",
    "edge_router",
    "pwa_router",
]
