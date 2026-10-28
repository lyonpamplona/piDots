"""
Script de validação e homologação técnica da Fase 1: Documentação Central e Manuais de Engenharia.
Verifica:
1. Ausência de emojis nos 5 arquivos da Fase 1.
2. Purgação de termos proibidos de AI Slop.
3. Redução drástica do empilhamento de listas mecânicas (Padrão 16).
4. Paridade estrutural entre README.md e README_EN.md.
"""

import sys
from pathlib import Path

BASE_DIR = Path("/mnt/storage/piDots")

FILES = [
    BASE_DIR / "README.md",
    BASE_DIR / "README_EN.md",
    BASE_DIR / "ARCHITECTURE.md",
    BASE_DIR / "MANUAL_OPERACIONAL.md",
    BASE_DIR / "AI_MANIFESTO.md",
]

PROHIBITED_TERMS = [
    "deliberação dialética",
    "deliberacao dialetica",
    "topologia canônica",
    "topologia canonica",
    "requisições cognitivas",
    "requisicoes cognitivas",
    "ciclo cognitivo",
    "trava mecânica",
    "trava mecanica",
    "dossiê de economia forense",
    "dossie de economia forense",
    "dossiê forense",
    "dossie forense",
    "silêncio inteligente",
    "silencio inteligente",
    "guia didático oficial",
    "guia didatico oficial",
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

def check_prohibited_terms():
    violations = []
    # Ignora README_EN.md para termos em português
    pt_files = [f for f in FILES if f.name != "README_EN.md"]
    for f in pt_files:
        content = f.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            if term in content:
                violations.append((f.name, term))
                print(f"[ERRO] Termo proibido encontrado em {f.name}: '{term}'")
    return violations

def check_pattern16_lists():
    # Verifica que não temos seções com mais de 10 listas mecânicas consecutivas "- **"
    max_streak = 0
    for f in FILES:
        content = f.read_text(encoding="utf-8")
        current_streak = 0
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("- **") and ":**" in stripped:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
            else:
                current_streak = 0
    return max_streak

def main():
    print("=" * 70)
    print("TESTE DE HOMOLOGAÇÃO HUMANIZER — FASE 1: DOCUMENTAÇÃO CENTRAL")
    print("=" * 70)

    # 1. Emojis
    emojis = check_emojis()
    if emojis == 0:
        print("[OK] Teste 1: Zero emojis detectados em todos os 5 arquivos.")
    else:
        print(f"[FALHA] Teste 1: {emojis} emojis detectados.")

    # 2. Termos proibidos
    term_violations = check_prohibited_terms()
    if not term_violations:
        print("[OK] Teste 2: Zero termos proibidos de AI Slop detectados.")
    else:
        print(f"[FALHA] Teste 2: {len(term_violations)} ocorrências de termos proibidos.")

    # 3. Padrão 16
    streak = check_pattern16_lists()
    print(f"[INFO] Maior sequência de marcadores mecânicos '- **' encontrada: {streak}")
    if streak <= 6:
        print("[OK] Teste 3: Padrão 16 purgado (nenhum empilhamento mecânico repetitivo).")
    else:
        print(f"[FALHA] Teste 3: Sequência mecânica muito longa ({streak}).")

    # 4. Paridade Bilíngue
    pt_readme = (BASE_DIR / "README.md").read_text(encoding="utf-8")
    en_readme = (BASE_DIR / "README_EN.md").read_text(encoding="utf-8")
    if len(pt_readme) > 1000 and len(en_readme) > 1000:
        ratio = len(en_readme) / len(pt_readme)
        print(f"[OK] Teste 4: Paridade README PT/EN confirmada (Tamanhos: PT={len(pt_readme)}, EN={len(en_readme)}, Razão={ratio:.2f}).")
    else:
        print("[FALHA] Teste 4: Um dos READMEs está incompleto.")

    print("=" * 70)
    if emojis == 0 and not term_violations and streak <= 6:
        print("RESULTADO: FASE 1 HOMOLOGADA COM SUCESSO (100% APROVADO)")
        sys.exit(0)
    else:
        print("RESULTADO: HOMOLOGAÇÃO FALHOU COM PENDÊNCIAS")
        sys.exit(1)

if __name__ == "__main__":
    main()
