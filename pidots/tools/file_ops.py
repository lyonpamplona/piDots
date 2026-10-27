"""
Gerenciador Atômico de Arquivos de Workspace para o piDots.
Garante proteção contra Path Traversal e realiza escrita atômica para evitar corrupção de dados.
"""

import os
import re
import asyncio
import tempfile
import logging
from typing import Any
from datetime import datetime, timezone

from ..config import settings

logger = logging.getLogger("pidots.tools.file_ops")


class FileManager:
    """Operações seguras de sistema de arquivos dentro do workspace de um Dot."""

    @staticmethod
    def _get_safe_path(dot_id: str, relative_path: str) -> str:
        """Resolve o caminho real (incluindo symlinks) e valida contenção estrita no workspace do Dot."""
        safe_dot_id = re.sub(r"[^\w\-_.]", "_", (dot_id or "default").strip()).strip(".") or "default"
        workspaces_root = os.path.realpath(settings.workspaces_root)
        workspace_dir = os.path.realpath(os.path.join(workspaces_root, safe_dot_id))
        if os.path.commonpath([workspaces_root, workspace_dir]) != workspaces_root:
            raise PermissionError("Identificador de workspace inválido.")

        os.makedirs(workspace_dir, exist_ok=True)
        clean_rel = (relative_path or "").lstrip("/\\")
        target_path = os.path.realpath(os.path.join(workspace_dir, clean_rel))

        # Proteção estrita contra Path Traversal e Symlink Bypass (previne colisão de prefixo ex: dot-1 vs dot-10)
        if os.path.commonpath([workspace_dir, target_path]) != workspace_dir:
            raise PermissionError(f"Acesso negado: o caminho '{relative_path}' escapa do workspace autorizado.")

        return target_path

    MAX_READ_BYTES = 10 * 1024 * 1024  # Limite de 10MB para proteger a memória RAM em hardware restrito

    @classmethod
    async def read_file(cls, dot_id: str, filename: str) -> dict[str, Any]:
        """Lê o conteúdo de um arquivo no workspace com I/O assíncrono em worker thread."""
        try:
            target_path = cls._get_safe_path(dot_id, filename)
            if not os.path.exists(target_path):
                return {"error": f"Arquivo '{filename}' não existe no workspace."}
            if os.path.isdir(target_path):
                return {"error": f"'{filename}' é um diretório, não um arquivo."}

            file_size = os.path.getsize(target_path)
            if file_size > cls.MAX_READ_BYTES:
                return {
                    "error": f"Arquivo '{filename}' ({round(file_size / (1024*1024), 2)}MB) excede o limite máximo permitido de {cls.MAX_READ_BYTES // (1024*1024)}MB."
                }

            def _read_sync() -> str:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()

            content = await asyncio.to_thread(_read_sync)

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
        """Grava um arquivo atomicamente (escreve em temporário e renomeia) em worker thread."""
        try:
            if sync_space:
                from ..storage.spaces_manager import SpacesManager
                space_res = await SpacesManager.save_document(
                    dot_id=dot_id,
                    filename=filename,
                    content=content,
                    title=filename
                )
                return {
                    "filename": filename,
                    "space_id": space_res.get("space_id"),
                    "version": space_res.get("version", 1),
                    "status": "success",
                    "bytes_written": len(content.encode("utf-8")),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            target_path = cls._get_safe_path(dot_id, filename)
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            def _write_atomic_sync() -> None:
                # Gravação atômica: cria temporário no mesmo diretório para garantir mesmo ponto de montagem
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tmp_f:
                        tmp_f.write(content)
                        tmp_path = tmp_f.name

                    # Substitui atomicamente o arquivo final
                    os.replace(tmp_path, target_path)
                    tmp_path = None
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass

            await asyncio.to_thread(_write_atomic_sync)

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
        """Lista arquivos e diretórios recursivamente dentro do workspace do Dot em worker thread."""
        try:
            target_dir = cls._get_safe_path(dot_id, subdirectory)

            def _list_sync() -> list[dict[str, Any]]:
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
                return file_list

            file_list = await asyncio.to_thread(_list_sync)

            return {
                "workspace_of": dot_id,
                "total_files": len(file_list),
                "files": file_list
            }
        except Exception as e:
            return {"error": str(e)}
