"""
Rotas REST para Gerenciamento de Tasks Agendadas, Shared Spaces e Workspaces do piDots.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ..storage.db import get_db
from ..storage.spaces_manager import SpacesManager
from ..storage.vector_store import VectorStore
from ..core.scheduler import EdgeScheduler, execute_proactive_task

router = APIRouter(tags=["Tasks & Spaces"])


class SaveDocumentPayload(BaseModel):
    dot_id: str
    filename: str
    content: str
    title: str | None = None


class VectorSearchPayload(BaseModel):
    query: str
    top_k: int = 3


class CreateTaskPayload(BaseModel):
    dot_id: str
    task_name: str
    cron_expr: str
    action_prompt: str
    target_channel_type: str = "internal"
    target_channel_id: str | None = None


class UpdateTaskPayload(BaseModel):
    is_active: bool | None = None
    cron_expr: str | None = None
    action_prompt: str | None = None
    task_name: str | None = None


@router.get("/api/spaces")
async def list_spaces(dot_id: str | None = None):
    """Lista todos os documentos versionados em Spaces."""
    return await SpacesManager.list_documents(dot_id=dot_id)


@router.get("/api/spaces/search")
async def search_spaces_get(query: str, top_k: int = 3):
    """Executa busca semântica KNN vetorial via GET nos documentos dos Spaces."""
    return await VectorStore.search(query=query, top_k=top_k)


@router.get("/api/spaces/{space_id}")
async def get_space_doc(space_id: str):
    """Retorna os dados completos de um documento em Space."""
    doc = await SpacesManager.get_document(space_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return doc


@router.get("/api/spaces/{space_id}/revisions")
async def get_space_revisions(space_id: str):
    """Retorna o histórico de revisões com diffs de um documento."""
    return await SpacesManager.get_revisions(space_id)


@router.post("/api/spaces")
async def save_space_doc(payload: SaveDocumentPayload):
    """Salva ou atualiza um documento com versionamento incremental e cálculo de diff."""
    return await SpacesManager.save_document(
        dot_id=payload.dot_id,
        filename=payload.filename,
        content=payload.content,
        title=payload.title
    )


@router.delete("/api/spaces/{space_id}")
async def delete_space_doc(space_id: str):
    """Remove um documento versionado e suas revisões do banco SQLite WAL."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id, filename FROM spaces WHERE id = ?", (space_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")
        await db.execute("DELETE FROM space_revisions WHERE space_id = ?", (space_id,))
        await db.execute("DELETE FROM spaces WHERE id = ?", (space_id,))
        await db.commit()
    return {"status": "deleted", "space_id": space_id, "filename": row["filename"]}


@router.post("/api/spaces/search")
async def search_spaces(payload: VectorSearchPayload):
    """Executa busca semântica KNN vetorial nos documentos dos Spaces."""
    return await VectorStore.search(query=payload.query, top_k=payload.top_k)


@router.get("/api/spaces/{space_id}/download")
async def download_space_doc(space_id: str):
    """Download individual do documento."""
    doc = await SpacesManager.get_document(space_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return Response(
        content=doc["content"],
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{doc['filename']}\""}
    )


@router.get("/api/tasks")
async def list_scheduled_tasks():
    """Lista todas as tarefas proativas agendadas (Dot Heartbeats)."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, dot_id, task_name, cron_expr, action_prompt,
                   target_channel_type, target_channel_id, next_run_at,
                   last_run_at, last_status, last_result_summary, is_active
            FROM scheduled_tasks ORDER BY next_run_at ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/api/tasks")
async def create_scheduled_task(payload: CreateTaskPayload):
    """Registra uma nova tarefa cron proativa para um Dot no SQLite WAL."""
    try:
        task_id = await EdgeScheduler.register_task(
            dot_id=payload.dot_id,
            task_name=payload.task_name,
            cron_expr=payload.cron_expr,
            action_prompt=payload.action_prompt,
            target_channel_type=payload.target_channel_type,
            target_channel_id=payload.target_channel_id
        )
        return {"id": task_id, "status": "scheduled", "task_name": payload.task_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/tasks/{task_id}/run")
async def run_scheduled_task_now(task_id: str, request: Request):
    """Dispara manualmente uma tarefa proativa agendada sob demanda."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, dot_id, task_name, cron_expr, action_prompt,
                   target_channel_type, target_channel_id, is_active
            FROM scheduled_tasks WHERE id = ?
            """,
            (task_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Tarefa '{task_id}' não encontrada.")
        task_dict = dict(row)

    if EdgeScheduler.is_running(task_id):
        return {"id": task_id, "status": "already_running", "task_name": task_dict["task_name"]}

    ai_provider = getattr(request.app.state, "ai_provider", None)
    await execute_proactive_task(task=task_dict, ai_provider=ai_provider)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT last_status, last_result_summary, last_run_at, next_run_at FROM scheduled_tasks WHERE id = ?",
            (task_id,)
        )
        updated = await cursor.fetchone()
        updated_dict = dict(updated) if updated else {}

    return {
        "id": task_id,
        "task_name": task_dict["task_name"],
        "status": updated_dict.get("last_status", "COMPLETED"),
        "summary": updated_dict.get("last_result_summary", ""),
        "last_run_at": updated_dict.get("last_run_at"),
        "next_run_at": updated_dict.get("next_run_at")
    }


@router.patch("/api/tasks/{task_id}")
async def update_scheduled_task(task_id: str, payload: UpdateTaskPayload):
    """Pausa, retoma ou atualiza parâmetros de uma tarefa agendada."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id, cron_expr, action_prompt, task_name, is_active FROM scheduled_tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Tarefa '{task_id}' não encontrada.")

        new_active = (1 if payload.is_active else 0) if payload.is_active is not None else row["is_active"]
        new_cron = payload.cron_expr.strip() if payload.cron_expr else row["cron_expr"]
        new_prompt = payload.action_prompt.strip() if payload.action_prompt else row["action_prompt"]
        new_name = payload.task_name.strip() if payload.task_name else row["task_name"]

        await db.execute(
            """
            UPDATE scheduled_tasks
            SET is_active = ?, cron_expr = ?, action_prompt = ?, task_name = ?
            WHERE id = ?
            """,
            (new_active, new_cron, new_prompt, new_name, task_id)
        )
        await db.commit()

    return {
        "id": task_id,
        "task_name": new_name,
        "is_active": bool(new_active),
        "cron_expr": new_cron,
        "status": "updated"
    }


@router.delete("/api/tasks/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Exclui uma tarefa agendada do banco de dados SQLite WAL."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id, task_name FROM scheduled_tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Tarefa '{task_id}' não encontrada.")
        await db.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
        await db.commit()

    return {"id": task_id, "task_name": row["task_name"], "status": "deleted"}


@router.get("/api/workspaces/{dot_id}/export.zip")
async def export_workspace_zip(dot_id: str):
    """Exporta o workspace completo de um Dot em formato ZIP."""
    zip_bytes = await SpacesManager.export_workspace_zip(dot_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=\"workspace_{dot_id}.zip\""}
    )

