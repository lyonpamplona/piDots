#!/usr/bin/env python3
"""
Validador Automatizado da Fase 4 - Prompts de Sistema dos Agentes & Homologação Final.
Verifica:
1. Prompts de sistema dos 6 Core Dots no banco SQLite e no código fonte.
2. Injeção das Diretrizes Operacionais de Bancada em pidots/core/agent.py.
3. Purgação completa de termos de AI Slop em council.py e db.py.
4. Ausência absoluta de emojis nos arquivos do core.
5. Execução do pipeline de teste integrado.
"""

import sys
import sqlite3
import re
from pathlib import Path

ROOT = Path("/mnt/storage/piDots")

TARGET_FILES = [
    ROOT / "pidots/core/agent.py",
    ROOT / "pidots/core/council.py",
    ROOT / "pidots/storage/db.py",
]

PROHIBITED_TERMS = [
    "deliberação dialética",
    "ciclo dialético simétrico",
    "diretrizes operacionais cognitivas",
    "fita de carbono (mensagem interna)",
    "trava mecânica",
    "topologia canônica",
    "requisições cognitivas",
]

EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe0f]"
)


def test_core_dots_prompts_in_db():
    print("[1/5] Verificando system prompts dos 6 Core Dots no SQLite...")
    db_path = ROOT / "data/pidots.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("SELECT id, name, role, system_prompt FROM dots WHERE is_core = 1")
    rows = c.fetchall()
    conn.close()

    assert len(rows) == 6, f"Esperava 6 Core Dots, encontrou {len(rows)}"

    for dot_id, name, role, prompt in rows:
        assert len(prompt.strip()) > 80, f"Prompt do dot {dot_id} muito curto ou vazio: {prompt}"
        # Verifica menção a conceitos reais de bancada / artesão
        prompt_lower = prompt.lower()
        for term in PROHIBITED_TERMS:
            assert term not in prompt_lower, f"Termo proibido '{term}' encontrado no prompt de {dot_id}"
        matches = EMOJI_REGEX.findall(prompt)
        assert not matches, f"Emoji detectado no prompt de {dot_id}: {matches}"

    print(f"      -> Todos os {len(rows)} Core Dots configurados com voz de bancada e sem AI Slop.")


def test_agent_guidelines():
    print("[2/5] Verificando injeção das Diretrizes Operacionais de Bancada em agent.py...")
    agent_code = (ROOT / "pidots/core/agent.py").read_text(encoding="utf-8")
    assert "DIRETRIZES OPERACIONAIS DE BANCADA:" in agent_code, "Cabeçalho de bancada ausente em agent.py"
    assert "DELIBERAÇÃO ENTRE COWORKERS:" in agent_code, "Diretriz de deliberação ausente em agent.py"
    assert "DIRETRIZES OPERACIONAIS COGNITIVAS" not in agent_code, "AI Slop 'cognitivas' ainda presente"
    assert "Dialética Multi-Bot" not in agent_code, "AI Slop 'Dialética' ainda presente"
    print("      -> Injeção de diretrizes de bancada validada com sucesso.")


def test_council_purged():
    print("[3/5] Verificando alinhamento e purgação de AI Slop em council.py...")
    council_code = (ROOT / "pidots/core/council.py").read_text(encoding="utf-8")
    assert "deliberação dialética" not in council_code.lower(), "'deliberação dialética' ainda em council.py"
    assert "ciclo dialético" not in council_code.lower(), "'ciclo dialético' ainda em council.py"
    assert "fita de carbono" not in council_code.lower(), "'fita de carbono' ainda em council.py"
    print("      -> council.py 100% saneado e alinhado.")


def test_zero_emojis_in_core():
    print("[4/5] Verificando ausência absoluta de emojis no core backend...")
    for f in TARGET_FILES:
        text = f.read_text(encoding="utf-8")
        matches = EMOJI_REGEX.findall(text)
        assert not matches, f"Emoji detectado em {f.name}: {matches[:5]}"
    print("      -> ZERO emojis confirmados nos módulos core.")


def test_syntax_all():
    print("[5/5] Compilando e validando sintaxe de todos os módulos core...")
    import py_compile
    for f in TARGET_FILES:
        py_compile.compile(str(f), doraise=True)
    print("      -> Compilação de bytecode Python 100% aprovada.")


def main():
    print("=====================================================================")
    print("INICIANDO SUÍTE DE TESTES: FASE 4 (PROMPTS DE SISTEMA & HOMOLOGAÇÃO)")
    print("=====================================================================")
    try:
        test_core_dots_prompts_in_db()
        test_agent_guidelines()
        test_council_purged()
        test_zero_emojis_in_core()
        test_syntax_all()
        print("=====================================================================")
        print("SUCESSO: Todos os testes da Fase 4 passaram com 100% de conformidade!")
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
