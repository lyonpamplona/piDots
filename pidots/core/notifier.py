"""
Sistema de Notificações Remotas e Mensageria para Alertas HITL do piDots.
Opera com baixíssimo consumo de memória (sem bibliotecas externas pesadas).
Permite notificar o operador via Webhook HTTP e Telegram Bot para aprovação no celular.
"""

import httpx
import logging
from typing import Any
from datetime import datetime, timezone
from ..config import settings

logger = logging.getLogger("pidots.notifier")


class HITLNotifier:
    """Despachante assíncrono de notificações de governança e segurança."""

    @classmethod
    async def notify_approval_requested(
        cls,
        approval_id: str,
        dot_id: str,
        action_type: str,
        payload: str,
        risk_level: str = "HIGH",
        http_client: httpx.AsyncClient | None = None
    ) -> dict[str, Any]:
        """
        Dispara notificações para todos os canais configurados (Webhook / Telegram).
        Executado de forma não-bloqueante para não retardar o loop do agente.
        """
        results = {
            "webhook_sent": False,
            "telegram_sent": False,
            "errors": []
        }

        # 1. Disparo de Webhook HTTP POST
        if settings.webhook_notification_url:
            try:
                webhook_payload = {
                    "event": "hitl_approval_required",
                    "approval_id": approval_id,
                    "dot_id": dot_id,
                    "action_type": action_type,
                    "payload": payload,
                    "risk_level": risk_level,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "resolve_endpoint": f"/api/hitl/{approval_id}/resolve"
                }

                client = http_client or httpx.AsyncClient(timeout=5.0)
                try:
                    resp = await client.post(
                        settings.webhook_notification_url,
                        json=webhook_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    results["webhook_sent"] = resp.status_code in (200, 201, 202, 204)
                    logger.info("Webhook HITL enviado com status: %d", resp.status_code)
                finally:
                    if not http_client:
                        await client.aclose()

            except Exception as e:
                err_msg = f"Falha ao enviar Webhook HITL: {str(e)}"
                logger.warning(err_msg)
                results["errors"].append(err_msg)

        # 2. Disparo de Mensagem no Telegram Bot
        if settings.telegram_bot_token and settings.telegram_chat_id:
            try:
                telegram_text = (
                    f"[ALERTA DE SEGURANCA HITL]\n"
                    f"Coworker: {dot_id}\n"
                    f"Risco: {risk_level}\n"
                    f"Acao: {action_type}\n"
                    f"Payload:\n{payload[:300]}\n\n"
                    f"ID de Aprovacao:\n{approval_id}\n\n"
                    f"Para resolver via API:\n"
                    f"POST /api/hitl/{approval_id}/resolve\n"
                    f"{{\"approved\": true}}"
                )

                tg_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
                tg_payload = {
                    "chat_id": settings.telegram_chat_id,
                    "text": telegram_text
                }

                client = http_client or httpx.AsyncClient(timeout=5.0)
                try:
                    resp = await client.post(tg_url, json=tg_payload)
                    results["telegram_sent"] = resp.status_code == 200
                    logger.info("Telegram HITL enviado com status: %d", resp.status_code)
                finally:
                    if not http_client:
                        await client.aclose()

            except Exception as e:
                err_msg = f"Falha ao enviar Telegram HITL: {str(e)}"
                logger.warning(err_msg)
                results["errors"].append(err_msg)

        return results

    @classmethod
    async def notify_hitl_request(
        cls,
        approval_id: str,
        dot_id: str,
        action_type: str,
        payload: str,
        risk_level: str = "HIGH",
        http_client: httpx.AsyncClient | None = None
    ) -> dict[str, Any]:
        """Alias de compatibilidade retrocompatível para notify_approval_requested."""
        return await cls.notify_approval_requested(
            approval_id=approval_id,
            dot_id=dot_id,
            action_type=action_type,
            payload=payload,
            risk_level=risk_level,
            http_client=http_client
        )


# Alias de compatibilidade retroativa para módulos legados
Notifier = HITLNotifier
