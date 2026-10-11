"""
Configurações centrais do piDots com validação Pydantic.
Suporta qualquer provedor de IA compatível com a API/SDK da OpenAI.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


import os


def _resolve_default_db_path() -> str:
    """Resolve o caminho padrão do banco com fallback para portabilidade entre hosts e CI."""
    env_val = os.getenv("SQLITE_DB_PATH")
    if env_val:
        return env_val
    root = Path(__file__).resolve().parent.parent
    if (root / "data").exists():
        return str(root / "data" / "pidots.db")
    return str(Path.cwd() / "data" / "pidots.db")


def _resolve_default_workspaces_root() -> str:
    """Resolve a raiz de workspaces com fallback para portabilidade entre hosts e CI."""
    env_val = os.getenv("WORKSPACES_ROOT")
    if env_val:
        return env_val
    root = Path(__file__).resolve().parent.parent
    if (root / "workspaces").exists():
        return str(root / "workspaces")
    return str(Path.cwd() / "workspaces")


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
        default="qwen3.8-27b",
        description="Identificador do modelo no provedor (ex: qwen3.8-27b, gpt-4o, claude-3-5-sonnet)"
    )
    ai_max_retries: int = Field(
        default=3,
        description="Número máximo de tentativas com backoff exponencial para 503/429"
    )
    ai_timeout_seconds: float = Field(
        default=60.0,
        description="Timeout máximo por requisição HTTP para inferência"
    )

    # Infraestrutura
    host: str = Field(default="0.0.0.0", description="IP de escuta do servidor FastAPI")
    port: int = Field(default=8000, description="Porta de escuta do servidor FastAPI")
    debug: bool = Field(default=False, description="Modo debug")

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
    max_iterations_per_goal: int = Field(
        default=8,
        description="Teto de ciclos de raciocínio autônomo para prevenir loops infinitos"
    )
    enable_thermal_throttle: bool = Field(
        default=True,
        description="Habilitar checagem térmica no SoC Broadcom do Raspberry Pi 4B"
    )
    thermal_limit_celsius: float = Field(
        default=72.0,
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

    def ensure_directories(self) -> None:
        """Garante que os diretórios necessários existam no disco."""
        db_dir = Path(self.sqlite_db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        Path(self.workspaces_root).mkdir(parents=True, exist_ok=True)

    def update_ai_params(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
        timeout_seconds: float | None = None
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
