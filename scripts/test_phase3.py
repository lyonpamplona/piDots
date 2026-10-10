"""
Script de validação e teste empírico da Fase 3 do piDots.
Testa o Terminal Sandbox, WebReader semântico, FileManager e a governança HITL.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.tools.terminal import TerminalSandbox
from pidots.tools.web_reader import WebReader
from pidots.tools.file_ops import FileManager
from pidots.tools.registry import registry
from pidots.core.hitl import HITLManager


async def main():
    print("=== [piDots] Teste e Validação da Fase 3 no Raspberry Pi 4B ===")
    await init_edge_database()
    dot_id = "dot-dev-core"

    # 1. Teste do Terminal Sandbox
    print("[1/5] Testando execução isolada no Terminal Sandbox...")
    term_res = await TerminalSandbox.execute(
        dot_id=dot_id,
        command="python3 -c \"import sys; print(f'Python {sys.version.split()[0]} no ARM64')\""
    )
    print(f"      Método: {term_res['method']}")
    print(f"      Código: {term_res['exit_code']}")
    print(f"      Saída:  {term_res['stdout'].strip()}")
    print(f"      Tempo:  {term_res['duration_ms']}ms")
    assert term_res["exit_code"] == 0, "Falha na execução do sandbox de terminal!"

    # 2. Teste de Auditoria em SQLite tool_runs
    print("[2/5] Verificando registro de auditoria em tool_runs...")
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT tool_name, exit_code, stdout_text, duration_ms FROM tool_runs WHERE dot_id = ? ORDER BY created_at DESC LIMIT 1",
            (dot_id,)
        )
        run_row = await cursor.fetchone()
    print(f"      Auditoria registrada: {run_row['tool_name']} (Exit: {run_row['exit_code']}, Duração: {run_row['duration_ms']}ms)")
    assert run_row is not None and run_row["exit_code"] == 0, "Auditoria de execução não registrada no SQLite!"

    # 3. Teste do FileManager (Escrita Atômica, Leitura e Execução)
    print("[3/5] Testando FileManager (Escrita atômica e leitura segura)...")
    code_content = "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\nprint(f'Fib(8) = {fib(8)}')\n"
    w_res = await FileManager.write_file(dot_id=dot_id, filename="fibonacci.py", content=code_content)
    print(f"      Gravado: {w_res['filename']} ({w_res['bytes_written']} bytes)")

    r_res = await FileManager.read_file(dot_id=dot_id, filename="fibonacci.py")
    assert "Fib(8)" in r_res["content"], "Conteúdo lido difere do gravado!"

    # Executa o script gravado no workspace do Dot
    run_script = await TerminalSandbox.execute(dot_id=dot_id, command="python3 fibonacci.py")
    print(f"      Execução do script gerado: {run_script['stdout'].strip()}")
    assert "Fib(8) = 21" in run_script["stdout"], "Resultado da execução do script inválido!"

    # Listagem de arquivos do workspace
    list_res = await FileManager.list_files(dot_id=dot_id)
    print(f"      Arquivos no workspace '{dot_id}': {list_res['total_files']} arquivo(s)")

    # 4. Teste de WebReader (Extração Semântica Camada 1 com Trafilatura)
    print("[4/5] Testando extrator web semântico (HTTPX + Trafilatura)...")
    # Testa em uma página padrão leve
    web_res = await WebReader.read_url("https://httpbin.org/html", timeout_seconds=15.0)
    if "error" not in web_res:
        print(f"      Página: {web_res['title']} (Extraídos {web_res['character_count']} caracteres)")
        print(f"      Amostra: {web_res['content_markdown'][:80].replace(chr(10), ' ')}...")
        assert web_res["status"] == "success", "Extração web falhou!"
    else:
        print(f"      Aviso de rede: {web_res.get('error')} (Esperado se offline)")

    # 5. Teste de Governança HITL com execute_shell_command
    print("[5/5] Testando bloqueio HITL de comandos perigosos...")
    cmd_dangerous = "rm -rf / --no-preserve-root"
    req_hitl, risk = HITLManager.requires_approval("execute_shell_command", json.dumps({"command": cmd_dangerous}))
    print(f"      Comando: '{cmd_dangerous}' -> Requer aprovação: {req_hitl} (Risco: {risk})")
    assert req_hitl is True and risk == "CRITICAL", "Falha de interceptação HITL em comando crítico!"

    cmd_safe = "ls -la"
    req_safe, risk_safe = HITLManager.requires_approval("execute_shell_command", json.dumps({"command": cmd_safe}))
    print(f"      Comando seguro: '{cmd_safe}' -> Requer aprovação: {req_safe} (Risco: {risk_safe})")
    assert req_safe is False, "Comando seguro não deveria ser bloqueado!"

    print("\n=== [SUCESSO] Fase 3 validada com 100% de êxito! Ferramental Operacional Ativo! ===")


if __name__ == "__main__":
    asyncio.run(main())
