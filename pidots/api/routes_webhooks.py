"""
Rotas REST para Webhooks Externos (Genérico, Telegram e WhatsApp) do piDots.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..storage.db import get_db
from ..core.messaging_gateway import MessagingGateway, UnifiedIncomingMessage
from .deps import get_ai_provider, get_http_client

router = APIRouter(tags=["Webhooks"])


class GenericIncomingWebhookPayload(BaseModel):
    text: str
    sender_name: str = "Webhook External"
    sender_id: str = "webhook-user"
    reply_target_id: str | None = None


@router.post("/api/webhooks/incoming/{dot_id}")
async def handle_generic_incoming_webhook(dot_id: str, payload: GenericIncomingWebhookPayload, request: Request):
    """Webhook genérico universal para envio de mensagens a um Dot por APIs, scripts ou CI/CD."""
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

    unified_msg = UnifiedIncomingMessage(
        platform="generic_webhook",
        sender_id=payload.sender_id,
        sender_name=payload.sender_name,
        text=payload.text,
        reply_target_id=payload.reply_target_id or payload.sender_id
    )
    ai_provider = get_ai_provider(request)
    http_client = get_http_client(request)
    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=ai_provider,
        http_client=http_client
    )
    return {
        "status": "success",
        "dot_id": dot_id,
        "response": response_text
    }


@router.post("/api/webhooks/telegram/{dot_id}")
async def handle_telegram_webhook(dot_id: str, request: Request):
    """Recebe webhooks oficiais de mensagens e callbacks interativos da API de bots do Telegram."""
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    # 1. Tratamento de Callback Interativo HITL (Botões Inline no Telegram)
    callback_query = body.get("callback_query")
    if callback_query:
        cb_id = callback_query.get("id", "")
        cb_data = callback_query.get("data", "")
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
        message_id = callback_query.get("message", {}).get("message_id")

        if cb_data.startswith("h:a:") or cb_data.startswith("h:r:"):
            from ..core.hitl import HITLManager
            from ..core.hitl_crypto import verify_hitl_hmac
            from ..config import settings

            parts = cb_data.split(":")
            if len(parts) >= 4:
                act_code = parts[1]
                approval_id = parts[2]
                hmac_token = parts[3]
                action = "approve" if act_code == "a" else "reject"

                if verify_hitl_hmac(approval_id, action, hmac_token):
                    approved = (action == "approve")
                    success = await HITLManager.resolve_approval(
                        approval_id=approval_id,
                        approved=approved,
                        notes="Resolvido via Telegram Callback Interativo (HMAC-SHA256 validado)"
                    )
                    status_text = "HOMOLOGADA" if approved else "BLOQUEADA"
                    # Responde ao Telegram se o token do bot estiver configurado
                    http_client = get_http_client(request)
                    if settings.telegram_bot_token and cb_id:
                        ans_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/answerCallbackQuery"
                        await http_client.post(ans_url, json={
                            "callback_query_id": cb_id,
                            "text": f"Operacao {status_text} com sucesso."
                        })
                    return {
                        "status": "hitl_resolved",
                        "approval_id": approval_id,
                        "approved": approved,
                        "resolved_success": success
                    }
                else:
                    return {
                        "status": "error",
                        "error": "Assinatura HMAC-SHA256 inválida ou expirada."
                    }

    message_data = body.get("message", {})
    text = message_data.get("text", "")
    if not text:
        return {"status": "ignored", "reason": "Sem mensagem de texto"}

    chat_id = str(message_data.get("chat", {}).get("id", ""))
    from_data = message_data.get("from", {})
    sender_id = str(from_data.get("id", chat_id))
    sender_name = from_data.get("first_name", "Telegram User")

    unified_msg = UnifiedIncomingMessage(
        platform="telegram",
        sender_id=sender_id,
        sender_name=sender_name,
        text=text,
        reply_target_id=chat_id
    )

    ai_provider = get_ai_provider(request)
    http_client = get_http_client(request)
    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=ai_provider,
        http_client=http_client
    )
    return {"status": "success", "dot_id": dot_id, "chat_id": chat_id, "response": response_text}


@router.post("/api/webhooks/whatsapp/{dot_id}")
async def handle_whatsapp_webhook(dot_id: str, request: Request):
    """Recebe webhooks de mensagens da Evolution API ou Baileys (WhatsApp)."""
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM dots WHERE id = ? AND is_active = 1", (dot_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Dot '{dot_id}' não encontrado ou inativo.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    data = body.get("data", {})
    key = data.get("key", {})
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "Mensagem enviada pelo próprio bot"}

    remote_jid = key.get("remoteJid", "")
    if not remote_jid or remote_jid == "status@broadcast":
        return {"status": "ignored", "reason": "Status broadcast ou remoteJid ausente"}

    push_name = data.get("pushName", "WhatsApp User")

    message_content = data.get("message", {})
    text = (
        message_content.get("conversation")
        or message_content.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "Sem conteúdo textual"}

    # Interceptação de comandos interativos de governança HITL no WhatsApp
    upper_text = text.upper()
    if upper_text.startswith("APROVAR ") or upper_text.startswith("BLOQUEAR "):
        parts = text.split()
        if len(parts) >= 3:
            cmd, approval_id, hmac_token = parts[0].upper(), parts[1], parts[2]
            action = "approve" if cmd == "APROVAR" else "reject"
            from ..core.hitl import HITLManager
            from ..core.hitl_crypto import verify_hitl_hmac

            if verify_hitl_hmac(approval_id, action, hmac_token):
                approved = (action == "approve")
                success = await HITLManager.resolve_approval(
                    approval_id=approval_id,
                    approved=approved,
                    notes="Resolvido via WhatsApp Mensageria (HMAC-SHA256 validado)"
                )
                verdict_txt = "HOMOLOGADA" if approved else "BLOQUEADA"
                reply_txt = f"[GOVERNANCA HITL]: Solicitacao '{approval_id}' foi {verdict_txt} com sucesso."
                http_client = get_http_client(request)
                await MessagingGateway.dispatch_outgoing_message("whatsapp", remote_jid, reply_txt, http_client)
                return {
                    "status": "hitl_resolved",
                    "approval_id": approval_id,
                    "approved": approved,
                    "resolved_success": success
                }

    unified_msg = UnifiedIncomingMessage(
        platform="whatsapp",
        sender_id=remote_jid,
        sender_name=push_name,
        text=text,
        reply_target_id=remote_jid
    )

    ai_provider = get_ai_provider(request)
    http_client = get_http_client(request)
    response_text = await MessagingGateway.process_and_respond(
        dot_id=dot_id,
        msg=unified_msg,
        ai_provider=ai_provider,
        http_client=http_client
    )
    return {"status": "success", "dot_id": dot_id, "remote_jid": remote_jid, "response": response_text}
