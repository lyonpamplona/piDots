"""
Motor de Memória Semântica Vetorial Edge para o piDots.
Busca por similaridade de cosseno de altíssima eficiência sem dependência de bancos vetoriais pesados.
Projetado para operar consumindo menos de 4MB de RAM no Raspberry Pi 4B.
"""

import math
import json
import re
import uuid
import zlib
import logging
from typing import Any
from .db import get_db
from .memory_manager import compute_compact_embedding, cosine_similarity as mm_cosine_similarity

logger = logging.getLogger("pidots.storage.vector")

VECTOR_DIM = 64  # Dimensão enxuta e densa calibrada para baixo consumo de memória


class VectorStore:
    """Índice vetorial embutido no SQLite para busca semântica KNN."""

    @staticmethod
    def _compute_embedding(text: str) -> list[float]:
        """
        Gera um vetor numérico de dimensão fixa (64) normalizado via projeção determinística
        unificada com o MemoryManager (clusters de domínio + feature hashing de tokens e 3-grams).
        """
        return compute_compact_embedding(text, dim=VECTOR_DIM)

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores normalizados."""
        return mm_cosine_similarity(v1, v2)

    @classmethod
    async def index_document(cls, space_id: str, content: str, chunk_size: int = 400) -> int:
        """
        Divide o documento em blocos de texto (chunks), gera embeddings e salva no SQLite.
        """
        # Remove embeddings antigos do documento
        async with get_db() as db:
            await db.execute("DELETE FROM document_embeddings WHERE space_id = ?", (space_id,))

            # Criação de chunks
            words = content.split()
            chunks = []
            curr = []
            curr_len = 0

            for w in words:
                curr.append(w)
                curr_len += len(w) + 1
                if curr_len >= chunk_size:
                    chunks.append(" ".join(curr))
                    curr = curr[-10:]  # Overlap de 10 palavras
                    curr_len = sum(len(x) + 1 for x in curr)
            if curr:
                chunks.append(" ".join(curr))

            inserted = 0
            for chunk in chunks:
                if not chunk.strip():
                    continue
                v = cls._compute_embedding(chunk)
                emb_id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO document_embeddings (id, space_id, chunk_text, vector_json, dimension)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (emb_id, space_id, chunk, json.dumps(v), VECTOR_DIM)
                )
                inserted += 1

            await db.commit()

        logger.debug("Documento %s indexado com %d chunks no SQLite.", space_id, inserted)
        return inserted

    @classmethod
    async def search(cls, query: str, top_k: int = 3, threshold: float = 0.25, dot_id: str | None = None) -> list[dict[str, Any]]:
        """
        Realiza busca semântica KNN no acervo de documentos indexados.
        """
        query_vec = cls._compute_embedding(query)
        matches = []

        async with get_db() as db:
            sql = """
                SELECT e.id, e.space_id, e.chunk_text, e.vector_json, s.filename, s.title
                FROM document_embeddings e
                JOIN spaces s ON e.space_id = s.id
            """
            params = []
            if dot_id:
                sql += " WHERE s.dot_id = ?"
                params.append(dot_id)
            sql += " ORDER BY e.created_at DESC LIMIT 200"

            cursor = await db.execute(sql, tuple(params))
            rows = await cursor.fetchall()

        for row in rows:
            try:
                doc_vec = json.loads(row["vector_json"])
                score = cls.cosine_similarity(query_vec, doc_vec)
                if score >= threshold:
                    matches.append({
                        "space_id": row["space_id"],
                        "filename": row["filename"],
                        "title": row["title"],
                        "chunk_text": row["chunk_text"],
                        "score": round(score, 4)
                    })
            except Exception:
                continue

        # Ordena pelos mais similares
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]
