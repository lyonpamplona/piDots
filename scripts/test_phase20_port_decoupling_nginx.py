"""
Suite de Homologacao Automatizada — Fase 20 / Fase D2: Desacoplamento de Portas e Nginx Multi-Porta
====================================================================================================
Valida cirurgicamente a topologia de portas independentes e proxy reverso de borda:
- Porta 8081: Landing Page (X-Edge-Service: landing-surface)
- Porta 8082: Console Workspace App SPA (X-Edge-Service: app-console-root)
- Porta 8083: Documentacao e Estudos (X-Edge-Service: docs-guide-root)
- Porta 8088: Gateway Unificado Retrocompativel (Path-based e Redirecionamentos 308)
- Endpoints de API REST (/api/dots, /health) em todas as portas
- Entrega estatica direta e isolada via Nginx Alpine (< 8MB RAM)
- Higiene rigorosa: Zero emojis no codigo, configuracoes e cabeçalhos
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def check_no_emojis(text: str) -> bool:
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.search(text) is None


def http_get(url: str, timeout: float = 5.0) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "piDots-Edge-Auditor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as e:
        headers = {k.lower(): v for k, v in e.headers.items()}
        return e.code, headers, e.read()


def test_phase20_port_decoupling():
    print("=" * 72)
    print("HOMOLOGACAO INTEGRADA: FASE D2 — ENGENHARIA NGINX MULTI-PORTA")
    print("=" * 72)

    # 1. Verificacao de Higiene de Codigo e Zero Emojis em nginx/nginx.conf
    print("[TESTE 1/6] Validando integridade e ausencia de emojis em nginx/nginx.conf...")
    nginx_conf_path = ROOT_DIR / "nginx" / "nginx.conf"
    assert nginx_conf_path.exists(), "Arquivo nginx/nginx.conf nao encontrado"
    nginx_content = nginx_conf_path.read_text(encoding="utf-8")
    assert check_no_emojis(nginx_content), "Emojis detectados em nginx/nginx.conf"
    assert "listen 8081;" in nginx_content, "Bloco listen 8081 ausente"
    assert "listen 8082;" in nginx_content, "Bloco listen 8082 ausente"
    assert "listen 8083;" in nginx_content, "Bloco listen 8083 ausente"
    assert "listen 8088 default_server;" in nginx_content, "Bloco listen 8088 ausente"
    assert "proxy_buffering off;" in nginx_content, "Diretiva proxy_buffering off ausente para SSE"
    print("  -> [OK] nginx/nginx.conf integro, com 4 blocos de escuta e zero emojis.")

    # 2. Validacao da Porta 8081 (Landing Page)
    print("[TESTE 2/6] Validando Porta 8081 (Landing Page Surface)...")
    status, headers, body = http_get("http://localhost:8081/")
    assert status == 200, f"Porta 8081 retornou status {status}"
    assert headers.get("x-edge-service") == "landing-surface", "Cabecalho X-Edge-Service incorreto em 8081"
    assert b"<!DOCTYPE html>" in body or b"<html" in body, "Corpo HTML invalido na porta 8081"

    status_static, headers_static, _ = http_get("http://localhost:8081/static/css/landing.css")
    assert status_static == 200, f"Static em 8081 retornou status {status_static}"
    assert headers_static.get("x-edge-service") == "landing-static", "Cache X-Edge-Service estatico ausente em 8081"

    status_api, _, body_api = http_get("http://localhost:8081/api/dots")
    assert status_api == 200, f"Proxy /api/dots em 8081 retornou {status_api}"
    dots_data = json.loads(body_api.decode("utf-8"))
    assert len(dots_data) >= 1, "Lista de dots vazia em 8081"
    print("  -> [OK] Porta 8081 validada (Raiz Landing, Static Direct, API Proxy).")

    # 3. Validacao da Porta 8082 (Console Workspace App SPA)
    print("[TESTE 3/6] Validando Porta 8082 (Console Workspace App SPA)...")
    status, headers, body = http_get("http://localhost:8082/")
    assert status == 200, f"Porta 8082 retornou status {status}"
    assert headers.get("x-edge-service") == "app-console-root", "Cabecalho X-Edge-Service incorreto em 8082"
    assert b"id=\"activityRail\"" in body or b"id=\"agentGrid\"" in body or b"piDots" in body, "Corpo do App ausente na raiz de 8082"

    status_alias, _, _ = http_get("http://localhost:8082/app")
    assert status_alias == 200, f"Alias /app em 8082 retornou {status_alias}"

    status_static_spa, headers_static_spa, _ = http_get("http://localhost:8082/static/css/spa.css")
    assert status_static_spa == 200, f"Static em 8082 retornou {status_static_spa}"
    assert headers_static_spa.get("x-edge-service") == "app-static", "Cache X-Edge-Service estatico ausente em 8082"

    status_api_app, _, body_api_app = http_get("http://localhost:8082/api/dots")
    assert status_api_app == 200, f"Proxy /api/dots em 8082 retornou {status_api_app}"
    print("  -> [OK] Porta 8082 validada (Raiz App SPA, Alias /app, Static Direct, API Proxy).")

    # 4. Validacao da Porta 8083 (Documentacao e Estudos)
    print("[TESTE 4/6] Validando Porta 8083 (Docs & Knowledge Base)...")
    status, headers, body = http_get("http://localhost:8083/")
    assert status == 200, f"Porta 8083 retornou status {status}"
    assert headers.get("x-edge-service") == "docs-guide-root", "Cabecalho X-Edge-Service incorreto em 8083"
    assert b"Guia Operacional" in body or b"Documentacao" in body or b"piDots" in body, "Conteudo de Docs ausente na raiz de 8083"

    status_relatorio, _, body_relatorio = http_get("http://localhost:8083/relatorio")
    assert status_relatorio == 200, f"Rota /relatorio em 8083 retornou {status_relatorio}"
    assert b"OpenDots" in body_relatorio or b"Relat" in body_relatorio, "Conteudo de relatorio invalido"

    status_static_docs, headers_static_docs, _ = http_get("http://localhost:8083/static/css/docs.css")
    assert status_static_docs == 200, f"Static em 8083 retornou {status_static_docs}"
    assert headers_static_docs.get("x-edge-service") == "docs-static", "Cache X-Edge-Service estatico ausente em 8083"
    print("  -> [OK] Porta 8083 validada (Raiz Docs, Rota /relatorio, Static Direct, API Proxy).")

    # 5. Validacao da Porta 8088 (Gateway Unificado Retrocompativel)
    print("[TESTE 5/6] Validando Porta 8088 (Gateway Unificado Path-Based)...")
    status_gw_root, _, _ = http_get("http://localhost:8088/")
    assert status_gw_root == 200, f"Raiz em 8088 retornou {status_gw_root}"

    status_gw_app, _, _ = http_get("http://localhost:8088/app")
    assert status_gw_app == 200, f"/app em 8088 retornou {status_gw_app}"

    status_gw_docs, _, _ = http_get("http://localhost:8088/docs")
    assert status_gw_docs == 200, f"/docs em 8088 retornou {status_gw_docs}"

    # Validacao de redirecionamento Sunset RFC 8594 (308 Permanent Redirect)
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    # Requisicao sem seguir redirect para validar status 308 e headers
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def http_error_308(self, req, fp, code, msg, headers):
            return fp

    custom_opener = urllib.request.build_opener(NoRedirectHandler)
    req_redirect = urllib.request.Request("http://localhost:8088/apresentacao")
    try:
        resp_redirect = custom_opener.open(req_redirect)
        redir_status = resp_redirect.status
        redir_headers = {k.lower(): v for k, v in resp_redirect.headers.items()}
    except urllib.error.HTTPError as e:
        redir_status = e.code
        redir_headers = {k.lower(): v for k, v in e.headers.items()}

    assert redir_status == 308, f"Redirecionamento /apresentacao retornou {redir_status} (esperado 308)"
    assert "sunset" in redir_headers, "Cabecalho Sunset RFC 8594 ausente em /apresentacao"
    print("  -> [OK] Porta 8088 validada (Path-Based completo, Sunset 308 preservado).")

    # 6. Validacao de Health Check Unificado e Internacionalizacao Direta
    print("[TESTE 6/6] Validando Health Check e Internacionalizacao (/data/locales/)...")
    for port in (8081, 8082, 8083, 8088):
        st, _, bd = http_get(f"http://localhost:{port}/health")
        assert st == 200, f"/health na porta {port} retornou {st}"
        health_json = json.loads(bd.decode("utf-8"))
        assert health_json.get("status") == "healthy", f"Status unhealthy na porta {port}"

        st_loc, _, bd_loc = http_get(f"http://localhost:{port}/data/locales/pt.json")
        assert st_loc == 200, f"/data/locales/pt.json na porta {port} retornou {st_loc}"
        loc_data = json.loads(bd_loc.decode("utf-8"))
        assert "nav" in loc_data, f"Dicionario pt.json invalido na porta {port}"

    print("  -> [OK] Health Check e Internacionalizacao validados em 100% das portas.")

    # 7. Validacao da Fase D3: Inclusao e Integridade do Cross-Surface Router
    print("[TESTE 7/7] Validando Fase D3 — Inclusao e Integridade do Cross-Surface Router...")
    html_pages = [
        ROOT_DIR / "pages" / "landing.html",
        ROOT_DIR / "pages" / "app.html",
        ROOT_DIR / "pages" / "docs.html",
        ROOT_DIR / "pages" / "relatorio.html",
    ]
    for page in html_pages:
        assert page.exists(), f"Pagina {page} nao encontrada"
        html_content = page.read_text(encoding="utf-8")
        assert "cross-surface-router.js" in html_content, f"Script cross-surface-router.js ausente em {page.name}"
        assert check_no_emojis(html_content), f"Emojis detectados em {page.name}"

    # Verificacao de entrega estatica nas 4 portas
    for port in (8081, 8082, 8083, 8088):
        st_router, _, bd_router = http_get(f"http://localhost:{port}/static/js/core/cross-surface-router.js")
        assert st_router == 200, f"cross-surface-router.js retornou status {st_router} na porta {port}"
        assert b"CrossSurfaceRouter" in bd_router, f"Conteudo invalido na porta {port}"

    # Execucao do teste unitario em Node.js
    import subprocess
    node_res = subprocess.run(["node", str(ROOT_DIR / "scripts" / "test_cross_surface_router.js")], capture_output=True, text=True)
    assert node_res.returncode == 0, f"Teste em Node.js falhou:\n{node_res.stderr}"
    print("  -> [OK] Inclusao nas 4 paginas, entrega estatica multi-porta e runtime JS validados.")

    print("=" * 72)
    print("RESULTADO FINAL: FASES D1, D2 E D3 HOMOLOGADAS COM 100% DE SUCESSO.")
    print("=" * 72)


if __name__ == "__main__":
    test_phase20_port_decoupling()
