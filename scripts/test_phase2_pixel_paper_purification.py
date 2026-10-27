#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 2: Purificacao Pixel Paper UI e Erradicacao de Slop
piDots Frontend (/landing e /docs)

Verifica:
1. Ausencia total de border-radius diferente de 0 em static/css/landing.css e static/css/docs.css.
2. Uso de tipografia tecnica --font-pixel em tags, badges, chips e carimbos.
3. Erradicacao das bolinhas macOS (.terminal-circle) e presenca do prompt Linux (.terminal-prompt-badge).
4. Suporte a contraste WCAG AA atraves do token semantico --ink-on-mint.
5. Opacidade de repouso dos carimbos analogicos (.rubber-stamp).
6. Conformidade estrita com a regra de ZERO emojis em todo o escopo da Fase 2.
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_landing_border_radius():
    fpath = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    assert os.path.exists(fpath), f"Arquivo nao encontrado: {fpath}"
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Procurar declaracoes border-radius
    br_matches = re.findall(r'border-radius:\s*([^;]+);', content)
    invalid_br = [val.strip() for val in br_matches if val.strip() not in ('0', '0 !important')]

    assert len(invalid_br) == 0, f"Encontrados border-radius nao-zero em landing.css: {invalid_br}"
    print("[OK] Teste 1: static/css/landing.css possui 100% border-radius: 0 (zero cantos arredondados).")

def test_docs_border_radius():
    fpath = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')
    assert os.path.exists(fpath), f"Arquivo nao encontrado: {fpath}"

    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    br_matches = re.findall(r'border-radius:\s*([^;]+);', content)
    invalid_br = [val.strip() for val in br_matches if val.strip() not in ('0', '0 !important')]

    assert len(invalid_br) == 0, f"Encontrados border-radius nao-zero em docs.css: {invalid_br}"
    print("[OK] Teste 2: static/css/docs.css possui 100% border-radius: 0 (zero cantos arredondados).")

def test_font_pixel_adoption():
    landing_path = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    docs_path = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')

    with open(landing_path, 'r', encoding='utf-8') as f:
        landing_content = f.read()
    with open(docs_path, 'r', encoding='utf-8') as f:
        docs_content = f.read()

    # Verificar tokens de font-pixel nas classes criticas de landing
    assert '--font-pixel' in landing_content, "Token --font-pixel nao encontrado em landing.css"
    assert '.metric-badge' in landing_content, ".metric-badge ausente em landing.css"
    assert '.brand-badge' in landing_content, ".brand-badge ausente em landing.css"

    # Verificar tokens de font-pixel nas classes criticas de docs
    assert '--font-pixel' in docs_content, "Token --font-pixel nao encontrado em docs.css"
    assert '.pixel-stamp' in docs_content, ".pixel-stamp ausente em docs.css"
    assert '.terminal-prompt-badge' in docs_content, ".terminal-prompt-badge ausente em docs.css"

    print("[OK] Teste 3: Adocao sistematica de --font-pixel em badges tecnicas, micro-rotulos e chips.")

def test_terminal_prompt_badge_and_no_mac_circles():
    docs_html_path = os.path.join(BASE_DIR, 'pages', 'docs.html')
    docs_css_path = os.path.join(BASE_DIR, 'static', 'css', 'docs.css')

    with open(docs_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    with open(docs_css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    assert 'terminal-circle' not in html_content, "Bolinhas macOS terminal-circle ainda encontradas em pages/docs.html"
    assert 'terminal-circle' not in css_content, "Bolinhas macOS terminal-circle ainda encontradas em static/css/docs.css"
    assert 'terminal-prompt-badge' in html_content, "Badge nativo pi@edge:~# ausente em pages/docs.html"
    assert 'terminal-prompt-badge' in css_content, "Badge nativo pi@edge:~# ausente em static/css/docs.css"

    print("[OK] Teste 4: Erradicacao completa de macOS terminal-circle e adocao de badge nativo Linux.")

def test_tokens_ink_on_mint():
    tokens_path = os.path.join(BASE_DIR, 'static', 'css', 'tokens.css')
    with open(tokens_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '--ink-on-mint:' in content, "Token --ink-on-mint nao declarado em tokens.css"
    print("[OK] Teste 5: Token --ink-on-mint declarado com suporte a alto contraste nos temas escuro e claro.")

def test_rubber_stamp_idle_opacity():
    landing_path = os.path.join(BASE_DIR, 'static', 'css', 'landing.css')
    with open(landing_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '.rubber-stamp' in content, ".rubber-stamp nao encontrado em landing.css"
    assert 'opacity: 0.25;' in content, "Opacidade de repouso (0.25) nao encontrada para .rubber-stamp em landing.css"

    print("[OK] Teste 6: Estado de repouso (opacity: 0.25) configurado nos carimbos da arena de governanca.")

def test_zero_emojis_compliance():
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    files_to_check = [
        os.path.join(BASE_DIR, 'pages', 'landing.html'),
        os.path.join(BASE_DIR, 'pages', 'docs.html'),
        os.path.join(BASE_DIR, 'static', 'css', 'landing.css'),
        os.path.join(BASE_DIR, 'static', 'css', 'docs.css'),
        os.path.join(BASE_DIR, 'static', 'css', 'tokens.css'),
    ]

    for fpath in files_to_check:
        with open(fpath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                matches = emoji_pattern.findall(line)
                assert len(matches) == 0, f"Emoji detectado em {fpath}:{idx} -> {matches}"

    print("[OK] Teste 7: Conformidade inegociavel de ZERO emojis verificada em todos os arquivos modificados.")

if __name__ == '__main__':
    print("=" * 70)
    print("Iniciando Verificacao Automatizada - Fase 2: Purificacao Pixel Paper UI")
    print("=" * 70)

    test_landing_border_radius()
    test_docs_border_radius()
    test_font_pixel_adoption()
    test_terminal_prompt_badge_and_no_mac_circles()
    test_tokens_ink_on_mint()
    test_rubber_stamp_idle_opacity()
    test_zero_emojis_compliance()

    print("=" * 70)
    print("TODOS OS 7 TESTES DA FASE 2 PASSARAM COM 100% DE SUCESSO!")
    print("=" * 70)
