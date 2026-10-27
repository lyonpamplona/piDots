#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Homologação: Fase 1 — Saneamento Arquitetural, Erradicação das 3 Colunas
e Restauração da Largura Total no /docs (piDots).
Zero Emojis.
"""

import sys
import re

def assert_true(condition, msg):
    if not condition:
        print(f"  -> [FALHA] {msg}")
        sys.exit(1)
    print(f"  -> [OK] {msg}")

def check_no_emojis(content, filename):
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\u2b50-\u2b55]'
        r'|[\u203c\u2049\u2139\u2194-\u21aa\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]'
    )
    matches = emoji_pattern.findall(content)
    assert_true(len(matches) == 0, f"Arquivo {filename} contem zero emojis (encontrados: {len(matches)})")

def test_docs_html():
    print("[TESTE 1/4] Validando integridade estrutural de pages/docs.html...")
    with open("pages/docs.html", "r", encoding="utf-8") as f:
        html = f.read()

    check_no_emojis(html, "pages/docs.html")

    assert_true("docs-3col-layout" not in html, "Ausencia de docs-3col-layout em pages/docs.html")
    assert_true("docs-toc-col" not in html, "Ausencia de docs-toc-col (Coluna 3) em pages/docs.html")
    assert_true("id=\"docsToc\"" not in html, "Ausencia do elemento #docsToc em pages/docs.html")
    assert_true("docs-sidebar" not in html, "Ausencia da classe docs-sidebar (sidebar estatica) em pages/docs.html")

    assert_true("<div class=\"guide-shell\">" in html, "guide-shell configurada sem divisao de 3 colunas")
    assert_true("<aside class=\"retractable-drawer\" id=\"retractableDrawer\"" in html, "Gaveta retratil declarada com id retractableDrawer")
    assert_true("<button id=\"toggleDrawerBtn\" class=\"pixel-btn btn-cyan\"" in html, "Botao toggleDrawerBtn disponivel sem mobile-drawer-trigger")
    assert_true("<main class=\"guide-viewport\" id=\"mainContent\">" in html, "main.guide-viewport configurado para prancheta panoramica")

def test_docs_css():
    print("[TESTE 2/4] Validando saneamento de CSS em static/css/docs.css...")
    with open("static/css/docs.css", "r", encoding="utf-8") as f:
        css = f.read()

    check_no_emojis(css, "static/css/docs.css")

    assert_true(".docs-3col-layout" not in css, "Ausencia de seletores .docs-3col-layout em static/css/docs.css")
    assert_true("aside.docs-toc-col" not in css, "Ausencia de regras de aside.docs-toc-col em static/css/docs.css")
    assert_true("aside.docs-sidebar" not in css, "Ausencia de aside.docs-sidebar em static/css/docs.css")
    assert_true(".mobile-drawer-trigger" not in css, "Ausencia de ocultacao .mobile-drawer-trigger { display: none; }")

    assert_true("aside.retractable-drawer" in css, "Declaracao canonica de aside.retractable-drawer presente")
    assert_true("right: calc(-1 * var(--drawer-width, 380px));" in css, "Gaveta posicionada na lateral direita fixa")
    assert_true("main.guide-viewport" in css, "main.guide-viewport configurado em largura total")
    assert_true("width: 100%;" in css, "Largura total mantida sem centralizacao")

def test_mobile_css():
    print("[TESTE 3/4] Validando remocao de excecoes artificiais em static/css/mobile.css...")
    with open("static/css/mobile.css", "r", encoding="utf-8") as f:
        mcss = f.read()

    check_no_emojis(mcss, "static/css/mobile.css")
    assert_true(":not(.docs-sidebar)" not in mcss, "Ausencia de seletores :not(.docs-sidebar) em static/css/mobile.css")

def test_docs_js():
    print("[TESTE 4/4] Validando controles do drawer e scroll em static/js/docs/docs.js...")
    with open("static/js/docs/docs.js", "r", encoding="utf-8") as f:
        js = f.read()

    check_no_emojis(js, "static/js/docs/docs.js")

    assert_true("docs-toc-link" not in js, "Remocao de dependencias de docs-toc-link em static/js/docs/docs.js")
    assert_true("openDrawer" in js and "closeDrawer" in js, "Funcoes openDrawer e closeDrawer presentes")
    assert_true("Escape" in js, "Suporte a tecla Escape para fechar a gaveta implementado")
    assert_true("altKey" in js, "Atalho de teclado Alt+I para alternar gaveta implementado")
    assert_true("scrollToStep" in js, "Navegacao suave scrollToStep preservada")

if __name__ == "__main__":
    print("========================================================================")
    print("HOMOLOGACAO: FASE 1 — SANEAMENTO ARQUITETURAL E LARGURA TOTAL NO /DOCS")
    print("========================================================================")
    test_docs_html()
    test_docs_css()
    test_mobile_css()
    test_docs_js()
    print("========================================================================")
    print("RESULTADO FINAL: 100% DOS TESTES DA FASE 1 APROVADOS COM SUCESSO.")
    print("========================================================================")
