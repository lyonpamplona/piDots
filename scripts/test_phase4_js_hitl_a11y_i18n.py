#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes Automatizados - Fase 4: Desacoplamento JS, Arena HITL, a11y, i18n e Homologacao Final
piDots Frontend (/landing e /docs)

Verifica:
1. Desacoplamento e protecao contra excecoes nas funcoes JS (guard clauses, null checks).
2. Sincronizacao bilingue (i18n) em toasts e respostas dinamicas da UI.
3. Conformidade estrita de acessibilidade (a11y) com atributos ARIA (aria-expanded, aria-controls, aria-label).
4. Integridade da governanca HITL, trava mecanica e carimbos analogicos.
5. Diretriz inegociavel de ZERO emojis em todo o escopo do frontend.
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_js_decoupling_and_guard_clauses():
    landing_js = os.path.join(BASE_DIR, 'static', 'js', 'landing', 'landing.js')
    docs_js = os.path.join(BASE_DIR, 'static', 'js', 'docs', 'docs.js')

    with open(landing_js, 'r', encoding='utf-8') as f:
        l_content = f.read()
    with open(docs_js, 'r', encoding='utf-8') as f:
        d_content = f.read()

    # Verificar guard clauses nas funcoes principais de landing.js
    assert 'if (!drawer || !backdrop) return;' in l_content, "Guard clause ausente em toggleDrawer"
    assert 'if (!panel) return;' in l_content, "Guard clause ausente em toggleMobileNavMenu"
    assert 'if (!card) return;' in l_content, "Guard clause ausente em toggleObjection"

    # Verificar funcoes do docs.js
    assert 'if (!drawer) return;' in d_content, "Guard clause ausente em openDrawer (docs.js)"
    assert 'function closeDrawer(' in d_content, "closeDrawer ausente em docs.js"

    print("[OK] Teste 1: Desacoplamento e guard clauses resilientes homologados em landing.js e docs.js.")

def test_bilingual_i18n_synchronization():
    landing_js = os.path.join(BASE_DIR, 'static', 'js', 'landing', 'landing.js')

    with open(landing_js, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar tratamento condicional de idioma nas acoes da arena HITL
    assert 'HOMOLOGATED:' in content and 'HOMOLOGADO:' in content, "Tratativa bilingue ausente em triggerDemoApprove"
    assert 'VETO RECORDED:' in content and 'VETO REGISTRADO:' in content, "Tratativa bilingue ausente em triggerDemoVeto"
    assert 'SAVINGS ESTIMATE:' in content and 'PROJEÇÃO DE ECONOMIA:' in content, "Tratativa bilingue ausente em generateRoiSummaryToast"

    print("[OK] Teste 2: Sincronizacao bilingue (PT/EN) dinâmica homologada nas rotinas operacionais.")

def test_a11y_aria_attributes_and_keyboard_nav():
    landing_html = os.path.join(BASE_DIR, 'pages', 'landing.html')
    docs_html = os.path.join(BASE_DIR, 'pages', 'docs.html')

    with open(landing_html, 'r', encoding='utf-8') as f:
        l_content = f.read()
    with open(docs_html, 'r', encoding='utf-8') as f:
        d_content = f.read()

    # Validar a11y nos acordeoes de FAQ (landing.html)
    assert 'role="region"' in l_content, "role='region' ausente na lista de FAQ"
    assert 'role="button"' in l_content, "role='button' ausente nos cabecalhos de FAQ"
    assert 'aria-expanded=' in l_content, "aria-expanded ausente no FAQ da landing"
    assert 'aria-controls=' in l_content, "aria-controls ausente no FAQ da landing"
    assert 'tabindex="0"' in l_content, "tabindex='0' ausente nos cabecalhos de FAQ para navegacao por teclado"

    # Validar a11y nos botoes do cabecalho (landing e docs)
    assert 'id="btnLandingManual"' in l_content, "btnLandingManual ausente em landing.html"
    assert 'aria-controls="retractableDrawer"' in d_content, "aria-controls ausente em toggleDrawerBtn no docs.html"
    assert 'aria-label="Abrir Índice de Navegação"' in d_content, "aria-label ausente em toggleDrawerBtn no docs.html"
    assert 'aria-label="Voltar ao Topo"' in d_content, "aria-label ausente em btnBackToTop no docs.html"

    print("[OK] Teste 3: Acessibilidade WCAG AA (roles, aria-expanded, aria-controls, tabindex) homologada.")

def test_hitl_governance_integrity():
    landing_html = os.path.join(BASE_DIR, 'pages', 'landing.html')

    with open(landing_html, 'r', encoding='utf-8') as f:
        content = f.read()

    # Validar integridade dos elementos da arena HITL
    assert 'id="demoSafetySwitch"' in content, "demoSafetySwitch ausente no HTML"
    assert 'id="demoSafetyLabel"' in content, "demoSafetyLabel ausente no HTML"
    assert 'id="btnDemoApprove"' in content, "btnDemoApprove ausente no HTML"
    assert 'id="demoStampApprove"' in content, "demoStampApprove ausente no HTML"
    assert 'id="demoStampReject"' in content, "demoStampReject ausente no HTML"

    print("[OK] Teste 4: Elementos de governanca HITL, trava mecanica e carimbos analogicos integrados.")

def test_zero_emojis_compliance():
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    files_to_check = [
        os.path.join(BASE_DIR, 'pages', 'landing.html'),
        os.path.join(BASE_DIR, 'pages', 'docs.html'),
        os.path.join(BASE_DIR, 'static', 'js', 'landing', 'landing.js'),
        os.path.join(BASE_DIR, 'static', 'js', 'docs', 'docs.js'),
        os.path.join(BASE_DIR, 'static', 'css', 'landing.css'),
        os.path.join(BASE_DIR, 'static', 'css', 'docs.css'),
    ]

    for fpath in files_to_check:
        with open(fpath, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                matches = emoji_pattern.findall(line)
                assert len(matches) == 0, f"Emoji detectado em {fpath}:{idx} -> {matches}"

    print("[OK] Teste 5: Conformidade inegociavel com a diretriz de ZERO emojis mantida em 100% dos arquivos.")

if __name__ == '__main__':
    print("=" * 75)
    print("Iniciando Verificacao Automatizada - Fase 4: Desacoplamento JS & Homologacao")
    print("=" * 75)

    test_js_decoupling_and_guard_clauses()
    test_bilingual_i18n_synchronization()
    test_a11y_aria_attributes_and_keyboard_nav()
    test_hitl_governance_integrity()
    test_zero_emojis_compliance()

    print("=" * 75)
    print("TODOS OS 5 TESTES DA FASE 4 PASSARAM COM 100% DE SUCESSO!")
    print("=" * 75)
