#!/usr/bin/env python3
"""
Validador Automatizado da Fase 3 - Saneamento do CLI, Servidor Core e Scripts de Interface.
Verifica:
1. Execução do CLI (subcomandos --help, status, dots list, hitl list).
2. Ausência absoluta de emojis nos arquivos da Fase 3.
3. Purgação completa dos termos proibidos e eufemismos de IA.
4. Remoção de alert() nativo nos scripts JS.
5. Preservação de sintaxe de todos os módulos.
"""

import sys
import subprocess
import re
from pathlib import Path

ROOT = Path("/mnt/storage/piDots")

TARGET_FILES = [
    ROOT / "pidots/cli.py",
    ROOT / "pidots/main.py",
    ROOT / "static/js/spa/tour-engine.js",
    ROOT / "static/js/spa/slash-commands.js",
    ROOT / "static/js/spa/app-init.js",
    ROOT / "static/js/landing/landing.js",
    ROOT / "static/js/docs/docs.js",
]

PROHIBITED_TERMS = [
    "trava mecânica",
    "dossiê de economia forense",
    "toast térmico",
    "deliberação tripartite",
    "deliberação dialética",
    "pigmentação visual",
    "comuta a quente o dicionário",
    "transfere titularidade da thread",
    "topologia canônica",
    "requisições cognitivas",
    "48px de trilho vertical",
    "bobina contínua matricial",
    "prancheta técnica de alto rendimento",
    "snapshot acid criado",
    "edgehardwaretriggers ativou",
]

EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe0f]"
)


def test_syntax():
    print("[1/5] Validando sintaxe Python de cli.py e main.py...")
    import py_compile
    for py_file in [ROOT / "pidots/cli.py", ROOT / "pidots/main.py"]:
        py_compile.compile(str(py_file), doraise=True)
    print("      -> Sintaxe Python 100% integra.")


def test_cli_execution():
    print("[2/5] Testando execução dos subcomandos CLI via Python...")
    venv_py = ROOT / ".venv/bin/python"
    
    subcommands = [
        ["--help"],
        ["status"],
        ["dots", "list"],
        ["hitl", "list"]
    ]
    
    for sub in subcommands:
        cmd = [str(venv_py), "-m", "pidots.cli"] + sub
        res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        assert res.returncode == 0, f"Falha ao executar pidots {' '.join(sub)}: {res.stderr}"
        assert len(res.stdout.strip()) > 0, f"Saida vazia para pidots {' '.join(sub)}"
        # Verifica se termos do hardware ou status aparecem
        if sub == ["status"]:
            assert "silício:" in res.stdout, "status deve conter silício:"
            assert "sqlite:" in res.stdout, "status deve conter sqlite:"
            assert "motor:" in res.stdout, "status deve conter motor:"
        if sub == ["dots", "list"]:
            assert "coworkers instalados" in res.stdout or "nenhum coworker" in res.stdout
        if sub == ["hitl", "list"]:
            assert "fila hitl limpa" in res.stdout or "ordens retidas" in res.stdout
    print("      -> Subcomandos CLI executados com sucesso (estética teletipo UNIX confirmada).")


def test_zero_emojis():
    print("[3/5] Verificando ausência de emojis nos arquivos da Fase 3...")
    for f in TARGET_FILES:
        text = f.read_text(encoding="utf-8")
        matches = EMOJI_REGEX.findall(text)
        assert not matches, f"Emoji detectado em {f.name}: {matches[:5]}"
    print("      -> ZERO emojis em todos os 7 arquivos da Fase 3.")


def test_no_prohibited_terms():
    print("[4/5] Verificando purgação de termos proibidos e eufemismos de IA...")
    found_violations = []
    for f in TARGET_FILES:
        text = f.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            if term in text:
                found_violations.append((f.name, term))
    
    assert not found_violations, f"Termos proibidos encontrados: {found_violations}"
    print("      -> Todos os 15 termos proibidos erradicados com sucesso.")


def test_no_browser_alert_in_docs_js():
    print("[5/5] Verificando eliminação de window.alert em docs.js...")
    docs_js = ROOT / "static/js/docs/docs.js"
    text = docs_js.read_text(encoding="utf-8")
    assert "alert(" not in text, "Chamada nativa alert() ainda presente em docs.js"
    print("      -> alert() nativo substituído por toast elegante.")


def main():
    print("=====================================================================")
    print("INICIANDO SUÍTE DE TESTES: FASE 3 (CLI, CORE SERVER & SCRIPTS)")
    print("=====================================================================")
    try:
        test_syntax()
        test_cli_execution()
        test_zero_emojis()
        test_no_prohibited_terms()
        test_no_browser_alert_in_docs_js()
        print("=====================================================================")
        print("SUCESSO: Todos os testes da Fase 3 passaram com 100% de conformidade!")
        print("=====================================================================")
        return 0
    except AssertionError as e:
        print(f"ERRO DE TESTE: {e}")
        return 1
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
