"""
Rotas para PWA, Manifest, Service Worker, Ícones Rasterizados e Superfícies HTML do piDots.
"""

import io
from typing import Dict
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from PIL import Image, ImageDraw

from .deps import get_page_manager

router = APIRouter(tags=["PWA & Surfaces"])

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


@router.get("/icon.svg")
async def get_app_icon():
    """Serve o ícone oficial vetorial SVG para favicons e navegadores desktop."""
    return Response(
        content=OFFICIAL_SVG_ICON.strip(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@router.get("/icon-192.png")
async def get_app_icon_192():
    """Serve o ícone oficial PNG 192x192 para Android WebAPK e Apple Touch Icon."""
    return Response(
        content=get_cached_icon("192"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@router.get("/icon-512.png")
async def get_app_icon_512():
    """Serve o ícone oficial PNG 512x512 para instalação e splash screen nativa."""
    return Response(
        content=get_cached_icon("512"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@router.get("/icon-maskable-192.png")
async def get_app_icon_maskable_192():
    """Serve o ícone oficial PNG adaptativo com Safe Zone de 80% (192x192)."""
    return Response(
        content=get_cached_icon("192_maskable"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@router.get("/icon-maskable-512.png")
async def get_app_icon_maskable_512():
    """Serve o ícone oficial PNG adaptativo com Safe Zone de 80% (512x512)."""
    return Response(
        content=get_cached_icon("512_maskable"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"}
    )


@router.get("/manifest.json")
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


@router.get("/sw.js")
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


# ==============================================================================
# Rotas Canônicas de Superfície & Redirecionamentos Suaves com Sunset RFC 8594
# ==============================================================================

@router.api_route("/", methods=["GET", "HEAD"], response_class=Response)
async def serve_landing_presentation(request: Request):
    """Serve a Landing Page Oficial de Apresentação e Onboarding do piDots em Pixel Paper UI."""
    page_mgr = get_page_manager(request)
    return page_mgr.serve("landing.html", request)


@router.api_route("/app", methods=["GET", "HEAD"], response_class=Response)
@router.api_route("/workspace", methods=["GET", "HEAD"], response_class=Response)
@router.api_route("/app/{path:path}", methods=["GET", "HEAD"], response_class=Response)
async def serve_spa_console(request: Request, path: str = ""):
    """Serve o Console Operacional SPA dos Agentes (100% Funcional e reativo)."""
    page_mgr = get_page_manager(request)
    return page_mgr.serve("app.html", request)


@router.api_route("/docs", methods=["GET", "HEAD"], response_class=Response)
async def serve_canonical_guide(request: Request):
    """Serve o Guia Didático Operacional e Documentação Oficial em Pixel Paper UI."""
    page_mgr = get_page_manager(request)
    return page_mgr.serve("docs.html", request)


@router.api_route("/relatorio", methods=["GET", "HEAD"], response_class=Response)
async def serve_study_report(request: Request):
    """Serve o relatório completo de estudo e viabilidade."""
    page_mgr = get_page_manager(request)
    return page_mgr.serve("relatorio.html", request)


@router.api_route("/apresentacao", methods=["GET", "HEAD"])
async def redirect_apresentacao():
    """Redireciona a rota legada /apresentacao para a raiz canonica / com cabecalho Sunset."""
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
        headers={
            "Sunset": "Wed, 01 Jan 2027 00:00:00 GMT",
            "Link": '</>; rel="canonical"'
        }
    )


@router.api_route("/guia", methods=["GET", "HEAD"])
async def redirect_guia():
    """Redireciona a rota legada /guia para a documentacao canonica /docs com cabecalho Sunset."""
    return RedirectResponse(
        url="/docs",
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
        headers={
            "Sunset": "Wed, 01 Jan 2027 00:00:00 GMT",
            "Link": '</docs>; rel="canonical"'
        }
    )


@router.api_route("/console", methods=["GET", "HEAD"])
async def redirect_console():
    """Redireciona o alias /console para a aplicacao /app com cabecalho Sunset."""
    return RedirectResponse(
        url="/app",
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
        headers={
            "Sunset": "Wed, 01 Jan 2027 00:00:00 GMT",
            "Link": '</app>; rel="canonical"'
        }
    )
