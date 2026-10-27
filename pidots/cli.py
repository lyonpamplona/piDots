"""
Interface de linha de comando do piDots para nós edge Linux.
Entrypoints para gerenciamento operacional e inicialização do servidor Edge.
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path

from .config import settings
from .storage.db import init_edge_database, get_db
from . import __version__

logger = logging.getLogger("pidots.cli")


def run_server() -> None:
    """Entrypoint dedicado para execução direta do servidor HTTP via 'pidots-server'."""
    import uvicorn

    # Calibrado para Raspberry Pi 4B (ARM64): worker único, uvloop e logs otimizados
    uvicorn.run(
        "pidots.main:app",
        host=settings.host,
        port=settings.port,
        workers=1,
        loop="uvloop" if sys.platform != "win32" else "asyncio",
        access_log=False,
    )


async def _init_cmd() -> None:
    """Inicializa as tabelas do banco SQLite WAL e diretórios necessários."""
    settings.ensure_directories()
    await init_edge_database()
    print(f"[OK] Banco SQLite WAL inicializado em: {settings.sqlite_db_path}")
    print(f"[OK] Raiz de workspaces configurada em: {settings.workspaces_root}")


async def _status_cmd() -> None:
    """Exibe telemetria do sistema Edge e métricas do SQLite WAL."""
    from .core.edge_triggers import EdgeHardwareTriggers

    temp = EdgeHardwareTriggers.get_soc_temperature()
    mem = EdgeHardwareTriggers.get_ram_metrics()

    db_path = Path(settings.sqlite_db_path)
    wal_path = Path(f"{settings.sqlite_db_path}-wal")
    db_size = db_path.stat().st_size / 1024 if db_path.exists() else 0.0
    wal_size = wal_path.stat().st_size / 1024 if wal_path.exists() else 0.0

    print("=== piDots Telemetria Edge ===")
    print(f"Versão:         piDots v{__version__}")
    print(f"Temperatura:    {temp} °C")
    print(f"Memória RAM:    Usada: {mem['used_mb']} MB / Total: {mem['total_mb']} MB (Livre: {mem['available_mb']} MB)")
    print(f"Banco (.db):    {db_size:.1f} KB")
    print(f"Journal (.wal): {wal_size:.1f} KB")
    print(f"Endpoint IA:    {settings.ai_base_url} (Modelo: {settings.ai_model})")


async def _dots_list_cmd() -> None:
    """Lista todos os Coworkers (Dots) cadastrados."""
    await init_edge_database()
    async with get_db() as db:
        cursor = await db.execute("SELECT id, name, role, model, created_at FROM dots ORDER BY created_at ASC")
        rows = await cursor.fetchall()

    print(f"Total de Dots cadastrados: {len(rows)}")
    for r in rows:
        print(f" - [{r['id']}] {r['name']} ({r['role']}) | Modelo: {r['model']}")


async def _hitl_list_cmd() -> None:
    """Lista solicitações de aprovação HITL pendentes."""
    await init_edge_database()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, dot_id, action_type, risk_level, status, requested_at FROM hitl_approvals WHERE status = 'PENDING'"
        )
        rows = await cursor.fetchall()

    print(f"Solicitações HITL pendentes: {len(rows)}")
    for r in rows:
        print(f" - [ID: {r['id']}] Dot: {r['dot_id']} | Ação: {r['action_type']} | Risco: {r['risk_level']} | Em: {r['requested_at']}")


async def _hitl_resolve_cmd(approval_id: str, approve: bool, notes: str) -> None:
    """Aprova ou rejeita uma solicitação HITL via CLI."""
    from .core.hitl import HITLManager

    await init_edge_database()
    success = await HITLManager.resolve_approval(approval_id, approve, notes)
    if success:
        action = "APROVADA" if approve else "REJEITADA"
        print(f"[OK] Solicitação {approval_id} resolvida como {action}.")
    else:
        print(f"[ERRO] Falha ao resolver solicitação {approval_id} (ID inexistente ou não pendente).")


def cli_entrypoint() -> None:
    """Ponto de entrada do comando 'pidots' com subcomandos."""
    parser = argparse.ArgumentParser(
        prog="pidots",
        description="piDots: orquestrador de agentes autônomos para hardware restrito (ARM64)."
    )
    parser.add_argument("--version", action="version", version=f"piDots {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comandos disponíveis")

    # Subcomando serve
    server_parser = subparsers.add_parser("serve", help="Inicia o servidor HTTP do piDots")
    server_parser.add_argument("--host", type=str, default=None, help="Host de escuta")
    server_parser.add_argument("--port", type=int, default=None, help="Porta de escuta")

    # Subcomando init
    subparsers.add_parser("init", help="Inicializa infraestrutura de banco e diretórios")

    # Subcomando status
    subparsers.add_parser("status", help="Exibe status do sistema, hardware e armazenamento")

    # Subcomando dots
    dots_parser = subparsers.add_parser("dots", help="Gerencia os Dots")
    dots_parser.add_argument("action", choices=["list"], help="Ação a executar")

    # Subcomando hitl
    hitl_parser = subparsers.add_parser("hitl", help="Gerencia aprovações Human-in-the-Loop")
    hitl_sub = hitl_parser.add_subparsers(dest="hitl_action")
    hitl_sub.add_parser("list", help="Lista solicitações pendentes")

    appr_p = hitl_sub.add_parser("approve", help="Aprova ação pendente")
    appr_p.add_argument("id", type=str, help="ID da solicitação")
    appr_p.add_argument("--notes", type=str, default="Aprovado via CLI", help="Justificativa")

    rej_p = hitl_sub.add_parser("reject", help="Rejeita ação pendente")
    rej_p.add_argument("id", type=str, help="ID da solicitação")
    rej_p.add_argument("--notes", type=str, default="Rejeitado via CLI", help="Justificativa")

    args = parser.parse_args()

    if args.subcommand == "serve":
        if args.host:
            settings.host = args.host
        if args.port:
            settings.port = args.port
        run_server()
    elif args.subcommand == "init":
        asyncio.run(_init_cmd())
    elif args.subcommand == "status":
        asyncio.run(_status_cmd())
    elif args.subcommand == "dots":
        if args.action == "list":
            asyncio.run(_dots_list_cmd())
    elif args.subcommand == "hitl":
        if args.hitl_action == "list":
            asyncio.run(_hitl_list_cmd())
        elif args.hitl_action == "approve":
            asyncio.run(_hitl_resolve_cmd(args.id, True, args.notes))
        elif args.hitl_action == "reject":
            asyncio.run(_hitl_resolve_cmd(args.id, False, args.notes))
        else:
            hitl_parser.print_help()
    else:
        parser.print_help()
