"""
Configurações centrais do piDots com validação Pydantic.
Suporta qualquer provedor de IA compatível com a API/SDK da OpenAI.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


import os


def _resolve_default_db_path() -> str:
    """Resolve o caminho padrao do banco com fallback para portabilidade entre hosts e CI."""
    env_val = os.getenv("SQLITE_DB_PATH")
    if env_val:
        return env_val
    root = Path(__file__).resolve().parent.parent
    return str(root / "data" / "pidots.db")


def _resolve_default_workspaces_root() -> str:
    """Resolve a raiz de workspaces com fallback para portabilidade entre hosts e CI."""
    env_val = os.getenv("WORKSPACES_ROOT")
    if env_val:
        return env_val
    root = Path(__file__).resolve().parent.parent
    return str(root / "workspaces")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Provedor de IA (OpenAI SDK Compatible)
    ai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Endpoint base da API OpenAI-compatível (ex: OpenAI, OpenRouter, Groq, DeepSeek ou gateway local)"
    )
    ai_api_key: str = Field(
        default="",
        description="Chave de autenticação Bearer para a API de IA"
    )
    ai_model: str = Field(
        default="gpt-4o-mini",
        description="Identificador do modelo no provedor (ex: gpt-4o-mini, gpt-4o, claude-3-5-sonnet, llama-3.1-8b)"
    )
    ai_max_retries: int = Field(
        default=3,
        description="Número máximo de tentativas com backoff exponencial para 503/429"
    )
    ai_timeout_seconds: float = Field(
        default=60.0,
        description="Timeout máximo por requisição HTTP para inferência"
    )

    # Provedor de IA Secundário (Failover Opcional e Desativado por Padrão)
    ai_fallback_url: str | None = Field(
        default=None,
        description="URL secundária para failover de inferência (opcional e desativada por padrão)"
    )
    ai_fallback_api_key: str | None = Field(
        default=None,
        description="Chave de autenticação para o provedor secundário de failover (opcional)"
    )
    ai_fallback_model: str | None = Field(
        default=None,
        description="Identificador do modelo secundário para failover (opcional)"
    )
    ai_circuit_breaker_consecutive_failures: int = Field(
        default=3,
        description="Número de falhas consecutivas com 5xx/timeout para abrir o Circuit Breaker do primário"
    )
    ai_circuit_breaker_cooldown_seconds: float = Field(
        default=60.0,
        description="Janela de cooldown em segundos com o circuito aberto antes de tentar requisição canário"
    )

    # Infraestrutura
    host: str = Field(default="0.0.0.0", description="IP de escuta do servidor FastAPI")
    port: int = Field(default=8000, description="Porta de escuta do servidor FastAPI")
    debug: bool = Field(default=False, description="Modo debug")

    # Desacoplamento de Portas Edge (Cloudflare Tunnel & Nginx)
    port_landing: int = Field(default=8081, description="Porta de escuta da Landing Page de apresentacao")
    port_app: int = Field(default=8082, description="Porta de escuta do console Workspace SPA dos agentes")
    port_docs: int = Field(default=8083, description="Porta de escuta do Guia Didatico e documentacao")
    port_gateway: int = Field(default=8088, description="Porta do gateway unificado de desenvolvimento")

    # Armazenamento e Diretórios
    sqlite_db_path: str = Field(
        default_factory=_resolve_default_db_path,
        description="Caminho do arquivo de banco SQLite WAL"
    )
    workspaces_root: str = Field(
        default_factory=_resolve_default_workspaces_root,
        description="Diretório raiz para armazenamento de workspaces isolados dos Dots"
    )

    # Governança e Limites de Hardware Edge
    strict_sandbox: bool = Field(
        default=False,
        description="Se verdadeiro, recusa comandos shell caso o Bubblewrap (bwrap) não esteja disponível ou falhe"
    )
    enable_legacy_redirects: bool = Field(
        default=True,
        description="Se verdadeiro, mantém redirecionamentos 308 (/apresentacao, /guia, /console) no FastAPI; desative se delegados exclusivamente ao Nginx"
    )
    max_iterations_per_goal: int = Field(
        default=8,
        description="Teto de ciclos de raciocínio autônomo para prevenir loops infinitos"
    )
    enable_thermal_throttle: bool = Field(
        default=True,
        description="Habilitar checagem térmica no SoC Broadcom do Raspberry Pi 4B"
    )
    thermal_limit_celsius: float = Field(
        default=78.0,
        description="Temperatura limite em °C antes de ativar backoff térmico"
    )

    # Notificações e Webhooks HITL
    webhook_notification_url: str | None = Field(
        default=None,
        description="URL de webhook HTTP POST para envio imediato de alertas HITL"
    )
    telegram_bot_token: str | None = Field(
        default=None,
        description="Token de bot do Telegram para notificações diretas ao operador"
    )
    telegram_chat_id: str | None = Field(
        default=None,
        description="ID do chat do Telegram para recebimento de alertas HITL"
    )

    # Gateway de Mensageria e WhatsApp (Evolution API)
    evolution_api_url: str = Field(
        default="http://host.docker.internal:8080",
        description="URL base da Evolution API para mensageria WhatsApp"
    )
    evolution_api_key: str = Field(
        default="",
        description="Chave de autenticação (apikey) para a Evolution API"
    )
    evolution_instance: str = Field(
        default="pidots",
        description="Identificador da instancia na Evolution API para envio de mensagens WhatsApp"
    )

    # Governança Criptográfica HITL via Mensageria (Fase 15)
    hitl_hmac_secret: str = Field(
        default="pidots-edge-hmac-secret-key-v15",
        description="Chave secreta para assinatura HMAC-SHA256 de aprovações HITL via mensageria"
    )

    # Barramento Físico GPIO & Sensores de Borda (Fase 17)
    gpio_enabled: bool = Field(
        default=False,
        description="Habilita monitoramento de pinos GPIO no nó Linux Edge (Raspberry Pi 4B)"
    )

    # Barramento MQTT Edge Triggers (Fase 17)
    mqtt_broker_host: str | None = Field(
        default=None,
        description="Host do broker MQTT local para eventos de sensores Edge (opcional)"
    )
    mqtt_broker_port: int = Field(
        default=1883,
        description="Porta de escuta do broker MQTT local"
    )
    mqtt_topic_prefix: str = Field(
        default="pidots/edge",
        description="Prefixo de tópicos MQTT escutados pelo piDots"
    )

    def ensure_directories(self) -> None:
        """Garante que os diretórios necessários existam no disco."""
        db_dir = Path(self.sqlite_db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        (db_dir / "backups").mkdir(parents=True, exist_ok=True)
        Path(self.workspaces_root).mkdir(parents=True, exist_ok=True)

    def update_ai_params(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
        timeout_seconds: float | None = None,
        fallback_url: str | None = None,
        fallback_api_key: str | None = None,
        fallback_model: str | None = None,
        circuit_breaker_consecutive_failures: int | None = None,
        circuit_breaker_cooldown_seconds: float | None = None
    ) -> None:
        """Atualiza os parâmetros de IA em memória dinamicamente."""
        if base_url is not None:
            self.ai_base_url = base_url.rstrip("/")
        if api_key is not None:
            self.ai_api_key = api_key
        if model is not None:
            self.ai_model = model
        if max_retries is not None:
            self.ai_max_retries = max_retries
        if timeout_seconds is not None:
            self.ai_timeout_seconds = timeout_seconds
        if fallback_url is not None:
            self.ai_fallback_url = fallback_url.rstrip("/") if fallback_url.strip() else None
        if fallback_api_key is not None:
            self.ai_fallback_api_key = fallback_api_key.strip() if fallback_api_key.strip() else None
        if fallback_model is not None:
            self.ai_fallback_model = fallback_model.strip() if fallback_model.strip() else None
        if circuit_breaker_consecutive_failures is not None:
            self.ai_circuit_breaker_consecutive_failures = max(1, circuit_breaker_consecutive_failures)
        if circuit_breaker_cooldown_seconds is not None:
            self.ai_circuit_breaker_cooldown_seconds = max(1.0, circuit_breaker_cooldown_seconds)

    def update_notification_params(
        self,
        webhook_url: str | None = None,
        telegram_token: str | None = None,
        telegram_chat_id: str | None = None,
        evolution_url: str | None = None,
        evolution_key: str | None = None
    ) -> None:
        """Atualiza os canais de notificação em memória dinamicamente."""
        if webhook_url is not None:
            self.webhook_notification_url = webhook_url if webhook_url.strip() else None
        if telegram_token is not None:
            self.telegram_bot_token = telegram_token if telegram_token.strip() else None
        if telegram_chat_id is not None:
            self.telegram_chat_id = telegram_chat_id if telegram_chat_id.strip() else None
        if evolution_url is not None:
            self.evolution_api_url = evolution_url.strip()
        if evolution_key is not None:
            self.evolution_api_key = evolution_key.strip()


settings = Settings()
