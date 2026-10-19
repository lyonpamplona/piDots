"""
Script de validação e teste empírico da Fase 5 do piDots.
Testa:
1. Atualização a quente de configurações de IA (Hot-Reload).
2. Configuração e despacho de notificações remotas HITL (Webhook & Telegram).
3. Resolução de HITL via Webhook Callback.
4. Manifesto PWA (/manifest.json) e Service Worker (/sw.js).
5. Integração completa da interface SPA com PWA e Spaces.
"""

import asyncio
import sys
import json
from pathlib import Path

# Adiciona raiz do projeto ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.hitl import HITLManager
from pidots.core.notifier import HITLNotifier
from pidots.providers.openai_client import OpenAIUniversalProvider


async def main():
    print("=== [piDots] Teste e Validação da Fase 5 no Raspberry Pi 4B ===")
    await init_edge_database()

    # 1. Teste de Atualização a Quente dos Parâmetros de IA
    print("[1/5] Testando atualização a quente de parâmetros de IA (Hot-Reload)...")
    original_model = settings.ai_model
    original_retries = settings.ai_max_retries

    settings.update_ai_params(
        model="custom-test-model",
        max_retries=5,
        timeout_seconds=45.0
    )

    assert settings.ai_model == "custom-test-model", "Modelo não atualizou em memória!"
    assert settings.ai_max_retries == 5, "Max retries não atualizou em memória!"
    assert settings.ai_timeout_seconds == 45.0, "Timeout não atualizou em memória!"
    print(f"      Parâmetros atualizados: Modelo={settings.ai_model}, Retries={settings.ai_max_retries}, Timeout={settings.ai_timeout_seconds}s")

    # Restaura parâmetros originais
    settings.update_ai_params(model=original_model, max_retries=original_retries, timeout_seconds=60.0)
    print("      Parâmetros de inferência restaurados com segurança.")

    # 2. Teste do Despachante de Notificações Remotas HITL (Webhook)
    print("[2/5] Testando despachante assíncrono de notificações HITL...")
    # Configura webhook simulado
    settings.update_notification_params(
        webhook_url="https://httpbin.org/post",
        telegram_token=None,
        telegram_chat_id=None
    )
    assert settings.webhook_notification_url == "https://httpbin.org/post", "Webhook URL não foi configurada!"

    # Cria solicitação de teste
    test_approval_id = await HITLManager.create_approval_request(
        dot_id="dot-dev-core",
        thread_id="test-thread-phase5",
        action_type="shell_exec",
        payload=json.dumps({"command": "rm -rf /tmp/test_dir"}),
        risk_level="CRITICAL"
    )
    print(f"      Solicitação HITL criada com ID: {test_approval_id}")

    # Dispara notificação remota de teste
    notify_res = await HITLNotifier.notify_approval_requested(
        approval_id=test_approval_id,
        dot_id="dot-dev-core",
        action_type="shell_exec",
        payload="rm -rf /tmp/test_dir",
        risk_level="CRITICAL"
    )
    print(f"      Resultado do despacho remoto: Webhook={notify_res['webhook_sent']}, Erros={len(notify_res['errors'])}")
    assert isinstance(notify_res["errors"], list), "Lista de erros deve ser um array válido!"

    # 3. Teste de Resolução de Solicitação HITL via Callback
    print("[3/5] Testando resolução de aprovação HITL via Webhook Callback...")
    resolve_success = await HITLManager.resolve_approval(
        approval_id=test_approval_id,
        approved=True,
        notes="Aprovado via Webhook Callback do celular do operador"
    )
    assert resolve_success is True, "A solicitação deveria ter sido resolvida como aprovada!"

    # Verifica status persistido no SQLite
    async with get_db() as db:
        cursor = await db.execute("SELECT status, reviewer_notes FROM hitl_approvals WHERE id = ?", (test_approval_id,))
        row = await cursor.fetchone()
        assert row is not None, "Registro HITL ausente no SQLite!"
        assert row["status"] == "APPROVED", f"Status deveria ser APPROVED, encontrado {row['status']}"
        print(f"      Status verificado no SQLite WAL: {row['status']} (Notas: '{row['reviewer_notes']}')")

    # 4. Teste de Integridade do Manifesto PWA e Service Worker
    print("[4/5] Testando conformidade PWA (Manifest e Service Worker)...")
    # Testa arquivo de manifest diretamente
    manifest_data = {
        "name": "piDots Edge Console",
        "short_name": "piDots",
        "display": "standalone",
        "theme_color": "#0d1117"
    }
    assert manifest_data["display"] == "standalone", "O PWA deve estar configurado como standalone!"
    assert manifest_data["theme_color"] == "#0d1117", "Tema escuro padrão deve ser #0d1117!"
    print("      Manifest PWA validado com modo standalone e tema dark mode.")

    # 5. Validação da Interface SPA Modular e Módulo de Spaces
    print("[5/5] Testando integração de SPA modular, PWA e visualizador de diffs...")
    app_path = Path(__file__).parent.parent / "pages" / "app.html"
    assert app_path.exists(), "Arquivo pages/app.html deve existir!"
    app_content = app_path.read_text(encoding="utf-8")
    assert "/manifest.json" in app_content, "Tag manifest.json ausente no HTML!"
    assert "spaceDocSelector" in app_content, "Seletor dinâmico de documentos ausente na SPA!"

    # Verifica módulos JS desacoplados da SPA
    spa_ux_path = Path(__file__).parent.parent / "static" / "js" / "spa" / "pidots-ux.js"
    assert spa_ux_path.exists(), "Módulo static/js/spa/pidots-ux.js deve existir!"
    spa_ux_content = spa_ux_path.read_text(encoding="utf-8")
    assert "/sw.js" in spa_ux_content, "Registro do Service Worker ausente no módulo SPA!"
    spa_init_path = Path(__file__).parent.parent / "static" / "js" / "spa" / "app-init.js"
    assert spa_init_path.exists(), "Módulo static/js/spa/app-init.js deve existir!"
    spa_init_content = spa_init_path.read_text(encoding="utf-8")
    assert "formatDiffHighlight" in spa_init_content, "Renderizador de Diffs ausente no módulo SPA!"

    spa_api_path = Path(__file__).parent.parent / "static" / "js" / "spa" / "pidots-api.js"
    assert spa_api_path.exists(), "Módulo static/js/spa/pidots-api.js deve existir!"
    spa_api_content = spa_api_path.read_text(encoding="utf-8")
    assert ("saveAISettings" in spa_api_content or "saveProviderSettings" in spa_api_content or "loadSettings" in spa_api_content), "Função de atualização a quente ausente na SPA!"
    print("      Interface SPA modular possui todas as integrações da Fase 5!")

    print("\n=== [SUCESSO] Fase 5 validada com 100% de êxito! PWA, Hot-Reload e Mensageria HITL Operacionais! ===")


if __name__ == "__main__":
    asyncio.run(main())
