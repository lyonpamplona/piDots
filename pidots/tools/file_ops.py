"""
Gerenciador Atômico de Arquivos de Workspace para o piDots.
Garante proteção contra Path Traversal e realiza escrita atômica para evitar corrupção de dados.
"""

import os
import uuid
import tempfile
import logging
from typing import Any
from datetime import datetime, timezone

from ..config import settings
from ..storage.db import get_db

logger = logging.getLogger("pidots.tools.file_ops")


class FileManager:
    """Operações seguras de sistema de arquivos dentro do workspace de um Dot."""

    @staticmethod
    def _get_safe_path(dot_id: str, relative_path: str) -> str:
        """Resolve o caminho absoluto e valida se está estritamente contido no workspace do Dot."""
        workspace_dir = os.path.abspath(os.path.join(settings.workspaces_root, dot_id))
        os.makedirs(workspace_dir, exist_ok=True)
        target_path = os.path.abspath(os.path.join(workspace_dir, relative_path.lstrip("/")))

        # Proteção contra Path Traversal (ex: ../../etc/passwd)
        if not target_path.startswith(workspace_dir):
            raise PermissionError(f"Acesso negado: o caminho '{relative_path}' escapa do workspace autorizado.")

        return target_path

    @classmethod
    async def read_file(cls, dot_id: str, filename: str) -> dict[str, Any]:
        """Lê o conteúdo de um arquivo no workspace."""
        try:
            target_path = cls._get_safe_path(dot_id, filename)
            if not os.path.exists(target_path):
                return {"error": f"Arquivo '{filename}' não existe no workspace."}
            if os.path.isdir(target_path):
                return {"error": f"'{filename}' é um diretório, não um arquivo."}

            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            return {
                "filename": filename,
                "status": "success",
                "bytes": len(content.encode("utf-8")),
                "content": content
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    async def write_file(cls, dot_id: str, filename: str, content: str, sync_space: bool = False) -> dict[str, Any]:
        """Grava um arquivo atomicamente (escreve em temporário e renomeia)."""
        try:
            target_path = cls._get_safe_path(dot_id, filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Gravação atômica: cria temporário no mesmo diretório para garantir mesmo ponto de montagem
            target_dir = os.path.dirname(target_path)
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tmp_f:
                tmp_f.write(content)
                tmp_path = tmp_f.name

            # Substitui atomicamente o arquivo final
            os.replace(tmp_path, target_path)

            # Sincroniza de forma idempotente na tabela Spaces somente se solicitado e sem duplicar
            if sync_space:
                try:
                    async with get_db() as db:
                        cursor = await db.execute("SELECT id FROM spaces WHERE dot_id = ? AND filename = ?", (dot_id, filename))
                        existing = await cursor.fetchone()
                        if existing:
                            await db.execute(
                                "UPDATE spaces SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                (content, existing["id"])
                            )
                        else:
                            space_id = str(uuid.uuid4())
                            await db.execute(
                                """
                                INSERT INTO spaces (id, dot_id, filename, title, content)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (space_id, dot_id, filename, filename, content)
                            )
                        await db.commit()
                except Exception as db_err:
                    logger.warning("Não foi possível sincronizar histórico em spaces: %s", str(db_err))

            return {
                "filename": filename,
                "status": "success",
                "bytes_written": len(content.encode("utf-8")),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    async def list_files(cls, dot_id: str, subdirectory: str = "") -> dict[str, Any]:
        """Lista arquivos e diretórios recursivamente dentro do workspace do Dot."""
        try:
            target_dir = cls._get_safe_path(dot_id, subdirectory)
            file_list = []
            for root, dirs, files in os.walk(target_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, target_dir)
                    stat = os.stat(full_p)
                    file_list.append({
                        "path": rel_p,
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })

            return {
                "workspace_of": dot_id,
                "total_files": len(file_list),
                "files": file_list
            }
        except Exception as e:
            return {"error": str(e)}
