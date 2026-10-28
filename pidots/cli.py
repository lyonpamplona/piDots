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
    print(f"sqlite3  pronto  -> {settings.sqlite_db_path} (modo WAL)")
    print(f"sandbox  pronto  -> {settings.workspaces_root} (isolamento bwrap)")


async def _status_cmd() -> None:
    """Exibe telemetria do sistema Edge e métricas do SQLite WAL."""
    from .core.edge_triggers import EdgeHardwareTriggers

    temp = EdgeHardwareTriggers.get_soc_temperature()
    mem = EdgeHardwareTriggers.get_ram_metrics()

    db_path = Path(settings.sqlite_db_path)
    wal_path = Path(f"{settings.sqlite_db_path}-wal")
    db_size = db_path.stat().st_size / 1024 if db_path.exists() else 0.0
    wal_size = wal_path.stat().st_size / 1024 if wal_path.exists() else 0.0

    print(f"[pidots :: nó de borda arm64 :: v{__version__}]")
    print(f"silício: {temp:.1f}°C | ram: {mem['used_mb']}/{mem['total_mb']} MB ({mem['available_mb']} MB livres)")
    print(f"sqlite:  {db_size:.1f} KB (.db) | {wal_size:.1f} KB (.wal)")
    print(f"motor:   {settings.ai_model} @ {settings.ai_base_url}")


async def _dots_list_cmd() -> None:
    """Lista todos os Coworkers (Dots) cadastrados."""
    await init_edge_database()
    async with get_db() as db:
        cursor = await db.execute("SELECT id, name, role, model, created_at FROM dots ORDER BY created_at ASC")
        rows = await cursor.fetchall()

    if not rows:
        print("nenhum coworker instalado na bancada.")
    else:
        print(f"coworkers instalados ({len(rows)} na bancada):")
        for r in rows:
            print(f" - [{r['id']}] {r['name']} ({r['role']}) | motor: {r['model']}")


async def _hitl_list_cmd() -> None:
    """Lista solicitações de aprovação HITL pendentes."""
    await init_edge_database()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, dot_id, action_type, risk_level, status, requested_at FROM hitl_approvals WHERE status = 'PENDING'"
        )
        rows = await cursor.fetchall()

    if not rows:
        print("fila hitl limpa. nenhum comando retido.")
    else:
        print(f"ordens retidas aguardando homologação humana ({len(rows)} pendentes):")
        for r in rows:
            print(f" - [id {r['id']}] coworker: {r['dot_id']} | ação: {r['action_type']} | risco: {r['risk_level']} | hora: {r['requested_at']}")


async def _hitl_resolve_cmd(approval_id: str, approve: bool, notes: str) -> None:
    """Aprova ou rejeita uma solicitação HITL via CLI."""
    from .core.hitl import HITLManager

    await init_edge_database()
    success = await HITLManager.resolve_approval(approval_id, approve, notes)
    if success:
        action_verb = "aprovada" if approve else "rejeitada"
        dest = "comando despachado para o sandbox" if approve else "execução cancelada"
        print(f"ordem {approval_id} {action_verb}: {dest}.")
    else:
        print(f"falha: ordem {approval_id} não encontrada ou já resolvida.")


def cli_entrypoint() -> None:
    """Ponto de entrada do comando 'pidots' com subcomandos."""
    parser = argparse.ArgumentParser(
        prog="pidots",
        description="piDots: orquestrador de coworkers autônomos para Raspberry Pi e nós de borda ARM64."
    )
    parser.add_argument("--version", action="version", version=f"piDots {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comandos disponíveis")

    # Subcomando serve
    server_parser = subparsers.add_parser("serve", help="Inicia o daemon HTTP e a interface web")
    server_parser.add_argument("--host", type=str, default=None, help="Host de escuta")
    server_parser.add_argument("--port", type=int, default=None, help="Porta de escuta")

    # Subcomando init
    subparsers.add_parser("init", help="Cria o banco SQLite (WAL) e pastas de trabalho")

    # Subcomando status
    subparsers.add_parser("status", help="Exibe temperatura do silício, RAM e armazenamento")

    # Subcomando dots
    dots_parser = subparsers.add_parser("dots", help="Lista os coworkers cadastrados")
    dots_parser.add_argument("action", choices=["list"], help="Ação a executar")

    # Subcomando hitl
    hitl_parser = subparsers.add_parser("hitl", help="Fila de homologação humana (HITL)")
    hitl_sub = hitl_parser.add_subparsers(dest="hitl_action")
    hitl_sub.add_parser("list", help="Lista comandos retidos aguardando aprovação")

    appr_p = hitl_sub.add_parser("approve", help="Libera execução de comando retido")
    appr_p.add_argument("id", type=str, help="ID da solicitação")
    appr_p.add_argument("--notes", type=str, default="Liberado pelo operador no terminal", help="Justificativa")

    rej_p = hitl_sub.add_parser("reject", help="Bloqueia e descarta comando retido")
    rej_p.add_argument("id", type=str, help="ID da solicitação")
    rej_p.add_argument("--notes", type=str, default="Bloqueado pelo operador no terminal", help="Justificativa")

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


if __name__ == "__main__":
    cli_entrypoint()
