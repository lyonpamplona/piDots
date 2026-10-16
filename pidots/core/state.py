"""
Modelos de dados Pydantic e especificação de eventos do protocolo AG-UI para o piDots.
"""

from typing import Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def now_utc() -> datetime:
    """Retorna timestamp UTC ciente de fuso horário sem usar utcnow depreciado."""
    return datetime.now(timezone.utc)


class DotModel(BaseModel):
    """Representa um AI Coworker persistente."""
    id: str
    name: str
    role: str
    system_prompt: str
    model: str
    workspace_path: str
    is_active: bool = True
    archetype: str = "generalist"
    avatar_stamp: str = "[DOT]"
    is_core: bool = False
    created_at: datetime = Field(default_factory=now_utc)


class ThreadModel(BaseModel):
    """Fio de conversa durável associado a um Dot."""
    id: str
    dot_id: str
    primary_dot_id: str | None = None
    title: str
    status: Literal["idle", "thinking", "running", "proactive", "awaiting_hitl", "completed", "error"] = "idle"
    created_at: datetime = Field(default_factory=now_utc)


class MessageModel(BaseModel):
    """Mensagem de diálogo multi-turn."""
    id: str
    thread_id: str
    actor_id: str | None = None
    actor_type: str = "user"
    target_dot_id: str | None = None
    visibility: Literal["public", "internal", "ephemeral"] = "public"
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    thought_log: str | None = None
    tool_calls_json: str | None = None
    parent_message_id: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class SpaceDocumentModel(BaseModel):
    """Documento ou artefato persistido e versionado no Space de um Dot."""
    id: str
    dot_id: str
    filename: str
    title: str
    content: str
    version: int = 1
    mime_type: str = "text/markdown"
    created_at: datetime = Field(default_factory=now_utc)


class HITLApprovalModel(BaseModel):
    """Solicitação de aprovação humana (Human-in-the-Loop)."""
    id: str
    dot_id: str
    thread_id: str | None = None
    action_type: str
    payload: str
    risk_level: Literal["LOW", "MEDIUM", "WARNING", "HIGH", "CRITICAL"] = "HIGH"
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    reviewer_notes: str | None = None
    requested_at: datetime = Field(default_factory=now_utc)
    resolved_at: datetime | None = None


class AGUIEvent(BaseModel):
    """Evento transmitido via Server-Sent Events (SSE) para a UI."""
    event: Literal[
        "run:started",
        "thought:delta",
        "tool:called",
        "tool:result",
        "self_healing:triggered",
        "hitl:approval_required",
        "artifact:updated",
        "run:finished",
        "state:sync"
    ]
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=now_utc)
