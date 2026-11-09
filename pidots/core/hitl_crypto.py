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
    Suporta token compacto de exatamente 16 caracteres hexadecimais (para Telegram callback_data)
    ou o hash completo de 64 caracteres hexadecimais (para webhooks REST/JSON).
    """
    if not approval_id or not action or not token:
        return False
    sanitized_token = token.strip().lower()
    try:
        token_bytes = sanitized_token.encode("ascii")
    except (UnicodeEncodeError, ValueError):
        return False

    if len(sanitized_token) == 16:
        expected = generate_hitl_hmac(approval_id, action, secret)
        return hmac.compare_digest(expected.encode("ascii"), token_bytes)
    elif len(sanitized_token) == 64:
        key = (secret or settings.hitl_hmac_secret).encode("utf-8")
        payload = f"{approval_id}:{action}".encode("utf-8")
        full_digest = hmac.new(key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(full_digest.encode("ascii"), token_bytes)
    return False
