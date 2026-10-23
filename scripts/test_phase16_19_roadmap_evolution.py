"""
Suíte de Homologação Integrada — Fases 16, 17, 18 e 19 (Roadmap de Evolução Contínua)
======================================================================================
Valida cirurgicamente todas as entregas do roadmap_evolution.md:
- Fase 16: UX Mobile-First (Header 48px, Drawer Quick Controls, Badge Canvas) e Tríptico Desktop (Footer Hardware ASCII, Badge CoAgents %, Bloco 5 MemGPT).
- Fase 17: Infraestrutura Nginx Alpine (nginx/nginx.conf, docker-compose.yml), Flag ENABLE_LEGACY_REDIRECTS (308 vs 410) e Sandbox Estrito (STRICT_SANDBOX -> exit code 126).
- Fase 18: Governança Cognitiva (HITL TTL expire-stale, Self-Healing MAX_HEAL_ATTEMPTS=2, Early Consensus Exit, Deduplicação Semântica >= 0.92 e Barramento GPIO/MQTT despertando @dot-supervisor).
- Fase 19: Engenharia Centauro (AI_MANIFESTO.md zero emojis), CI Multi-Arch (linux/amd64,linux/arm64) e Catálogo Oficial de Dot Packs v1.1 Assinados com SHA-256 (dot-secops, dot-homelab, dot-finops).
"""

import os
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pidots.config import settings
from pidots.core.council import CouncilOrchestrator
from pidots.core.dot_pack import DotPackManager
from pidots.core.self_healing import MAX_HEAL_ATTEMPTS, SelfHealingHarness
from pidots.main import app


def check_no_emojis(text: str) -> bool:
    """Verifica ausência de caracteres pictográficos/emojis."""
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


def test_phase16_ui_ux_and_mobile():
    print("[TESTE 1/4] Validando Fase 16 — Ergonomia Mobile & Tríptico Desktop...")
    app_html = (ROOT_DIR / "pages" / "app.html").read_text(encoding="utf-8")
    mobile_css = (ROOT_DIR / "static" / "css" / "mobile.css").read_text(encoding="utf-8")
    spa_css = (ROOT_DIR / "static" / "css" / "spa.css").read_text(encoding="utf-8")
    app_init_js = (ROOT_DIR / "static" / "js" / "spa" / "app-init.js").read_text(encoding="utf-8")
    pidots_api_js = (ROOT_DIR / "static" / "js" / "spa" / "pidots-api.js").read_text(encoding="utf-8")

    # 16.1: Consolidação do Header Mobile (48px) e Quick Controls no Drawer
    assert 'id="mobileQuickControlsBar"' in app_html, "Barra #mobileQuickControlsBar ausente em pages/app.html"
    assert "min-height: 48px" in mobile_css or "height: 48px" in mobile_css, "Altura 48px do header mobile ausente em mobile.css"

    # 16.2: Rodapé Fixo de Telemetria Física em ASCII na Sidebar Esquerda
    assert 'id="sidebarHardwareFooter"' in app_html, "Rodapé #sidebarHardwareFooter ausente em pages/app.html"
    assert 'id="sidebarAsciiRamBar"' in app_html, "Indicador #sidebarAsciiRamBar ausente em pages/app.html"
    assert 'id="sidebarAsciiTemp"' in app_html, "Indicador #sidebarAsciiTemp ausente em pages/app.html"
    assert 'id="sidebarAsciiWal"' in app_html, "Indicador #sidebarAsciiWal ausente em pages/app.html"
    assert ".sidebar-hardware-footer" in spa_css, "Estilo .sidebar-hardware-footer ausente em spa.css"

    # 16.3: Aba CoAgents com Badge de Progresso (%) e Inspetor Rápido MemGPT
    assert 'id="canvasTabCoagentsLabel"' in app_html, "Label dinâmico #canvasTabCoagentsLabel ausente em pages/app.html"
    assert 'id="coagentMemgptBox"' in app_html, "Bloco 5 #coagentMemgptBox ausente em pages/app.html"
    assert "canvasTabCoagentsLabel" in pidots_api_js, "Atualização dinâmica de canvasTabCoagentsLabel ausente em pidots-api.js"

    # 16.4: Transição Não-Intrusiva do Live Canvas no Mobile com Badge
    assert 'id="mobileCanvasBadge"' in app_html, "Badge #mobileCanvasBadge ausente no botão #mobileNavCanvas"
    assert "notifyMobileCanvasUpdate" in app_init_js, "Função notifyMobileCanvasUpdate ausente em app-init.js"
    assert "silentMobile" in pidots_api_js, "Suporte a silentMobile em loadArtifact ausente em pidots-api.js"
    print("  -> [OK] Fase 16 validada com sucesso.")


def test_phase17_nginx_routes_and_sandbox():
    print("[TESTE 2/4] Validando Fase 17 — Nginx Alpine, Rotas Legadas e Sandbox Estrito...")
    nginx_conf = ROOT_DIR / "nginx" / "nginx.conf"
    compose_file = ROOT_DIR / "docker-compose.yml"
    assert nginx_conf.exists(), "Arquivo nginx/nginx.conf não encontrado"
    nginx_text = nginx_conf.read_text(encoding="utf-8")
    assert "location /static/" in nginx_text, "Bloco location /static/ ausente no nginx.conf"
    assert "location /data/locales/" in nginx_text, "Bloco location /data/locales/ ausente no nginx.conf"
    assert "proxy_buffering off;" in nginx_text, "Diretiva proxy_buffering off para SSE ausente no nginx.conf"

    compose_text = compose_file.read_text(encoding="utf-8")
    assert "pidots-nginx:" in compose_text, "Serviço pidots-nginx ausente no docker-compose.yml"
    assert "nginx:1.27-alpine" in compose_text, "Imagem nginx:1.27-alpine ausente no docker-compose.yml"

    # Testar flag enable_legacy_redirects (308 vs 410) e STRICT_SANDBOX (126)
    with TestClient(app) as client:
        orig_flag = settings.enable_legacy_redirects
        try:
            settings.enable_legacy_redirects = True
            res_308 = client.get("/console", follow_redirects=False)
            assert res_308.status_code == 308, f"Esperado 308 com enable_legacy_redirects=True, obtido {res_308.status_code}"

            settings.enable_legacy_redirects = False
            res_410 = client.get("/console", follow_redirects=False)
            assert res_410.status_code == 410, f"Esperado 410 com enable_legacy_redirects=False, obtido {res_410.status_code}"
        finally:
            settings.enable_legacy_redirects = orig_flag

    # Verificar implementação de STRICT_SANDBOX (exit_code 126) em pidots/tools/terminal.py
    terminal_py = (ROOT_DIR / "pidots" / "tools" / "terminal.py").read_text(encoding="utf-8")
    assert "strict_sandbox" in terminal_py and "126" in terminal_py, "Trava STRICT_SANDBOX (exit 126) ausente em terminal.py"
    print("  -> [OK] Fase 17 validada com sucesso.")


def test_phase18_cognitive_governance_and_triggers():
    print("[TESTE 3/4] Validando Fase 18 — Governança Cognitiva, HITL TTL e Gatilhos GPIO/MQTT...")
    assert MAX_HEAL_ATTEMPTS == 2, f"Esperado MAX_HEAL_ATTEMPTS == 2, obtido {MAX_HEAL_ATTEMPTS}"

    council_py = (ROOT_DIR / "pidots" / "core" / "council.py").read_text(encoding="utf-8")
    assert "early_consensus" in council_py or "Early Consensus Exit" in council_py, "Lógica de Early Consensus Exit ausente em council.py"

    memory_py = (ROOT_DIR / "pidots" / "storage" / "memory_manager.py").read_text(encoding="utf-8")
    assert "0.92" in memory_py, "Limiar de deduplicação semântica >= 0.92 ausente em memory_manager.py"

    with TestClient(app) as client:
        # Testar varredura determinística de expiração HITL TTL
        res_ttl = client.post("/api/hitl/expire-stale")
        assert res_ttl.status_code == 200, f"Falha em POST /api/hitl/expire-stale: {res_ttl.text}"
        ttl_data = res_ttl.json()
        assert ttl_data.get("status") in ("ok", "success"), f"Resposta inesperada em expire-stale: {ttl_data}"

        # Testar simulação de gatilho físico GPIO despertando @dot-supervisor
        res_gpio = client.post(
            "/api/edge/triggers/simulate",
            json={
                "gpio_pin": 17,
                "gpio_value": 1,
                "wake_supervisor": True,
            },
        )
        assert res_gpio.status_code == 200, f"Falha em POST /api/edge/triggers/simulate (GPIO): {res_gpio.text}"
        gpio_data = res_gpio.json()
        assert "supervisor_wakeup" in gpio_data, f"supervisor_wakeup ausente em gpio_data: {gpio_data}"
        assert gpio_data["supervisor_wakeup"]["supervisor_dot_id"] == "dot-supervisor"
        assert gpio_data["supervisor_wakeup"]["thread_id"] == "edge-supervisor-wakeup"

        # Testar simulação de gatilho MQTT despertando @dot-supervisor
        res_mqtt = client.post(
            "/api/edge/triggers/simulate",
            json={
                "mqtt_topic": "pidots/edge/ups/battery",
                "mqtt_payload": {"battery_pct": 18, "on_battery": True},
                "wake_supervisor": True,
            },
        )
        assert res_mqtt.status_code == 200, f"Falha em POST /api/edge/triggers/simulate (MQTT): {res_mqtt.text}"
        mqtt_data = res_mqtt.json()
        assert "supervisor_wakeup" in mqtt_data, f"supervisor_wakeup ausente em mqtt_data: {mqtt_data}"
        assert mqtt_data["supervisor_wakeup"]["supervisor_dot_id"] == "dot-supervisor"

    print("  -> [OK] Fase 18 validada com sucesso.")


def test_phase19_centaur_engineering_and_dot_packs():
    print("[TESTE 4/4] Validando Fase 19 — AI_MANIFESTO.md, CI Multi-Arch e Catálogo de Dot Packs...")
    manifesto_file = ROOT_DIR / "AI_MANIFESTO.md"
    assert manifesto_file.exists(), "AI_MANIFESTO.md não encontrado na raiz do projeto"
    manifesto_text = manifesto_file.read_text(encoding="utf-8")
    assert check_no_emojis(manifesto_text), "AI_MANIFESTO.md contém caracteres de emoji proibidos"
    assert "Engenharia Centauro" in manifesto_text, "Conteúdo esperado ausente em AI_MANIFESTO.md"

    ci_file = ROOT_DIR / ".github" / "workflows" / "ci.yml"
    assert ci_file.exists(), ".github/workflows/ci.yml não encontrado"
    ci_text = ci_file.read_text(encoding="utf-8")
    assert "linux/amd64,linux/arm64" in ci_text, "Build multi-arch linux/amd64,linux/arm64 ausente no ci.yml"
    assert "setup-qemu-action" in ci_text, "QEMU action ausente no ci.yml"

    with TestClient(app) as client:
        # Listar catálogo de Dot Packs oficiais
        res_cat = client.get("/api/dots/packs/catalog")
        assert res_cat.status_code == 200, f"Falha em GET /api/dots/packs/catalog: {res_cat.text}"
        cat_data = res_cat.json()
        assert cat_data["count"] >= 3, f"Esperado ao menos 3 pacotes no catálogo, obtido {cat_data['count']}"

        pack_ids = {p["pack_id"] for p in cat_data["packs"]}
        for expected_id in ("dot-secops", "dot-homelab", "dot-finops"):
            assert expected_id in pack_ids, f"Pacote oficial {expected_id} ausente no catálogo"

        for p in cat_data["packs"]:
            assert p["sha256_checksum"] != "", f"Pacote {p['pack_id']} sem sha256_checksum"

        # Testar instalação em 1 clique com validação SHA-256 dos 3 pacotes oficiais
        for pack_id in ("dot-secops", "dot-homelab", "dot-finops"):
            res_inst = client.post(f"/api/dots/packs/install/{pack_id}")
            assert res_inst.status_code == 200, f"Falha ao instalar {pack_id}: {res_inst.text}"
            inst_data = res_inst.json()
            assert inst_data["success"] is True, f"Status inválido na instalação de {pack_id}: {inst_data}"
            assert inst_data["dot_id"] == pack_id

    print("  -> [OK] Fase 19 validada com sucesso.")


if __name__ == "__main__":
    print("=" * 72)
    print("HOMOLOGAÇÃO INTEGRADA: ROADMAP EVOLUTION (FASES 16, 17, 18 E 19)")
    print("=" * 72)
    test_phase16_ui_ux_and_mobile()
    test_phase17_nginx_routes_and_sandbox()
    test_phase18_cognitive_governance_and_triggers()
    test_phase19_centaur_engineering_and_dot_packs()
    print("=" * 72)
    print("RESULTADO FINAL: 100% DOS TESTES DAS FASES 16 A 19 APROVADOS.")
    print("=" * 72)
