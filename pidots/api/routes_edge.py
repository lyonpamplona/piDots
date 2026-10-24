"""
Rotas REST de Telemetria, Hardware Triggers, Configurações a Quente e Manutenção do piDots.
"""

import json
import time
import logging
import resource
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import settings
from ..storage.db import get_db
from ..core.edge_triggers import EdgeHardwareTriggers
from ..providers.openai_client import OpenAIUniversalProvider
from ..tools.terminal import TerminalSandbox
from ..tools.file_ops import FileManager
from ..tools.registry import ToolRegistry
from ..tools.mcp_client import LiteMCPClient, MCPRegistryManager

logger = logging.getLogger("pidots.api.edge")
router = APIRouter(tags=["Edge & System"])

APP_VERSION = "1.5.2"


def get_process_rss_mb() -> float:
    """Lê o consumo real de RAM (RSS) do processo Python atual em MB via /proc/self/status."""
    try:
        status_path = Path("/proc/self/status")
        if status_path.exists():
            for line in status_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return round(int(parts[1]) / 1024.0, 2)
    except Exception:
        pass
    try:
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
    except Exception:
        return 42.0


def get_soc_temperature() -> float:
    """Delega leitura térmica unificada para EdgeHardwareTriggers."""
    return EdgeHardwareTriggers.get_soc_temperature()


def get_memory_info() -> dict:
    """Delega leitura de memória RAM unificada para EdgeHardwareTriggers incluindo RSS do processo."""
    ram = EdgeHardwareTriggers.get_ram_metrics()
    return {
        "total_mb": ram["total_mb"],
        "used_mb": ram["used_mb"],
        "available_mb": ram["available_mb"],
        "process_rss_mb": get_process_rss_mb()
    }


class AISettingsUpdatePayload(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_retries: int | None = None
    timeout_seconds: float | None = None
    fallback_url: str | None = None
    fallback_api_key: str | None = None
    fallback_model: str | None = None
    circuit_breaker_consecutive_failures: int | None = None
    circuit_breaker_cooldown_seconds: float | None = None


class NotificationSettingsUpdatePayload(BaseModel):
    webhook_url: str | None = None
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    evolution_url: str | None = None
    evolution_key: str | None = None


class EdgeMaintenancePayload(BaseModel):
    days_threshold: int = 7
    create_backup: bool = False
    dot_id: str | None = None


class ComputerExecPayload(BaseModel):
    dot_id: str = "dot-coder"
    command: str
    timeout_seconds: float = 30.0


class ComputerWriteFilePayload(BaseModel):
    dot_id: str = "dot-coder"
    filename: str
    content: str
    sync_space: bool = True


class MCPServerRegisterPayload(BaseModel):
    server_name: str
    transport: str = "stdio"
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] | None = None
    sse_url: str | None = None
    http_endpoint: str | None = None


@router.get("/health")
async def health_check():
    """Retorna o estado de integridade e telemetria do Raspberry Pi 4B."""
    return {
        "status": "healthy",
        "system": "piDots Edge Core",
        "soc_temperature_celsius": get_soc_temperature(),
        "memory": get_memory_info(),
        "ai_provider": {
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "max_retries": settings.ai_max_retries
        },
        "database": {
            "path": settings.sqlite_db_path,
            "mode": "WAL"
        }
    }


class TriggerSimulationPayload(BaseModel):
    gpio_pin: int | None = None
    gpio_value: int | None = None
    mqtt_topic: str | None = None
    mqtt_payload: dict[str, Any] | str | None = None
    wake_supervisor: bool = True


@router.get("/api/edge/triggers")
async def get_edge_hardware_triggers():
    """Retorna o status em tempo real dos triggers de hardware (SoC Broadcom, MicroSD, RAM + RSS do processo)."""
    data = EdgeHardwareTriggers.check_triggers()
    data["process_rss_mb"] = get_process_rss_mb()
    return data


@router.post("/api/edge/triggers/simulate")
async def simulate_edge_physical_trigger(payload: TriggerSimulationPayload):
    """
    Simula um sinal físico de pino GPIO ou mensagem no barramento MQTT de borda,
    avalia os limiares e desperta proativamente o @dot-supervisor no SQLite WAL.
    """
    from ..core.edge_triggers import EdgeGPIOMonitor, EdgeMQTTListener

    mqtt_dispatched = 0
    wakeup_result = None

    if payload.gpio_pin is not None and payload.gpio_value is not None:
        EdgeGPIOMonitor.set_pin_simulation(payload.gpio_pin, payload.gpio_value)

    if payload.mqtt_topic:
        mqtt_dispatched = await EdgeMQTTListener.simulate_incoming_message(
            payload.mqtt_topic,
            payload.mqtt_payload if payload.mqtt_payload is not None else {"status": "triggered"}
        )
        if payload.wake_supervisor:
            wakeup_result = await EdgeHardwareTriggers.wake_supervisor_on_trigger(
                trigger_source=f"MQTT:{payload.mqtt_topic}",
                event_summary=f"Mensagem recebida em {payload.mqtt_topic}: {payload.mqtt_payload}",
                severity="WARNING"
            )

    report = await EdgeHardwareTriggers.evaluate_and_alert(
        notify_hitl=False,
        wake_supervisor=payload.wake_supervisor
    )

    if payload.gpio_pin is not None:
        EdgeGPIOMonitor.clear_simulation()

    if wakeup_result and "supervisor_wakeup" not in report:
        report["supervisor_wakeup"] = wakeup_result
    report["mqtt_handlers_dispatched"] = mqtt_dispatched
    return report


@router.get("/api/edge/tool-runs")
async def list_edge_tool_runs(dot_id: str | None = None, limit: int = 30):
    """Lista o histórico auditável de execuções de ferramentas e comandos no Sandbox (tool_runs)."""
    safe_limit = max(1, min(limit, 100))
    async with get_db() as db:
        if dot_id:
            cursor = await db.execute(
                """
                SELECT id, dot_id, tool_name, arguments_json, exit_code,
                       stdout_text, stderr_text, duration_ms, created_at
                FROM tool_runs
                WHERE dot_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (dot_id, safe_limit)
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, dot_id, tool_name, arguments_json, exit_code,
                       stdout_text, stderr_text, duration_ms, created_at
                FROM tool_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@router.post("/api/edge/computer/exec")
async def execute_in_dot_computer(payload: ComputerExecPayload):
    """
    Executa um comando diretamente no Computador de Borda (Bubblewrap Sandbox) do Dot
    quando o operador humano assume o controle em modo Takeover.
    """
    if not payload.command or not payload.command.strip():
        raise HTTPException(status_code=400, detail="Comando não pode ser vazio.")
    res = await TerminalSandbox.execute(
        dot_id=payload.dot_id,
        command=payload.command.strip(),
        timeout_seconds=min(max(payload.timeout_seconds, 1.0), 120.0)
    )
    return res


@router.get("/api/edge/computer/files")
async def list_or_read_computer_files(dot_id: str = "dot-coder", filename: str | None = None, subdirectory: str = ""):
    """Lista os arquivos do workspace de um Dot ou lê o conteúdo de um arquivo específico."""
    if filename:
        res = await FileManager.read_file(dot_id=dot_id, filename=filename)
        if "error" in res:
            raise HTTPException(status_code=404, detail=res["error"])
        return res
    return await FileManager.list_files(dot_id=dot_id, subdirectory=subdirectory)


@router.post("/api/edge/computer/files")
async def write_computer_file(payload: ComputerWriteFilePayload):
    """Grava atomicamente um arquivo no workspace do Dot (e opcionalmente sincroniza em Spaces)."""
    res = await FileManager.write_file(
        dot_id=payload.dot_id,
        filename=payload.filename,
        content=payload.content,
        sync_space=payload.sync_space
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.get("/api/tools")
async def list_available_tools():
    """Retorna o catálogo completo de ferramentas operacionais nativas e MCP disponíveis para os Dots."""
    registry = ToolRegistry()
    definitions = registry.get_tool_definitions()
    tools_catalog: list[dict[str, Any]] = []
    for t in definitions:
        fn = t.get("function", {})
        name = fn.get("name", "")
        is_mcp = name.startswith("mcp_")
        params = fn.get("parameters", {}).get("properties", {})
        required = fn.get("parameters", {}).get("required", [])
        tools_catalog.append({
            "name": name,
            "description": fn.get("description", ""),
            "category": "mcp" if is_mcp else "native",
            "parameters": list(params.keys()),
            "required": required,
            "schema": fn
        })
    return {
        "total": len(tools_catalog),
        "tools": tools_catalog
    }


@router.get("/api/mcp/servers")
async def list_mcp_servers():
    """Lista os servidores MCP Lite atualmente conectados ao piDots."""
    servers = []
    for name, client in MCPRegistryManager._active_clients.items():
        servers.append({
            "server_name": name,
            "transport": client.transport,
            "command": client.command,
            "args": client.args,
            "sse_url": client.sse_url,
            "http_endpoint": client.http_endpoint,
            "initialized": client._is_initialized
        })
    return {"servers": servers, "total": len(servers)}


@router.post("/api/mcp/servers")
async def register_mcp_server(payload: MCPServerRegisterPayload):
    """Registra e conecta a quente um servidor MCP Lite (STDIO ou SSE/HTTP)."""
    client = LiteMCPClient(
        server_name=payload.server_name,
        transport=payload.transport,
        command=payload.command,
        args=payload.args,
        env=payload.env,
        sse_url=payload.sse_url,
        http_endpoint=payload.http_endpoint
    )
    registry = ToolRegistry()
    registered_tools = await MCPRegistryManager.register_server(
        server_name=payload.server_name,
        client=client,
        tool_registry=registry
    )
    if not registered_tools and not client._is_initialized:
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível conectar ou inicializar o servidor MCP '{payload.server_name}'."
        )
    return {
        "status": "connected",
        "server_name": payload.server_name,
        "transport": payload.transport,
        "registered_tools": registered_tools
    }


@router.delete("/api/mcp/servers/{server_name}")
async def disconnect_mcp_server(server_name: str):
    """Desconecta e remove um servidor MCP ativo."""
    client = MCPRegistryManager.get_client(server_name)
    if not client:
        raise HTTPException(status_code=404, detail=f"Servidor MCP '{server_name}' não encontrado.")
    await client.close()
    MCPRegistryManager._active_clients.pop(server_name, None)
    return {"status": "disconnected", "server_name": server_name}


@router.post("/api/edge/settings/test-provider")
@router.post("/api/settings/ai/test")
async def test_ai_provider_connection(request: Request):
    """Realiza um diagnóstico de conectividade e estado do Circuit Breaker do provedor LLM configurado."""
    provider = getattr(request.app.state, "ai_provider", None)
    circuit_state = getattr(provider, "circuit_state", "CLOSED") if provider else "CLOSED"
    consecutive_failures = getattr(provider, "consecutive_failures", 0) if provider else 0

    start_ts = time.perf_counter()
    if not settings.ai_api_key or settings.ai_api_key in ("sua_chave_aqui", "placeholder"):
        return {
            "status": "auth_required",
            "reachable": False,
            "latency_ms": 0,
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "circuit_state": circuit_state,
            "consecutive_failures": consecutive_failures,
            "message": "Chave AI_API_KEY com valor placeholder ou não configurada."
        }

    try:
        if provider is None:
            provider = OpenAIUniversalProvider(
                base_url=settings.ai_base_url,
                api_key=settings.ai_api_key,
                default_model=settings.ai_model
            )
        resp = await provider.chat_completion(
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
            temperature=0.0
        )
        latency_ms = round((time.perf_counter() - start_ts) * 1000, 1)
        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "status": "ok",
            "reachable": True,
            "latency_ms": latency_ms,
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "circuit_state": getattr(provider, "circuit_state", "CLOSED"),
            "consecutive_failures": getattr(provider, "consecutive_failures", 0),
            "sample_reply": content[:80]
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_ts) * 1000, 1)
        return {
            "status": "error",
            "reachable": False,
            "latency_ms": latency_ms,
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "circuit_state": getattr(provider, "circuit_state", "CLOSED"),
            "consecutive_failures": getattr(provider, "consecutive_failures", 0),
            "message": str(exc)[:240]
        }


@router.post("/api/edge/maintenance")
async def trigger_edge_maintenance(payload: EdgeMaintenancePayload | None = None):
    """Executa sob demanda a suíte de compactação e saúde do MicroSD."""
    from ..storage.maintenance import EdgeMaintenanceManager
    p = payload or EdgeMaintenancePayload()
    backup_dir = None
    if p.create_backup:
        backup_dir = str(Path(settings.sqlite_db_path).parent / "backups")

    report = await EdgeMaintenanceManager.run_full_maintenance(
        backup_dir=backup_dir,
        days_threshold=p.days_threshold,
        dot_id=p.dot_id
    )
    return report



@router.get("/api/settings")
async def get_system_settings(request: Request):
    """Retorna o estado operacional e configurações ativas do piDots."""
    masked_key = ""
    if settings.ai_api_key:
        masked_key = settings.ai_api_key[:4] + "..." + settings.ai_api_key[-3:] if len(settings.ai_api_key) > 7 else "***"

    masked_fallback_key = ""
    if settings.ai_fallback_api_key:
        masked_fallback_key = settings.ai_fallback_api_key[:4] + "..." + settings.ai_fallback_api_key[-3:] if len(settings.ai_fallback_api_key) > 7 else "***"

    masked_evo_key = ""
    if settings.evolution_api_key:
        masked_evo_key = settings.evolution_api_key[:3] + "..." + settings.evolution_api_key[-3:] if len(settings.evolution_api_key) > 6 else "***"

    provider = getattr(request.app.state, "ai_provider", None)
    circuit_state = getattr(provider, "circuit_state", "CLOSED") if provider else "CLOSED"
    consecutive_failures = getattr(provider, "consecutive_failures", 0) if provider else 0

    return {
        "ai": {
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "api_key_masked": masked_key,
            "max_retries": settings.ai_max_retries,
            "timeout_seconds": settings.ai_timeout_seconds,
            "fallback_url": settings.ai_fallback_url,
            "fallback_configured": bool(settings.ai_fallback_url),
            "fallback_model": settings.ai_fallback_model,
            "fallback_api_key_masked": masked_fallback_key,
            "circuit_breaker": {
                "state": circuit_state,
                "consecutive_failures": consecutive_failures,
                "threshold": settings.ai_circuit_breaker_consecutive_failures,
                "cooldown_seconds": settings.ai_circuit_breaker_cooldown_seconds
            }
        },
        "notifications": {
            "webhook_url": settings.webhook_notification_url,
            "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
            "telegram_chat_id": settings.telegram_chat_id,
            "evolution_api_url": settings.evolution_api_url,
            "evolution_api_key_masked": masked_evo_key
        },
        "governance": {
            "max_iterations_per_goal": settings.max_iterations_per_goal,
            "thermal_throttle_enabled": settings.enable_thermal_throttle,
            "thermal_limit_celsius": settings.thermal_limit_celsius
        }
    }


@router.post("/api/settings/ai")
async def update_ai_settings(payload: AISettingsUpdatePayload, request: Request):
    """Atualiza a quente os parâmetros de IA sem reiniciar o contêiner."""
    settings.update_ai_params(
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
        max_retries=payload.max_retries,
        timeout_seconds=payload.timeout_seconds,
        fallback_url=payload.fallback_url,
        fallback_api_key=payload.fallback_api_key,
        fallback_model=payload.fallback_model,
        circuit_breaker_consecutive_failures=payload.circuit_breaker_consecutive_failures,
        circuit_breaker_cooldown_seconds=payload.circuit_breaker_cooldown_seconds
    )
    provider = getattr(request.app.state, "ai_provider", None)
    if provider is not None:
        provider.base_url = settings.ai_base_url.rstrip("/")
        provider.api_key = settings.ai_api_key
        provider.default_model = settings.ai_model
        provider.max_retries = settings.ai_max_retries
        provider.timeout = settings.ai_timeout_seconds
        provider.fallback_url = settings.ai_fallback_url
        provider.fallback_api_key = settings.ai_fallback_api_key
        provider.fallback_model = settings.ai_fallback_model
        provider.circuit_breaker_threshold = settings.ai_circuit_breaker_consecutive_failures
        provider.circuit_breaker_cooldown = settings.ai_circuit_breaker_cooldown_seconds
    else:
        request.app.state.ai_provider = OpenAIUniversalProvider(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            default_model=settings.ai_model,
            http_client=getattr(request.app.state, "http_client", None),
            fallback_url=settings.ai_fallback_url,
            fallback_api_key=settings.ai_fallback_api_key,
            fallback_model=settings.ai_fallback_model,
            circuit_breaker_threshold=settings.ai_circuit_breaker_consecutive_failures,
            circuit_breaker_cooldown=settings.ai_circuit_breaker_cooldown_seconds
        )

    if payload.model:
        async with get_db() as db:
            await db.execute(
                "UPDATE dots SET model = ? WHERE is_core = 1",
                (settings.ai_model,)
            )
            await db.commit()

    return {"status": "success", "message": "Parâmetros de IA atualizados a quente."}


@router.post("/api/settings/notifications")
async def update_notification_settings(payload: NotificationSettingsUpdatePayload):
    """Atualiza a quente os canais de notificação e alertas remotos."""
    settings.update_notification_params(
        webhook_url=payload.webhook_url,
        telegram_token=payload.telegram_token,
        telegram_chat_id=payload.telegram_chat_id,
        evolution_url=payload.evolution_url,
        evolution_key=payload.evolution_key
    )
    return {"status": "success", "message": "Canais de notificação atualizados com sucesso."}


@router.get("/api/changelog")
async def get_changelog():
    """Retorna as notas de versão e histórico do changelog do piDots."""
    changelog_path = Path(__file__).resolve().parent.parent.parent / "data" / "changelog.json"
    if not changelog_path.exists():
        return JSONResponse(
            content={
                "system": "piDots",
                "current_version": APP_VERSION,
                "patch_notes": {"version": APP_VERSION, "categories": {}},
                "history": []
            },
            headers={"Cache-Control": "public, max-age=60"}
        )
    try:
        content = json.loads(changelog_path.read_text(encoding="utf-8"))
        return JSONResponse(
            content=content,
            headers={"Cache-Control": "public, max-age=300"}
        )
    except Exception as exc:
        logger.error(f"Erro ao ler data/changelog.json: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar o changelog")


@router.get("/data/locales/{lang}.json")
async def get_locale_dictionary(lang: str):
    """Serve os dicionários de internacionalização (PT/EN) para o frontend com cache de borda."""
    if lang not in ["pt", "en"]:
        raise HTTPException(status_code=404, detail="Locale não suportado")
    locale_path = Path(__file__).resolve().parent.parent.parent / "data" / "locales" / f"{lang}.json"
    if not locale_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de locale não encontrado")
    try:
        content = json.loads(locale_path.read_text(encoding="utf-8"))
        return JSONResponse(
            content=content,
            headers={
                "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
                "Content-Language": "pt-BR" if lang == "pt" else "en-US"
            }
        )
    except Exception as exc:
        logger.error(f"Erro ao carregar locale {lang}: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar dicionário de idioma")


@router.get("/static/pidots-i18n.js")
async def get_i18n_script():
    """Serve o micro-motor Vanilla JS de internacionalização com cache estático (rota de retrocompatibilidade)."""
    script_path = Path(__file__).resolve().parent.parent.parent / "static" / "js" / "core" / "pidots-i18n.js"
    if not script_path.exists():
        script_path = Path(__file__).resolve().parent.parent.parent / "static" / "pidots-i18n.js"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script i18n não encontrado")
    return Response(
        content=script_path.read_text(encoding="utf-8"),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"}
    )
