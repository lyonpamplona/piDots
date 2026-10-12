"""
Módulo de Self-Healing Harness (Auto-Correção e Validação Autônoma) para piDots.
Inspirado em padrões SWE-agent, OpenHands e Devin, adaptado para Raspberry Pi 4B (ARM64).
Detecta falhas de execução, tracebacks e testes quebrados, fornecendo diagnósticos
estruturados para que o Dot corrija o código de forma iterativa antes da resposta final.
"""

import re
import logging
from typing import Any

logger = logging.getLogger("pidots.self_healing")

# Padrões comuns de erros em Python e Shell
PYTHON_TRACEBACK_PATTERN = re.compile(
    r'File\s+["\'](?P<file>[^"\']+)["\'],\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<scope>\w+))?',
    re.MULTILINE
)
ERROR_TYPE_PATTERN = re.compile(
    r'(?P<err_type>[A-Za-z_]+Error|[A-Za-z_]+Exception|AssertionError):\s*(?P<err_msg>.*)',
    re.MULTILINE
)


class SelfHealingHarness:
    """Harness de inspeção e orientação de auto-correção para o loop do DotAgent."""

    @classmethod
    def inspect_execution_result(
        cls,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Inspeciona o resultado da execução de ferramentas (como execute_shell_command).
        Se detectar código de saída diferente de zero ou traceback, gera diagnóstico de cura.
        """
        # Apenas inspeciona ferramentas de execução de comandos ou código
        if tool_name not in ("execute_shell_command", "execute_and_verify"):
            return None

        exit_code = tool_result.get("exit_code")
        stdout = tool_result.get("stdout", "")
        stderr = tool_result.get("stderr", "")

        # Se exit_code for 0 e não houver traceback explícito, execução foi bem-sucedida
        if exit_code == 0 and "Traceback (most recent call last):" not in stderr and "Traceback (most recent call last):" not in stdout:
            return None

        combined_output = f"{stderr}\n{stdout}".strip()
        analysis = cls.analyze_failure(combined_output, exit_code)

        logger.info(
            "Self-Healing ativado para ferramenta '%s'. Tipo de falha: %s (Arquivo: %s, Linha: %s)",
            tool_name,
            analysis["error_type"],
            analysis.get("target_file", "desconhecido"),
            analysis.get("target_line", "desconhecido")
        )

        return analysis

    @classmethod
    def analyze_failure(cls, output_text: str, exit_code: int | None = None) -> dict[str, Any]:
        """Analisa a saída textual de erro e extrai arquivo, linha, tipo de exceção e orientação."""
        target_file = None
        target_line = None
        target_scope = None

        # 1. Busca por rastros de pilha (Stack Trace)
        trace_matches = list(PYTHON_TRACEBACK_PATTERN.finditer(output_text))
        if trace_matches:
            # Pega o último quadro do traceback (local mais próximo da raiz do erro)
            last_match = trace_matches[-1]
            target_file = last_match.group("file")
            target_line = int(last_match.group("line"))
            target_scope = last_match.group("scope")

        # 2. Busca por tipo e mensagem de erro
        err_matches = list(ERROR_TYPE_PATTERN.finditer(output_text))
        error_type = "CommandExecutionError"
        error_message = ""
        if err_matches:
            last_err = err_matches[-1]
            error_type = last_err.group("err_type")
            error_message = last_err.group("err_msg").strip()
        elif exit_code is not None and exit_code != 0:
            error_message = f"Processo encerrou com código de retorno {exit_code}."
            if "not found" in output_text.lower():
                error_type = "CommandNotFoundError"
            elif "permission denied" in output_text.lower():
                error_type = "PermissionDeniedError"
            elif "syntax error" in output_text.lower():
                error_type = "SyntaxError"

        # 3. Formulação da sugestão cirúrgica de auto-correção
        suggestion_parts = []
        if target_file and target_line:
            suggestion_parts.append(
                f"Falha detectada no arquivo '{target_file}', linha {target_line}"
                + (f" (escopo: {target_scope}):" if target_scope else ":")
            )
        else:
            suggestion_parts.append("Falha detectada na execução do comando:")

        suggestion_parts.append(f"Exceção [{error_type}]: {error_message or 'Falha na execução do processo.'}")
        suggestion_parts.append(
            "DIRETRIZ DE AUTO-CORREÇÃO: Não conclua a tarefa com este erro. "
            "Examine o código-fonte via 'workspace_read_file', aplique o ajuste cirúrgico via 'workspace_write_file' "
            "e reexecute o comando/teste para comprovar a resolução antes de emitir a resposta final."
        )

        return {
            "needs_healing": True,
            "exit_code": exit_code,
            "error_type": error_type,
            "error_message": error_message,
            "target_file": target_file,
            "target_line": target_line,
            "target_scope": target_scope,
            "diagnosis": "\n".join(suggestion_parts)
        }
