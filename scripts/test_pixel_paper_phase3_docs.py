#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 3: Refatoracao Pixel Paper UI da Documentacao Tecnica (/docs)
Design System Pixel Paper UI // piDots Edge Core
"""

import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_docs_html():
    print("[TESTE 1] Inspecionando pages/docs.html...")
    path = os.path.join(BASE_DIR, "pages/docs.html")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1.1 Todos os SVGs com shape-rendering="crispEdges"
    svg_tags = re.findall(r"<svg\b[^>]*>", content)
    assert len(svg_tags) >= 50, f"Poucos SVGs encontrados: {len(svg_tags)}"
    missing_crisp = [tag for tag in svg_tags if 'shape-rendering="crispEdges"' not in tag]
    assert len(missing_crisp) == 0, f"SVGs sem crispEdges em docs.html: {len(missing_crisp)}"

    # 1.2 Zero raios curvos rx ou ry em SVGs
    curved_radii = re.findall(r'r[xy]=["\'][1-9][0-9]*["\']', content)
    assert len(curved_radii) == 0, f"Raios curvos encontrados em SVGs de docs.html: {curved_radii}"

    # 1.3 Zero border-radius inline maior que zero
    inline_radii = re.findall(r'style="[^"]*border-radius:\s*[1-9][^"]*"', content)
    assert len(inline_radii) == 0, f"border-radius inline maior que zero: {inline_radii}"

    # 1.4 Icone de copia de codigo com tracado ortogonal estrito
    assert '<rect x="9" y="9" width="13" height="13" rx="0" ry="0"></rect>' in content, "Icone de copia com cantos curvos remanescente"
    assert '<path d="M5 15H3V3h12v2"></path>' in content, "Tracado ortogonal de copia ausente em docs.html"

    # 1.5 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em docs.html: {emojis}"

    print(" -> pages/docs.html: 100% CONFORME")

def test_docs_css():
    print("[TESTE 2] Inspecionando static/css/docs.css...")
    path = os.path.join(BASE_DIR, "static/css/docs.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 2.1 Varredura de border-radius > 0
    violations_radius = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line):
            violations_radius.append((idx, line.strip()))
    assert len(violations_radius) == 0, f"border-radius > 0 encontrado em docs.css: {violations_radius}"

    # 2.2 Varredura de cubic-bezier e scale continuo
    assert "cubic-bezier" not in content, "cubic-bezier encontrado em docs.css"
    assert "scale(" not in content, "scale(..) transform encontrado em docs.css"

    # 2.3 Ausencia de sombras genericas com var(--shadow*)
    var_shadows = re.findall(r'box-shadow:\s*var\(--shadow', content)
    assert len(var_shadows) == 0, f"box-shadow generico var(--shadow*) encontrado em docs.css: {var_shadows}"

    # 2.4 Tipografia Dual (Pixel Head nos titulos e tabular-nums nos dados e tabelas)
    assert "--font-pixel-head" in content or "Silkscreen" in content, "Tipografia de cabecalho pixel ausente em docs.css"
    assert "font-variant-numeric: tabular-nums;" in content, "tabular-nums ausente em docs.css"

    # 2.5 Sombras Cartesianas Duras (Preto Solido)
    assert "box-shadow: 2px 2px 0px #000000;" in content, "Sombra cartesiana 2px 2px 0px ausente em docs.css"
    assert "box-shadow: 3px 3px 0px #000000;" in content, "Sombra cartesiana 3px 3px 0px ausente em docs.css"
    assert "box-shadow: 4px 4px 0px #000000;" in content, "Sombra cartesiana 4px 4px 0px ausente em docs.css"
    assert "box-shadow: -6px 0px 0px #000000;" in content, "Sombra cartesiana do drawer ausente em docs.css"

    # 2.6 Microinteracoes Mecanicas com steps
    assert "steps(" in content, "Microinteracoes discretas steps(...) ausentes em docs.css"

    # 2.7 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em docs.css: {emojis}"

    print(" -> static/css/docs.css: 100% CONFORME")

def test_docs_js():
    print("[TESTE 3] Inspecionando static/js/docs/docs.js...")
    path = os.path.join(BASE_DIR, "static/js/docs/docs.js")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 3.1 Zero scale(...) em animacoes
    assert "scale(" not in content, "scale(..) transform encontrado em docs.js"

    # 3.2 Zero alert(...) nativo do navegador
    assert "alert(" not in content, "alert(..) encontrado em docs.js"

    # 3.3 Zero scroll suave de IA (behavior: 'smooth')
    assert "behavior: 'smooth'" not in content and 'behavior: "smooth"' not in content, "scroll smooth encontrado em docs.js (deve ser auto)"

    # 3.4 Zero border-radius inline em HTML injetado
    violations_radius = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px)", line):
            violations_radius.append((idx, line.strip()))
    assert len(violations_radius) == 0, f"border-radius > 0 no HTML injetado em docs.js: {violations_radius}"

    # 3.5 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em docs.js: {emojis}"

    print(" -> static/js/docs/docs.js: 100% CONFORME")

def main():
    print("=====================================================================")
    print("HOMOLOGACAO PIXEL PAPER UI - FASE 3: DOCUMENTACAO TECNICA (/docs)")
    print("=====================================================================")
    try:
        test_docs_html()
        test_docs_css()
        test_docs_js()
        print("=====================================================================")
        print("SUCESSO TOTAL: TODOS OS TESTES DA FASE 3 FORAM HOMOLOGADOS COM EXITO!")
        print("=====================================================================")
        return 0
    except AssertionError as err:
        print("=====================================================================")
        print(f"FALHA NO TESTE: {err}")
        print("=====================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
