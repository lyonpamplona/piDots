"""
Módulo de Empacotamento, Exportação e Importação de Templates de Agentes (Dot Packs) para piDots.
Inspirado em padrões OpenDots e CopilotKit, permite serializar e restaurar personas, memórias primárias,
arquétipos e ferramentas permitidas em manifestos portáveis JSON.
"""

import os
import re
import json
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

from ..config import settings
from ..storage.db import get_db

logger = logging.getLogger("pidots.dot_pack")

DOT_PACK_FORMAT = "DotPack"
DOT_PACK_VERSION = "1.0"


class DotPackManager:
    """Gerencia a exportação e importação atômica de pacotes de Dots."""

    @classmethod
    async def export_dot_pack(cls, dot_id: str) -> dict[str, Any]:
        """
        Exporta a especificação completa de um Dot em formato padronizado DotPack v1.0.
        Inclui persona, arquétipo, ferramentas, blocos da Core Memory e memórias arquivísticas.
        """
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM dots WHERE id = ?", (dot_id,))
            dot_row = await cursor.fetchone()
            if not dot_row:
                return {"success": False, "error": f"Dot '{dot_id}' não encontrado para exportação."}

            dot_data = dict(dot_row)

            # Recupera blocos da Core Memory
            cursor = await db.execute(
                "SELECT block_name, content, max_chars FROM agent_core_memory_blocks WHERE dot_id = ?",
                (dot_id,)
            )
            core_rows = await cursor.fetchall()
            core_memory = {r["block_name"]: r["content"] for r in core_rows}

            # Recupera memórias arquivísticas
            cursor = await db.execute(
                "SELECT content, tags_json FROM archival_memories WHERE dot_id = ? ORDER BY created_at ASC",
                (dot_id,)
            )
            archival_rows = await cursor.fetchall()
            archival_list = []
            for ar in archival_rows:
                tags = json.loads(ar["tags_json"]) if ar["tags_json"] else []
                archival_list.append({"content": ar["content"], "tags": tags})

        # Processa catálogo de ferramentas
        tools_raw = dot_data.get("allowed_tools_json")
        try:
            allowed_tools = json.loads(tools_raw) if isinstance(tools_raw, str) else (tools_raw or [])
        except Exception:
            allowed_tools = []

        manifest = {
            "format": DOT_PACK_FORMAT,
            "version": DOT_PACK_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "dot": {
                "id": dot_data["id"],
                "name": dot_data["name"],
                "role": dot_data.get("role", "Operador de Borda"),
                "archetype": dot_data.get("archetype", "general"),
                "avatar_stamp": dot_data.get("avatar_stamp", "DOT"),
                "system_prompt": dot_data.get("system_prompt", ""),
                "model": dot_data.get("model", "qwen3.8-27b"),
                "allowed_tools": allowed_tools
            },
            "core_memory": core_memory,
            "archival_memories": archival_list
        }

        logger.info("DotPack exportado para o Dot '%s' (Memórias Arquivísticas: %d).", dot_id, len(archival_list))
        return {
            "success": True,
            "dot_id": dot_id,
            "manifest": manifest
        }

    @classmethod
    async def import_dot_pack(
        cls,
        pack_data: dict[str, Any],
        override_id: str | None = None
    ) -> dict[str, Any]:
        """
        Importa e restaura atomicamente um Dot a partir de um manifesto DotPack.
        Cria o registro do Dot, seu workspace físico, blocos de Core Memory e memórias arquivísticas.
        """
        if not isinstance(pack_data, dict):
            return {"success": False, "error": "Estrutura do manifesto DotPack inválida."}

        fmt = pack_data.get("format")
        if fmt != DOT_PACK_FORMAT:
            return {"success": False, "error": f"Formato inválido '{fmt}'. Esperado '{DOT_PACK_FORMAT}'."}

        dot_info = pack_data.get("dot", {})
        if not dot_info.get("name"):
            return {"success": False, "error": "Campo 'name' obrigatório no manifesto do Dot."}

        raw_dot_id = override_id or dot_info.get("id") or f"dot-{uuid.uuid4().hex[:6]}"
        target_dot_id = re.sub(r"[^\w\-_.]", "_", str(raw_dot_id).strip()).strip(".") or f"dot-{uuid.uuid4().hex[:6]}"
        name = dot_info["name"]
        role = dot_info.get("role", "Operador de Borda")
        archetype = dot_info.get("archetype", "general")
        avatar_stamp = dot_info.get("avatar_stamp", "DOT")
        system_prompt = dot_info.get("system_prompt", "")
        model = dot_info.get("model", "qwen3.8-27b")
        allowed_tools = dot_info.get("allowed_tools", [])

        # Garante criação segura do workspace
        workspaces_root = os.path.realpath(settings.workspaces_root)
        workspace_path = os.path.realpath(os.path.join(workspaces_root, target_dot_id))
        if os.path.commonpath([workspaces_root, workspace_path]) != workspaces_root:
            return {"success": False, "error": "Identificador de Dot inválido."}
        os.makedirs(workspace_path, exist_ok=True)

        async with get_db() as db:
            # 1. Cadastra ou atualiza o Dot
            await db.execute(
                """
                INSERT INTO dots (id, name, role, system_prompt, model, workspace_path, archetype, avatar_stamp, allowed_tools_json, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    system_prompt = excluded.system_prompt,
                    model = excluded.model,
                    archetype = excluded.archetype,
                    avatar_stamp = excluded.avatar_stamp,
                    allowed_tools_json = excluded.allowed_tools_json,
                    is_active = 1
                """,
                (
                    target_dot_id, name, role, system_prompt, model,
                    workspace_path, archetype, avatar_stamp, json.dumps(allowed_tools, ensure_ascii=False)
                )
            )

            # 2. Restaura blocos de Core Memory
            core_mem = pack_data.get("core_memory", {})
            for block_name, content in core_mem.items():
                block_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO agent_core_memory_blocks (id, dot_id, block_name, content, max_chars, updated_at)
                    VALUES (?, ?, ?, ?, 2000, CURRENT_TIMESTAMP)
                    ON CONFLICT(dot_id, block_name) DO UPDATE SET
                        content = excluded.content,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (block_id, target_dot_id, block_name, content)
                )

            # 3. Restaura memórias arquivísticas sem duplicar entradas existentes
            from ..storage.memory_manager import compute_compact_embedding
            archival_list = pack_data.get("archival_memories", [])
            for mem in archival_list:
                m_content = mem.get("content", "").strip()
                if not m_content:
                    continue
                cur_dup = await db.execute(
                    "SELECT id FROM archival_memories WHERE dot_id = ? AND content = ? LIMIT 1",
                    (target_dot_id, m_content)
                )
                if await cur_dup.fetchone():
                    continue
                m_tags = mem.get("tags", [])
                m_id = str(uuid.uuid4())
                m_vec = compute_compact_embedding(m_content, dim=64)

                await db.execute(
                    """
                    INSERT INTO archival_memories (id, dot_id, content, tags_json, vector_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (m_id, target_dot_id, m_content, json.dumps(m_tags, ensure_ascii=False), json.dumps(m_vec))
                )

            await db.commit()

        logger.info(
            "DotPack importado com sucesso: Dot '%s' (Nome: '%s', Arquétipo: '%s', Memórias: %d).",
            target_dot_id, name, archetype, len(archival_list)
        )
        return {
            "success": True,
            "dot_id": target_dot_id,
            "name": name,
            "archetype": archetype,
            "core_blocks_restored": len(core_mem),
            "archival_memories_restored": len(archival_list)
        }
