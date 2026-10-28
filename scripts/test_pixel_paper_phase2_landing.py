#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 2: Refatoracao Pixel Paper UI da Landing Page
Design System Pixel Paper UI // piDots Edge Core
"""

import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_landing_html():
    print("[TESTE 1] Inspecionando pages/landing.html...")
    path = os.path.join(BASE_DIR, "pages/landing.html")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1.1 Todos os SVGs com shape-rendering="crispEdges"
    svg_tags = re.findall(r"<svg\b[^>]*>", content)
    assert len(svg_tags) >= 20, f"Poucos SVGs encontrados: {len(svg_tags)}"
    missing_crisp = [tag for tag in svg_tags if 'shape-rendering="crispEdges"' not in tag]
    assert len(missing_crisp) == 0, f"SVGs sem crispEdges: {len(missing_crisp)}"

    # 1.2 Zero raios curvos rx ou ry em SVGs
    curved_radii = re.findall(r'r[xy]=["\'][1-9][0-9]*["\']', content)
    assert len(curved_radii) == 0, f"Raios curvos encontrados em SVGs: {curved_radii}"

    # 1.3 Zero border-radius inline maior que zero
    inline_radii = re.findall(r'style="[^"]*border-radius:\s*[1-9][^"]*"', content)
    assert len(inline_radii) == 0, f"border-radius inline maior que zero: {inline_radii}"

    # 1.4 Padroes Bayer dither procedural de 1-bit
    assert "bayerRamPattern" in content, "Padrao Bayer dither para RAM ausente em landing.html"
    assert "bayerTempPattern" in content, "Padrao Bayer dither para Temperatura ausente em landing.html"

    # 1.5 Elementos de materialidade analogica (perfuracao e cursor de bloco)
    assert "slip-perforation" in content, "Picote de teletipo .slip-perforation ausente em landing.html"
    assert "ticker-cursor" in content, "Cursor de bloco .ticker-cursor ausente em landing.html"

    # 1.6 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em landing.html: {emojis}"

    print(" -> pages/landing.html: 100% CONFORME")

def test_landing_css():
    print("[TESTE 2] Inspecionando static/css/landing.css...")
    path = os.path.join(BASE_DIR, "static/css/landing.css")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 2.1 Varredura de border-radius > 0
    violations_radius = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px|\s*!important)", line):
            violations_radius.append((idx, line.strip()))
    assert len(violations_radius) == 0, f"border-radius > 0 encontrado em landing.css: {violations_radius}"

    # 2.2 Varredura de cubic-bezier e scale contínuo
    assert "cubic-bezier" not in content, "cubic-bezier encontrado em landing.css (use steps(1) ou steps(2))"
    assert "scale(" not in content, "scale(..) transform encontrado em landing.css (use depressao 2D ou steps(1))"

    # 2.3 Tipografia Dual (Silkscreen / Pixel Head nos titulos e tabular-nums nos dados)
    assert "--font-pixel-head" in content or "Silkscreen" in content, "Tipografia de cabecalho pixel ausente em landing.css"
    assert "font-variant-numeric: tabular-nums;" in content, "tabular-nums ausente em landing.css"

    # 2.4 Geometria de Cartoes e Fichas Catalograficas
    assert "clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%)" in content, "Chanfro de ficha catalografica ausente em .catalog-tab-card"
    assert "box-shadow: 2px 2px 0px #000000;" in content, "Sombra cartesiana 2px 2px 0px ausente em landing.css"

    # 2.5 Carimbos Analogicos de Borracha (HITL)
    assert ".rubber-stamp" in content, "Classe .rubber-stamp ausente em landing.css"
    assert "background-image: radial-gradient" in content and "background-size: 4px 4px;" in content, "Dither procedural de carimbo ausente em landing.css"

    # 2.6 Microinteracoes Mecanicas em steps(1)
    assert "steps(1)" in content, "Microinteracoes discretas steps(1) ausentes em landing.css"

    # 2.7 Menu Lateral Retratil (Drawer Tecnico)
    assert "aside.retractable-drawer" in content, "Regra aside.retractable-drawer ausente em landing.css"
    assert "steps(2)" in content, "steps(2) ausente no drawer tecnico em landing.css"
    assert "box-shadow: -6px 0px 0px #000000;" in content, "Sombra cartesiana do drawer ausente em landing.css"

    # 2.8 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em landing.css: {emojis}"

    print(" -> static/css/landing.css: 100% CONFORME")

def test_landing_js():
    print("[TESTE 3] Inspecionando static/js/landing/landing.js...")
    path = os.path.join(BASE_DIR, "static/js/landing/landing.js")
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        content = "".join(lines)

    # 3.1 Zero scale(...) em animacoes de carimbo
    assert "scale(" not in content, "scale(..) transform encontrado em landing.js"

    # 3.2 Zero alert(...) nativo do navegador
    assert "alert(" not in content, "alert(..) encontrado em landing.js (deve usar showToast)"

    # 3.3 Zero scroll suave de IA (behavior: 'smooth')
    assert "behavior: 'smooth'" not in content and 'behavior: "smooth"' not in content, "scroll smooth encontrado em landing.js (deve ser auto)"

    # 3.4 Zero border-radius inline em HTML injetado
    violations_radius = []
    for idx, line in enumerate(lines, 1):
        if "border-radius" in line and not re.search(r"border-radius:\s*0(\s*;|px)", line):
            violations_radius.append((idx, line.strip()))
    assert len(violations_radius) == 0, f"border-radius > 0 no HTML injetado em landing.js: {violations_radius}"

    # 3.5 Verificacao de zero emojis
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]"
    )
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Emojis proibidos encontrados em landing.js: {emojis}"

    print(" -> static/js/landing/landing.js: 100% CONFORME")

def main():
    print("=====================================================================")
    print("HOMOLOGACAO PIXEL PAPER UI - FASE 2: LANDING PAGE")
    print("=====================================================================")
    try:
        test_landing_html()
        test_landing_css()
        test_landing_js()
        print("=====================================================================")
        print("SUCESSO TOTAL: TODOS OS TESTES DA FASE 2 FORAM HOMOLOGADOS COM EXITO!")
        print("=====================================================================")
        return 0
    except AssertionError as err:
        print("=====================================================================")
        print(f"FALHA NO TESTE: {err}")
        print("=====================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
