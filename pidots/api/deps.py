"""
Dependências e Injeções Compartilhadas da API do piDots.
Fornece acessores desacoplados para recursos instanciados no ciclo de vida (Lifespan).
"""

from fastapi import Request
import httpx
from ..providers.openai_client import OpenAIUniversalProvider


def get_ai_provider(request: Request) -> OpenAIUniversalProvider:
    """Recupera a instância ativa do cliente de inferência IA a partir do estado do app."""
    provider = getattr(request.app.state, "ai_provider", None)
    if provider is None:
        provider = OpenAIUniversalProvider()
        request.app.state.ai_provider = provider
    return provider


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Recupera o pool de conexões HTTP compartilhado."""
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        request.app.state.http_client = client
    return client


def get_page_manager(request: Request):
    """Recupera o gerenciador EdgeAssetManager em RAM."""
    page_mgr = getattr(request.app.state, "page_manager", None)
    if page_mgr is None:
        from ..main import page_manager
        return page_manager
    return page_mgr
