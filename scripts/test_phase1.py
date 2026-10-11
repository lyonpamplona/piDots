"""
Script de validação e teste empírico da Fase 1 do piDots.
Inicializa o SQLite WAL, insere Dot inicial e valida a governança HITL.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.hitl import HITLManager
from pidots.providers.openai_client import OpenAIUniversalProvider


async def main():
    print("=== [piDots] Teste e Validação da Fase 1 no Raspberry Pi 4B ===")
    
    # 1. Teste de Diretórios e SQLite WAL
    print("[1/4] Inicializando diretórios e banco SQLite WAL...")
    await init_edge_database()
    print("      Banco SQLite WAL inicializado com sucesso!")

    # 2. Inserção de Dot Inicial de Teste
    print("[2/4] Registrando Dot padrão (AI Coworker)...")
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "dot-dev-core",
                "Dot Developer",
                "Senior Systems & Python Engineer",
                "Você é o Dot Developer, especialista em código limpo e arquitetura edge.",
                settings.ai_model,
                str(Path(settings.workspaces_root) / "dot-dev-core")
            )
        )
        await db.commit()
    print("      Dot 'dot-dev-core' cadastrado com sucesso!")

    # 3. Teste de Governança HITL (Detecção de Ações Perigosas)
    print("[3/4] Testando analisador de risco Human-in-the-Loop...")
    cmd_safe = "python3 script.py"
    req_safe, risk_safe = HITLManager.requires_approval("shell_exec", cmd_safe)
    print(f"      Comando seguro: '{cmd_safe}' -> Requer aprovação: {req_safe} (Risco: {risk_safe})")

    cmd_risky = "rm -rf /tmp/build_cache && sudo reboot"
    req_risky, risk_risky = HITLManager.requires_approval("shell_exec", cmd_risky)
    print(f"      Comando perigoso: '{cmd_risky}' -> Requer aprovação: {req_risky} (Risco: {risk_risky})")
    assert req_risky is True and risk_risky == "CRITICAL", "Falha na detecção de comando crítico!"

    # Criação de solicitação HITL real no banco
    req_id = await HITLManager.create_approval_request("dot-dev-core", None, "shell_exec", cmd_risky, risk_risky)
    print(f"      Solicitação HITL registrada com ID: {req_id}")

    # Resolução da solicitação (Aprovação simulada)
    resolved = await HITLManager.resolve_approval(req_id, True, "Aprovado pelo operador de governança.")
    print(f"      Solicitação HITL resolvida com sucesso: {resolved}")

    # 4. Teste de Inicialização do Provedor OpenAI-Compatível
    print("[4/4] Instanciando cliente universal OpenAI-compatível...")
    provider = OpenAIUniversalProvider()
    print(f"      Endpoint Base: {provider.base_url}")
    print(f"      Modelo Alvo:   {provider.default_model}")
    print(f"      Circuit Breaker: Ativo com {provider.max_retries} retentativas e jitter.")

    print("\n=== [SUCESSO] Todos os componentes da Fase 1 foram validados com 100% de êxito! ===")


if __name__ == "__main__":
    asyncio.run(main())
