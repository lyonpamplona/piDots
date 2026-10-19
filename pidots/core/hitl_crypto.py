"""
Módulo de Criptografia e Assinatura HMAC-SHA256 para Governança HITL Remota do piDots.
Garante autenticidade e não-repúdio de callbacks de aprovação vindos de mensageiros
como Telegram e WhatsApp (Evolution API) sem expor segredos nem permitir forjamento de ações.
"""

import hmac
import hashlib
import logging
from ..config import settings

logger = logging.getLogger("pidots.hitl_crypto")


def generate_hitl_hmac(approval_id: str, action: str, secret: str | None = None) -> str:
    """
    Gera assinatura HMAC-SHA256 para o par (approval_id, action).
    Retorna 16 caracteres hexadecimais para caber com folga no limite de 64 bytes
    do callback_data do Telegram Bot API.
    """
    key = (secret or settings.hitl_hmac_secret).encode("utf-8")
    payload = f"{approval_id}:{action}".encode("utf-8")
    digest = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return digest[:16]


def verify_hitl_hmac(approval_id: str, action: str, token: str, secret: str | None = None) -> bool:
    """
    Verifica a autenticidade da assinatura HMAC-SHA256 em tempo constante (anti-timing attacks).
    """
    if not approval_id or not action or not token:
        return False
    expected = generate_hitl_hmac(approval_id, action, secret)
    # Suporta tokens de 16 chars ou tokens completos caso enviados por webhook REST
    if len(token) == 16:
        return hmac.compare_digest(expected, token)
    elif len(token) == 64:
        key = (secret or settings.hitl_hmac_secret).encode("utf-8")
        payload = f"{approval_id}:{action}".encode("utf-8")
        full_digest = hmac.new(key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(full_digest, token)
    return False
