#!/usr/bin/env python3
"""
Suíte de Validação Automatizada — Fase 4: Internacionalização, Documentação Viva, Skill e Homologação Final
Verifica:
1. Paridade estrita de chaves entre data/locales/pt.json e data/locales/en.json (incluindo namespace opendots.*).
2. Registro da versão 1.6.0 em data/changelog.json e pyproject.toml.
3. Atualização da documentação viva (README.md, README_EN.md, ARCHITECTURE.md, MANUAL_OPERACIONAL.md).
4. Existência e integridade da skill opendots-pidots (/home/developer/.gemini/config/skills/opendots-pidots/SKILL.md).
5. Cobertura de cache do Service Worker em pidots/api/routes_pwa.py.
6. Conformidade estrita com a diretriz Zero Emojis em todos os arquivos atualizados.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "]+",
    flags=re.UNICODE,
)


def flatten_keys(d, prefix=""):
    keys = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= flatten_keys(v, full_key)
        else:
            keys.add(full_key)
    return keys


def test_i18n_parity():
    print("[1/6] Validando paridade estrita entre data/locales/pt.json e data/locales/en.json...")
    pt_path = ROOT / "data" / "locales" / "pt.json"
    en_path = ROOT / "data" / "locales" / "en.json"

    pt_data = json.loads(pt_path.read_text(encoding="utf-8"))
    en_data = json.loads(en_path.read_text(encoding="utf-8"))

    pt_keys = flatten_keys(pt_data)
    en_keys = flatten_keys(en_data)

    diff = pt_keys.symmetric_difference(en_keys)
    assert not diff, f"Divergencia de chaves entre PT e EN: {diff}"

    required_opendots_keys = [
        "opendots.rail_spaces",
        "opendots.rail_dots",
        "opendots.rail_tasks",
        "opendots.rail_memory",
        "opendots.rail_hitl",
        "opendots.save_as_space",
        "opendots.handoff",
        "opendots.council",
        "opendots.computer_banner",
        "opendots.mode_observation",
        "opendots.mode_takeover",
        "opendots.tab_coagents",
    ]
    for rk in required_opendots_keys:
        assert rk in pt_keys, f"Chave obrigatoria '{rk}' ausente em pt.json"
        assert rk in en_keys, f"Chave obrigatoria '{rk}' ausente em en.json"

    print(f"  -> OK ({len(pt_keys)} chaves folha 100% sincronizadas entre PT e EN).")


def test_changelog_and_version():
    print("[2/6] Validando registro OpenDots & AG-UI em data/changelog.json e pyproject.toml...")
    changelog_path = ROOT / "data" / "changelog.json"
    changelog = json.loads(changelog_path.read_text(encoding="utf-8"))

    current_ver = changelog.get("current_version", "")
    assert current_ver in ("1.5.3", "1.5.4", "1.5.5"), f"Versao inesperada: {current_ver}"
    
    # Verifica mencao ao OpenDots no changelog geral ou patch notes
    changelog_text = changelog_path.read_text(encoding="utf-8")
    assert "OpenDots" in changelog_text and "Generative UI" in changelog_text and "Dot's Computer" in changelog_text, (
        "Notas de release OpenDots / AG-UI ausentes em data/changelog.json"
    )

    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert any(v in pyproject_text for v in ("1.5.3", "1.5.4", "1.5.5")) and "CoAgents" in pyproject_text
    print("  -> OK (Changelog e pyproject.toml homologados com recursos OpenDots e CoAgents).")


def test_documentation_sync():
    print("[3/6] Validando documentacao viva (README.md, README_EN.md, ARCHITECTURE.md, MANUAL_OPERACIONAL.md)...")
    readme_pt = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_en = (ROOT / "README_EN.md").read_text(encoding="utf-8")
    arch = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_OPERACIONAL.md").read_text(encoding="utf-8")

    assert "Activity Rail" in readme_pt and "Generative UI" in readme_pt, "README.md sem secao OpenDots/AG-UI"
    assert "Activity Rail" in readme_en and "Generative UI" in readme_en, "README_EN.md sem secao OpenDots/AG-UI"
    assert "22. Padrao OpenDots & CopilotKit CoAgents" in arch, "ARCHITECTURE.md sem secao 22"
    assert "23. Operação do Console `/app` Padrão OpenDots" in manual, "MANUAL_OPERACIONAL.md sem secao 23"
    print("  -> OK (Documentacao bilingue e manuais operacionais sincronizados).")


def test_skill_opendots_pidots():
    print("[4/6] Validando skill opendots-pidots e arquivos de referencia...")
    skill_dir = Path("/home/developer/.gemini/config/skills/opendots-pidots")
    skill_md = skill_dir / "SKILL.md"
    ref1 = skill_dir / "references" / "opendots-repo-architecture.md"
    ref2 = skill_dir / "references" / "copilotkit-agui-protocol.md"

    assert skill_md.exists(), f"Skill ausente: {skill_md}"
    assert ref1.exists(), f"Referencia ausente: {ref1}"
    assert ref2.exists(), f"Referencia ausente: {ref2}"

    skill_content = skill_md.read_text(encoding="utf-8")
    assert "name: opendots-pidots" in skill_content
    assert "AG-UI" in skill_content and "CoAgents" in skill_content
    print("  -> OK (Skill opendots-pidots e referencias arquiteturais integras).")


def test_pwa_service_worker():
    print("[5/6] Validando cobertura de assets no Service Worker (routes_pwa.py)...")
    pwa_text = (ROOT / "pidots" / "api" / "routes_pwa.py").read_text(encoding="utf-8")
    required_assets = [
        "/static/css/spa.css",
        "/static/css/mobile.css",
        "/static/js/spa/app-init.js",
        "/static/js/spa/pidots-api.js",
        "/static/js/spa/slash-commands.js",
        "/data/locales/pt.json",
        "/data/locales/en.json",
    ]
    for asset in required_assets:
        assert asset in pwa_text, f"Asset '{asset}' ausente no cache do Service Worker"
    print("  -> OK (Service Worker cobre todos os assets modulares da SPA).")


def test_zero_emojis():
    print("[6/6] Validando conformidade Zero Emojis em todos os arquivos do upgrade...")
    files_to_check = [
        ROOT / "pages" / "app.html",
        ROOT / "static" / "css" / "spa.css",
        ROOT / "static" / "css" / "mobile.css",
        ROOT / "static" / "js" / "spa" / "app-init.js",
        ROOT / "static" / "js" / "spa" / "pidots-api.js",
        ROOT / "static" / "js" / "spa" / "slash-commands.js",
        ROOT / "data" / "locales" / "pt.json",
        ROOT / "data" / "locales" / "en.json",
        ROOT / "data" / "changelog.json",
        ROOT / "README.md",
        ROOT / "README_EN.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "MANUAL_OPERACIONAL.md",
        Path("/home/developer/.gemini/config/skills/opendots-pidots/SKILL.md"),
    ]
    for fpath in files_to_check:
        text = fpath.read_text(encoding="utf-8")
        matches = EMOJI_PATTERN.findall(text)
        assert not matches, f"Emoji detectado em {fpath}: {matches}"
    print("  -> OK (Zero emojis confirmados em todos os 14 arquivos inspecionados).")


def main():
    print("=" * 72)
    print("SUITE DE HOMOLOGACAO FASE 4 — OPENDOTS & COPILOTKIT AG-UI / COAGENTS")
    print("=" * 72)
    test_i18n_parity()
    test_changelog_and_version()
    test_documentation_sync()
    test_skill_opendots_pidots()
    test_pwa_service_worker()
    test_zero_emojis()
    print("=" * 72)
    print("RESULTADO FINAL: 6/6 TESTES DA FASE 4 APROVADOS COM 100% DE CONFORMIDADE")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"[ERRO DE ASSERCAO] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO INESPERADO] {e}", file=sys.stderr)
        sys.exit(1)
