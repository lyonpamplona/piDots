"""
Teste e Validação da Fase 4: Shared Knowledge Space e Templates de Agentes (Dot Packs).
Homologa o espaço de anotações e conhecimento compartilhado entre bots na mesma thread
e o empacotamento, exportação e importação portável de Dots (Dot Packs v1.0) no piDots.
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timezone


import sys
from pathlib import Path

# Adiciona o diretorio raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.shared_space import SharedSpaceManager
from pidots.core.dot_pack import DotPackManager
from pidots.tools.registry import registry
from pidots.storage.memory_manager import MemoryManager


async def run_phase12_tests():
    print("=== [piDots] Teste e Validação da Fase 4: Shared Knowledge Space & Dot Packs ===")

    # 1. Inicialização do SQLite WAL
    print("[1/5] Inicializando banco SQLite WAL e verificando esquemas de shared_space...")
    await init_edge_database()

    test_thread = f"thread-space-{uuid.uuid4().hex[:6]}"
    dot_author_1 = f"dot-auth1-{uuid.uuid4().hex[:4]}"
    dot_author_2 = f"dot-auth2-{uuid.uuid4().hex[:4]}"

    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, 'Dot Autor 1', 'Arquiteto', 'Prompt 1', 'test-model', '/tmp', 'general'),
                   (?, 'Dot Autor 2', 'Segurança', 'Prompt 2', 'test-model', '/tmp', 'grok')
            """,
            (dot_author_1, dot_author_2)
        )
        await db.execute("INSERT INTO threads (id, dot_id, title) VALUES (?, ?, 'Sessão Shared Space')", (test_thread, dot_author_1))
        await db.commit()

    print(f"      Ambiente de teste configurado: Thread '{test_thread}', Autores: @{dot_author_1} e @{dot_author_2}.")

    # 2. Testando SharedSpaceManager (Escrita, Leitura e Atualização Idempotente)
    print("[2/5] Testando SharedSpaceManager: gravação, sobrescrita atômica e leitura...")
    # Grava nota 1
    w1 = await SharedSpaceManager.write_note(
        thread_id=test_thread,
        dot_id=dot_author_1,
        topic_key="arquitetura_banco",
        content="SQLite em modo WAL com mmap_size configurado para 256MB e cache_size de -64000."
    )
    assert w1["success"] is True, f"Falha na gravação da nota 1: {w1}"

    # Grava nota 2
    w2 = await SharedSpaceManager.write_note(
        thread_id=test_thread,
        dot_id=dot_author_2,
        topic_key="regras_segurança",
        content="Comandos shell perigosos como 'rm -rf' e 'reboot' exigem aprovação explícita via HITL."
    )
    assert w2["success"] is True

    # Atualiza nota 1 por outro autor (sobrescrita colaborativa)
    w1_updated = await SharedSpaceManager.write_note(
        thread_id=test_thread,
        dot_id=dot_author_2,
        topic_key="arquitetura_banco",
        content="SQLite em modo WAL com mmap_size=256MB e rotina periódica de checkpoint a cada 900 segundos."
    )
    assert w1_updated["success"] is True

    # Lê nota atualizada
    read_note = await SharedSpaceManager.read_note(thread_id=test_thread, topic_key="arquitetura_banco")
    assert read_note["found"] is True
    assert "checkpoint a cada 900 segundos" in read_note["content"]
    assert read_note["author_dot_id"] == dot_author_2
    print("      Sobrescrita colaborativa validada: novo autor e conteúdo atualizados com sucesso.")

    # Lista notas
    all_notes = await SharedSpaceManager.list_notes(thread_id=test_thread)
    assert len(all_notes) == 2, f"Esperado 2 tópicos, obtido {len(all_notes)}"
    topic_keys = [n["topic_key"] for n in all_notes]
    assert "arquitetura_banco" in topic_keys and "regras_segurança" in topic_keys
    print(f"      Listagem de notas confirmada: {len(all_notes)} tópicos recuperados.")

    # Formata prompt XML in-context
    xml_prompt = await SharedSpaceManager.format_shared_space_prompt(thread_id=test_thread)
    assert "<shared_knowledge_space>" in xml_prompt
    assert "arquitetura_banco" in xml_prompt
    assert f"@{dot_author_2}" in xml_prompt
    print("      Bloco XML de conhecimento compartilhado formatado perfeitamente para injeção in-context.")

    # 3. Testando Ferramentas nativas do ToolRegistry (shared_space_write e shared_space_read)
    print("[3/5] Testando ferramentas nativas 'shared_space_write' e 'shared_space_read'...")
    tw_res = await registry.execute_tool(
        name="shared_space_write",
        arguments={"topic_key": "telemetria_edge", "content": "Temperatura do SoC Broadcom monitorada abaixo de 72 graus."},
        dot_id=dot_author_1,
        thread_id=test_thread
    )
    assert tw_res.get("success") is True, f"Falha na ferramenta shared_space_write: {tw_res}"

    tr_single = await registry.execute_tool(
        name="shared_space_read",
        arguments={"topic_key": "telemetria_edge"},
        thread_id=test_thread
    )
    assert tr_single.get("found") is True
    assert "Broadcom" in tr_single.get("content", "")

    tr_all = await registry.execute_tool(
        name="shared_space_read",
        arguments={},
        thread_id=test_thread
    )
    assert tr_all.get("count", 0) == 3
    print("      Ferramentas de shared_space integradas e operacionais no ToolRegistry com 100% de sucesso.")

    # 4. Testando Exportação de Dot Pack (Manifesto DotPack v1.0)
    print("[4/5] Testando exportação de Dot Pack completo (DotPackManager.export_dot_pack)...")
    # Configura Core Memory e Archival Memory prévia no autor 1 para testar exportação completa
    await MemoryManager.append_core_memory(dot_id=dot_author_1, section="persona", content="Especialista em firmware e barramentos.")
    await MemoryManager.insert_archival_memory(dot_id=dot_author_1, content="Manual de pinagem GPIO do Raspberry Pi 4B.", tags=["gpio", "hardware"])

    export_res = await DotPackManager.export_dot_pack(dot_id=dot_author_1)
    assert export_res.get("success") is True, f"Falha ao exportar DotPack: {export_res}"
    manifest = export_res["manifest"]

    assert manifest["format"] == "DotPack"
    assert manifest["version"] == "1.0"
    assert manifest["dot"]["id"] == dot_author_1
    assert "persona" in manifest["core_memory"]
    assert len(manifest["archival_memories"]) >= 1
    print(f"      Manifesto DotPack exportado com sucesso: {len(manifest['core_memory'])} blocos core e {len(manifest['archival_memories'])} memórias duradouras.")

    # 5. Testando Importação Atômica de Dot Pack
    print("[5/5] Testando importação e instanciação atômica de novo Dot via DotPack (import_dot_pack)...")
    new_dot_id = f"dot-imported-{uuid.uuid4().hex[:6]}"
    sample_pack = {
        "format": "DotPack",
        "version": "1.0",
        "dot": {
            "name": "Especialista Edge IoT",
            "role": "Engenheiro de Protocolos e Sensores",
            "archetype": "grok",
            "avatar_stamp": "[IOT]",
            "system_prompt": "Você é um especialista em sensores I2C, SPI e barramento GPIO no Raspberry Pi 4B.",
            "model": "test-model",
            "allowed_tools": ["execute_shell_command", "workspace_read_file", "workspace_write_file"]
        },
        "core_memory": {
            "persona": "Engenheiro de automação e instrumentação industrial.",
            "human": "Operador responsável pelo laboratório de hardware.",
            "active_context": "Calibração dos sensores de temperatura I2C."
        },
        "archival_memories": [
            {
                "content": "Protocolo I2C opera na porta /dev/i2c-1 com endereços hexadecimais padrão de 7 bits no Linux ARM64.",
                "tags": ["i2c", "linux", "hardware"]
            },
            {
                "content": "Diretrizes de proteção contra ruídos no barramento SPI em cabos longos.",
                "tags": ["spi", "hardware"]
            }
        ]
    }

    import_res = await DotPackManager.import_dot_pack(pack_data=sample_pack, override_id=new_dot_id)
    assert import_res.get("success") is True, f"Falha ao importar DotPack: {import_res}"
    assert import_res["dot_id"] == new_dot_id
    assert import_res["core_blocks_restored"] == 3
    assert import_res["archival_memories_restored"] == 2

    # Verificando se o Dot foi cadastrado e opera no SQLite WAL
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM dots WHERE id = ?", (new_dot_id,))
        imported_dot = await cursor.fetchone()
        assert imported_dot is not None
        assert imported_dot["archetype"] == "grok"
        assert imported_dot["avatar_stamp"] == "[IOT]"

        cursor = await db.execute("SELECT block_name, content FROM agent_core_memory_blocks WHERE dot_id = ?", (new_dot_id,))
        restored_core = {r["block_name"]: r["content"] for r in await cursor.fetchall()}
        assert "sensores de temperatura I2C" in restored_core["active_context"]

    # Busca híbrida FTS5 nas memórias arquivísticas importadas
    search_res = await MemoryManager.search_archival_memory(dot_id=new_dot_id, query="endereços hexadecimais do barramento I2C")
    assert len(search_res) > 0, "Memórias importadas não foram localizadas na busca híbrida FTS5."
    assert "i2c-1" in search_res[0]["content"]
    print(f"      DotPack importado e operacional: Dot '@{new_dot_id}' homologado com busca híbrida FTS5 ativa!")

    print("\n=== [SUCESSO TOTAL] Fase 4 (Shared Knowledge Space & Dot Packs) Homologada com 100% de Êxito! ===")


if __name__ == "__main__":
    asyncio.run(run_phase12_tests())
