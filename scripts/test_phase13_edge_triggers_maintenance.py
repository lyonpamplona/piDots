"""
Teste e Validação da Fase 5: Triggers de Hardware Edge Orientados a Eventos e
Rotina de Manutenção Noturna Autônoma para piDots.
Homologa a telemetria proativa do SoC Broadcom e MicroSD, avaliação de limiares,
truncamento síncrono de WAL, poda episódica e ferramentas no ToolRegistry.
"""

import asyncio
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pidots.config import settings
from pidots.storage.db import init_edge_database, get_db
from pidots.core.edge_triggers import EdgeHardwareTriggers
from pidots.storage.maintenance import EdgeMaintenanceManager
from pidots.tools.registry import registry


async def run_phase13_tests():
    print("=== [piDots] Teste e Validação da Fase 5: Edge Triggers & Manutenção Noturna ===")

    # 1. Inicialização do SQLite WAL e Preparação de Dados de Teste
    print("[1/5] Inicializando banco SQLite WAL e configurando ambiente de teste...")
    await init_edge_database()

    dot_test_id = f"dot-edge-{uuid.uuid4().hex[:4]}"
    thread_old_id = f"thread-old-{uuid.uuid4().hex[:4]}"
    thread_recent_id = f"thread-recent-{uuid.uuid4().hex[:4]}"

    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO dots (id, name, role, system_prompt, model, workspace_path, archetype)
            VALUES (?, 'Dot Edge Teste', 'Monitor Hardware', 'Prompt Edge', 'qwen3.8-27b', '/tmp', 'general')
            """,
            (dot_test_id,)
        )
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, 'Sessão Histórica Antiga')",
            (thread_old_id, dot_test_id)
        )
        await db.execute(
            "INSERT INTO threads (id, dot_id, title) VALUES (?, ?, 'Sessão Ativa Recente')",
            (thread_recent_id, dot_test_id)
        )

        # Insere 6 mensagens antigas com data retroativa forçada (12 dias atrás)
        for i in range(6):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Mensagem histórica de log #{i} sobre carga de memória e I/O de disco."
            await db.execute(
                """
                INSERT INTO messages (id, thread_id, actor_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', '-12 days'))
                """,
                (f"msg-old-{i}-{uuid.uuid4().hex[:4]}", thread_old_id, dot_test_id, role, content)
            )

        # Insere 2 mensagens recentes (data corrente)
        for i in range(2):
            role = "user" if i == 0 else "assistant"
            content = f"Mensagem operacional recente ativa #{i}."
            await db.execute(
                """
                INSERT INTO messages (id, thread_id, actor_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (f"msg-recent-{i}-{uuid.uuid4().hex[:4]}", thread_recent_id, dot_test_id, role, content)
            )

        await db.commit()

    print(f"      Ambiente preparado: Dot '{dot_test_id}', Thread antiga: '{thread_old_id}', Thread recente: '{thread_recent_id}'.")

    # 2. Homologação do Módulo EdgeHardwareTriggers
    print("[2/5] Testando EdgeHardwareTriggers: leituras físicas e avaliação de limiares...")
    soc_temp = EdgeHardwareTriggers.get_soc_temperature()
    assert isinstance(soc_temp, float), "Temperatura deve ser float."
    assert soc_temp > 0.0, "Temperatura deve ser positiva."

    disk = EdgeHardwareTriggers.get_disk_metrics()
    assert "total_gb" in disk and "free_percent" in disk
    assert 0.0 <= disk["free_percent"] <= 100.0

    ram = EdgeHardwareTriggers.get_ram_metrics()
    assert "total_mb" in ram and "free_percent" in ram

    load = EdgeHardwareTriggers.get_load_metrics()
    assert "load_1m" in load

    # Avaliação nominal (sem violações simuladas)
    report_nominal = EdgeHardwareTriggers.check_triggers()
    assert "Linux Edge Node" in report_nominal["device"] or "Raspberry" in report_nominal["device"]
    assert "status" in report_nominal
    print(f"      Telemetria nominal coletada: SoC={soc_temp}C, Disco livre={disk['free_percent']}%, RAM livre={ram['free_percent']}%. Status: {report_nominal['status']}.")

    # Teste de violação simulada: Temperatura Crítica e Disco Baixo
    EdgeHardwareTriggers.set_simulation(temp=80.5, disk_free_percent=4.2, ram_free_percent=3.1)
    report_critical = EdgeHardwareTriggers.check_triggers()
    assert report_critical["status"] == "CRITICAL", f"Esperava status CRITICAL, obteve {report_critical['status']}"
    assert report_critical["triggered_count"] >= 3, f"Esperava 3 triggers acionados, obteve {report_critical['triggered_count']}"
    assert report_critical["is_throttled"] is True

    # Validação dos tipos de evento
    triggers_set = {ev["trigger"] for ev in report_critical["triggered_events"]}
    assert "THERMAL_EXCEEDED" in triggers_set, "Trigger térmico não identificado."
    assert "DISK_LOW_SPACE" in triggers_set, "Trigger de disco não identificado."
    assert "RAM_EXHAUSTION" in triggers_set, "Trigger de RAM não identificado."
    print("      Violações simuladas de limiares detectadas com precisão: THERMAL_EXCEEDED, DISK_LOW_SPACE, RAM_EXHAUSTION.")

    # Limpeza da simulação e validação com limiares relaxados
    EdgeHardwareTriggers.set_simulation(None, None, None)
    report_restored = EdgeHardwareTriggers.check_triggers(
        thermal_limit=95.0,
        disk_min_free_percent=1.0,
        ram_min_free_percent=1.0
    )
    assert report_restored["status"] == "OK", f"Esperava OK com limiares relaxados, obteve {report_restored['status']}"
    print("      Simulação limpa: telemetria real do hardware restabelecida.")


    # 3. Homologação do Módulo EdgeMaintenanceManager
    print("[3/5] Testando EdgeMaintenanceManager: WAL checkpoint TRUNCATE, consolidação e VACUUM INTO...")
    # a) Checkpoint WAL TRUNCATE
    chk_res = await EdgeMaintenanceManager.checkpoint_wal(mode="TRUNCATE")
    assert chk_res["mode"] == "TRUNCATE"
    assert "log_pages" in chk_res and "checkpointed_pages" in chk_res
    print(f"      PRAGMA wal_checkpoint(TRUNCATE) executado com sucesso: log={chk_res['log_pages']}, chk={chk_res['checkpointed_pages']}.")

    # b) Consolidação episódica de mensagens antigas (> 7 dias)
    cons_res = await EdgeMaintenanceManager.consolidate_old_episodes(days_threshold=7)
    assert cons_res["threads_consolidated"] >= 1, "Deveria consolidar pelo menos 1 thread antiga."
    assert cons_res["messages_pruned"] >= 6, "Deveria podar pelo menos as 6 mensagens antigas criadas."
    assert cons_res["episodic_records_created"] >= 1, "Deveria criar ao menos 1 registro episódico."
    print(f"      Consolidação episódica concluída: {cons_res['threads_consolidated']} thread(s), {cons_res['messages_pruned']} mensagens podadas.")

    # Verifica integridade no SQLite: mensagens recentes devem persistir intactas
    async with get_db() as db:
        cursor_recent = await db.execute("SELECT COUNT(*) FROM messages WHERE thread_id = ?", (thread_recent_id,))
        count_recent = (await cursor_recent.fetchone())[0]
        assert count_recent == 2, f"Mensagens recentes deveriam ser 2, encontrou {count_recent}."

        cursor_old = await db.execute("SELECT COUNT(*) FROM messages WHERE thread_id = ?", (thread_old_id,))
        count_old = (await cursor_old.fetchone())[0]
        assert count_old == 0, f"Mensagens antigas da thread deveriam ter sido podadas (0), encontrou {count_old}."

        cursor_ep = await db.execute("SELECT summary, key_decisions FROM episodic_memories WHERE thread_id = ?", (thread_old_id,))
        row_ep = await cursor_ep.fetchone()
        assert row_ep is not None, "Registro na tabela episodic_memories não encontrado."
        assert "Consolidação episódica" in row_ep["summary"]
    print("      Integridade pós-poda confirmada: mensagens recentes preservadas e memória episódica persistida.")

    # c) Backup atômico VACUUM INTO
    backup_temp_file = Path("/tmp/pidots_test_backup.db")
    if backup_temp_file.exists():
        backup_temp_file.unlink()

    vac_res = await EdgeMaintenanceManager.backup_vacuum_into(str(backup_temp_file))
    assert vac_res["success"] is True
    assert backup_temp_file.exists()
    assert backup_temp_file.stat().st_size > 0
    print(f"      VACUUM INTO executado com sucesso: backup gerado ({vac_res['size_mb']} MB).")
    backup_temp_file.unlink()

    # d) Otimização de índices
    opt_res = await EdgeMaintenanceManager.optimize_database()
    assert opt_res["success"] is True

    # e) Execução da suíte completa run_full_maintenance
    backup_dir_test = "/tmp/pidots_backups_test"
    full_report = await EdgeMaintenanceManager.run_full_maintenance(backup_dir=backup_dir_test, days_threshold=7)
    assert full_report["status"] == "COMPLETED"
    assert "metrics_before" in full_report and "metrics_after" in full_report
    assert full_report["duration_ms"] >= 0
    if os.path.exists(backup_dir_test):
        shutil.rmtree(backup_dir_test)
    print("      Suíte completa de manutenção noturna run_full_maintenance executada com relatório consolidado.")

    # 4. Homologação das Ferramentas no ToolRegistry
    print("[4/5] Testando ferramentas nativas no ToolRegistry via Function Calling...")
    tools_def = registry.get_tool_definitions()
    tool_names = [t["function"]["name"] for t in tools_def]
    assert "hardware_trigger_check" in tool_names, "Ferramenta hardware_trigger_check ausente no registro."
    assert "edge_maintenance_run" in tool_names, "Ferramenta edge_maintenance_run ausente no registro."

    # Executa hardware_trigger_check via ToolRegistry
    res_hw = await registry.execute_tool(
        name="hardware_trigger_check",
        arguments={"thermal_limit_celsius": 75.0, "disk_min_free_percent": 8.0},
        dot_id=dot_test_id
    )
    assert res_hw.get("status") in ("OK", "WARNING", "CRITICAL")
    assert "metrics" in res_hw
    print(f"      Ferramenta 'hardware_trigger_check' validada com status: {res_hw.get('status')}.")

    # Executa edge_maintenance_run via ToolRegistry
    res_maint = await registry.execute_tool(
        name="edge_maintenance_run",
        arguments={"days_threshold": 14, "create_backup": False},
        dot_id=dot_test_id
    )
    assert res_maint.get("status") == "COMPLETED"
    assert "wal_checkpoint_final" in res_maint
    print("      Ferramenta 'edge_maintenance_run' validada com status COMPLETED via Function Calling.")

    # 5. Avaliação Proativa e Conclusão
    print("[5/5] Testando evaluate_and_alert proativo e integridade final...")
    alert_report = await EdgeHardwareTriggers.evaluate_and_alert(notify_hitl=False)
    assert alert_report["status"] in ("OK", "WARNING", "CRITICAL")
    print("      Avaliação proativa evaluate_and_alert concluída com sucesso.")

    print("\n=== Todos os testes da Fase 5 passaram com 100% de sucesso! ===")


if __name__ == "__main__":
    asyncio.run(run_phase13_tests())
