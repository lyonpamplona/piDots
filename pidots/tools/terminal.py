"""
Executor de Comandos de Terminal Sandbox para o piDots.
Suporta isolamento via Bubblewrap (bwrap) com fallback resiliente para Subprocess Sandbox com ambiente sanitizado.
"""

import os
import re
import json
import uuid
import signal
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from ..config import settings
from ..storage.db import get_db

logger = logging.getLogger("pidots.tools.terminal")

MAX_OUTPUT_BYTES = 10000  # Limite de 10KB de saída para preservar a RAM do Pi 4B


class TerminalSandbox:
    """Gerencia a execução isolada de comandos de terminal por Dot."""

    @staticmethod
    def _terminate_process_group(proc: asyncio.subprocess.Process | None) -> None:
        """Encerra toda a árvore de processos da sessão em caso de timeout."""
        if not proc or proc.returncode is not None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception as kill_err:
                logger.debug("Falha ao interromper processo após timeout: %s", kill_err)

    @classmethod
    async def _safe_terminate(cls, proc: asyncio.subprocess.Process | None) -> None:
        """Encerra a arvore de processos e colhe o processo pai evitando zumbis defunct."""
        if not proc or proc.returncode is not None:
            return
        cls._terminate_process_group(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except Exception:
            pass

    @classmethod
    async def execute(
        cls,
        dot_id: str,
        command: str,
        timeout_seconds: float = 30.0
    ) -> dict[str, Any]:
        """
        Executa um comando no diretório de trabalho do Dot.
        Registra a auditoria em tool_runs no SQLite WAL.
        """
        safe_dot_id = re.sub(r"[^\w\-_.]", "_", (dot_id or "default").strip()).strip(".") or "default"
        workspace_dir = os.path.realpath(os.path.join(settings.workspaces_root, safe_dot_id))
        os.makedirs(workspace_dir, exist_ok=True)

        start_time = datetime.now(timezone.utc)
        execution_method = "subprocess"

        # Ambiente sanitizado (remove variáveis confidenciais como chaves de API)
        sanitized_env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": workspace_dir,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TERM": "xterm-256color",
            "PYTHONUNBUFFERED": "1",
        }

        # Tentativa inicial via Bubblewrap se bwrap estiver disponível no sistema
        bwrap_path = "/usr/bin/bwrap"
        if os.path.exists(bwrap_path):
            bwrap_cmd = [
                bwrap_path,
                "--die-with-parent",
                "--ro-bind", "/usr", "/usr",
                "--ro-bind", "/lib", "/lib",
                "--ro-bind", "/bin", "/bin",
                "--dev", "/dev",
                "--proc", "/proc",
                "--bind", workspace_dir, "/workspace",
                "--chdir", "/workspace",
                "--tmpfs", "/tmp",
                "--unshare-pid",
                "bash", "-c", command
            ]
            if os.path.exists("/lib64"):
                bwrap_cmd[8:8] = ["--ro-bind", "/lib64", "/lib64"]
            if os.path.exists("/etc/alternatives"):
                bwrap_cmd[8:8] = ["--ro-bind", "/etc/alternatives", "/etc/alternatives"]

            bwrap_proc = None
            try:
                bwrap_proc = await asyncio.create_subprocess_exec(
                    *bwrap_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workspace_dir,
                    env=sanitized_env,
                    start_new_session=True
                )
                stdout_b, stderr_b = await asyncio.wait_for(bwrap_proc.communicate(), timeout=timeout_seconds)
                # Se rodou com código 0 ou erro do comando interno, registra sucesso do bwrap
                if bwrap_is_working(bwrap_proc.returncode, stderr_b):
                    execution_method = "bubblewrap"
                    return await cls._record_run(
                        dot_id=safe_dot_id,
                        command=command,
                        exit_code=bwrap_proc.returncode,
                        stdout_b=stdout_b,
                        stderr_b=stderr_b,
                        method=execution_method,
                        start_time=start_time
                    )
            except asyncio.TimeoutError:
                await cls._safe_terminate(bwrap_proc)
                return await cls._record_run(
                    dot_id=safe_dot_id,
                    command=command,
                    exit_code=-1,
                    stdout_b=b"",
                    stderr_b=f"Erro: Timeout de execução excedido ({timeout_seconds}s).".encode("utf-8"),
                    method="bubblewrap",
                    start_time=start_time
                )
            except Exception as bwrap_err:
                await cls._safe_terminate(bwrap_proc)
                logger.debug("bwrap indisponível ou sem permissão de namespace (%s). Usando Subprocess Sandbox.", str(bwrap_err))

        # Fallback resiliente: Subprocess Sandbox com diretório restrito e timeout
        proc = None
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_dir,
                env=sanitized_env,
                start_new_session=True
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
            exit_code = proc.returncode
        except asyncio.TimeoutError:
            await cls._safe_terminate(proc)
            exit_code = -1
            stdout_b = b""
            stderr_b = f"Erro: Timeout de execução excedido ({timeout_seconds}s).".encode("utf-8")
        except Exception as e:
            await cls._safe_terminate(proc)
            exit_code = -1
            stdout_b = b""
            stderr_b = f"Falha na execução do processo: {str(e)}".encode("utf-8")

        return await cls._record_run(
            dot_id=safe_dot_id,
            command=command,
            exit_code=exit_code,
            stdout_b=stdout_b,
            stderr_b=stderr_b,
            method=execution_method,
            start_time=start_time
        )

    @classmethod
    async def _record_run(
        cls,
        dot_id: str,
        command: str,
        exit_code: int,
        stdout_b: bytes,
        stderr_b: bytes,
        method: str,
        start_time: datetime
    ) -> dict[str, Any]:
        """Trunca a saída para teto seguro e persiste auditoria no SQLite."""
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        stdout_str = stdout_b[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
        stderr_str = stderr_b[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
        arguments_json = json.dumps({"command": command}, ensure_ascii=False)

        run_id = str(uuid.uuid4())
        try:
            async with get_db() as db:
                await db.execute(
                    """
                    INSERT OR IGNORE INTO dots (
                        id, name, role, system_prompt, model, workspace_path
                    ) VALUES (?, ?, 'AI Coworker', 'Assistente técnico.', ?, ?)
                    """,
                    (dot_id, dot_id, settings.ai_model, f"workspaces/{dot_id}")
                )
                await db.execute(
                    """
                    INSERT INTO tool_runs (id, dot_id, tool_name, arguments_json, exit_code, stdout_text, stderr_text, duration_ms)
                    VALUES (?, ?, 'execute_shell_command', ?, ?, ?, ?, ?)
                    """,
                    (run_id, dot_id, arguments_json, exit_code, stdout_str, stderr_str, duration_ms)
                )
                await db.commit()
        except Exception as err:
            logger.warning("Falha ao registrar auditoria em tool_runs: %s", str(err))

        return {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "duration_ms": duration_ms,
            "method": method
        }


def bwrap_is_working(returncode: int, stderr_b: bytes) -> bool:
    """Verifica se o retorno não foi uma recusa de permissão do próprio binário bwrap."""
    err_str = stderr_b.decode("utf-8", errors="ignore")
    if err_str.startswith("bwrap:") and returncode != 0:
        if "No permissions" in err_str or "Operation not permitted" in err_str or "setting up uid map" in err_str:
            return False
    if "No permissions to create a new namespace" in err_str:
        return False
    if "pivot_root: Operation not permitted" in err_str:
        return False
    return True
