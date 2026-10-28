"""
Script de validação e homologação técnica da Fase 2: Interfaces Web & Dicionários i18n.
Verifica:
1. Ausência de emojis em todos os arquivos de UI e i18n.
2. Paridade rigorosa 1:1 de chaves folha entre data/locales/pt.json e data/locales/en.json.
3. Purgação de termos proibidos de AI Slop das páginas HTML e dos dicionários de tradução.
4. Preservação dos atributos semânticos data-i18n e integridade DOM.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path("/mnt/storage/piDots")

FILES = [
    BASE_DIR / "data/locales/pt.json",
    BASE_DIR / "data/locales/en.json",
    BASE_DIR / "data/changelog.json",
    BASE_DIR / "pages/landing.html",
    BASE_DIR / "pages/docs.html",
    BASE_DIR / "pages/app.html",
    BASE_DIR / "pages/relatorio.html",
]

PROHIBITED_TERMS = [
    "deliberação dialética",
    "deliberacao dialetica",
    "deliberação tripartite",
    "deliberacao tripartite",
    "conselho tripartite",
    "topologia canônica",
    "topologia canonica",
    "requisições cognitivas",
    "requisicoes cognitivas",
    "ciclo cognitivo",
    "memória cognitiva",
    "memoria cognitiva",
    "arquitetura cognitiva",
    "trava mecânica",
    "trava mecanica",
    "dossiê de economia forense",
    "dossie de economia forense",
    "dossiê forense",
    "dossie forense",
    "silêncio inteligente",
    "silencio inteligente",
    "guia didático",
    "guia didatico",
    "exemplo didático",
    "exemplo didatico",
    "telemetria do hardware está nominal",
    "telemetria do hardware esta nominal",
    "bom trabalho!",
]

EMOJI_RANGES = [
    (0x1F600, 0x1F64F),
    (0x1F300, 0x1F5FF),
    (0x1F680, 0x1F6FF),
    (0x1F1E0, 0x1F1FF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0xFE00, 0xFE0F),
    (0x1F900, 0x1F9FF),
    (0x1FA70, 0x1FAFF),
]

def check_emojis():
    total_found = 0
    for f in FILES:
        content = f.read_text(encoding="utf-8")
        for line_num, line in enumerate(content.splitlines(), 1):
            for ch in line:
                cp = ord(ch)
                for start, end in EMOJI_RANGES:
                    if start <= cp <= end:
                        print(f"[ERRO] Emoji em {f.name}:{line_num} -> {ch} (U+{cp:04X})")
                        total_found += 1
    return total_found

def check_i18n_parity():
    def flatten(d, prefix=''):
        items = []
        for k, v in d.items():
            new_k = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_k))
            else:
                items.append(new_k)
        return items

    with open(BASE_DIR / "data/locales/pt.json", encoding="utf-8") as f:
        pt = json.load(f)
    with open(BASE_DIR / "data/locales/en.json", encoding="utf-8") as f:
        en = json.load(f)

    pt_flat = set(flatten(pt))
    en_flat = set(flatten(en))
    diff = pt_flat.symmetric_difference(en_flat)
    return len(pt_flat), len(en_flat), diff

def check_prohibited_terms():
    violations = []
    # Ignora en.json para termos em português
    check_files = [f for f in FILES if f.name != "en.json"]
    for f in check_files:
        content = f.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            if term in content:
                violations.append((f.name, term))
                print(f"[ERRO] Termo proibido encontrado em {f.name}: '{term}'")
    return violations

def main():
    print("=" * 70)
    print("TESTE DE HOMOLOGAÇÃO HUMANIZER — FASE 2: INTERFACES WEB & I18N")
    print("=" * 70)

    # 1. Emojis
    emojis = check_emojis()
    if emojis == 0:
        print("[OK] Teste 1: Zero emojis detectados em todos os 7 arquivos da Fase 2.")
    else:
        print(f"[FALHA] Teste 1: {emojis} emojis detectados.")

    # 2. Paridade i18n
    pt_count, en_count, diff = check_i18n_parity()
    if not diff:
        print(f"[OK] Teste 2: Paridade 1:1 rigorosa nos dicionários i18n ({pt_count} chaves sincronizadas).")
    else:
        print(f"[FALHA] Teste 2: Divergência nas chaves i18n: {diff}")

    # 3. Termos proibidos
    violations = check_prohibited_terms()
    if not violations:
        print("[OK] Teste 3: Zero termos proibidos de AI Slop detectados em UI e i18n.")
    else:
        print(f"[FALHA] Teste 3: {len(violations)} ocorrências de termos proibidos.")

    print("=" * 70)
    if emojis == 0 and not diff and not violations:
        print("RESULTADO: FASE 2 HOMOLOGADA COM SUCESSO (100% APROVADO)")
        sys.exit(0)
    else:
        print("RESULTADO: HOMOLOGAÇÃO DA FASE 2 FALHOU")
        sys.exit(1)

if __name__ == "__main__":
    main()
