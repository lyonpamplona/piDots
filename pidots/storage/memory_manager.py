"""
Gerenciador de Memória Hierárquica Autônoma para piDots (Padrão MemGPT / Letta).
Implementa três camadas de contexto calibradas para Raspberry Pi 4B (ARM64):
1. Core Memory (Memória Primária de Trabalho in-context: persona, human, active_context).
2. Recall Memory (Memória Retrospectiva de Diálogo em SQLite WAL).
3. Archival Memory (Memória Arquivística Duradoura com busca híbrida FTS5 BM25 + Projeção Vetorial 64d).
"""

import hashlib
import json
import logging
import math
import re
import uuid
from typing import Any

from .db import get_db

logger = logging.getLogger("pidots.memory")

ALLOWED_CORE_SECTIONS = ("persona", "human", "active_context")
DEFAULT_MAX_CHARS = 2000


DOMAIN_CLUSTERS = {
    "hardware": ["arm", "arm64", "cortex", "cpu", "soc", "ram", "lpddr", "lpddr4", "memoria", "memory", "processador", "raspberry", "pi", "borda", "edge", "microsd", "sd", "gpio", "hardware"],
    "software": ["python", "linux", "sqlite", "docker", "codigo", "software", "uvloop", "api", "backend", "frontend", "git", "bash"],
    "network": ["rede", "network", "cloudflare", "tunnel", "porta", "http", "proxy", "dns", "ip", "websocket"]
}


def compute_compact_embedding(text: str, dim: int = 64) -> list[float]:
    """
    Gera uma projecao vetorial deterministica compacta de N dimensoes normalizada L2.
    Utiliza ativacao de clusters semanticos e feature hashing esparso de subpalavras (3-grams).
    Executa com zero dependencias externas (sem PyTorch, sem ONNX), consumindo < 1ms e zero memoria adicional.
    """
    if not text:
        return [0.0] * dim

    vec = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        tokens = [text.lower()]

    # 1. Ativacao semantica orientada a dominios tecnicos
    for cluster_name, words in DOMAIN_CLUSTERS.items():
        cluster_hash = int(hashlib.md5(cluster_name.encode("utf-8")).hexdigest(), 16)
        base_slot = cluster_hash % (dim // 2)
        count = sum(1 for t in tokens if any(w in t for w in words))
        if count > 0:
            for offset in range(4):
                vec[(base_slot + offset) % dim] += count * 2.0

    # 2. Feature hashing esparso de tokens individuais e 3-grams
    for token in tokens:
        th = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        vec[th % dim] += 1.0

        if len(token) >= 3:
            for j in range(len(token) - 2):
                ng = token[j:j + 3]
                nh = int(hashlib.md5(ng.encode("utf-8")).hexdigest(), 16)
                vec[nh % dim] += 0.3

    # Normalizacao L2 (Norma Euclidiana unitaria para produto escalar direto)
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [round(x / norm, 5) for x in vec]
    return vec


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores normalizados."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


class MemoryManager:
    """Gerenciador central de memória episódica, core e arquivística dos Dots."""

    # --------------------------------------------------------------------------
    # 1. CORE MEMORY (In-Context Working Memory)
    # --------------------------------------------------------------------------

    @classmethod
    async def get_core_memory_blocks(
        cls,
        dot_id: str,
        default_persona: str = ""
    ) -> dict[str, str]:
        """
        Recupera os blocos da Core Memory do Dot.
        Se ainda não existirem, inicializa blocos padrão de forma atômica no SQLite WAL.
        """
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT block_name, content FROM agent_core_memory_blocks WHERE dot_id = ?",
                (dot_id,)
            )
            rows = await cursor.fetchall()
            existing = {r["block_name"]: r["content"] for r in rows}

            # Inicializa seções ausentes
            defaults = {
                "persona": default_persona or "AI Coworker persistente operando no nó piDots.",
                "human": "Operador técnico e criador do nó soberano.",
                "active_context": "Inicialização de tarefas e cooperação contínua."
            }

            needed_inserts = []
            for sec, def_val in defaults.items():
                if sec not in existing:
                    block_id = str(uuid.uuid4())
                    needed_inserts.append((block_id, dot_id, sec, def_val, DEFAULT_MAX_CHARS))
                    existing[sec] = def_val

            if needed_inserts:
                await db.executemany(
                    """
                    INSERT OR IGNORE INTO agent_core_memory_blocks (id, dot_id, block_name, content, max_chars)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    needed_inserts
                )
                await db.commit()

        return {k: existing.get(k, "") for k in ALLOWED_CORE_SECTIONS}

    @classmethod
    async def format_core_memory_prompt(
        cls,
        dot_id: str,
        default_persona: str = ""
    ) -> str:
        """Formata os blocos de Core Memory como tag XML limpa para injeção no prompt de sistema."""
        blocks = await cls.get_core_memory_blocks(dot_id, default_persona)
        return (
            "<core_memory>\n"
            f"<persona>\n{blocks.get('persona', '')}\n</persona>\n"
            f"<human>\n{blocks.get('human', '')}\n</human>\n"
            f"<active_context>\n{blocks.get('active_context', '')}\n</active_context>\n"
            "</core_memory>"
        )

    @classmethod
    async def append_core_memory(
        cls,
        dot_id: str,
        section: str,
        content: str
    ) -> dict[str, Any]:
        """Anexa informações ao final de uma seção da Core Memory validando limite de caracteres."""
        sec_clean = section.strip().lower()
        if sec_clean not in ALLOWED_CORE_SECTIONS:
            return {
                "success": False,
                "error": f"Seção inválida '{section}'. Seções permitidas: {', '.join(ALLOWED_CORE_SECTIONS)}."
            }

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT content, max_chars FROM agent_core_memory_blocks WHERE dot_id = ? AND block_name = ?",
                (dot_id, sec_clean)
            )
            row = await cursor.fetchone()
            current_content = row["content"] if row else ""
            max_chars = row["max_chars"] if row else DEFAULT_MAX_CHARS

            sep = "\n" if current_content and not current_content.endswith("\n") else ""
            new_content = f"{current_content}{sep}{content.strip()}"

            if len(new_content) > max_chars:
                return {
                    "success": False,
                    "error": (
                        f"Limite de capacidade atingido para a seção '{sec_clean}'. "
                        f"Comprimento atual: {len(current_content)} | Tentativa: {len(new_content)} | Máximo: {max_chars}. "
                        "Utilize a ferramenta 'core_memory_replace' para substituir dados obsoletos."
                    )
                }

            await db.execute(
                """
                INSERT INTO agent_core_memory_blocks (id, dot_id, block_name, content, max_chars, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(dot_id, block_name) DO UPDATE SET
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (str(uuid.uuid4()), dot_id, sec_clean, new_content, max_chars)
            )
            await db.commit()

        logger.info("Core Memory atualizada (append) para Dot '%s' [%s]: %d caracteres.", dot_id, sec_clean, len(new_content))
        return {
            "success": True,
            "section": sec_clean,
            "current_length": len(new_content),
            "max_chars": max_chars,
            "content": new_content
        }

    @classmethod
    async def replace_core_memory(
        cls,
        dot_id: str,
        section: str,
        old_content: str,
        new_content: str
    ) -> dict[str, Any]:
        """Substitui um trecho específico dentro de uma seção da Core Memory."""
        sec_clean = section.strip().lower()
        if sec_clean not in ALLOWED_CORE_SECTIONS:
            return {
                "success": False,
                "error": f"Seção inválida '{section}'. Seções permitidas: {', '.join(ALLOWED_CORE_SECTIONS)}."
            }

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT content, max_chars FROM agent_core_memory_blocks WHERE dot_id = ? AND block_name = ?",
                (dot_id, sec_clean)
            )
            row = await cursor.fetchone()
            current_content = row["content"] if row else ""
            max_chars = row["max_chars"] if row else DEFAULT_MAX_CHARS

            if old_content not in current_content:
                return {
                    "success": False,
                    "error": f"O trecho especificado em 'old_content' não foi encontrado na seção '{sec_clean}'."
                }

            updated_content = current_content.replace(old_content, new_content, 1)

            if len(updated_content) > max_chars:
                return {
                    "success": False,
                    "error": f"A substituição excedeu o limite máximo de {max_chars} caracteres (Novo tamanho: {len(updated_content)})."
                }

            await db.execute(
                """
                UPDATE agent_core_memory_blocks
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE dot_id = ? AND block_name = ?
                """,
                (updated_content, dot_id, sec_clean)
            )
            await db.commit()

        logger.info("Core Memory atualizada (replace) para Dot '%s' [%s]: %d caracteres.", dot_id, sec_clean, len(updated_content))
        return {
            "success": True,
            "section": sec_clean,
            "current_length": len(updated_content),
            "max_chars": max_chars,
            "content": updated_content
        }

    # --------------------------------------------------------------------------
    # 2. ARCHIVAL MEMORY (Long-Term Knowledge & FTS5 BM25)
    # --------------------------------------------------------------------------

    @classmethod
    async def insert_archival_memory(
        cls,
        dot_id: str,
        content: str,
        tags: list[str] | None = None
    ) -> dict[str, Any]:
        """Insere um fato ou documento na memória arquivística duradoura com projeção vetorial e FTS5."""
        if not content.strip():
            return {"success": False, "error": "Conteúdo da memória não pode ser vazio."}

        mem_id = str(uuid.uuid4())
        tags_list = tags or []
        tags_str = json.dumps(tags_list, ensure_ascii=False)
        vec = compute_compact_embedding(content, dim=64)
        vec_json = json.dumps(vec)

        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO archival_memories (id, dot_id, content, tags_json, vector_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mem_id, dot_id, content.strip(), tags_str, vec_json)
            )
            await db.commit()

        logger.info("Memória arquivística gravada para Dot '%s': ID %s (%d chars).", dot_id, mem_id, len(content))
        return {
            "success": True,
            "id": mem_id,
            "dot_id": dot_id,
            "tags": tags_list,
            "content_length": len(content)
        }

    @classmethod
    async def search_archival_memory(
        cls,
        dot_id: str,
        query: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Executa busca híbrida na memória arquivística combinando BM25 (FTS5) e Projeção Vetorial 64d.
        """
        if not query.strip():
            return []

        query_vec = compute_compact_embedding(query, dim=64)
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        async with get_db() as db:
            # 1. Busca textual BM25 via tabela virtual FTS5
            # Sanitiza query para FTS5 removendo caracteres especiais de sintaxe
            clean_fts_query = re.sub(r"[^\w\s]", "", query).strip()
            if clean_fts_query:
                # Divide termos para operador OR ou prefix match
                fts_terms = " OR ".join([f"{term}*" for term in clean_fts_query.split() if term])
                if fts_terms:
                    try:
                        cursor = await db.execute(
                            """
                            SELECT a.id, a.content, a.tags_json, a.vector_json, a.created_at, f.rank
                            FROM archival_memories_fts f
                            JOIN archival_memories a ON a.id = f.id
                            WHERE f.dot_id = ? AND archival_memories_fts MATCH ?
                            ORDER BY f.rank
                            LIMIT ?
                            """,
                            (dot_id, fts_terms, limit)
                        )
                        rows = await cursor.fetchall()
                        for r in rows:
                            vec_loaded = json.loads(r["vector_json"]) if r["vector_json"] else []
                            sim = cosine_similarity(query_vec, vec_loaded)
                            bm25_weight = abs(r["rank"]) if r["rank"] is not None else 0.0
                            results.append({
                                "id": r["id"],
                                "content": r["content"],
                                "tags": json.loads(r["tags_json"]) if r["tags_json"] else [],
                                "created_at": r["created_at"],
                                "relevance_score": round(bm25_weight + sim * 0.5, 3),
                                "source": "fts5_bm25"
                            })
                            seen_ids.add(r["id"])
                    except Exception as e:
                        logger.warning("Consulta FTS5 falhou para '%s': %s. Usando fallback vetorial.", query, e)

            # 2. Complementação/Fallback por Similaridade Vetorial Direta
            cursor = await db.execute(
                "SELECT id, content, tags_json, vector_json, created_at FROM archival_memories WHERE dot_id = ? ORDER BY created_at DESC LIMIT 50",
                (dot_id,)
            )
            all_rows = await cursor.fetchall()

            for r in all_rows:
                if r["id"] in seen_ids:
                    continue
                vec_loaded = json.loads(r["vector_json"]) if r["vector_json"] else []
                sim = cosine_similarity(query_vec, vec_loaded)
                if sim >= 0.25:
                    results.append({
                        "id": r["id"],
                        "content": r["content"],
                        "tags": json.loads(r["tags_json"]) if r["tags_json"] else [],
                        "created_at": r["created_at"],
                        "relevance_score": round(sim, 3),
                        "source": "vector_64d"
                    })

        # Ordena pelo score decrescente e aplica limit
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    # --------------------------------------------------------------------------
    # 3. RECALL MEMORY (Dialogue Retrospective Search)
    # --------------------------------------------------------------------------

    @classmethod
    async def search_recall_memory(
        cls,
        thread_id: str,
        query: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Busca retrospectiva no histórico de mensagens arquivadas de uma thread."""
        if not query.strip():
            return []

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id, role, content, actor_id, visibility, created_at
                FROM messages
                WHERE thread_id = ? AND content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (thread_id, f"%{query.strip()}%", limit)
            )
            rows = await cursor.fetchall()
            return [
                {
                    "message_id": r["id"],
                    "role": r["role"],
                    "actor_id": r["actor_id"],
                    "content": r["content"],
                    "visibility": r["visibility"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]
