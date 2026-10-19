"""
Suite de Testes Automatizados - Fase 2: Upgrade Estrutural do Layout de /app
Padrão CopilotKit/OpenDots + Pixel Paper UI (Raspberry Pi 4B ARM64)
Diretriz: Zero Emojis // Validação Estrita de DOM, CSS, JS e Mobile-First
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_app_html_opendots_structure():
    app_html = (ROOT / "pages" / "app.html").read_text(encoding="utf-8")

    # 1. Activity Rail + Context Panes
    required_ids = [
        'id="railBtnSpaces"',
        'id="railBtnDots"',
        'id="railBtnTasks"',
        'id="railBtnMemory"',
        'id="railBtnHitl"',
        'id="sidebarCtxSpaces"',
        'id="sidebarCtxDots"',
        'id="sidebarCtxTasks"',
        'id="sidebarCtxMemory"',
        # Elementos originais preservados para tour-engine.js e PiDotsAPI
        'id="dotsListContainer"',
        'id="channelsListContainer"',
        'id="threadsListContainer"',
        'id="spacesListContainer"',
        'id="hitlSidebarSection"',
        # Header Contextual OpenDots
        'id="threadParticipantPills"',
        'id="btnSaveThreadAsSpace"',
        # Computador de Borda do Dot + CoAgents + Takeover
        'id="computerConsoleBanner"',
        'id="computerTakeoverBtn"',
        'id="canvasTabCoagents"',
        'id="canvas-coagent-state"',
        'id="coagentActivePlanBox"',
        'id="coagentSharedNotesBox"',
        'id="coagentHandoffsBox"',
        'id="coagentToolRunsBox"',
        'id="computerWorkspaceFilesBox"',
        'id="computerTakeoverBar"',
        'id="computerExecInput"',
        # Modal Studio de Criação/Edição de Dots
        'id="pixelDotCreatorModal"',
        'id="dotFormId"',
        'id="dotFormName"',
        'id="dotFormRole"',
        'id="dotFormArchetype"',
        'id="dotFormPrompt"',
        'id="dotFormToolsCheckboxes"',
    ]
    for req_id in required_ids:
        assert req_id in app_html, f"Elemento obrigatorio ausente em pages/app.html: {req_id}"

    # Verifica balanceamento das tags <aside>
    open_asides = len(re.findall(r"<aside\b", app_html))
    close_asides = len(re.findall(r"</aside>", app_html))
    assert open_asides == close_asides, f"Desbalanceamento de <aside> em pages/app.html: {open_asides} abertas vs {close_asides} fechadas"
    print(f"[OK] pages/app.html validado ({len(required_ids)} IDs estruturais OpenDots e {open_asides} tags <aside> balanceadas).")


def test_spa_and_mobile_css_rules():
    spa_css = (ROOT / "static" / "css" / "spa.css").read_text(encoding="utf-8")
    mobile_css = (ROOT / "static" / "css" / "mobile.css").read_text(encoding="utf-8")

    for selector in [
        ".opendots-sidebar-layout",
        ".activity-rail",
        ".rail-btn",
        ".sidebar-context-stack",
        ".sidebar-ctx-pane",
        ".computer-console-banner",
        ".thread-sidebar-item",
        ".task-sidebar-card",
    ]:
        assert selector in spa_css, f"Seletor CSS ausente em static/css/spa.css: {selector}"

    for mobile_selector in [
        ".opendots-sidebar-layout",
        ".activity-rail",
        ".rail-btn",
        ".computer-console-banner",
    ]:
        assert mobile_selector in mobile_css, f"Regra responsiva ausente em static/css/mobile.css: {mobile_selector}"

    print("[OK] static/css/spa.css e static/css/mobile.css validados com regras Pixel Paper UI + OpenDots.")


def test_app_init_js_exports():
    app_init = (ROOT / "static" / "js" / "spa" / "app-init.js").read_text(encoding="utf-8")
    for fn_name in [
        "function switchSidebarContext",
        "function openDotCreatorModal",
        "function closeDotCreatorModal",
        "function toggleComputerTakeoverMode",
        "window.switchSidebarContext = switchSidebarContext;",
        "window.openDotCreatorModal = openDotCreatorModal;",
        "window.closeDotCreatorModal = closeDotCreatorModal;",
        "window.toggleComputerTakeoverMode = toggleComputerTakeoverMode;",
    ]:
        assert fn_name in app_init, f"Declaracao/exportacao ausente em static/js/spa/app-init.js: {fn_name}"

    print("[OK] static/js/spa/app-init.js validado com funcoes e exportacoes globais da Fase 2.")


def test_zero_emojis_compliance():
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "]+",
        flags=re.UNICODE,
    )
    target_files = [
        ROOT / "pages" / "app.html",
        ROOT / "static" / "css" / "spa.css",
        ROOT / "static" / "css" / "mobile.css",
        ROOT / "static" / "js" / "spa" / "app-init.js",
    ]
    for path in target_files:
        text = path.read_text(encoding="utf-8")
        matches = emoji_pattern.findall(text)
        assert not matches, f"Emoji proibido encontrado em {path.name}: {matches}"

    print("[OK] Conformidade Zero Emojis 100% verificada nos arquivos da Fase 2.")


if __name__ == "__main__":
    test_app_html_opendots_structure()
    test_spa_and_mobile_css_rules()
    test_app_init_js_exports()
    test_zero_emojis_compliance()
    print("=== TODOS OS TESTES DA FASE 2 PASSARAM COM SUCESSO ===")
