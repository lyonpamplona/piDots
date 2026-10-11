# piDots

**Persistent Edge AI Coworker for Resource-Constrained Hardware (Raspberry Pi 4B 4GB ARM64)**

[Português](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)
![Arch](https://img.shields.io/badge/Architecture-ARM64%20%7C%20x86__64-informational?style=flat&logo=arm&logoColor=white)
![Hardware](https://img.shields.io/badge/Target-Raspberry%20Pi%204B%20(4GB)-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=flat&logo=docker&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Overview

**piDots** is a platform for persistent autonomous agents (AI Coworkers) specifically designed to run 24/7 on resource-constrained edge hardware, with the **Raspberry Pi 4B with 4GB RAM (ARM64)** as its primary target.

Inspired by the persistent coworker concepts of corporate OpenDots, piDots was re-engineered and optimized as a high-performance, asynchronous modular monolith. It eliminates heavy dependencies such as headless Chromium browsers, bulky vector database containers, and Node.js orchestrators, achieving an idle memory footprint of under **50 MB RAM** and less than **150 MB RAM** during simultaneous multi-agent execution.

The platform provides persistent agents tailored for technical workflows (DevOps, Research, Code Auditing), equipped with long-term memory, filesystem sandbox isolation, Human-in-the-Loop (HITL) governance for high-risk operations, and an ultra-responsive dark-mode SPA/PWA web interface.

---

## Technical Comparison: piDots vs Corporate OpenDots

| Parameter | OpenDots (Corporate Standard) | piDots (Edge Computing) |
| :--- | :--- | :--- |
| **Minimum Hardware** | x86_64 Server with 8GB to 16GB RAM | Raspberry Pi 4B (4GB RAM) / ARM64 / x86_64 |
| **Runtime Stack** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Memory Footprint (Idle)** | 2,000 MB - 3,500 MB RAM | ~48 MB - 52 MB RAM (~98% reduction) |
| **Memory under Load (Peak)** | 4,000 MB - 6,000 MB RAM | < 150 MB RAM |
| **Database & State** | PostgreSQL / Neo4j / Redis | SQLite with WAL Mode and tuned PRAGMAs |
| **Vector Database / Memory** | ChromaDB / Pinecone / Qdrant (500MB+) | On-disk CRC32 KNN Vector Extractor (< 5MB) |
| **Web Browser & Scraping** | Headless Chromium / Playwright (~500MB RAM) | Pure CPU async Trafilatura / httpx (~20MB) |
| **Security Isolation** | Nested Docker / Cloud VM | Native Linux Bubblewrap (`bwrap`) sandbox |
| **Storage Wear** | High fsync disk overhead | Optimized to minimize MicroSD / USB SSD wear |
| **Integration & Distribution** | Closed monolith / Microservices mesh | Modular Python package (`pip install -e .`) & Docker |

---

## Architecture and Core Modules

piDots follows a clean modular monolith architecture designed for minimal computational overhead:

```
pidots/
├── __init__.py
├── cli.py               # Native terminal command-line interface
├── config.py            # Centralized configuration and environment variable resolution
├── main.py              # FastAPI entrypoint, REST endpoints, AG-UI SSE streaming, and SPA console
├── core/
│   ├── __init__.py
│   ├── agent.py         # Asynchronous ReAct execution engine with Dynamic Tool Pruning
│   ├── hitl.py          # Human-in-the-Loop governance engine with retention queue
│   ├── messaging_gateway.py # Unified messaging gateway and collaborative channel bus
│   ├── notifier.py      # HTTP notifier and remote webhook dispatching
│   ├── orchestrator.py  # Multi-Bot orchestrator (Supervisor, Handoff, @dot mentions)
│   ├── scheduler.py     # Proactive Dot Heartbeat engine powered by croniter
│   └── state.py         # AG-UI protocol event definitions and session state tracking
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Universal OpenAI-compatible inference client with retries
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL layer tuned for microSD and idempotent migrations
│   ├── spaces_manager.py # Isolated dot workspaces, document versioning, and unified diffs
│   └── vector_store.py  # On-disk KNN vector store with CRC32 n-gram hashing
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Atomic file reading, writing, and workspace listing
    ├── registry.py      # Centralized tool registry supporting Dynamic Tool Pruning
    ├── terminal.py      # Bubblewrap-isolated and secure subprocess shell executor
    └── web_reader.py    # Lightweight async web reader powered by Trafilatura
```

---

## Advanced Edge Capabilities

### 1. Multi-Bot Orchestration and Cognitive Archetypes
piDots provides in-process multi-agent collaboration optimized for edge resources:
- **Dynamic Mentions (@dot):** The `ThreadRouter` parses `@dot_name` mentions, resolves interlocutors against SQLite, and enrolls them into `thread_participants`.
- **Supervisor-Worker Topology:** A supervisor plans and delegates subtasks using the `delegate_task` tool, executing workers in isolated threads and consolidating summaries into the parent conversation.
- **Leadership Handoff:** The `handoff_to_dot` tool formally reassigns thread leadership to a domain specialist, persisting audit trails in `agent_handoffs`.
- **Carbon-Copy Internal Messages:** Inter-bot exchanges are marked with `visibility: 'internal'`, keeping technical dialogues accessible for auditing without cluttering user feeds.
- **Cognitive Archetypes:**
  - `supervisor`: Workflow coordinator, planning, and goal tracking.
  - `grok`: Analytical-convergent specialist for code auditing, terminal operations, and root-cause debugging.
  - `muse`: Creative-divergent specialist for system architecture, concept synthesis, and documentation.
  - `auditor`: System telemetry, integrity verification, and compliance checks.
- **Dynamic Tool Pruning:** Agents load only the tool definitions allowed in `allowed_tools_json`, slashing prompt token overhead by up to 75% and preventing tool hallucination.

### 2. Proactive Automations: Dot Heartbeat Pattern and Circuit Breaker
The `pidots/core/scheduler.py` module introduces an in-process background scheduler driven by `croniter` without requiring Celery or Redis:
- **Cron Tasks:** Schedules are stored and tracked in SQLite WAL table `scheduled_tasks`.
- **Operational Silence Directive (HEARTBEAT_OK):** During routine inspections, if system telemetry and log checks indicate normal operational conditions, the agent responds strictly with `HEARTBEAT_OK`. The scheduler registers the run as `SILENT` and sleeps without issuing unnecessary external alerts.
- **In-Process Mutual Exclusion Concurrency:** Memory-backed lock set (`_running_tasks`) that prevents duplicate or cascading triggers when LLM reasoning cycles exceed the periodic 15-second heartbeat sweep interval.
- **Circuit Breaker with Exponential Backoff:** Proactive tasks experiencing consecutive failures back off progressively from 30s up to 3,600s (`min(3600, 30 * 2^(n-1))`). Upon the 5th consecutive failure, the circuit trips (`CIRCUIT_OPEN`), deactivating the task (`is_active = 0`) to preserve ARM64 CPU cycles and network sockets.
- **Preventive Credential Sanity Check (AUTH_REQUIRED):** Proactive tasks check for missing or placeholder credentials (`AI_API_KEY`), pausing execution with an `AUTH_REQUIRED` status and a 10-minute protective backoff before triggering pointless remote API calls.

### 3. Unified Messaging Gateway and Team Channels
The `pidots/core/messaging_gateway.py` module exposes stateless HTTP endpoints for external messaging platforms:
- **Native Platform Adapters:** Dedicated webhooks for Telegram (`/api/webhooks/telegram/{dot_id}`), WhatsApp via Evolution API with apikey authentication (`/api/webhooks/whatsapp/{dot_id}`), and Generic Webhooks (`/api/webhooks/incoming/{dot_id}`).
- **Native Evolution API Integration:** First-class `EVOLUTION_API_URL` and `EVOLUTION_API_KEY` configuration with hot-reload and async HTTPx dispatching.
- **Collaborative Channels (#channels):** Multi-agent discussion rooms tracked in the `channels` table.
- **Strict Anti-Recursion Safeguard:** To eliminate infinite conversation loops between bots:
  1. Strict recursion counter (`hop_count <= 3`).
  2. Bots only answer other bots when explicitly mentioned via `@dot_id`.
  3. Silent `NO_ACTION` directive when an agent has no actionable contribution.
- **Graceful Operational Failure Handling:** When upstream inference fails, the gateway catches the event and dispatches an informative `[FALHA OPERACIONAL]` notice to the remote user without degrading communication channel integrity.

### 4. Cognitive Resilience Architecture and Typed Exception Handling
The core piDots engine enforces an end-to-end resilient execution loop:
- **Typed Provider Exceptions:** The `OpenAIUniversalProvider` client strictly differentiates `ProviderAuthError` (HTTP 401/403 with immediate short-circuiting and no wasteful retries) from `ProviderTransientError` (HTTP 503/429/timeout with exponential backoff and jitter).
- **Standardized AG-UI v1.0 Protocol Contract:** The `DotAgent.run_thread` lifecycle emits a terminal `run:finished` event with `status: "failed"`, providing structured `error`, `error_type` (`auth_error` or `transient_error`), and `final_response: ""`.
- **Internal Carbon Diagnostic Tape:** Root-cause errors are persisted to SQLite WAL `messages` with `internal` visibility (`[FALHA DE INFERENCIA]` or `[FALHA DE AUTENTICACAO]`), ensuring complete forensic auditability without polluting human-facing feeds.
- **Integrated Resilience across Three Consumer Subsystems:**
  - *EdgeScheduler:* Accurately persists `FAILED` status with actual technical error summaries in SQLite, eliminating false-positive completions.
  - *MessagingGateway:* Returns structured, user-friendly error notices (`[FALHA OPERACIONAL]`) across external chat bridges.
  - *MultiBotOrchestrator:* Marks subtasks in `agent_handoffs` as `FAILED`, writes internal diagnostic alerts to parent threads, and provides structured feedback `{'success': False, 'error': ...}` allowing supervisory replanning.

---

## System Requirements

- **Operating System:** Linux (Debian 12 / Ubuntu 22.04+ / 64-bit Raspberry Pi OS recommended).
- **Architecture:** ARM64 (aarch64) or x86_64.
- **Python:** Version 3.11, 3.12, or 3.13.
- **Docker (Optional for container mode):** Docker Engine 24+ and Docker Compose v2.
- **Bubblewrap (Optional for strict sandboxing):** `bubblewrap` package (`apt install bubblewrap`).

---

## Installation and Quickstart

### Option 1: Docker Compose (Recommended for Production & Raspberry Pi)

Containerized execution is the standard approach for persistent edge environments:

1. Clone the repository:
```bash
git clone https://github.com/lyon-christopher/pidots.git
cd pidots
```

2. Configure environment variables:
```bash
cp .env.example .env
nano .env
```
Fill in your API key, target language model, and optional alert endpoints:
```dotenv
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=qwen3.8-27b

# Optional: Remote HITL Alerts & Messaging
WEBHOOK_NOTIFICATION_URL=https://your-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=your-evolution-apikey
```

3. Start the service with Docker Compose:
```bash
docker compose up -d
```

4. Verify telemetry and application health:
```bash
docker compose ps
docker compose logs -f pidots-core
```
The server will be reachable on port `8000` (`http://localhost:8000`).

---

### Option 2: Local Installation and CLI Execution

For local development or direct host execution:

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the piDots package and dependencies in editable mode:
```bash
pip install -e .
```

3. Initialize the database schemas and workspace structures:
```bash
pidots init
```

4. Start the FastAPI server:
```bash
pidots serve --host 0.0.0.0 --port 8000
```

---

## Command Line Interface (CLI)

piDots provides the `pidots` command-line utility for operations and management:

```bash
# Display installed version
pidots --version

# Show system status, memory metrics, database size, and workspaces
pidots status

# List all registered AI Coworkers (Dots)
pidots dots list

# Start the HTTP and WebSocket server
pidots serve --host 127.0.0.1 --port 8000 --reload

# Manage pending actions in the HITL governance queue
pidots hitl list
pidots hitl approve <ACTION_ID>
pidots hitl reject <ACTION_ID>
```

---

## Usage as Python Library / Agent SDK

piDots can be imported directly into other Python applications or agent CLIs:

```python
import asyncio
from pathlib import Path
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.spaces_manager import SpacesManager

async def main():
    # 1. Initialize edge-optimized SQLite WAL database schemas
    await init_edge_database()

    dot_id = "dev-assistant"
    workspace_path = str(Path(settings.workspaces_root) / dot_id)

    # 2. Register the Dot in the SQLite database if it does not already exist
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dot_id,
                "DevOps Assistant",
                "Edge Operator",
                "You are an operational assistant on resource-constrained hardware.",
                settings.ai_model,
                workspace_path
            )
        )
        await db.commit()

    # 3. Initialize universal AI provider (OpenAI-compatible)
    provider = OpenAIUniversalProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        default_model=settings.ai_model,
    )

    # 4. Instantiate the autonomous coworker agent (Dot)
    agent = DotAgent(
        dot_id=dot_id,
        provider=provider,
    )

    # 5. Save versioned document in Spaces with diffs and KNN vector indexing
    doc = await SpacesManager.save_document(
        dot_id=agent.dot_id,
        filename="status_relatorio.txt",
        content="Operational summary report generated via piDots official SDK.",
        title="Status Report"
    )
    print(f"Versioned document saved in Spaces: {doc['filename']} (v{doc['version']})")

    # 6. Execute reasoning turn with AG-UI streaming events
    async for event in agent.run_thread(thread_id="main-thread", user_message="Service health check"):
        if event["event"] == "message:chunk":
            print(event["data"].get("delta", ""), end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## REST API and Real-Time Streaming

The application exposes endpoints for external integration with Server-Sent Events (SSE) streaming support:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Official SPA/PWA operational console in Pixel Paper UI (Dark Noir and Blueprint) |
| `GET` | `/apresentacao` | Official landing page in Pixel Paper UI |
| `GET` | `/guia` | Step-by-step interactive operator guide |
| `GET` | `/relatorio` | Engineering feasibility and benchmark technical report |
| `GET` | `/health` | Hardware telemetry (SoC temperature, RAM, SQLite WAL status) |
| `GET` | `/manifest.json` | Progressive Web App manifest for desktop and mobile installation |
| `GET` | `/icon.svg` | Official vector SVG icon with 24-hour cache headers |
| `GET` | `/api/dots` | List all registered AI Coworkers with archetypes and status |
| `POST` | `/api/threads` | Create a durable conversation thread |
| `GET` | `/api/threads/{id}/messages` | Message history with multi-actor metadata and visibility scope |
| `POST` | `/api/threads/{id}/runs` | Execute autonomous agent loop with AG-UI SSE streaming |
| `GET` | `/api/hitl/pending` | List pending Human-in-the-Loop approval requests |
| `POST` | `/api/hitl/{id}/resolve` | Formally approve or reject a retained command |
| `POST` | `/api/hitl/webhook-callback` | Remote webhook callback for asynchronous HITL resolution |
| `GET` | `/api/spaces` | List versioned documents stored in Spaces |
| `POST` | `/api/spaces` | Save or update a document with incremental versioning and diffs |
| `GET` | `/api/spaces/{id}` | Retrieve full contents of a Spaces document |
| `GET` | `/api/spaces/{id}/revisions` | Revision history with unified diff calculation |
| `POST` | `/api/spaces/search` | Fast KNN semantic vector search in edge memory (CRC32) |
| `GET` | `/api/spaces/{id}/download` | Download document contents in plain text |
| `GET` | `/api/workspaces/{dot_id}/export.zip` | Export entire Dot workspace as a ZIP archive (with Spaces fallback) |
| `GET` | `/api/tasks` | List proactive scheduled tasks (Dot Heartbeats) |
| `POST` | `/api/tasks` | Register a new proactive task with a cron expression |
| `GET` | `/api/channels` | List collaborative team channels with message counts |
| `POST` | `/api/channels` | Create a new team channel |
| `GET` | `/api/channels/{id}/messages` | Retrieve recent messages from a channel with limit parameter |
| `POST` | `/api/channels/{id}/messages` | Post a message to a channel and trigger multi-bot collaboration |
| `POST` | `/api/channels/{id}/members` | Add a member (Dot or user) to a channel |
| `POST` | `/api/webhooks/incoming/{dot_id}` | Universal incoming webhook for scripts and external APIs |
| `POST` | `/api/webhooks/telegram/{dot_id}` | Incoming webhook handler for official Telegram Bot API |
| `POST` | `/api/webhooks/whatsapp/{dot_id}` | Incoming webhook handler for Evolution API / Baileys (WhatsApp) |
| `GET` | `/api/settings` | Operational system settings, notification channels, Evolution API status, and active model |
| `POST` | `/api/settings/ai` | Hot-reload AI provider parameters without restarting container |
| `POST` | `/api/settings/notifications` | Hot-reload notification endpoints (Webhook, Telegram, and Evolution API) |

> [!NOTE]
> **HTTP Defensive Security Headers:** All HTTP responses from the FastAPI edge server automatically include security hardening headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`), shielding embedded kiosks and remote HTTPS tunnels (Cloudflared) against MIME sniffing and clickjacking attacks.

---

### Web SPA Operational Console and Pixel Paper UI Design System
piDots includes a native dark-mode SPA/PWA interface served directly on the root path (`http://localhost:8000/`), engineered under the **Pixel Paper UI** design system:
- **Pixel Paper UI Aesthetics:** Tactical visual style inspired by technical teletypes, library catalog cards, and graph paper with high density and zero emojis.
- **Official Vector Logo:** piDots identity branding served via `/icon.svg` with interconnected nodes in green (#10b981) and cyan (#38bdf8).
- **26 Technical SVG Icons System:** Consistent iconography (`stroke-width: 2`, `stroke-linecap: round`) across telemetry, workspace tabs, sidebar sections, and action triggers.
- **Diff Viewer and Versioning:** Side-by-side inspection of file modifications persisted in SQLite WAL with analog status stamps.
- **Interactive HITL Governance:** Forensic approval and veto cards for commands with audit trail logging and state stamps.
- **AG-UI Reasoning Streaming:** Progressive token-by-token display of agent thoughts and tool calls.

---

## Governance and Security

### Human-in-the-Loop (HITL)
Commands with destructive potential (such as recursive file deletion, permission modifications with `chmod/chown`, `sudo` execution, or modifications to critical system paths) are intercepted by the governance engine. Execution is suspended in a pending state until a human operator explicitly approves the action via the web dashboard or CLI (`pidots hitl approve`).

### Bubblewrap Sandboxing
To protect host integrity, command execution is sandboxed using native Linux Bubblewrap (`bwrap`). Processes run within isolated filesystem namespaces and restricted process trees, preventing unauthorized access outside the designated agent workspace.

---

## Automated Testing

The repository includes automated test suites and stress benchmarks to validate concurrent resilience on edge hardware:

```bash
# Infrastructure and sandboxing test suites
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Multi-Bot orchestration and Dynamic Tool Pruning suite
python3 scripts/test_phase6_multibot.py

# Proactive Dot Heartbeat scheduler suite (croniter & HEARTBEAT_OK)
python3 scripts/test_phase7_scheduler.py

# Messaging gateway, webhooks, and team channels suite
python3 scripts/test_phase8_messaging.py

# End-to-end resilience suite (Phases 1-4: typed exceptions, AG-UI v1.0, 3 consumers, Circuit Breaker)
python3 scripts/test_resilience_phases.py

# Full edge load and concurrency stress test
python3 scripts/stress_test.py
```

---

## Repository Structure

```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── ARCHITECTURE.md                  # In-depth architectural and I/O specifications
├── CONTRIBUTING.md                  # Technical contribution guidelines
├── docker-compose.yml               # Official Docker Compose orchestration
├── Dockerfile                       # Lean image based on python:3.13-slim
├── LICENSE                          # MIT License
├── MANUAL_OPERACIONAL.md            # Operational administration guide
├── pidots/                          # Core application package source code
│   ├── config.py                    # Pydantic configuration and environment variables
│   ├── main.py                      # FastAPI server, REST endpoints, and SSE streaming
│   ├── core/                        # ReAct loop, multi-bot, scheduler, and messaging
│   │   ├── agent.py                 # Autonomous agent reasoning with Dynamic Tool Pruning
│   │   ├── hitl.py                  # High-risk command interception and review
│   │   ├── messaging_gateway.py     # Unified messaging gateway and collaborative channel bus
│   │   ├── notifier.py              # Outbound notifications and webhooks
│   │   ├── orchestrator.py          # Multi-Bot orchestrator and subtask delegation
│   │   ├── scheduler.py             # Proactive Dot Heartbeat scheduler via croniter
│   │   └── state.py                 # Session state and context manager
│   ├── providers/                   # Language model adapters (LLM/SLM)
│   │   └── openai_client.py         # Universal OpenAI-compatible gateway provider
│   ├── storage/                     # SQLite WAL persistence and vector search
│   │   ├── db.py                    # Connection lifecycle and schema management
│   │   ├── spaces_manager.py        # File versioning and unified diffs
│   │   └── vector_store.py          # CRC32-accelerated KNN vector search engine
│   └── tools/                       # Executable agent tools
│       ├── file_ops.py              # Atomic read and write operations
│       ├── registry.py              # Centralized tool registry
│       ├── terminal.py              # Process execution with Bubblewrap (bwrap) sandbox
│       └── web_reader.py            # Lightweight web extraction via trafilatura
├── pidots_apresentacao_pixel_paper.html # Official high-conversion presentation page
├── pidots_guia.html                 # Step-by-step interactive operational guide
├── pidots_spa_prototype.html        # Official SPA/PWA operational console
├── pyproject.toml                   # PEP 517/518/621 packaging specification
├── README.md                        # Primary documentation (Brazilian Portuguese)
├── README_EN.md                     # Mirrored documentation (American English)
├── relatorio_estudo_pidots.html     # Technical feasibility and engineering study report
├── requirements.txt                 # Strict dependency pinning
├── SECURITY.md                      # Security policy and vulnerability reporting
└── scripts/                         # Automated test suites and stress benchmarks
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Developed by **lyon christopher** (2026).
