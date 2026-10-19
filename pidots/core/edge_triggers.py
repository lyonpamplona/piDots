"""
Módulo de Triggers de Hardware Edge Orientados a Eventos para piDots.
Monitora a saúde física do nó de borda (SBCs / Linux, calibrado com telemetria
térmica para o SoC do Raspberry Pi 4B, espaço em disco Flash/MicroSD, memória RAM
e carga de sistema) e dispara alertas e mitigações proativas quando limiares são violados.
"""

import os
import shutil
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from ..config import settings

logger = logging.getLogger("pidots.edge_triggers")


class EdgeGPIOMonitor:
    """Monitor de pinos físicos GPIO para sensores de borda e sinais de hardware (SBC/RPi4)."""

    SYSFS_GPIO_PATH = "/sys/class/gpio"
    _simulated_pins: dict[int, int] = {}

    @classmethod
    def set_pin_simulation(cls, pin: int, value: int) -> None:
        """Configura estado simulado (0 ou 1) de um pino GPIO para testes."""
        cls._simulated_pins[pin] = 1 if value else 0

    @classmethod
    def clear_simulation(cls) -> None:
        """Limpa simulações de pinos GPIO."""
        cls._simulated_pins.clear()

    @classmethod
    def is_hardware_available(cls) -> bool:
        """Verifica se o subsistema GPIO do Linux está presente no nó host."""
        return os.path.exists(cls.SYSFS_GPIO_PATH) or os.path.exists("/dev/gpiochip0")

    @classmethod
    def read_pin(cls, pin: int) -> int | None:
        """Lê o valor lógico (0 ou 1) do pino GPIO especificado."""
        if pin in cls._simulated_pins:
            return cls._simulated_pins[pin]

        pin_path = f"{cls.SYSFS_GPIO_PATH}/gpio{pin}/value"
        if os.path.exists(pin_path):
            try:
                with open(pin_path, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    return int(val) if val.isdigit() else None
            except Exception as e:
                logger.debug("Falha na leitura do pino GPIO %d: %s", pin, str(e))
        return None

    @classmethod
    def check_gpio_triggers(cls, trigger_pins_config: dict[int, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """
        Avalia os pinos de trigger configurados.
        Formato de trigger_pins_config: {pin_number: {"label": "PIR_SENSOR", "active_level": 1, "severity": "WARNING"}}
        """
        configs = trigger_pins_config or {
            17: {"label": "EMERGENCY_STOP", "active_level": 1, "severity": "CRITICAL"},
            27: {"label": "MOTION_PIR", "active_level": 1, "severity": "WARNING"}
        }
        events: list[dict[str, Any]] = []
        for pin, cfg in configs.items():
            val = cls.read_pin(pin)
            if val is not None and val == cfg.get("active_level", 1):
                severity = cfg.get("severity", "WARNING")
                label = cfg.get("label", f"GPIO_{pin}")
                events.append({
                    "trigger": f"GPIO_PIN_{pin}_ACTIVE",
                    "severity": severity,
                    "metric": f"gpio_pin_{pin}",
                    "current_value": val,
                    "threshold": cfg.get("active_level", 1),
                    "message": f"Pino GPIO {pin} ({label}) atingiu nível lógico ativo ({val}).",
                    "recommendation": f"Acionar rotina autônoma vinculada ao sensor {label}."
                })
        return events


class EdgeMQTTListener:
    """Listener assíncrono ultraleve para barramento de tópicos MQTT em nós de borda."""

    _handlers: dict[str, list[Any]] = {}
    _simulated_inbox: list[dict[str, Any]] = []

    @classmethod
    def register_handler(cls, topic_prefix: str, handler: Any) -> None:
        """Registra handler assíncrono para mensagens de um tópico ou padrão."""
        cls._handlers.setdefault(topic_prefix, []).append(handler)

    @classmethod
    async def dispatch_message(cls, topic: str, payload: Any) -> int:
        """Despacha uma mensagem recebida no barramento para os handlers registrados."""
        dispatched_count = 0
        for pattern, handlers in cls._handlers.items():
            if topic.startswith(pattern) or pattern == "#":
                for h in handlers:
                    try:
                        res = h(topic, payload)
                        if asyncio.iscoroutine(res):
                            await res
                        dispatched_count += 1
                    except Exception as e:
                        logger.error("Erro no handler MQTT para tópico '%s': %s", topic, str(e))
        return dispatched_count

    @classmethod
    async def simulate_incoming_message(cls, topic: str, payload: Any) -> int:
        """Simula recepção de mensagem MQTT para homologação de gatilhos sem broker externo."""
        cls._simulated_inbox.append({
            "topic": topic,
            "payload": payload,
            "received_at": datetime.now(timezone.utc).isoformat()
        })
        return await cls.dispatch_message(topic, payload)


class EdgeHardwareTriggers:
    """Gerenciador e avaliador de gatilhos orientados a eventos de hardware no Edge."""

    THERMAL_SYS_PATH = "/sys/class/thermal/thermal_zone0/temp"

    # Propriedades de simulação para testes unitários ou plataformas sem acesso a /sys
    _simulated_temp: float | None = None
    _simulated_disk_free_percent: float | None = None
    _simulated_ram_free_percent: float | None = None

    @classmethod
    def set_simulation(
        cls,
        temp: float | None = None,
        disk_free_percent: float | None = None,
        ram_free_percent: float | None = None
    ) -> None:
        """Define ou limpa valores simulados de telemetria para validação de limiares."""
        cls._simulated_temp = temp
        cls._simulated_disk_free_percent = disk_free_percent
        cls._simulated_ram_free_percent = ram_free_percent

    @classmethod
    def get_soc_temperature(cls) -> float:
        """
        Lê a temperatura real do SoC Broadcom BCM2711 via sysfs do Linux.
        Retorna a temperatura em graus Celsius com uma casa decimal.
        """
        if cls._simulated_temp is not None:
            return round(cls._simulated_temp, 1)

        if os.path.exists(cls.THERMAL_SYS_PATH):
            try:
                with open(cls.THERMAL_SYS_PATH, "r", encoding="utf-8") as f:
                    raw_temp = f.read().strip()
                    if raw_temp.isdigit():
                        return round(float(raw_temp) / 1000.0, 1)
            except Exception as e:
                logger.debug("Falha na leitura direta de %s: %s", cls.THERMAL_SYS_PATH, str(e))

        # Fallback nominal para ambientes de emulação, CI ou contêiner sem montagem de /sys
        return 45.0

    @classmethod
    def get_disk_metrics(cls, target_path: str | None = None) -> dict[str, Any]:
        """
        Calcula as métricas de espaço em disco no MicroSD/Flash para o diretório alvo.
        """
        path = target_path or settings.workspaces_root
        try:
            total, used, free = shutil.disk_usage(path)
        except Exception:
            # Fallback para diretório corrente caso o path configurado não exista
            total, used, free = shutil.disk_usage(".")

        total_gb = round(total / (1024 ** 3), 2)
        used_gb = round(used / (1024 ** 3), 2)
        free_gb = round(free / (1024 ** 3), 2)

        if cls._simulated_disk_free_percent is not None:
            free_percent = round(cls._simulated_disk_free_percent, 2)
            used_percent = round(100.0 - free_percent, 2)
        else:
            free_percent = round((free / total) * 100.0, 2) if total > 0 else 0.0
            used_percent = round((used / total) * 100.0, 2) if total > 0 else 0.0

        return {
            "target_path": path,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "free_percent": free_percent,
            "used_percent": used_percent
        }

    @classmethod
    def get_ram_metrics(cls) -> dict[str, Any]:
        """
        Lê a utilização de memória RAM a partir de /proc/meminfo no Linux.
        """
        total_kb = 0
        available_kb = 0

        meminfo_path = "/proc/meminfo"
        if os.path.exists(meminfo_path):
            try:
                with open(meminfo_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            parts = line.split()
                            if len(parts) >= 2:
                                total_kb = int(parts[1])
                        elif line.startswith("MemAvailable:"):
                            parts = line.split()
                            if len(parts) >= 2:
                                available_kb = int(parts[1])
            except Exception as e:
                logger.debug("Falha na leitura de /proc/meminfo: %s", str(e))

        # Fallback nominal se /proc/meminfo for inacessível
        if total_kb == 0:
            total_kb = 4 * 1024 * 1024  # 4GB nominal de referência (Raspberry Pi 4B)
            available_kb = int(total_kb * 0.70)

        total_mb = round(total_kb / 1024.0, 1)
        available_mb = round(available_kb / 1024.0, 1)
        used_mb = round((total_kb - available_kb) / 1024.0, 1)

        if cls._simulated_ram_free_percent is not None:
            free_percent = round(cls._simulated_ram_free_percent, 2)
        else:
            free_percent = round((available_kb / total_kb) * 100.0, 2) if total_kb > 0 else 0.0

        return {
            "total_mb": total_mb,
            "available_mb": available_mb,
            "used_mb": used_mb,
            "free_percent": free_percent
        }

    get_memory_metrics = get_ram_metrics

    @classmethod
    def get_load_metrics(cls) -> dict[str, Any]:
        """Recupera a média de carga do sistema (Load Average 1m, 5m, 15m)."""
        try:
            load1, load5, load15 = os.getloadavg()
            return {
                "load_1m": round(load1, 2),
                "load_5m": round(load5, 2),
                "load_15m": round(load15, 2)
            }
        except Exception:
            return {
                "load_1m": 0.15,
                "load_5m": 0.10,
                "load_15m": 0.08
            }

    @classmethod
    def check_triggers(
        cls,
        thermal_limit: float | None = None,
        disk_min_free_percent: float | None = None,
        ram_min_free_percent: float | None = None,
        target_path: str | None = None
    ) -> dict[str, Any]:
        """
        Avalia o conjunto de limites operacionais de hardware.
        Retorna status ('OK', 'WARNING', 'CRITICAL') e eventos disparados.
        """
        eff_thermal_limit = thermal_limit if thermal_limit is not None else settings.thermal_limit_celsius
        eff_disk_limit = disk_min_free_percent if disk_min_free_percent is not None else 10.0
        eff_ram_limit = ram_min_free_percent if ram_min_free_percent is not None else 5.0

        soc_temp = cls.get_soc_temperature()
        disk_metrics = cls.get_disk_metrics(target_path)
        ram_metrics = cls.get_ram_metrics()
        load_metrics = cls.get_load_metrics()

        triggered_events: list[dict[str, Any]] = []

        # 1. Avaliação Térmica
        if settings.enable_thermal_throttle and soc_temp >= eff_thermal_limit:
            # Se ultrapassar mais de 6°C acima do teto, classifica como CRÍTICO
            severity = "CRITICAL" if soc_temp >= (eff_thermal_limit + 6.0) else "WARNING"
            triggered_events.append({
                "trigger": "THERMAL_EXCEEDED",
                "severity": severity,
                "metric": "soc_temperature_celsius",
                "current_value": soc_temp,
                "threshold": eff_thermal_limit,
                "message": f"Temperatura do SoC Broadcom ({soc_temp}C) atingiu ou excedeu o teto seguro de {eff_thermal_limit}C.",
                "recommendation": "Ativar throttle no loop de agentes, espaçar chamadas de inferência e verificar ventilação física."
            })

        # 2. Avaliação de Espaço em Disco (Proteção de MicroSD)
        if disk_metrics["free_percent"] < eff_disk_limit:
            severity = "CRITICAL" if disk_metrics["free_percent"] < 5.0 else "WARNING"
            triggered_events.append({
                "trigger": "DISK_LOW_SPACE",
                "severity": severity,
                "metric": "disk_free_percent",
                "current_value": disk_metrics["free_percent"],
                "threshold": eff_disk_limit,
                "message": f"Espaço livre no MicroSD ({disk_metrics['free_percent']}%) inferior ao limiar mínimo de {eff_disk_limit}%.",
                "recommendation": "Executar compactação síncrona WAL (PRAGMA wal_checkpoint TRUNCATE) e podar mensagens antigas."
            })

        # 3. Avaliação de Memória RAM
        if ram_metrics["free_percent"] < eff_ram_limit:
            triggered_events.append({
                "trigger": "RAM_EXHAUSTION",
                "severity": "CRITICAL",
                "metric": "ram_free_percent",
                "current_value": ram_metrics["free_percent"],
                "threshold": eff_ram_limit,
                "message": f"Memória RAM livre ({ram_metrics['free_percent']}%) abaixo do limiar crítico de {eff_ram_limit}%.",
                "recommendation": "Despejar caches in-memory, truncar buffers de contexto e disparar coleta de lixo."
            })

        # 4. Avaliação de Gatilhos Físicos GPIO
        if settings.gpio_enabled or bool(EdgeGPIOMonitor._simulated_pins):
            gpio_events = EdgeGPIOMonitor.check_gpio_triggers()
            triggered_events.extend(gpio_events)

        # Determinação de status geral consolidado
        if any(ev["severity"] == "CRITICAL" for ev in triggered_events):
            status = "CRITICAL"
        elif triggered_events:
            status = "WARNING"
        else:
            status = "OK"

        return {
            "status": status,
            "device": "Linux Edge Node (Ref: RPi4 ARM64)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "temperature_celsius": soc_temp,
                "disk": disk_metrics,
                "ram": ram_metrics,
                "load_average": load_metrics,
                "gpio": {
                    "hardware_available": EdgeGPIOMonitor.is_hardware_available(),
                    "simulated_active": bool(EdgeGPIOMonitor._simulated_pins),
                    "monitored_pins": list(EdgeGPIOMonitor._simulated_pins.keys())
                }
            },
            "triggered_count": len(triggered_events),
            "triggered_events": triggered_events,
            "is_throttled": status in ("WARNING", "CRITICAL")
        }

    @classmethod
    async def evaluate_and_alert(
        cls,
        notify_hitl: bool = True,
        thermal_limit: float | None = None,
        disk_min_free_percent: float | None = None
    ) -> dict[str, Any]:
        """
        Avalia os triggers de hardware e, se anomalia detectada, despacha notificação
        imediata ao operador através do canal HITL sem aguardar comando do usuário.
        """
        report = cls.check_triggers(
            thermal_limit=thermal_limit,
            disk_min_free_percent=disk_min_free_percent
        )

        if report["status"] != "OK" and notify_hitl:
            from .notifier import HITLNotifier
            events_summary = " | ".join(
                f"[{ev['severity']}] {ev['trigger']}: {ev['message']}"
                for ev in report["triggered_events"]
            )
            logger.warning("Alerta de Hardware Edge disparado: %s", events_summary)
            try:
                await HITLNotifier.notify_approval_requested(
                    approval_id=f"edge-hw-{datetime.now(timezone.utc).strftime('%H%M%S')}",
                    dot_id="system-monitor",
                    action_type="hardware_trigger_alert",
                    risk_level=report["status"],
                    payload=f"Status: {report['status']} | Eventos: {events_summary}"
                )
            except Exception as e:
                logger.error("Falha ao despachar notificação de hardware trigger: %s", str(e))

        return report
