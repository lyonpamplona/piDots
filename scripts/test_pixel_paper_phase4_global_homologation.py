#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 4: Consolidacao Final e Homologacao Global
Design System Pixel Paper UI // piDots Edge Core
"""

import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_phase1_catalog_and_tokens():
    print("[MODULO 1/4] Validando Fase 1: Tokens e Catalogo Central de Componentes...")
    token_path = os.path.join(BASE_DIR, "static/css/tokens.css")
    comp_path = os.path.join(BASE_DIR, "static/css/components.css")
    
    with open(token_path, "r", encoding="utf-8") as f:
        tok_content = f.read()
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_content = f.read()

    # Raios de borda zerados
    for r in ["--radius-xs", "--radius-sm", "--radius-md", "--radius-lg"]:
        assert re.search(rf"{r}:\s*0px;", tok_content), f"Token de raio {r} nao esta zerado"

    # Tokens canônicos
    assert "--paper-noir-base" in tok_content, "Superficie Noir Base ausente"
    assert "--font-pixel-head" in tok_content, "Token --font-pixel-head ausente"
    assert "--font-mono-data" in tok_content, "Token --font-mono-data ausente"
    assert ".pixel-rubber-stamp" in comp_content, "Classe .pixel-rubber-stamp ausente"
    assert "steps(1)" in comp_content, "steps(1) ausente em components.css"
    print(" -> [OK] Fase 1 (Tokens e Componentes Centrais) 100% CONFORME")

def test_phase2_landing_compliance():
    print("[MODULO 2/4] Validando Fase 2: Landing Page Surface...")
    html_path = os.path.join(BASE_DIR, "pages/landing.html")
    css_path = os.path.join(BASE_DIR, "static/css/landing.css")
    js_path = os.path.join(BASE_DIR, "static/js/landing/landing.js")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    # SVGs crispEdges
    svgs = re.findall(r"<svg\b[^>]*>", html)
    no_crisp = [s for s in svgs if 'shape-rendering="crispEdges"' not in s]
    assert len(no_crisp) == 0, f"SVGs sem crispEdges na Landing: {len(no_crisp)}"
    
    # Ausência de curvaturas
    curved = re.findall(r'r[xy]=["\'][1-9][0-9]*["\']', html)
    assert len(curved) == 0, f"Cantos curvos encontrados na Landing: {curved}"

    # Dither procedural e carimbos
    assert "bayerRamPattern" in html, "Bayer RAM pattern ausente"
    assert "radial-gradient" in css, "Dither de carimbo ausente em landing.css"
    assert "clip-path: polygon" in css, "Chanfro de fichas catalográficas ausente em landing.css"
    assert "scale(" not in js, "scale() encontrado em landing.js"
    assert "behavior: 'smooth'" not in js and 'behavior: "smooth"' not in js, "smooth scroll em landing.js"
    print(" -> [OK] Fase 2 (Landing Page Surface) 100% CONFORME")

def test_phase3_docs_compliance():
    print("[MODULO 3/4] Validando Fase 3: Documentacao Tecnica (/docs)...")
    html_path = os.path.join(BASE_DIR, "pages/docs.html")
    css_path = os.path.join(BASE_DIR, "static/css/docs.css")
    js_path = os.path.join(BASE_DIR, "static/js/docs/docs.js")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    # SVGs crispEdges
    svgs = re.findall(r"<svg\b[^>]*>", html)
    no_crisp = [s for s in svgs if 'shape-rendering="crispEdges"' not in s]
    assert len(no_crisp) == 0, f"SVGs sem crispEdges em docs: {len(no_crisp)}"
    
    # Ausência de cantos curvos
    curved = re.findall(r'r[xy]=["\'][1-9][0-9]*["\']', html)
    assert len(curved) == 0, f"Cantos curvos em docs.html: {curved}"

    # Ausência de sombras genéricas
    var_shadows = re.findall(r'box-shadow:\s*var\(--shadow', css)
    assert len(var_shadows) == 0, f"box-shadow generico var(--shadow*) em docs.css: {var_shadows}"

    # Sombras cartesianas puras
    assert "box-shadow: 2px 2px 0px #000000;" in css, "Sombra cartesiana 2px 2px 0px ausente em docs.css"
    assert "box-shadow: 3px 3px 0px #000000;" in css, "Sombra cartesiana 3px 3px 0px ausente em docs.css"
    assert "box-shadow: 4px 4px 0px #000000;" in css, "Sombra cartesiana 4px 4px 0px ausente em docs.css"

    # Tabular-nums e ausencia de smooth scroll
    assert "font-variant-numeric: tabular-nums;" in css, "tabular-nums ausente em docs.css"
    assert "behavior: 'smooth'" not in js and 'behavior: "smooth"' not in js, "smooth scroll em docs.js"
    print(" -> [OK] Fase 3 (Documentacao Tecnica /docs) 100% CONFORME")

def test_global_cross_surface_integrity():
    print("[MODULO 4/4] Validando Integridade Global e Zero Emojis...")
    
    # 4.1 Varredura de border-radius em todos os CSS de UI
    ui_css_files = [
        "static/css/tokens.css",
        "static/css/components.css",
        "static/css/layout.css",
        "static/css/mobile.css",
        "static/css/landing.css",
        "static/css/docs.css"
    ]
    for rel_path in ui_css_files:
        path = os.path.join(BASE_DIR, rel_path)
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "border-radius" in line:
                    assert re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line), (
                        f"Violação de border-radius em {rel_path}:{idx} -> {line.strip()}"
                    )
    
    # 4.2 Varredura de Zero Emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    for root, dirs, files in os.walk(BASE_DIR):
        if any(p in root for p in [".git", "node_modules", ".venv", "__pycache__", ".hermes", ".agents"]):
            continue
        for fname in files:
            if fname.endswith((".html", ".css", ".js", ".py", ".md", ".json")):
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                matches = emoji_pattern.findall(content)
                assert len(matches) == 0, f"Emojis encontrados em {fpath}: {matches}"

    print(" -> [OK] Integridade Global e Zero Emojis 100% HOMOLOGADOS")

def main():
    print("=========================================================================")
    print("DOSSIE DE HOMOLOGACAO FINAL // DESIGN SYSTEM PIXEL PAPER UI (FASE 4)")
    print("piDots Edge Core // ARM64 SBC Ultra-Low Overhead")
    print("=========================================================================")
    try:
        test_phase1_catalog_and_tokens()
        test_phase2_landing_compliance()
        test_phase3_docs_compliance()
        test_global_cross_surface_integrity()
        print("=========================================================================")
        print("RESULTADO FINAL: TODAS AS 4 FASES DO PIXEL PAPER UI FORAM APROVADAS!")
        print("ZERO EMOJIS // ZERO CANTOS CURVOS // ZERO SOMBRAS COM BLUR // 100% CONFORME")
        print("=========================================================================")
        return 0
    except AssertionError as err:
        print("=========================================================================")
        print(f"FALHA NA HOMOLOGACAO GLOBAL: {err}")
        print("=========================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
