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

logger = logging.getLogger("pidots.storage.vector")

VECTOR_DIM = 64  # Dimensão enxuta e densa calibrada para baixo consumo de memória


class VectorStore:
    """Índice vetorial embutido no SQLite para busca semântica KNN."""

    @staticmethod
    def _compute_embedding(text: str) -> list[float]:
        """
        Gera um vetor numérico de dimensão fixa (64) normalizado via projeção determinística.
        Usa zlib.crc32 para estabilidade total entre processos e reinicializações de contêiner.
        """
        vec = [0.0] * VECTOR_DIM
        words = re.findall(r"\w+", text.lower())

        if not words:
            return vec

        for i, word in enumerate(words):
            h = zlib.crc32(word.encode("utf-8"))
            idx = h % VECTOR_DIM
            weight = 1.0 / (1.0 + math.log(1.0 + i * 0.1))
            vec[idx] += weight

            # 2-grams para captura de contexto sintático
            if i > 0:
                bi_h = zlib.crc32(f"{words[i - 1]}_{word}".encode("utf-8"))
                bi_idx = bi_h % VECTOR_DIM
                vec[bi_idx] += 0.5 * weight

        # Normalização L2 (vetor unitário)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 5) for x in vec]
        return vec

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores normalizados."""
        if len(v1) != len(v2):
            return 0.0
        return sum(a * b for a, b in zip(v1, v2))

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
