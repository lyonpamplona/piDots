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
    archetype TEXT DEFAULT 'general',
    avatar_stamp TEXT DEFAULT 'DOT',
    allowed_tools_json TEXT DEFAULT '[]',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Threads de Conversação Duráveis
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    title TEXT NOT NULL,
    primary_dot_id TEXT,
    orchestration_mode TEXT DEFAULT 'direct',
    status TEXT DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Mensagens e Diálogo Multi-Turn
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    actor_id TEXT DEFAULT 'assistant',
    actor_type TEXT DEFAULT 'dot',
    target_dot_id TEXT,
    visibility TEXT DEFAULT 'public',
    role TEXT NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    thought_log TEXT,
    tool_calls_json TEXT,
    parent_message_id TEXT,
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

-- Participantes da Thread (Suporte Multi-Bot N:N)
CREATE TABLE IF NOT EXISTS thread_participants (
    thread_id TEXT NOT NULL,
    dot_id TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_speaker INTEGER DEFAULT 1,
    turn_order INTEGER DEFAULT 0,
    PRIMARY KEY (thread_id, dot_id),
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Fila e Histórico de Delegações e Handoffs entre Bots
CREATE TABLE IF NOT EXISTS agent_handoffs (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    source_dot_id TEXT NOT NULL,
    target_dot_id TEXT NOT NULL,
    task_goal TEXT NOT NULL,
    handoff_type TEXT NOT NULL DEFAULT 'delegate_subtask',
    status TEXT DEFAULT 'PENDING',
    result_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
    FOREIGN KEY(source_dot_id) REFERENCES dots(id) ON DELETE CASCADE,
    FOREIGN KEY(target_dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Metas e Marcos Persistentes (Goals & Milestones)
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    thread_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE,
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    evidence_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

-- Memória Episódica Estruturada com Sumarização Periódica
CREATE TABLE IF NOT EXISTS episodic_memories (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_decisions TEXT,
    modified_artifacts TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE,
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

-- Tarefas Proativas e Agendamentos (Dot Heartbeat)
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    cron_expr TEXT NOT NULL,
    action_prompt TEXT NOT NULL,
    target_channel_type TEXT DEFAULT 'internal',
    target_channel_id TEXT,
    next_run_at TIMESTAMP NOT NULL,
    last_run_at TIMESTAMP,
    last_status TEXT DEFAULT 'IDLE',
    last_result_summary TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    backoff_until TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

-- Salas Temáticas de Equipe (Bot Channels)
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_messages (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    author_type TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,
    hop_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS channel_members (
    channel_id TEXT NOT NULL,
    member_type TEXT NOT NULL, -- 'user', 'dot', 'webhook'
    member_id TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, member_id),
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

-- Índices de Alta Eficiência para Consultas Rápidas
CREATE INDEX IF NOT EXISTS idx_threads_dot_id ON threads(dot_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_spaces_dot_id ON spaces(dot_id);
CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitl_approvals(status);
CREATE INDEX IF NOT EXISTS idx_participants_thread ON thread_participants(thread_id);
CREATE INDEX IF NOT EXISTS idx_handoffs_thread ON agent_handoffs(thread_id, status);
CREATE INDEX IF NOT EXISTS idx_milestones_goal ON milestones(goal_id, order_index);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON scheduled_tasks(is_active, next_run_at, backoff_until);
CREATE INDEX IF NOT EXISTS idx_channel_msgs ON channel_messages(channel_id, created_at);
CREATE INDEX IF NOT EXISTS idx_channel_members ON channel_members(channel_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_episodic_dot_thread ON episodic_memories(dot_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_episodic_created_at ON episodic_memories(created_at);


-- Memória Autônoma Hierárquica (Padrão MemGPT / Letta)
CREATE TABLE IF NOT EXISTS agent_core_memory_blocks (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    block_name TEXT NOT NULL, -- 'human', 'persona', 'active_context'
    content TEXT NOT NULL DEFAULT '',
    max_chars INTEGER DEFAULT 2000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dot_id, block_name),
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS archival_memories (
    id TEXT PRIMARY KEY,
    dot_id TEXT NOT NULL,
    content TEXT NOT NULL,
    tags_json TEXT DEFAULT '[]',
    vector_json TEXT, -- Projeção vetorial determinística compacta de 64 floats
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS archival_memories_fts USING fts5(
    id UNINDEXED,
    dot_id UNINDEXED,
    content,
    tags,
    tokenize = 'porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS trg_archival_insert AFTER INSERT ON archival_memories BEGIN
    INSERT INTO archival_memories_fts (id, dot_id, content, tags)
    VALUES (new.id, new.dot_id, new.content, new.tags_json);
END;

CREATE TRIGGER IF NOT EXISTS trg_archival_delete AFTER DELETE ON archival_memories BEGIN
    DELETE FROM archival_memories_fts WHERE id = old.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_archival_update AFTER UPDATE ON archival_memories BEGIN
    DELETE FROM archival_memories_fts WHERE id = old.id;
    INSERT INTO archival_memories_fts (id, dot_id, content, tags)
    VALUES (new.id, new.dot_id, new.content, new.tags_json);
END;

CREATE INDEX IF NOT EXISTS idx_core_mem_dot ON agent_core_memory_blocks(dot_id);
CREATE INDEX IF NOT EXISTS idx_archival_dot ON archival_memories(dot_id, created_at);

-- Espaço de Conhecimento Compartilhado entre Bots (Shared Knowledge Space)
CREATE TABLE IF NOT EXISTS thread_shared_notes (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    dot_id TEXT NOT NULL,
    topic_key TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(thread_id, topic_key),
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
    FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_shared_notes_thread ON thread_shared_notes(thread_id, topic_key);
"""


async def _apply_schema_migrations(db: aiosqlite.Connection) -> None:
    """Aplica migrações idempotentes de colunas em tabelas existentes."""
    # 1. Tabela dots: colunas para arquétipos, carimbo e catálogo de ferramentas
    cursor = await db.execute("PRAGMA table_info(dots);")
    dots_cols = {row["name"] for row in await cursor.fetchall()}
    if "archetype" not in dots_cols:
        await db.execute("ALTER TABLE dots ADD COLUMN archetype TEXT DEFAULT 'general';")
    if "avatar_stamp" not in dots_cols:
        await db.execute("ALTER TABLE dots ADD COLUMN avatar_stamp TEXT DEFAULT 'DOT';")
    if "allowed_tools_json" not in dots_cols:
        await db.execute("ALTER TABLE dots ADD COLUMN allowed_tools_json TEXT DEFAULT '[]';")

    # 2. Tabela threads: colunas para orquestração multi-bot
    cursor = await db.execute("PRAGMA table_info(threads);")
    threads_cols = {row["name"] for row in await cursor.fetchall()}
    if "primary_dot_id" not in threads_cols:
        await db.execute("ALTER TABLE threads ADD COLUMN primary_dot_id TEXT;")
    if "orchestration_mode" not in threads_cols:
        await db.execute("ALTER TABLE threads ADD COLUMN orchestration_mode TEXT DEFAULT 'direct';")

    # 3. Tabela messages: colunas para multi-ator, destinatário e visibilidade
    cursor = await db.execute("PRAGMA table_info(messages);")
    msg_cols = {row["name"] for row in await cursor.fetchall()}
    if "actor_id" not in msg_cols:
        await db.execute("ALTER TABLE messages ADD COLUMN actor_id TEXT DEFAULT 'assistant';")
    if "actor_type" not in msg_cols:
        await db.execute("ALTER TABLE messages ADD COLUMN actor_type TEXT DEFAULT 'dot';")
    if "target_dot_id" not in msg_cols:
        await db.execute("ALTER TABLE messages ADD COLUMN target_dot_id TEXT;")
    if "visibility" not in msg_cols:
        await db.execute("ALTER TABLE messages ADD COLUMN visibility TEXT DEFAULT 'public';")
    if "parent_message_id" not in msg_cols:
        await db.execute("ALTER TABLE messages ADD COLUMN parent_message_id TEXT;")

    # 4. Tabela scheduled_tasks: colunas para resiliência e circuit breaker
    cursor = await db.execute("PRAGMA table_info(scheduled_tasks);")
    tasks_cols = {row["name"] for row in await cursor.fetchall()}
    if "consecutive_failures" not in tasks_cols:
        await db.execute("ALTER TABLE scheduled_tasks ADD COLUMN consecutive_failures INTEGER DEFAULT 0;")
    if "backoff_until" not in tasks_cols:
        await db.execute("ALTER TABLE scheduled_tasks ADD COLUMN backoff_until TIMESTAMP;")

    # 5. Tabelas e Gatilhos de Memória Autônoma Hierárquica
    await db.execute("""
        CREATE TABLE IF NOT EXISTS agent_core_memory_blocks (
            id TEXT PRIMARY KEY,
            dot_id TEXT NOT NULL,
            block_name TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            max_chars INTEGER DEFAULT 2000,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dot_id, block_name),
            FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
        );
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS archival_memories (
            id TEXT PRIMARY KEY,
            dot_id TEXT NOT NULL,
            content TEXT NOT NULL,
            tags_json TEXT DEFAULT '[]',
            vector_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
        );
    """)
    await db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS archival_memories_fts USING fts5(
            id UNINDEXED,
            dot_id UNINDEXED,
            content,
            tags,
            tokenize = 'porter unicode61'
        );
    """)
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_archival_insert AFTER INSERT ON archival_memories BEGIN
            INSERT INTO archival_memories_fts (id, dot_id, content, tags)
            VALUES (new.id, new.dot_id, new.content, new.tags_json);
        END;
    """)
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_archival_delete AFTER DELETE ON archival_memories BEGIN
            DELETE FROM archival_memories_fts WHERE id = old.id;
        END;
    """)
    await db.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_archival_update AFTER UPDATE ON archival_memories BEGIN
            DELETE FROM archival_memories_fts WHERE id = old.id;
            INSERT INTO archival_memories_fts (id, dot_id, content, tags)
            VALUES (new.id, new.dot_id, new.content, new.tags_json);
        END;
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_core_mem_dot ON agent_core_memory_blocks(dot_id);")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_archival_dot ON archival_memories(dot_id, created_at);")

    # 5. Tabela de Conhecimento Compartilhado entre Bots (Shared Knowledge Space)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS thread_shared_notes (
            id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            dot_id TEXT NOT NULL,
            topic_key TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(thread_id, topic_key),
            FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
            FOREIGN KEY(dot_id) REFERENCES dots(id) ON DELETE CASCADE
        );
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_shared_notes_thread ON thread_shared_notes(thread_id, topic_key);")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_episodic_dot_thread ON episodic_memories(dot_id, thread_id);")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_episodic_created_at ON episodic_memories(created_at);")

    await db.commit()



async def init_edge_database(db_path: str | None = None) -> None:
    """
    Inicializa o banco SQLite com pragmas estritos de proteção flash para Raspberry Pi 4B
    e aplica migrações idempotentes de esquema.
    """
    path = db_path or settings.sqlite_db_path
    settings.ensure_directories()

    logger.info("Inicializando banco SQLite Edge em: %s", path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        # Pragmas obrigatórios de calibração para MicroSD
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        await db.execute("PRAGMA cache_size = -16000;")     # Teto de 16MB de RAM
        await db.execute("PRAGMA temp_store = MEMORY;")      # Operações transitórias na RAM
        await db.execute("PRAGMA mmap_size = 67108864;")     # Limite de 64MB para mmap
        await db.execute("PRAGMA busy_timeout = 5000;")      # Previne concorrência de locks

        # Execução do Schema base
        await db.executescript(SQL_SCHEMA)
        await db.commit()

        # Execução das migrações idempotentes de colunas
        await _apply_schema_migrations(db)

        # Inicialização idempotente de Dot e Thread padrão para integridade relacional de Foreign Keys
        await db.execute("""
            INSERT OR IGNORE INTO dots (
                id, name, role, system_prompt, model, workspace_path, archetype, avatar_stamp
            ) VALUES (
                'dot-dev-core', 'Dev Core', 'Engenheiro de Software & Arquiteto Edge',
                'Você é o Dev Core, assistente técnico de desenvolvimento e infraestrutura.',
                'qwen3.8-27b', 'workspaces/dot-dev-core', 'general', 'DOT'
            );
        """)
        await db.execute("""
            INSERT OR IGNORE INTO threads (id, dot_id, title, status)
            VALUES ('default-thread', 'dot-dev-core', 'Sessão Padrão', 'idle');
        """)
        await db.commit()
    logger.info("Banco SQLite Edge inicializado com sucesso em modo WAL com migrações.")


@asynccontextmanager
async def get_db(db_path: str | None = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Gerenciador de contexto assíncrono para obter conexões leves ao SQLite.
    Garante foreign keys ativas e busy_timeout de 5000ms contra bloqueios de concorrência.
    """
    path = db_path or settings.sqlite_db_path
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA busy_timeout = 5000;")
        yield conn
