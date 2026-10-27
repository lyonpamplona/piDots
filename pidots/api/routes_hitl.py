"""
Rotas REST para Governança Human-in-the-Loop (HITL) do piDots.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..storage.db import get_db
from ..core.hitl import HITLManager

router = APIRouter(tags=["HITL"])


class HITLResolutionPayload(BaseModel):
    approved: bool
    notes: str | None = None
    reviewer_notes: str | None = None
    execute_action: bool = True
    execute_immediately: bool | None = None
    modified_args: dict | str | None = None


class WebhookCallbackPayload(BaseModel):
    approval_id: str
    approved: bool
    notes: str | None = None
    hmac_token: str | None = None


@router.get("/api/hitl/pending")
async def list_pending_hitl():
    """Lista solicitações de aprovação humana pendentes após purgar itens com TTL expirado."""
    await HITLManager.expire_stale_approvals()
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM hitl_approvals WHERE status = 'PENDING' ORDER BY requested_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/api/hitl/expire-stale")
async def trigger_expire_stale_hitl():
    """Executa varredura imediata de TTL (30 min) nas solicitações HITL pendentes e retorna os IDs expirados."""
    expired_ids = await HITLManager.expire_stale_approvals()
    return {
        "status": "success",
        "event": "hitl:expired",
        "expired_count": len(expired_ids),
        "expired_ids": expired_ids
    }


@router.get("/api/hitl/history")
async def list_hitl_history(limit: int = 30):
    """Lista o histórico forense de aprovações, vetos e expirações HITL."""
    await HITLManager.expire_stale_approvals()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM hitl_approvals ORDER BY COALESCE(resolved_at, requested_at) DESC LIMIT ?",
            (max(1, min(limit, 100)),)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/api/hitl/{approval_id}")
async def get_hitl_approval_detail(approval_id: str):
    """Retorna os argumentos congelados no servidor de uma solicitação HITL específica (Padrão OpenDots)."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM hitl_approvals WHERE id = ?", (approval_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada.")
        return dict(row)


@router.post("/api/hitl/{approval_id}/resolve")
async def resolve_hitl(approval_id: str, payload: HITLResolutionPayload):
    """Resolve (aprova ou rejeita) uma solicitação Human-in-the-Loop e despacha a ação se aprovada."""
    effective_notes = payload.notes or payload.reviewer_notes
    success = await HITLManager.resolve_approval(approval_id, payload.approved, effective_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada ou já resolvida.")

    should_execute = payload.execute_immediately if payload.execute_immediately is not None else payload.execute_action
    execution_result = None
    if payload.approved and should_execute:
        execution_result = await HITLManager.execute_approved_action(
            approval_id,
            modified_args=payload.modified_args
        )

    return {
        "status": "success",
        "approval_id": approval_id,
        "approved": payload.approved,
        "decision": "APPROVED" if payload.approved else "REJECTED",
        "execution_result": execution_result,
        "execution": execution_result
    }


@router.post("/api/hitl/webhook-callback")
async def handle_hitl_webhook_callback(payload: WebhookCallbackPayload):
    """
    Endpoint de retorno para resolução de aprovação HITL via mensageria/webhook.
    Exige autenticação HMAC-SHA256 para prevenir resoluções não autorizadas de operações sensíveis.
    """
    from ..core.hitl_crypto import verify_hitl_hmac

    action = "approve" if payload.approved else "reject"
    if not payload.hmac_token or not verify_hitl_hmac(payload.approval_id, action, payload.hmac_token):
        raise HTTPException(
            status_code=403,
            detail="Assinatura HMAC-SHA256 ausente, inválida ou não autorizada para esta solicitação HITL."
        )

    success = await HITLManager.resolve_approval(
        approval_id=payload.approval_id,
        approved=payload.approved,
        notes=payload.notes or f"Resolvido via Webhook Callback com HMAC validado (Ação: {action})"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada ou já resolvida.")
    return {
        "status": "success",
        "approval_id": payload.approval_id,
        "resolved_state": "APPROVED" if payload.approved else "REJECTED"
    }


class SignedResolutionPayload(BaseModel):
    approval_id: str
    action: str  # "approve" ou "reject"
    hmac_token: str
    notes: str | None = None


@router.post("/api/hitl/signed-resolve")
async def resolve_hitl_signed(payload: SignedResolutionPayload):
    """Resolve uma solicitação HITL mediante validação criptográfica de assinatura HMAC-SHA256."""
    from ..core.hitl_crypto import verify_hitl_hmac

    is_valid = verify_hitl_hmac(payload.approval_id, payload.action, payload.hmac_token)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Assinatura HMAC-SHA256 inválida ou não autorizada.")

    approved = (payload.action.lower() in ("approve", "aprovar", "a"))
    success = await HITLManager.resolve_approval(
        approval_id=payload.approval_id,
        approved=approved,
        notes=payload.notes or f"Resolvido com assinatura HMAC válida (Ação: {payload.action})"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Solicitação HITL não encontrada ou já resolvida.")

    return {
        "status": "success",
        "approval_id": payload.approval_id,
        "resolved_state": "APPROVED" if approved else "REJECTED"
    }
