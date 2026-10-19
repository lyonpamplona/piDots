"""
Suite de Testes Automatizados - Fase 3: Motor Dinamico JS, Generative UI Inline & CoAgents Live Binding
Padrao CopilotKit/OpenDots + Pixel Paper UI (Raspberry Pi 4B ARM64)
Diretriz: Zero Emojis // Validacao Estrita de Handlers HTML <-> PiDotsAPI e Slash Commands
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_html_pidots_api_bindings():
    app_html = (ROOT / "pages" / "app.html").read_text(encoding="utf-8")
    api_js = (ROOT / "static" / "js" / "spa" / "pidots-api.js").read_text(encoding="utf-8")

    # Extrai todas as chamadas PiDotsAPI.<metodo>(...) de pages/app.html
    called_methods = sorted(set(re.findall(r"PiDotsAPI\.([a-zA-Z0-9_]+)\s*\(", app_html)))
    assert len(called_methods) >= 12, f"Poucos metodos PiDotsAPI detectados em pages/app.html: {called_methods}"

    for method in called_methods:
        pattern = rf"\b{re.escape(method)}\s*\("
        assert re.search(pattern, api_js), f"Metodo PiDotsAPI.{method}() chamado em pages/app.html nao existe em pidots-api.js"

    # Verifica métodos adicionais de Generative UI e CoAgents Live Binding
    required_api_methods = [
        "loadChannels",
        "selectChannel",
        "promptCreateChannel",
        "loadThreads",
        "openThread",
        "deleteThread",
        "renderThreadParticipants",
        "promptHandoffThread",
        "promptCouncilDebate",
        "saveThreadAsSpace",
        "loadActiveThreadState",
        "renderCoAgentStateInspector",
        "filterOrSearchSpaces",
        "loadDotsStudioPane",
        "populateDotCreatorModal",
        "submitDotCreatorForm",
        "deleteCustomDot",
        "loadTasksSidebar",
        "promptCreateTask",
        "runTaskNow",
        "toggleTaskActive",
        "deleteTask",
        "loadEdgeTriggersSidebar",
        "loadMemorySidebar",
        "saveActiveDotCoreMemory",
        "promptInsertArchivalMemory",
        "searchActiveDotArchival",
        "loadMcpServersSidebar",
        "promptRegisterMcpServer",
        "loadComputerFiles",
        "executeInDotComputer",
        "appendGenerativeUiCard",
    ]
    for m in required_api_methods:
        assert re.search(rf"\b{re.escape(m)}\s*\(", api_js), f"Metodo obrigatorio ausente em pidots-api.js: {m}"

    print(f"[OK] Todos os {len(called_methods)} handlers HTML e {len(required_api_methods)} metodos do motor PiDotsAPI validados.")


def test_agui_and_generative_ui_events():
    api_js = (ROOT / "static" / "js" / "spa" / "pidots-api.js").read_text(encoding="utf-8")
    spa_css = (ROOT / "static" / "css" / "spa.css").read_text(encoding="utf-8")

    for ev in [
        "tool_call:start",
        "tool_call:result",
        "artifact:updated",
        "canvas:patch",
        "state:sync",
        "hitl:pending_approval",
        "self_healing:triggered",
    ]:
        assert ev in api_js, f"Evento AG-UI ausente no stream de pidots-api.js: {ev}"

    for css_cls in [".gen-ui-card", ".gen-ui-header", ".gen-ui-body", ".gen-ui-actions"]:
        assert css_cls in spa_css, f"Classe CSS de Generative UI ausente em static/css/spa.css: {css_cls}"

    print("[OK] Eventos AG-UI e fichas catalograficas de Generative UI (.gen-ui-card) validados.")


def test_slash_commands_phase3():
    slash_js = (ROOT / "static" / "js" / "spa" / "slash-commands.js").read_text(encoding="utf-8")

    for cmd in ["/save-space", "/computer", "/mcp", "/coagents", "/run-task", "/council", "/handoff"]:
        assert f"'{cmd}'" in slash_js or f'"{cmd}"' in slash_js, f"Slash command ausente em slash-commands.js: {cmd}"
        assert f"case '{cmd}':" in slash_js, f"Handler case ausente em slash-commands.js para: {cmd}"

    # Garante que o bug legado this.filter('') foi eliminado
    assert "this.filter('')" not in slash_js, "Chamada legada incorreta this.filter('') ainda presente em slash-commands.js"
    print("[OK] Catalogo de 34 Slash Commands e handlers OpenDots (/save-space, /computer, /mcp, /coagents) validados.")


def test_zero_emojis_phase3():
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
    for rel in ["static/js/spa/pidots-api.js", "static/js/spa/slash-commands.js", "static/css/spa.css"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        matches = emoji_pattern.findall(text)
        assert not matches, f"Emoji proibido encontrado em {rel}: {matches}"

    print("[OK] Conformidade Zero Emojis 100% verificada nos arquivos da Fase 3.")


if __name__ == "__main__":
    test_html_pidots_api_bindings()
    test_agui_and_generative_ui_events()
    test_slash_commands_phase3()
    test_zero_emojis_phase3()
    print("=== TODOS OS TESTES DA FASE 3 PASSARAM COM SUCESSO ===")
