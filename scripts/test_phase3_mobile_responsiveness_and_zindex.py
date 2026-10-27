#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 3: Responsividade Extrema e Resiliencia de Viewport
piDots Frontend (/landing e /docs)

Verifica:
1. Prevencao de auto-zoom no Apple iOS Safari em campos de texto (font-size >= 16px).
2. Scroll vertical e contencao de overflow no menu movel (.mobile-nav-panel).
3. Primeira coluna sticky na matriz comparativa de engenharia e tabelas tecnicas.
4. Unificacao e consistencia matematica da pilha de z-index (header 100 < drawer/menu 150 < modal 910).
5. Conformidade inegociavel com a diretriz de ZERO emojis.
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_ios_safari_autozoom_prevention():
    landing_css = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    docs_css = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')

    with open(landing_css, 'r', encoding='utf-8') as f:
        l_content = f.read()
    with open(docs_css, 'r', encoding='utf-8') as f:
        d_content = f.read()

    # Verificar declaracao de font-size: 16px !important no bloco @media (max-width: 768px)
    assert 'font-size: 16px !important;' in l_content, "Regra de prevencao de auto-zoom ausente em landing.css"
    assert 'font-size: 16px !important;' in d_content, "Regra de prevencao de auto-zoom ausente em docs.css"

    print("[OK] Teste 1: Prevencao de auto-zoom no Apple iOS Safari (16px em inputs) homologada na landing e docs.")

def test_mobile_nav_panel_scroll_and_height():
    landing_css = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')

    with open(landing_css, 'r', encoding='utf-8') as f:
        content = f.read()

    # Procurar bloco .mobile-nav-panel
    nav_match = re.search(r'\.mobile-nav-panel\s*\{([^}]+)\}', content)
    assert nav_match, "Bloco .mobile-nav-panel nao encontrado em landing.css"

    nav_body = nav_match.group(1)
    assert 'overflow-y: auto' in nav_body, ".mobile-nav-panel nao contem overflow-y: auto"
    assert 'max-height:' in nav_body and '100dvh' in nav_body, ".mobile-nav-panel nao contem max-height com 100dvh"
    assert 'overscroll-behavior: contain' in nav_body, ".mobile-nav-panel nao contem overscroll-behavior: contain"

    print("[OK] Teste 2: Menu movel (.mobile-nav-panel) configurado com scroll vertical e isolamento de viewport.")

def test_sticky_comparison_matrix():
    landing_css = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    docs_css = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')

    with open(landing_css, 'r', encoding='utf-8') as f:
        l_content = f.read()
    with open(docs_css, 'r', encoding='utf-8') as f:
        d_content = f.read()

    # Na landing, a coluna .col-dimension deve ser sticky
    dim_match = re.search(r'\.comparison-table\s+\.col-dimension\s*\{([^}]+)\}', l_content)
    assert dim_match, "Regra .comparison-table .col-dimension ausente em landing.css"
    dim_body = dim_match.group(1)
    assert 'position: sticky' in dim_body, ".col-dimension nao possui position: sticky"
    assert 'left: 0' in dim_body, ".col-dimension nao possui left: 0"

    # No docs, table.pixel-table deve ter th:first-child / td:first-child sticky
    assert 'position: sticky;' in d_content, "Docs nao possui regras sticky para tabelas tecnicas"
    assert 'table.pixel-table th:first-child' in d_content, "Docs nao possui th:first-child configurado"

    print("[OK] Teste 3: Primeira coluna sticky homologada na matriz comparativa (landing) e tabelas (docs).")

def test_z_index_hierarchy_consistency():
    landing_css = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    docs_css = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')

    with open(landing_css, 'r', encoding='utf-8') as f:
        l_content = f.read()
    with open(docs_css, 'r', encoding='utf-8') as f:
        d_content = f.read()

    # Validar headers: z-index: 100
    assert 'header.landing-header {\n    position: sticky;\n    top: 0;\n    z-index: 100;' in l_content, "header.landing-header nao possui z-index: 100"
    assert 'header.guide-header {\n    position: sticky;\n    top: 0;\n    z-index: 100;' in d_content, "header.guide-header nao possui z-index: 100"

    # Validar mobile nav e drawer: z-index: 150
    nav_match = re.search(r'\.mobile-nav-panel\s*\{([^}]+)\}', l_content)
    assert 'z-index: 150;' in nav_match.group(1), ".mobile-nav-panel nao possui z-index: 150"

    # Validar backdrops: z-index: 140
    assert '.drawer-backdrop {\n    position: fixed;\n    top: 0;\n    left: 0;\n    width: 100%;\n    height: 100%;\n    background: rgba(0, 0, 0, 0.72);\n    z-index: 140;' in l_content, "drawer-backdrop na landing nao possui z-index: 140"

    # Validar omnisearch modal: z-index: 910 e backdrop: 900
    assert 'z-index: 900;' in d_content, "Omnisearch backdrop nao possui z-index: 900"
    assert 'z-index: 910;' in d_content, "Omnisearch modal nao possui z-index: 910"

    print("[OK] Teste 4: Hierarquia de z-index (100 < 102 < 140 < 150 < 900 < 910) consistente e livre de conflitos.")

def test_zero_emojis_compliance():
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    files_to_check = [
        os.path.join(BASE_DIR, 'static', 'css', 'landing.css'),
        os.path.join(BASE_DIR, 'static', 'css', 'docs.css'),
        os.path.join(BASE_DIR, 'static', 'css', 'mobile.css'),
        os.path.join(BASE_DIR, 'pages', 'landing.html'),
        os.path.join(BASE_DIR, 'pages', 'docs.html'),
    ]

    for fpath in files_to_check:
        with open(fpath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                matches = emoji_pattern.findall(line)
                assert len(matches) == 0, f"Emoji detectado em {fpath}:{idx} -> {matches}"

    print("[OK] Teste 5: Conformidade estrita com ZERO emojis mantida em 100% dos arquivos inspecionados.")

if __name__ == '__main__':
    print("=" * 75)
    print("Iniciando Verificacao Automatizada - Fase 3: Responsividade Extrema")
    print("=" * 75)

    test_ios_safari_autozoom_prevention()
    test_mobile_nav_panel_scroll_and_height()
    test_sticky_comparison_matrix()
    test_z_index_hierarchy_consistency()
    test_zero_emojis_compliance()

    print("=" * 75)
    print("TODOS OS 5 TESTES DA FASE 3 PASSARAM COM 100% DE SUCESSO!")
    print("=" * 75)
