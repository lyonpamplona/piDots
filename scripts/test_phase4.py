"""
Script de validação e teste empírico da Fase 4 do piDots.
Testa Spaces (documentos), versionamento com diffs, memória vetorial e exportação ZIP.
"""

import asyncio
import sys
import io
import zipfile
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.spaces_manager import SpacesManager
from pidots.storage.vector_store import VectorStore


async def main():
    print("=== [piDots] Teste e Validação da Fase 4 no Raspberry Pi 4B ===")
    await init_edge_database()
    dot_id = "dot-dev-core"

    # Limpa qualquer registro prévio de teste para garantir idempotência
    async with get_db() as db:
        await db.execute("DELETE FROM document_embeddings WHERE space_id IN (SELECT id FROM spaces WHERE filename = 'architecture_spec_phase4.md')")
        await db.execute("DELETE FROM space_revisions WHERE space_id IN (SELECT id FROM spaces WHERE filename = 'architecture_spec_phase4.md')")
        await db.execute("DELETE FROM spaces WHERE filename = 'architecture_spec_phase4.md'")
        await db.commit()

    # 1. Criação Inicial de Documento em Spaces (Versão 1)
    print("[1/5] Criando documento inicial no Space (Versão 1)...")
    doc_v1 = "# piDots Especificação v1\n\nMotor de IA leve para Raspberry Pi 4B.\nConsumo alvo: 250MB RAM.\n"
    res_v1 = await SpacesManager.save_document(
        dot_id=dot_id,
        filename="architecture_spec_phase4.md",
        content=doc_v1,
        title="Especificação de Arquitetura piDots"
    )
    print(f"      Criado: {res_v1['filename']} (Versão: {res_v1['version']})")
    assert res_v1["version"] == 1, "A versão inicial deveria ser 1!"

    # 2. Atualização Incremental e Cálculo de Diff (Versão 2)
    print("[2/5] Atualizando documento com cálculo automático de Diff (Versão 2)...")
    doc_v2 = "# piDots Especificação v2\n\nMotor de IA leve para Raspberry Pi 4B.\nConsumo alvo: 180MB RAM.\n\n## Seção Nova\nAdicionado suporte a SQLite WAL e tmpfs.\n"
    res_v2 = await SpacesManager.save_document(
        dot_id=dot_id,
        filename="architecture_spec_phase4.md",
        content=doc_v2
    )
    print(f"      Atualizado para versão: {res_v2['version']}")
    print(f"      Diff gerado:\n{res_v2['diff_summary'][:150]}...")
    assert res_v2["version"] == 2, "A versão deveria ter incrementado para 2!"
    assert "-Consumo alvo: 250MB RAM." in res_v2["diff_summary"], "Diff unificado não detectou linha removida!"
    assert "+Consumo alvo: 180MB RAM." in res_v2["diff_summary"], "Diff unificado não detectou linha adicionada!"

    # 3. Consulta ao Histórico de Revisões
    print("[3/5] Consultando histórico de revisões em space_revisions...")
    revisions = await SpacesManager.get_revisions(res_v1["space_id"])
    print(f"      Total de revisões registradas: {len(revisions)}")
    assert len(revisions) >= 2, "Deveriam existir pelo menos 2 revisões registradas!"

    # 4. Memória Semântica Vetorial Edge (Indexação e Busca KNN)
    print("[4/5] Testando motor de busca semântica vetorial Edge (VectorStore)...")
    # Salva documento específico sobre banco de dados
    doc_db = "# Calibração de SQLite em Flash MicroSD\n\nDiretrizes para evitar queima de células flash:\n1. Usar PRAGMA journal_mode = WAL;\n2. PRAGMA synchronous = NORMAL;\n3. Evitar fsync contínuo em Raspberry Pi 4B.\n"
    await SpacesManager.save_document(
        dot_id=dot_id,
        filename="sqlite_guide.md",
        content=doc_db,
        title="Guia de Otimização SQLite WAL"
    )

    # Busca semântica por conceito
    query = "Como evitar desgaste do cartão de memória flash com SQLite WAL?"
    search_results = await VectorStore.search(query=query, top_k=2)
    print(f"      Resultados encontrados para '{query}': {len(search_results)}")
    for s in search_results:
        print(f"      - [{s['score']}] {s['filename']}: {s['chunk_text'][:60]}...")

    assert len(search_results) > 0, "A busca semântica deveria retornar resultados!"
    filenames_found = [doc["filename"] for doc in search_results]
    assert any("sqlite_guide.md" in fn for fn in filenames_found), "O guia de SQLite deveria estar entre os resultados mais relevantes!"

    # 5. Exportação do Workspace em ZIP
    print("[5/5] Testando exportação compactada do Workspace em ZIP...")
    zip_bytes = await SpacesManager.export_workspace_zip(dot_id)
    print(f"      Tamanho do arquivo ZIP gerado: {len(zip_bytes)} bytes")
    assert len(zip_bytes) > 0, "O arquivo ZIP não pode estar vazio!"

    # Valida estrutura interna do ZIP
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        namelist = z.namelist()
        print(f"      Arquivos empacotados no ZIP: {namelist}")
        assert "architecture_spec.md" in namelist or any("architecture_spec.md" in n for n in namelist), "Arquivo principal ausente no ZIP!"

    print("\n=== [SUCESSO] Fase 4 validada com 100% de êxito! Spaces, Diffs e Memória Vetorial Operacionais! ===")


if __name__ == "__main__":
    asyncio.run(main())
