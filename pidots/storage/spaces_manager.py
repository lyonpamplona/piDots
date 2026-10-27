"""
Gerenciador de Spaces (Biblioteca de Artefatos) com Versionamento Incremental e Diffs.
"""

import os
import io
import uuid
import asyncio
import zipfile
import difflib
import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from .db import get_db
from .vector_store import VectorStore
from ..tools.file_ops import FileManager
from ..config import settings

logger = logging.getLogger("pidots.storage.spaces")


class SpacesManager:
    """Orquestra o ciclo de vida, versionamento e exportação de documentos em Spaces."""

    @classmethod
    async def save_document(
        cls,
        dot_id: str,
        filename: str,
        content: str,
        title: str | None = None
    ) -> dict[str, Any]:
        """
        Salva ou atualiza um documento no Space.
        Calcula diff contra versão anterior e indexa na memória vetorial.
        """
        # Validação prévia estrita contra Path Traversal antes de comitar no banco
        FileManager._get_safe_path(dot_id, filename)

        doc_title = title or filename
        diff_summary = ""

        async with get_db() as db:
            # Garante que o Dot exista de forma idempotente para cumprir Foreign Key
            target_ws = str(Path(settings.workspaces_root) / dot_id)
            await db.execute(
                """
                INSERT OR IGNORE INTO dots (
                    id, name, role, system_prompt, model, workspace_path
                ) VALUES (?, ?, 'AI Coworker', 'Assistente técnico.', ?, ?)
                """,
                (dot_id, dot_id, settings.ai_model, target_ws)
            )

            # Verifica se já existe documento com mesmo filename para o Dot
            cursor = await db.execute(
                "SELECT id, content, version FROM spaces WHERE dot_id = ? AND filename = ?",
                (dot_id, filename)
            )
            existing = await cursor.fetchone()

            if existing:
                space_id = existing["id"]
                old_content = existing["content"]
                new_version = existing["version"] + 1

                # Calcula diff unificado linha a linha
                diff_lines = list(difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"{filename} (v{existing['version']})",
                    tofile=f"{filename} (v{new_version})"
                ))
                diff_summary = "".join(diff_lines) if diff_lines else "Sem alterações textuais."

                # Atualiza documento principal
                now = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    """
                    UPDATE spaces
                    SET content = ?, version = ?, title = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (content, new_version, doc_title, now, space_id)
                )

                # Salva nova revisão no histórico
                rev_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO space_revisions (id, space_id, version, diff_summary, content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rev_id, space_id, new_version, diff_summary, content)
                )
            else:
                # Documento novo (Versão 1)
                space_id = str(uuid.uuid4())
                new_version = 1
                diff_summary = "Criação inicial do documento (Versão 1)."

                await db.execute(
                    """
                    INSERT INTO spaces (id, dot_id, filename, title, content, version)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (space_id, dot_id, filename, doc_title, content)
                )

                rev_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO space_revisions (id, space_id, version, diff_summary, content)
                    VALUES (?, ?, 1, ?, ?)
                    """,
                    (rev_id, space_id, diff_summary, content)
                )

            await db.commit()

        # Grava também fisicamente no workspace do Dot (sem duplicar entrada na tabela spaces)
        await FileManager.write_file(dot_id=dot_id, filename=filename, content=content, sync_space=False)

        # Indexa na memória semântica vetorial
        await VectorStore.index_document(space_id=space_id, content=content)

        return {
            "id": space_id,
            "space_id": space_id,
            "dot_id": dot_id,
            "filename": filename,
            "title": doc_title,
            "version": new_version,
            "diff_summary": diff_summary,
            "status": "success"
        }

    @classmethod
    async def get_document(cls, space_id: str) -> dict[str, Any] | None:
        """Obtém documento completo por ID."""
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM spaces WHERE id = ?", (space_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    async def list_documents(cls, dot_id: str | None = None) -> list[dict[str, Any]]:
        """Lista todos os documentos versionados em Spaces."""
        async with get_db() as db:
            if dot_id:
                cursor = await db.execute(
                    "SELECT id, dot_id, filename, title, version, mime_type, updated_at FROM spaces WHERE dot_id = ? ORDER BY updated_at DESC",
                    (dot_id,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, dot_id, filename, title, version, mime_type, updated_at FROM spaces ORDER BY updated_at DESC"
                )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @classmethod
    async def get_revisions(cls, space_id: str) -> list[dict[str, Any]]:
        """Retorna histórico de revisões com diffs de um documento."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, space_id, version, diff_summary, created_at FROM space_revisions WHERE space_id = ? ORDER BY version DESC",
                (space_id,)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @classmethod
    async def export_workspace_zip(cls, dot_id: str) -> bytes:
        """
        Compacta todos os arquivos do workspace do Dot em um arquivo ZIP em memória em worker thread.
        Inclui fallback para recuperar documentos versionados da tabela spaces caso o disco local
        ainda não tenha sido sincronizado ou contenha arquivos apenas no banco.
        """
        workspace_dir = FileManager._get_safe_path(dot_id, "")

        # Coleta prévia dos documentos do banco SQLite de forma assíncrona
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT filename, content FROM spaces WHERE dot_id = ?",
                (dot_id,)
            )
            space_rows = await cursor.fetchall()
            db_docs = [(r["filename"], r["content"].encode("utf-8")) for r in space_rows]

        def _compress_sync() -> bytes:
            zip_buffer = io.BytesIO()
            written_files = set()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_f:
                if os.path.exists(workspace_dir):
                    real_workspace = os.path.realpath(workspace_dir)
                    for root, _, files in os.walk(workspace_dir, followlinks=False):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # Prevenção estrita de symlink traversal
                            real_file = os.path.realpath(full_path)
                            if os.path.commonpath([real_workspace, real_file]) != real_workspace:
                                continue
                            rel_path = os.path.relpath(full_path, workspace_dir)
                            zip_f.write(full_path, arcname=rel_path)
                            written_files.add(rel_path)

                # Complemento: inclui documentos de Spaces que não estejam no disco
                for fname, content_bytes in db_docs:
                    if fname not in written_files:
                        zip_f.writestr(fname, content_bytes)
                        written_files.add(fname)

            zip_buffer.seek(0)
            return zip_buffer.getvalue()

        return await asyncio.to_thread(_compress_sync)
