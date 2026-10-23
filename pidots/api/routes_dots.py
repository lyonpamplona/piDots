"""
Rotas REST para Gerenciamento de Dots, Memória Cognitiva em 3 Camadas e DotPacks do piDots.
"""

import json
import re
import uuid
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import settings
from ..storage.db import get_db
from ..storage.memory_manager import MemoryManager, ALLOWED_CORE_SECTIONS, DEFAULT_MAX_CHARS

router = APIRouter(tags=["Dots"])


class ImportDotPackPayload(BaseModel):
    pack: dict[str, Any]
    override_id: str | None = None


class CreateDotPayload(BaseModel):
    id: str | None = None
    name: str
    role: str = "Especialista Técnico"
    archetype: str = "general"
    avatar_stamp: str = "DOT"
    system_prompt: str
    model: str | None = None
    allowed_tools: list[str] | None = None


class UpdateDotPayload(BaseModel):
    name: str | None = None
    role: str | None = None
    archetype: str | None = None
    avatar_stamp: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    allowed_tools: list[str] | None = None
    is_active: int | None = None


class UpdateCoreMemoryPayload(BaseModel):
    content: str


class CreateArchivalMemoryPayload(BaseModel):
    content: str
    tags: list[str] | None = None
    deduplicate: bool = True


@router.get("/api/dots")
async def list_dots(core_only: bool = True):
    """Lista AI coworkers (Dots) registrados. Por padrão retorna o Squad Central enxuto."""
    async with get_db() as db:
        if core_only:
            cursor = await db.execute(
                """
                SELECT id, name, role, system_prompt, model, workspace_path,
                       is_active, archetype, avatar_stamp, allowed_tools_json, is_core
                FROM dots
                WHERE is_core = 1
                ORDER BY CASE id
                    WHEN 'dot-supervisor' THEN 1
                    WHEN 'dev-assistant' THEN 2
                    WHEN 'dot-muse' THEN 3
                    WHEN 'dot-auditor' THEN 4
                    ELSE 5
                END
                """
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, name, role, system_prompt, model, workspace_path,
                       is_active, archetype, avatar_stamp, allowed_tools_json, is_core
                FROM dots
                ORDER BY is_core DESC, name ASC
                """
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/api/dots/packs/catalog")
async def list_dot_packs_catalog():
    """Lista o catálogo comunitário oficial de Dot Packs v1.1 assinados com SHA-256 disponíveis em data/packs/."""
    packs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "packs"
    catalog: list[dict[str, Any]] = []
    if packs_dir.exists():
        for p_file in sorted(packs_dir.glob("*.json")):
            try:
                data = json.loads(p_file.read_text(encoding="utf-8"))
                dot_info = data.get("dot", {})
                catalog.append({
                    "pack_id": p_file.stem,
                    "filename": p_file.name,
                    "format": data.get("format", "DotPack"),
                    "version": data.get("version", "1.1"),
                    "sha256_checksum": data.get("sha256_checksum", ""),
                    "dot_id": dot_info.get("id", p_file.stem),
                    "name": dot_info.get("name", p_file.stem),
                    "role": dot_info.get("role", ""),
                    "archetype": dot_info.get("archetype", "general"),
                    "tools_count": len(dot_info.get("allowed_tools", [])),
                    "archival_facts_count": len(data.get("archival_memories", []))
                })
            except Exception:
                continue
    return {"packs": catalog, "count": len(catalog)}


@router.post("/api/dots/packs/install/{pack_id}")
async def install_official_dot_pack(pack_id: str):
    """Valida a assinatura SHA-256 e instala um Dot Pack oficial do catálogo data/packs/ no SQLite WAL."""
    from ..core.dot_pack import DotPackManager
    safe_id = re.sub(r"[^a-zA-Z0-9\-_]", "", pack_id)
    pack_path = Path(__file__).resolve().parent.parent.parent / "data" / "packs" / f"{safe_id}.json"
    if not pack_path.exists():
        raise HTTPException(status_code=404, detail=f"Dot Pack oficial '{safe_id}' não encontrado em data/packs/.")
    try:
        pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Manifesto JSON inválido: {exc}")

    result = await DotPackManager.import_dot_pack(pack_data=pack_data)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha na validação SHA-256 ou auditoria do pacote."))
    return result


@router.get("/api/dots/{dot_id}")
async def get_dot_detail(dot_id: str):
    """Retorna os metadados completos de um especialista Dot."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, name, role, system_prompt, model, workspace_path,
                   is_active, archetype, avatar_stamp, allowed_tools_json, is_core, created_at, updated_at
            FROM dots WHERE id = ?
            """,
            (dot_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado.")
        return dict(row)


@router.post("/api/dots")
async def create_dot_endpoint(payload: CreateDotPayload):
    """Cria e persiste um novo especialista Dot customizado no SQLite WAL (Padrão OpenDots)."""
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Nome do Dot não pode ser vazio.")

    raw_id = payload.id or f"dot-{re.sub(r'[^a-z0-9]+', '-', clean_name.lower()).strip('-')}"
    dot_id = re.sub(r"[^a-z0-9\-_]", "", raw_id.lower())[:48] or f"dot-{uuid.uuid4().hex[:8]}"
    stamp = (payload.avatar_stamp or clean_name[:3]).upper()[:4]
    model = (payload.model or settings.ai_model).strip()
    ws_path = str(Path(settings.workspaces_root) / dot_id)
    Path(ws_path).mkdir(parents=True, exist_ok=True)
    tools_json = json.dumps(payload.allowed_tools or [], ensure_ascii=False)

    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ?", (dot_id,))
        if await cur.fetchone():
            raise HTTPException(status_code=409, detail=f"Já existe um Dot com o identificador '{dot_id}'.")

        await db.execute(
            """
            INSERT INTO dots (
                id, name, role, system_prompt, model, workspace_path,
                archetype, avatar_stamp, allowed_tools_json, is_active, is_core
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (
                dot_id,
                clean_name,
                payload.role.strip(),
                payload.system_prompt.strip(),
                model,
                ws_path,
                payload.archetype.strip(),
                stamp,
                tools_json
            )
        )
        await db.commit()

    # Inicializa os blocos de Core Memory do novo Dot
    await MemoryManager.get_core_memory_blocks(dot_id=dot_id, default_persona=payload.system_prompt.strip())
    return await get_dot_detail(dot_id)


@router.put("/api/dots/{dot_id}")
async def update_dot_endpoint(dot_id: str, payload: UpdateDotPayload):
    """Atualiza as instruções, modelo, arquétipo e ferramentas permitidas de um especialista Dot."""
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM dots WHERE id = ?", (dot_id,))
        existing = await cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado.")

        row = dict(existing)
        new_name = payload.name.strip() if payload.name is not None else row["name"]
        new_role = payload.role.strip() if payload.role is not None else row["role"]
        new_arch = payload.archetype.strip() if payload.archetype is not None else row["archetype"]
        new_stamp = payload.avatar_stamp.strip().upper()[:4] if payload.avatar_stamp is not None else row["avatar_stamp"]
        new_prompt = payload.system_prompt.strip() if payload.system_prompt is not None else row["system_prompt"]
        new_model = payload.model.strip() if payload.model is not None else row["model"]
        new_tools = (
            json.dumps(payload.allowed_tools, ensure_ascii=False)
            if payload.allowed_tools is not None
            else row["allowed_tools_json"]
        )
        new_active = payload.is_active if payload.is_active is not None else row["is_active"]

        await db.execute(
            """
            UPDATE dots
            SET name = ?, role = ?, archetype = ?, avatar_stamp = ?,
                system_prompt = ?, model = ?, allowed_tools_json = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_name, new_role, new_arch, new_stamp, new_prompt, new_model, new_tools, new_active, dot_id)
        )
        await db.commit()

    return await get_dot_detail(dot_id)


@router.delete("/api/dots/{dot_id}")
async def delete_dot_endpoint(dot_id: str):
    """Remove um especialista Dot customizado (protegendo os 5 Core Dots contra exclusão)."""
    async with get_db() as db:
        cur = await db.execute("SELECT id, is_core FROM dots WHERE id = ?", (dot_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado.")
        if row["is_core"] == 1:
            raise HTTPException(status_code=400, detail="Especialistas Core de fábrica não podem ser excluídos.")

        await db.execute("DELETE FROM dots WHERE id = ?", (dot_id,))
        await db.commit()
    return {"status": "deleted", "dot_id": dot_id}


@router.get("/api/dots/{dot_id}/memory")
async def get_dot_memory_layers(dot_id: str, limit: int = 30):
    """Retorna as 3 camadas de memória do Dot (Core Memory + Archival Memory + Contagem)."""
    async with get_db() as db:
        cur = await db.execute("SELECT id, system_prompt FROM dots WHERE id = ?", (dot_id,))
        dot_row = await cur.fetchone()
        if not dot_row:
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado.")

        core_blocks = await MemoryManager.get_core_memory_blocks(
            dot_id=dot_id,
            default_persona=dot_row["system_prompt"]
        )

        cur_arch = await db.execute(
            """
            SELECT id, dot_id, content, tags_json, created_at
            FROM archival_memories WHERE dot_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (dot_id, max(1, min(limit, 100)))
        )
        arch_rows = await cur_arch.fetchall()
        archival_list = []
        for r in arch_rows:
            try:
                tags = json.loads(r["tags_json"]) if r["tags_json"] else []
            except Exception:
                tags = []
            archival_list.append({
                "id": r["id"],
                "dot_id": r["dot_id"],
                "content": r["content"],
                "tags": tags,
                "created_at": r["created_at"]
            })

    return {
        "dot_id": dot_id,
        "core_memory": core_blocks,
        "archival_memories": archival_list,
        "archival_count": len(archival_list)
    }


@router.put("/api/dots/{dot_id}/memory/{section}")
async def update_dot_core_memory_section(dot_id: str, section: str, payload: UpdateCoreMemoryPayload):
    """Atualiza diretamente uma seção da Core Memory ('persona', 'human', 'active_context') de um Dot."""
    sec_clean = section.strip().lower()
    if sec_clean not in ALLOWED_CORE_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Seção inválida '{section}'. Permitidas: {', '.join(ALLOWED_CORE_SECTIONS)}."
        )
    new_text = payload.content.strip()
    if len(new_text) > DEFAULT_MAX_CHARS:
        raise HTTPException(status_code=400, detail=f"Conteúdo excede o limite de {DEFAULT_MAX_CHARS} caracteres.")

    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO agent_core_memory_blocks (id, dot_id, block_name, content, max_chars, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(dot_id, block_name) DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(uuid.uuid4()), dot_id, sec_clean, new_text, DEFAULT_MAX_CHARS)
        )
        await db.commit()

    return {
        "success": True,
        "dot_id": dot_id,
        "section": sec_clean,
        "content": new_text,
        "length": len(new_text)
    }


@router.post("/api/dots/{dot_id}/memory/archival")
async def create_dot_archival_memory(dot_id: str, payload: CreateArchivalMemoryPayload):
    """Insere um novo registro na Archival Memory (com deduplicação semântica 64D)."""
    res = await MemoryManager.insert_archival_memory(
        dot_id=dot_id,
        content=payload.content,
        tags=payload.tags,
        deduplicate=payload.deduplicate
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Falha ao gravar memória arquivística."))
    return res


@router.get("/api/dots/{dot_id}/memory/search")
async def search_dot_archival_memory(dot_id: str, query: str, limit: int = 10):
    """Executa busca híbrida (FTS5 BM25 + Vetor 64D) na memória arquivística do Dot."""
    return await MemoryManager.search_archival_memory(dot_id=dot_id, query=query, limit=limit)


@router.delete("/api/dots/{dot_id}/memory/archival/{memory_id}")
async def delete_dot_archival_memory(dot_id: str, memory_id: str):
    """Remove um registro específico da Archival Memory de um Dot."""
    async with get_db() as db:
        cur = await db.execute(
            "DELETE FROM archival_memories WHERE id = ? AND dot_id = ?",
            (memory_id, dot_id)
        )
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de memória arquivística não encontrado.")
    return {"status": "deleted", "id": memory_id, "dot_id": dot_id}


@router.get("/api/dots/{dot_id}/export-pack")
async def export_dot_pack_endpoint(dot_id: str):
    """Exporta manifesto estruturado DotPack v1.0 com personas, core memory e arquivística."""
    from ..core.dot_pack import DotPackManager
    result = await DotPackManager.export_dot_pack(dot_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Dot não encontrado"))
    return JSONResponse(
        content=result["manifest"],
        headers={"Content-Disposition": f"attachment; filename=dotpack_{dot_id}.json"}
    )


@router.post("/api/dots/import-pack")
async def import_dot_pack_endpoint(payload: ImportDotPackPayload):
    """Importa e instancia um novo Dot no SQLite WAL a partir de manifesto DotPack."""
    from ..core.dot_pack import DotPackManager
    result = await DotPackManager.import_dot_pack(pack_data=payload.pack, override_id=payload.override_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao importar DotPack"))
    return result

