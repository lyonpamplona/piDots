"""
Gerenciador de Banco de Dados SQLite em modo WAL calibrado para Raspberry Pi 4B.
Minimiza I/O em disco flash (MicroSD), reduz fsync e previne corrupção de dados.
"""

import aiosqlite
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from ..config import settings

logger = logging.getLogger("pidots.storage")

SQL_SCHEMA = """
-- =============================================================================
-- SCHEMA piDots (Edge SQLite WAL Engine)
-- =============================================================================

-- Dots (AI Coworkers Persistentes)
CREATE TABLE IF NOT EXISTS dots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    model TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Threads de Conversação Duráveis
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Mensagens e Diálogo Multi-Turn
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    thought_log TEXT,
    tool_calls_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

-- Spaces: Biblioteca de Documentos e Artefatos Versionados
CREATE TABLE IF NOT EXISTS spaces (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    mime_type TEXT DEFAULT 'text/markdown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Histórico de Revisões e Diffs de Documentos em Spaces
CREATE TABLE IF NOT EXISTS space_revisions (
    id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    diff_summary TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(space_id) REFERENCES spaces(id) ON DELETE CASCADE
);

-- Memória Semântica Vetorial Edge
CREATE TABLE IF NOT EXISTS document_embeddings (
    id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    dimension INTEGER DEFAULT 64,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(space_id) REFERENCES spaces(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_revisions_space ON space_revisions(space_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_space ON document_embeddings(space_id);

-- Governança Human-in-the-Loop (HITL)
CREATE TABLE IF NOT EXISTS hitl_approvals (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    thread_id TEXT,
    action_type TEXT NOT NULL, -- 'shell_exec', 'file_delete', 'network_call', 'skill_create'
    payload TEXT NOT NULL,
    risk_level TEXT DEFAULT 'HIGH', -- 'MEDIUM', 'HIGH', 'CRITICAL'
    status TEXT DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED'
    reviewer_notes TEXT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Auditoria de Execução de Ferramentas
CREATE TABLE IF NOT EXISTS tool_runs (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    exit_code INTEGER,
    stdout_text TEXT,
    stderr_text TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Índices de Alta Eficiência para Consultas Rápidas
CREATE INDEX IF NOT EXISTS idx_threads_dot_id ON threads(dot_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_spaces_dot_id ON spaces(dot_id);
CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitl_approvals(status);
"""


async def init_edge_database(db_path: str | None = None) -> None:
    """
    Inicializa o banco SQLite com pragmas estritos de proteção flash para Raspberry Pi 4B.
    """
    path = db_path or settings.sqlite_db_path
    settings.ensure_directories()

    logger.info("Inicializando banco SQLite Edge em: %s", path)
    async with aiosqlite.connect(path) as db:
        # Pragmas obrigatórios de calibração para MicroSD
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        await db.execute("PRAGMA cache_size = -16000;")     # Teto de 16MB de RAM
        await db.execute("PRAGMA temp_store = MEMORY;")      # Operações transitórias na RAM
        await db.execute("PRAGMA mmap_size = 67108864;")     # Limite de 64MB para mmap
        await db.execute("PRAGMA busy_timeout = 5000;")      # Previne concorrência de locks

        # Execução do Schema
        await db.executescript(SQL_SCHEMA)
        await db.commit()
    logger.info("Banco SQLite Edge inicializado com sucesso em modo WAL.")


@asynccontextmanager
async def get_db(db_path: str | None = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Gerenciador de contexto assíncrono para obter conexões leves ao SQLite.
    """
    path = db_path or settings.sqlite_db_path
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn
