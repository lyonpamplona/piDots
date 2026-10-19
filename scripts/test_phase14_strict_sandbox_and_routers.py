"""
Teste e Homologação da Fase 14: Sandbox Estrito Bubblewrap e Fatiamento Modular de Rotas.
Valida o bloqueio defensivo de terminal sem bwrap (STRICT_SANDBOX=true),
a integridade funcional dos sub-roteadores desacoplados em pidots/api/,
os redirecionamentos suaves com Sunset RFC 8594 e a higiene total da base de código.
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from pidots.config import settings
from pidots.storage.db import init_edge_database
from pidots.tools.terminal import execute_shell_command
from pidots.main import app, page_manager, EdgeAssetManager, APP_VERSION


async def test_strict_sandbox_governance():
    """Valida a recusa de shell em modo STRICT_SANDBOX quando bwrap não está disponível."""
    print("\n--- [1/4] Testando Governança e Isolamento de Terminal Sandbox ---")

    # Caso 1: Teste com strict_sandbox=True simulando ausência de bwrap
    print("  -> Verificando recusa estrita (exit_code 126) quando bwrap inexiste e STRICT_SANDBOX=True...")
    original_strict = settings.strict_sandbox
    try:
        settings.strict_sandbox = True
        with patch("pidots.tools.terminal.shutil.which", return_value=None):
            result = await execute_shell_command(dot_id="test-dot", command="echo 'Tentativa de escape'")
            assert result["exit_code"] == 126, f"Esperado exit_code 126, obtido {result['exit_code']}"
            assert "Erro de Governanca: Execucao recusada" in result["stderr"]
            assert result.get("method") == "strict_rejection"
            print("     [OK] Bloqueio estrito efetuado com sucesso (exit_code 126 e log de auditoria).")

        # Caso 2: Teste com strict_sandbox=False (desenvolvimento permissivo)
        print("  -> Verificando fallback permissivo em modo desenvolvimento (STRICT_SANDBOX=False)...")
        settings.strict_sandbox = False
        with patch("pidots.tools.terminal.shutil.which", return_value=None):
            result = await execute_shell_command(dot_id="test-dot", command="echo 'piDots Sandbox Permissivo'")
            assert result["exit_code"] == 0, f"Esperado exit_code 0, obtido {result['exit_code']}"
            assert "piDots Sandbox Permissivo" in result["stdout"]
            assert result.get("method") == "subprocess"
            print("     [OK] Fallback permissivo funcional para ambientes de desenvolvimento sem namespaces.")

        # Caso 3: Teste de truncamento defensivo de 10KB
        print("  -> Verificando truncamento de buffer para comandos que excedem 10KB...")
        # Gera uma saída de 20KB
        result_large = await execute_shell_command(dot_id="test-dot", command="python3 -c \"print('A' * 20000)\"")
        assert len(result_large["stdout"]) <= 10240 + 200, "Saída excedeu o teto estrito de truncamento"
        assert "[TRUNCADO:" in result_large["stdout"]
        print("     [OK] Truncamento defensivo em 10KB validado com sucesso.")

    finally:
        settings.strict_sandbox = original_strict


async def test_modular_api_routers():
    """Valida todos os sub-roteadores desacoplados em pidots/api/ via chamadas ASGI."""
    print("\n--- [2/4] Testando Contratos de Rotas Modulares em pidots/api/ ---")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Rotas Canônicas de Páginas e Assets
        print("  -> Validando superfícies HTML e EdgeAssetManager em RAM...")
        r_root = await client.get("/")
        assert r_root.status_code == 200, f"GET / falhou com status {r_root.status_code}"
        assert r_root.headers.get("ETag"), "Falta header ETag na entrega de landing.html"

        r_app = await client.get("/app")
        assert r_app.status_code == 200, f"GET /app falhou com status {r_app.status_code}"

        r_docs = await client.get("/docs")
        assert r_docs.status_code == 200, f"GET /docs falhou com status {r_docs.status_code}"

        r_relatorio = await client.get("/relatorio")
        assert r_relatorio.status_code == 200, f"GET /relatorio falhou com status {r_relatorio.status_code}"
        print("     [OK] Superfícies HTML entregues com sucesso via EdgeAssetManager.")

        # 2. Redirecionamentos Suaves com Sunset RFC 8594
        print("  -> Validando redirecionamentos HTTP 308 com Sunset RFC 8594...")
        r_red_apres = await client.get("/apresentacao", follow_redirects=False)
        assert r_red_apres.status_code == 308, f"Esperado 308, obtido {r_red_apres.status_code}"
        assert r_red_apres.headers.get("location") == "/"
        assert "Wed, 01 Jan 2027" in r_red_apres.headers.get("sunset", "")

        r_red_guia = await client.get("/guia", follow_redirects=False)
        assert r_red_guia.status_code == 308
        assert r_red_guia.headers.get("location") == "/docs"

        r_red_console = await client.get("/console", follow_redirects=False)
        assert r_red_console.status_code == 308
        assert r_red_console.headers.get("location") == "/app"
        print("     [OK] Redirecionamentos legados preservados com cabeçalho Sunset.")

        # 3. PWA, Ícones e Service Worker
        print("  -> Validando PWA Manifest, Ícones e Service Worker...")
        r_icon = await client.get("/icon.svg")
        assert r_icon.status_code == 200
        assert "image/svg+xml" in r_icon.headers.get("content-type", "")

        r_png192 = await client.get("/icon-192.png")
        assert r_png192.status_code == 200
        assert "image/png" in r_png192.headers.get("content-type", "")

        r_manifest = await client.get("/manifest.json")
        assert r_manifest.status_code == 200
        assert r_manifest.json()["short_name"] == "piDots"

        r_sw = await client.get("/sw.js")
        assert r_sw.status_code == 200
        assert "pidots-cache-v7" in r_sw.text
        print("     [OK] Recursos de PWA e Service Worker v7 íntegros.")

        # 4. Telemetria Edge e Settings
        print("  -> Validando rotas de telemetria edge e configurações...")
        r_health = await client.get("/health")
        assert r_health.status_code == 200
        data_health = r_health.json()
        assert data_health["status"] == "healthy"
        assert "soc_temperature_celsius" in data_health

        r_triggers = await client.get("/api/edge/triggers")
        assert r_triggers.status_code == 200

        r_settings = await client.get("/api/settings")
        assert r_settings.status_code == 200
        assert "ai" in r_settings.json()

        r_changelog = await client.get("/api/changelog")
        assert r_changelog.status_code == 200
        assert r_changelog.json()["current_version"] in ("1.5.2", "1.5.3")
        print("     [OK] Endpoints de telemetria, hardware triggers e configurações ativos.")

        # 5. Dots, Spaces, Tasks e Canais
        print("  -> Validando endpoints de Dots, Spaces, Tasks e Canais...")
        r_dots = await client.get("/api/dots")
        assert r_dots.status_code == 200
        assert isinstance(r_dots.json(), list)

        r_spaces = await client.get("/api/spaces")
        assert r_spaces.status_code == 200

        r_tasks = await client.get("/api/tasks")
        assert r_tasks.status_code == 200

        r_channels = await client.get("/api/channels")
        assert r_channels.status_code == 200

        r_hitl = await client.get("/api/hitl/pending")
        assert r_hitl.status_code == 200
        print("     [OK] Endpoints de entidades corporativas e colaboração multi-bot validados.")


async def test_codebase_hygiene():
    """Valida a ausência de termos obsoletos no código (verboo, qwen3.8)."""
    print("\n--- [3/4] Testando Higiene da Base de Código (Zero Resíduos) ---")

    forbidden_patterns = ["verboocode", "qwen3.8"]
    source_dir = Path(__file__).resolve().parent.parent / "pidots"
    violating_files = []

    for py_file in source_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in content:
                violating_files.append((str(py_file), pattern))

    assert not violating_files, f"Encontradas violações de menções obsoletas: {violating_files}"
    print("     [OK] Zero menções a 'verboocode' ou 'qwen3.8' detectadas no pacote pidots/.")


async def test_edge_asset_manager_performance():
    """Valida a performance e headers do EdgeAssetManager em memória RAM."""
    print("\n--- [4/4] Testando Performance e Mecanismo de Cache do EdgeAssetManager ---")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Primeira requisição: obtém ETag
        r1 = await client.get("/app")
        etag = r1.headers.get("ETag")
        assert etag, "EdgeAssetManager deve gerar ETag SHA-256 para documentos em RAM"

        # Segunda requisição condicional: If-None-Match deve retornar HTTP 304 Not Modified
        r2 = await client.get("/app", headers={"If-None-Match": etag})
        assert r2.status_code == 304, f"Esperado HTTP 304 Not Modified, obtido {r2.status_code}"
        print("     [OK] Validação condicional ETag (HTTP 304) validada com economia de I/O.")


async def main():
    print("================================================================================")
    print(" [piDots] Teste e Homologação Automatizada - Fase 14")
    print(f" Versão: {APP_VERSION} | Topologia: Modular FastAPI + Sandbox Estrito")
    print("================================================================================")

    await init_edge_database()
    await test_strict_sandbox_governance()
    await test_modular_api_routers()
    await test_codebase_hygiene()
    await test_edge_asset_manager_performance()

    print("\n================================================================================")
    print(" [SUCESSO TOTAL] Todos os testes da Fase 14 foram homologados com 100% de êxito.")
    print("================================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
