#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados - Fase 1: Purificação de Tokens e Catálogo Central
Design System Pixel Paper UI // piDots Edge Core
"""

import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_tokens_css():
    print("[TESTE 1] Inspecionando static/css/tokens.css...")
    path = os.path.join(BASE_DIR, "static/css/tokens.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1.1 Raios de Borda zerados
    for r in ["--radius-xs", "--radius-sm", "--radius-md", "--radius-lg"]:
        pattern = rf"{r}:\s*0px;"
        assert re.search(pattern, content), f"Token de raio {r} nao esta zerado (esperado '0px;')"

    # 1.2 Superfícies Noir Canônicas
    assert "--paper-noir-base:        #07090c;" in content or "--paper-noir-base: #07090c;" in content, "Superfície Noir Base desalinhada"
    assert "--paper-surface-sheet:    #0b0e12;" in content or "--paper-surface-sheet: #0b0e12;" in content, "Superfície Folha desalinhada"
    assert "--paper-surface-card:     #11161d;" in content or "--paper-surface-card: #11161d;" in content, "Superfície Ficha Catalográfica desalinhada"
    assert "--paper-surface-elevated: #182029;" in content or "--paper-surface-elevated: #182029;" in content, "Superfície Elevada desalinhada"
    assert "--paper-surface-recessed: #040608;" in content or "--paper-surface-recessed: #040608;" in content, "Superfície Recuada desalinhada"

    # 1.3 Tintas Mecânicas Canônicas
    assert "#33ff66" in content, "Fósforo verde P31 (#33ff66) ausente em tokens.css"
    assert "#ffb830" in content, "Fósforo âmbar P4 (#ffb830) ausente em tokens.css"
    assert "#ef4444" in content, "Carmim de carimbo de veto (#ef4444) ausente em tokens.css"
    assert "#334155" in content, "Cinza-carvão técnico de picote (#334155) ausente em tokens.css"

    # 1.4 Dual-Typography Tokens
    assert "--font-pixel-head" in content, "Token --font-pixel-head ausente"
    assert "--font-pixel-sub" in content, "Token --font-pixel-sub ausente"
    assert "--font-mono-data" in content, "Token --font-mono-data ausente"

    # 1.5 Bordas Hexadecimais Opacas (Sem transparência alfa em contornos mecânicos)
    assert "--border-pixel-subtle:  #1c2633;" in content or "--border-pixel-subtle: #1c2633;" in content, "Borda sutil opaca ausente"
    assert "--border-pixel-default: #283340;" in content or "--border-pixel-default: #283340;" in content, "Borda padrão opaca ausente"
    assert "--border-pixel-strong:  #3d5168;" in content or "--border-pixel-strong: #3d5168;" in content, "Borda forte opaca ausente"
    assert "--border-pixel-accent:  #38bdf8;" in content or "--border-pixel-accent: #38bdf8;" in content, "Borda acento opaca ausente"

    print(" -> tokens.css: 100% CONFORME")

def test_components_css():
    print("[TESTE 2] Inspecionando static/css/components.css...")
    path = os.path.join(BASE_DIR, "static/css/components.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 2.1 Varredura de border-radius > 0
    violations = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line):
            violations.append((idx, line.strip()))
    
    assert len(violations) == 0, f"Violações de border-radius encontradas em components.css: {violations}"

    # 2.2 Botão mecânico (.pixel-btn)
    assert "border-radius: 0;" in content, "Botão sem border-radius: 0"
    assert "steps(1)" in content, "Microinterações de steps(1) ausentes no botão"
    assert "translate(-1px, -1px)" in content, "Depressão 2D hover ausente no botão"
    assert "translate(2px, 2px)" in content, "Depressão 2D active ausente no botão"

    # 2.3 Utilitários Centrais do Pixel Paper UI
    assert ".pixel-box" in content, "Classe utilitária .pixel-box ausente em components.css"
    assert ".pixel-tab" in content, "Classe utilitária .pixel-tab ausente em components.css"
    assert "clip-path: polygon" in content, "Chanfro clip-path polygon ausente nas abas/fichas"
    assert ".pixel-card" in content, "Classe utilitária .pixel-card ausente em components.css"
    assert "table.pixel-table" in content, "Classe utilitária table.pixel-table ausente em components.css"
    assert "font-variant-numeric: tabular-nums;" in content, "tabular-nums ausente em table.pixel-table"
    assert ".pixel-stamp" in content, "Classe utilitária .pixel-stamp ausente em components.css"
    assert ".pixel-rubber-stamp" in content, "Classe utilitária .pixel-rubber-stamp ausente em components.css"
    assert "radial-gradient" in content and "background-size: 4px 4px;" in content, "Dither procedural de carimbo ausente"
    assert ".tractor-feed" in content, "Trator lateral .tractor-feed ausente em components.css"
    assert ".slip-perforation" in content or ".tear-off" in content, "Picote serrilhado ausente em components.css"

    # 2.4 LED quadrado mecânico sem blur/fade
    assert "pixelBlink" in content, "Animação mecânica discreta pixelBlink ausente"

    print(" -> components.css: 100% CONFORME")

def test_layout_css():
    print("[TESTE 3] Inspecionando static/css/layout.css...")
    path = os.path.join(BASE_DIR, "static/css/layout.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 3.1 Varredura de border-radius > 0
    violations = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line):
            violations.append((idx, line.strip()))
    
    assert len(violations) == 0, f"Violações de border-radius encontradas em layout.css: {violations}"

    # 3.2 Tipografia de comando e marca
    assert "--font-pixel" in content or "--font-pixel-head" in content, "Tipografia pixel art ausente na marca/abas de layout.css"

    # 3.3 Transições discretas em passos
    assert "steps(2)" in content or "steps(1)" in content, "Transições mecânicas em degraus ausentes em layout.css"

    print(" -> layout.css: 100% CONFORME")

def test_mobile_css():
    print("[TESTE 4] Inspecionando static/css/mobile.css...")
    path = os.path.join(BASE_DIR, "static/css/mobile.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 4.1 Varredura de border-radius > 0
    violations = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line):
            violations.append((idx, line.strip()))
    
    assert len(violations) == 0, f"Violações de border-radius encontradas em mobile.css: {violations}"

    # 4.2 Blindagem ortogonal explícita
    assert "border-radius: 0 !important;" in content, "Blindagem ortogonal explícita para mobile ausente"

    # 4.3 Otimização da gaveta retrátil
    assert "transition: transform 0.1s steps(2) !important;" in content, "Gaveta móvel com duração excessiva ou sem steps(2)"

    print(" -> mobile.css: 100% CONFORME")

def test_zero_emojis():
    print("[TESTE 5] Varredura Forense de Zero Emojis nos 4 arquivos...")
    files = [
        "static/css/tokens.css",
        "static/css/components.css",
        "static/css/layout.css",
        "static/css/mobile.css"
    ]
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff"
        "\u2600-\u26ff"
        "\u2700-\u27bf"
        "\u2300-\u23ff"
        "\u2b50-\u2b55"
        "\u200d"
        "\ufe0f]"
    )
    for rel_path in files:
        full_path = os.path.join(BASE_DIR, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                m = emoji_pattern.search(line)
                assert not m, f"Emoji detectado em {rel_path}:{idx} -> {line.strip()}"
    print(" -> Zero Emojis: 100% HOMOLOGADO (0 caracteres pictográficos)")

def main():
    print("=" * 65)
    print("EXECUCAO DA SUITE DE TESTES // FASE 1: TOKENS E COMPONENTES")
    print("=" * 65)
    try:
        test_tokens_css()
        test_components_css()
        test_layout_css()
        test_mobile_css()
        test_zero_emojis()
        print("=" * 65)
        print("RESULTADO: TODOS OS TESTES DA FASE 1 PASSARAM COM SUCESSO!")
        print("=" * 65)
    except AssertionError as e:
        print(f"\n[ERRO DE VALIDACAO]: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
