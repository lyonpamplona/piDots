# piDots

**Persistent Edge AI Coworker for Edge Computing (SBCs, ARM64 / x86_64, Benchmark: Raspberry Pi 4B)**

[Português](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)
![Arch](https://img.shields.io/badge/Architecture-ARM64%20%7C%20x86__64-informational?style=flat&logo=arm&logoColor=white)
![Hardware](https://img.shields.io/badge/Target-Edge%20SBCs%20%7C%20ARM64%20%7C%20x86__64-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=flat&logo=docker&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Overview

**piDots** is an edge-native autonomous agent platform (AI Coworkers) built to run continuously 24/7 on Single Board Computers (SBCs), Mini PCs, and local servers, using the **Raspberry Pi 4B with 4GB RAM (ARM64)** as its physical benchmark.

We designed piDots from scratch for real silicon. Traditional enterprise agent frameworks assume cloud instances with dozens of gigabytes of RAM, hidden headless browsers, and containerized vector databases. On real edge hardware, this architecture breaks down. Temperatures soar, MicroSD cards wear out quickly under relentless fsync calls, and monthly cloud bills skyrocket.

piDots solves this as an asynchronous modular monolith in Python (`FastAPI + uvloop`). By removing bloated runtimes, we deliver a deterministic engine that uses **less than 50 MB RAM at idle** and **under 80 MB during concurrent multi-agent execution**.

The system provides persistent coworkers tailored for real-world tasks (coding, system architecture, security auditing, and autonomous maintenance), backed by SQLite WAL persistence, Bubblewrap sandbox containment, HMAC-SHA256 signed Human-in-the-Loop governance, and a tactical dark-mode web console.

---

## Technical Comparison: piDots vs Traditional Cloud Frameworks

| Parameter | Traditional Frameworks (Cloud Standard) | piDots (Edge Computing) |
| :--- | :--- | :--- |
| **Minimum Hardware** | x86_64 Server with 8GB to 16GB RAM | Raspberry Pi 4B (4GB RAM) / ARM64 / x86_64 |
| **Runtime Stack** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Memory Footprint (Idle)** | 2,000 MB - 3,500 MB RAM | ~48 MB - 52 MB RAM (~98% reduction) |
| **Memory under Load (Peak)** | 4,000 MB - 6,000 MB RAM | < 100 MB RAM |
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
├── main.py              # FastAPI bootstrap, Lifespan manager, and middleware configuration
├── api/                 # Decoupled modular sub-routers (APIRouters)
│   ├── __init__.py      # Central route aggregator
│   ├── routes_dots.py   # Agent management and Dot Packs v1.1
│   ├── routes_threads.py # Conversation sessions, channels, and SSE streaming
│   ├── routes_tasks.py  # Proactive schedules and maintenance
│   ├── routes_webhooks.py # Telegram, WhatsApp, and incoming webhooks
│   ├── routes_edge.py   # Telemetry, hardware triggers, and changelog
│   ├── routes_hitl.py   # Governance and HMAC-SHA256 remote resolution
│   ├── routes_mcp.py    # MCP Lite server discovery and management
│   └── routes_static.py # Canonical delivery via EdgeAssetManager
├── core/
│   ├── __init__.py
│   ├── agent.py         # Asynchronous ReAct execution engine with Dynamic Tool Pruning
│   ├── council.py       # Advisory Council tripartite dialectic deliberation engine
│   ├── dot_pack.py      # Dot Packs v1.1 signed with SHA-256 and prompt injection defense
│   ├── edge_triggers.py # Event-driven hardware triggers, GPIO bus, and MQTT listener
│   ├── hitl.py          # Human-in-the-Loop governance engine with TTL expiration
│   ├── hitl_crypto.py   # HMAC-SHA256 signature and constant-time token verification
│   ├── messaging_gateway.py # Unified messaging gateway and collaborative channel bus
│   ├── notifier.py      # HTTP notifier and signed remote webhook alerts
│   ├── orchestrator.py  # Multi-Bot orchestrator (Supervisor, Handoff, @dot mentions)
│   ├── planner.py       # Two-Stage Planning engine (Goals, Milestones, and Checkpoints)
│   ├── scheduler.py     # Proactive Dot Heartbeat engine powered by croniter and circuit breaker
│   ├── self_healing.py  # Self-Healing Harness and surgical traceback diagnostic analyzer
│   └── state.py         # AG-UI protocol event definitions and session state tracking
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Universal inference gateway with 3-state Circuit Breaker
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL layer tuned for microSD and idempotent migrations
│   ├── maintenance.py   # Autonomous edge maintenance, WAL checkpoint TRUNCATE, and VACUUM INTO
│   ├── memory_manager.py # Hierarchical MemGPT memory (Core Memory, Archival FTS5 + 64d)
│   ├── shared_space.py  # Shared knowledge space for collaborative in-thread multi-bot notes
│   ├── spaces_manager.py # Isolated dot workspaces, document versioning, and unified diffs
│   └── vector_store.py  # On-disk KNN vector store with CRC32 n-gram hashing
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Atomic file reading, writing, and workspace listing
    ├── mcp_client.py    # Async MCP Lite client over STDIO/SSE with Tool Pruning
    ├── registry.py      # Centralized tool registry with Dynamic Tool Pruning
    ├── terminal.py      # Bubblewrap-isolated shell executor with STRICT_SANDBOX guard
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
  - `supervisor`: Workflow coordinator, planning, and executive goal tracking.
  - `coder`: Software development, terminal debugging, isolated sandbox runs, and automated testing.
  - `architect`: System architecture, data modeling, conceptual synthesis, and technical documentation.
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
- **Graceful Operational Failure Handling:** When upstream inference fails, the gateway catches the event and dispatches an informative `[OPERATIONAL_ERROR]` notice to the remote user without degrading communication channel integrity.

### 4. Cognitive Resilience Architecture and Typed Exception Handling
The core piDots engine enforces an end-to-end resilient execution loop:
- **Typed Provider Exceptions:** The `OpenAIUniversalProvider` client strictly differentiates `ProviderAuthError` (HTTP 401/403 with immediate short-circuiting and no wasteful retries) from `ProviderTransientError` (HTTP 503/429/timeout with exponential backoff and jitter).
- **Standardized AG-UI v1.0 Protocol Contract:** The `DotAgent.run_thread` lifecycle emits a terminal `run:finished` event with `status: "failed"`, providing structured `error`, `error_type` (`auth_error` or `transient_error`), and `final_response: ""`.
- **Internal Diagnostic Tape:** Root-cause errors are persisted to SQLite WAL `messages` with `internal` visibility (`[INFERENCE_ERROR]` or `[AUTH_ERROR]`), ensuring complete technical auditability without polluting human-facing feeds.
- **Integrated Resilience across Three Consumer Subsystems:**
  - *EdgeScheduler:* Accurately persists `FAILED` status with actual technical error summaries in SQLite, eliminating false-positive completions.
  - *MessagingGateway:* Returns structured, user-friendly error notices (`[OPERATIONAL_ERROR]`) across external chat bridges.
  - *MultiBotOrchestrator:* Marks subtasks in `agent_handoffs` as `FAILED`, writes internal diagnostic alerts to parent threads, and provides structured feedback `{'success': False, 'error': ...}` allowing supervisory replanning.

### 5. Hierarchical Autonomous Memory (MemGPT / Letta Pattern)
The `pidots/storage/memory_manager.py` module delivers a 3-tier memory hierarchy managed autonomously by the Dot via native Function Calling:
- **In-Context Core Memory (`<core_memory>`):** Resident prompt blocks with strict character boundaries preventing token bloat: `human` (user profile), `persona` (agent identity), and `active_context` (operational mission).
- **Self-Editing Memory Tools:** `core_memory_append` and `core_memory_replace` allow the Dot to update its identity and guidelines without human prompts.
- **Archival Memory with Hybrid Search:** Enduring factual knowledge persisted to SQLite table `archival_memories` and indexed synchronously via FTS5 (`archival_memories_fts`). Blends BM25 keyword rankings with 64-dimensional sparse vector projections (3-gram feature hashing with semantic activation), queried via `archival_memory_insert` and `archival_memory_search`.
- **Recall Memory:** The `recall_memory_search` tool queries previous turns and decisions in the active conversation thread without stuffing raw messages into active context.

### 6. Self-Healing Harness and Two-Stage Planning (Goals & Milestones)
- **Self-Healing Harness (`pidots/core/self_healing.py`):** Inspects shell and Python execution outputs. Upon failure, it parses tracebacks, isolates the failing file, line, and exception type, triggers an AG-UI `self_healing:triggered` event, and generates surgical remediation advice via `execute_and_verify`.
- **Two-Stage Planning (`pidots/core/planner.py`):** Models persistent `goals` and `milestones` in SQLite WAL. The agent constructs plans (`plan_create`), updates milestone completion with technical evidence (`plan_update_step`), and tracks progress percent (`plan_get_status`), injecting formatted `<execution_plan>` blocks into reasoning context.

### 7. Advisory Council and Dialectic Multi-Bot Deliberation
The `pidots/core/council.py` module coordinates formal multi-agent deliberation:
- **Council Roles:** Proponent (`@coder` formulates technical designs), Critical Auditor (`@auditor` conducts adversarial risk reviews), and Supervisor (`@supervisor` synthesizes executive resolutions).
- **Deliberation Log Isolation:** Intermediary deliberation rounds are tagged with `visibility: 'internal'`. Only the final resolution is published with an `[ADVISORY COUNCIL - FINAL RESOLUTION]` header.
- **Safety Ceiling:** Strict 3-round upper limit to enforce finite inference expenditure, maintaining resident RAM consumption below 53 MB.
- **Native Tool:** Accessible to agents via `run_council_debate`.

### 8. Shared Knowledge Space and Portable Dot Packs (v1.1)
- **Shared Knowledge Space (`pidots/storage/shared_space.py`):** Collaborative in-thread note board indexed by `(thread_id, topic_key)` in `thread_shared_notes`. Supports atomic writes (`shared_space_write`), reads (`shared_space_read`), and collaborative overwriting across thread bots, rendered into `<shared_knowledge_space>`.
- **Dot Packs v1.1 with SHA-256 Signatures (`pidots/core/dot_pack.py`):** Standardized JSON manifest with an embedded cryptographic `sha256_checksum`. During atomic import (`POST /api/dots/import-pack`), the system validates manifest integrity and runs static security audits against Prompt Injection patterns in `core_memory` before instantiating the coworker.

### 9. Edge Hardware Triggers and Autonomous MicroSD Maintenance
- **Event-Driven Hardware Triggers (`pidots/core/edge_triggers.py`):** Proactively reads SoC Broadcom BCM2711 temperatures via sysfs (`/sys/class/thermal/thermal_zone0/temp`), MicroSD free disk space, and free RAM. Automatically triggers inference throttling and dispatches HITL alerts if temperature exceeds 72°C or free storage drops below 10%. Endpoint: `GET /api/edge/triggers`.
- **Nightly Autonomous Maintenance (`pidots/storage/maintenance.py`):** Runs `PRAGMA wal_checkpoint(TRUNCATE)` to zero out WAL size, consolidates older messages (> 7 days) into `episodic_memories` while pruning raw rows, performs atomic backups via `VACUUM INTO` in an isolated connection (`isolation_level=None`), and optimizes SQLite query planner indices via `PRAGMA optimize`. Endpoint: `POST /api/edge/maintenance`.

### 10. Native Bilingual Internationalization (PT/EN) & Edge Micro-Engine
- **Vanilla JS Micro-Engine (`static/pidots-i18n.js`):** Instant language switching (< 10ms) without bloated frontend frameworks or memory overhead, persisting preference safely in `localStorage.getItem('pidots_lang')`.
- **Atomic JSON Dictionaries (`data/locales/pt.json` and `data/locales/en.json`):** Semantic edge localization dictionaries with proactive stale-while-revalidate caching and graceful fallbacks.
- **Strict textContent DOM Mutation:** Declarative attribute bindings via `data-i18n` and `data-i18n-attr`, guaranteeing complete immunity against cross-site scripting (XSS).
- **Interactive Onboarding & SemVer v1.5.3 Patch Notes:** Five-step first-run walkthrough with persistent client completion and dynamic patch notes modal synchronized via `/api/changelog`.

### 11. Unified Slash Commands Protocol (/), Adaptive Triptych & Mobile-First Engineering
- **Comprehensive 30 Slash Commands Catalog:** Commands structured across 6 operational domains (System, Agents, Memory, Tasks, Edge, Export), triggered with `/` in the teletype or via the mechanical touch button `[/]`. Local commands (`/clear`, `/theme`, `/lang`, `/telemetry`, etc.) execute client-side in under 16ms with zero LLM API calls and zero token consumption.
- **Mechanical Slash Trigger Button [/]:** Dedicated tactile button (`#slashTriggerBtn`) inside the operational console opening the slash command popover instantly on mobile devices without requiring virtual keyboard engagement.
- **Vanilla JS Autocomplete Popover Engine:** Lightweight client-side engine (< 10KB) providing in-memory fuzzy search, cyclic arrow key navigation (ArrowUp/ArrowDown), Tab/Enter completion, Escape dismissal, and Levenshtein fault-tolerance.
- **Tactile Teletype Slips (Slash Receipt Slip):** Receipts generated with UTC timestamps, sequential `SEQ#` audit tags, jagged perforation lines, and an enforced DOM ceiling of 150 nodes to avoid memory leaks.
- **Adaptive Workspace Triptych (1024px-1440px):** Responsive 3-column layout collapsing the left sidebar on-demand into an overlaid 260px drawer with backdrop, expanding useful teletype width from 202px to > 750px while keeping the Live Canvas in a 50/50 split.
- **Consolidated Edge Pulse Chip Telemetry:** High-density single-line header monitor (`[EDGE // 48.2 °C // 118 MB // WAL ACTIVE // HITL 0]`), conserving over 360px of horizontal viewport real estate.
- **Mobile Bottom Navigation Bar:** High-density fixed footer bar active on screens <= 768px (`.mobile-bottom-nav`) with 4 ergonomic tabs (`[O] DOTS`, `[>] CHAT`, `[*] CANVAS`, `[?] GUIDE`), isolated with `env(safe-area-inset-bottom)` and minimum 44x44pt hitboxes (Thumb Zone) via `::after` pseudo-elements.
- **Dynamic Virtual Keyboard Synchronization (window.visualViewport):** Reactive `window.visualViewport` listener adjusting physical body height (`document.body.style.height = ${vv.height}px`), hiding bottom navigation via the `keyboard-open` class, and auto-scrolling the ticker after 60ms to eliminate UI collisions on iOS Safari and Android Chrome.
- **Apple WebKit Anti-Zoom Protection:** Mandatory `font-size: 16px` on mobile inputs and textareas with `touch-action: manipulation`, completely preventing Safari's destructive viewport auto-zoom.

### 12. High-Performance In-Context Spotlight Tour & FTUE Onboarding
- **Vanilla JS PiDotsTourEngine (< 12KB):** Completely replaces static blocking modals with an in-context spotlight anchoring system in the live DOM. Uses single-layer `box-shadow: 0 0 0 9999px rgba(7, 9, 12, 0.84)` composited directly on the GPU, requiring < 1% CPU on the Raspberry Pi 4B and zero third-party dependencies.
- **Five Canonical Walkthrough Steps:** Practical interactive guide spotlighting the Central Agent Squad, Command Terminal & Teletipo, Workspace Focus Switcher (Zen vs 50/50), Live Canvas & Diffs, and System Drawer (F1).
- **Safe-Area Anchoring & Non-Intrusive Mobile Focus:** Fixed positioning of `.pixel-tour-popover` above the bottom navigation bar respecting iOS safe areas, alongside virtual keyboard suppression during mobile walkthroughs.
- **Slash Command `/tour`:** Allows revisiting the walkthrough anytime or resetting operator state via `/tour reset`.
- **System Drawer & Context Menu Integration:** Dedicated card `[REVER GUIA OPERACIONAL SPOTLIGHT]` in the F1 drawer and rapid context menu shortcut.
- **First-Time Access Auto-Trigger:** Automatically detects new operators via `localStorage.getItem('pidots_tour_completed')` with a smooth 600ms boot decoupling delay.

### 13. MCP Lite Client (Model Context Protocol) with Dynamic Tool Pruning
- **On-Demand External Tooling (`pidots/tools/mcp_client.py`):** Connects lightweight external MCP servers via STDIO or async Server-Sent Events (SSE) in pure Python (< 5MB RAM).
- **Automatic Schema Conversion:** Translates JSON-RPC 2.0 tool definitions into validated Python callables registered dynamically into the `ToolRegistry`.
- **Strict Dynamic Tool Pruning:** Connected MCP tools are bound to each agent's `allowed_tools_json` whitelist, keeping prompt tokens minimal and preventing hallucinations.

### 14. Remote Signed HITL Governance with HMAC-SHA256 and TTL
- **Mobile Action Approval (`pidots/core/hitl_crypto.py`):** Generates signed interactive approval and veto links for Telegram and WhatsApp using constant-time HMAC-SHA256 (`hmac.compare_digest`).
- **Dedicated Endpoint (`/api/hitl/signed-resolve`):** Authorizes or rejects sensitive commands with one tap on a smartphone without needing a browser login session.
- **Automatic Time-To-Live Expiration (TTL 30m):** Retained requests automatically transition to `EXPIRED` status after 30 minutes, freeing resources and writing an audit security record.

### 15. Physical GPIO Bus and Edge MQTT Sensor Listener
- **Hardware Direct Interfacing (`pidots/core/edge_triggers.py`):** Native pin reading on Raspberry Pi 4B GPIO (with graceful container and x86_64 fallbacks).
- **Async MQTT Listener:** Allows local edge sensors and IoT relays to publish telemetry directly to piDots, triggering autonomous agent runs without blocking the uvloop.

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
git clone https://github.com/lyonchristopher/piDots.git
cd piDots
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
AI_MODEL=gpt-4o-mini

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
| `GET` | `/` | Official landing and onboarding page (ReAct simulator and silicon calculator) |
| `GET` | `/app` | Official SPA/PWA operational console (Dark Noir and Blueprint monospace) |
| `GET` | `/workspace` | Canonical operational alias for the SPA/PWA workspace console (`/app`) |
| `GET` | `/docs` | Canonical operator guide with client-side search (Ctrl+K), retractable drawer, and API tester |
| `GET` | `/relatorio` | Engineering feasibility and benchmark technical report |
| `GET` | `/api/docs` | Decoupled interactive OpenAPI Swagger UI for developers |
| `GET` | `/api/openapi.json` | Raw JSON structured OpenAPI 3.0 schema |
| `GET` | `/health` | Hardware telemetry (SoC temperature, RAM, SQLite WAL status) |
| `GET` | `/manifest.json` | Progressive Web App manifest for desktop and mobile installation (`start_url: /app`) |
| `GET` | `/sw.js` | Progressive Web App Service Worker with defensive v7 cache for offline resilience |
| `GET` | `/icon.svg` | Official vector SVG icon with 24-hour cache headers |
| `GET` | `/static/pidots-i18n.js` | Client-side Vanilla JS internationalization micro-engine |
| `GET` | `/data/locales/{lang}.json` | Atomic bilingual localization dictionaries (PT/EN) with edge caching |
| `GET` | `/api/changelog` | SemVer release history and categorized update notes (Patch Notes v1.5.3) |
| `GET` | `/api/dots` | List all registered AI Coworkers with archetypes and status |
| `GET` | `/api/dots/{id}/export-pack` | Portable DotPack v1.1 export with SHA-256 integrity signature |
| `POST` | `/api/dots/import-pack` | Atomic import of AI Coworker packages from DotPack v1.1 with security audit |
| `POST` | `/api/threads` | Create a durable conversation thread |
| `GET` | `/api/threads/{id}/messages` | Message history with multi-actor metadata and visibility scope |
| `POST` | `/api/threads/{id}/runs` | Execute autonomous agent loop with AG-UI SSE streaming |
| `GET` | `/api/hitl/pending` | List pending Human-in-the-Loop approval requests |
| `POST` | `/api/hitl/{id}/resolve` | Formally approve or reject a retained command |
| `POST` | `/api/hitl/signed-resolve` | Remote HMAC-SHA256 signed HITL approval/rejection for Telegram/WhatsApp |
| `POST` | `/api/hitl/webhook-callback` | Remote webhook callback for asynchronous HITL resolution |
| `GET` | `/api/mcp/servers` | Discover connected lightweight MCP Lite external servers |
| `GET` | `/api/spaces` | List versioned documents stored in Spaces |
| `POST` | `/api/spaces` | Save or update a document with incremental versioning and diffs |
| `GET` | `/api/spaces/{id}` | Retrieve full contents of a Spaces document |
| `GET` | `/api/spaces/{id}/revisions` | Revision history with unified diff calculation |
| `POST` | `/api/spaces/search` | Fast KNN semantic vector search in edge memory (CRC32) |
| `GET` | `/api/spaces/{id}/download` | Download document contents in plain text |
| `GET` | `/api/workspaces/{dot_id}/export.zip` | Export entire Dot workspace as a ZIP archive (with Spaces fallback) |
| `GET` | `/api/tasks` | List proactive scheduled tasks (Dot Heartbeats) |
| `POST` | `/api/tasks` | Register a new proactive task with a cron expression |
| `GET` | `/api/edge/triggers` | Hardware trigger telemetry (SoC temperature, MicroSD space, free RAM) |
| `POST` | `/api/edge/maintenance` | On-demand execution of autonomous maintenance (WAL checkpoint and backup) |
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

### Web SPA Operational Console and Minimalist Technical Interface
piDots includes a native dark-mode SPA/PWA interface served on the canonical path `/app` (or `/workspace`), engineered as a tactical monospace console:
- **High-Density Technical Aesthetics:** Tactical visual style inspired by technical matrix consoles with high information density, crisp typography, and 1-bit retro minimalism.
- **Official Vector Logo:** piDots identity branding served via `/icon.svg` with interconnected nodes in green (#10b981) and cyan (#38bdf8).
- **Three Ergonomic Operational Modes:**
  - *Mode 1: 50/50 Creation:* Side-by-side teletype chat and Live Canvas for simultaneous coding, artifact generation, and document review.
  - *Mode 2: Zen Focus (Claude Code / Linear style):* Collapsed sidebar and canvas, centering chat at an optimal 880px width for deep reading and continuous thought.
  - *Mode 3: Technical Management Panel:* On-demand access to hardware telemetry (SoC/RAM/WAL), LLM settings, and bubblewrap sandbox via the retractable drawer (F1 / `[SISTEMA]` or `/telemetry`).
- **Core Specialist Squad:** Clean interface displaying only the 4 essential coworkers (Supervisor, Coder, Architect, and Auditor), eliminating the clutter of dozens of test bots.
- **Unobstructed Teletype & Input:** Removed 20px tractor-feed margins (40px reclaimed) and rigid command prompt sign, granting maximum horizontal width for reading and drafting.
- **Diff Viewer and Versioning:** Side-by-side inspection of file modifications persisted in SQLite WAL with analog status stamps.
- **Just-in-Time Interactive HITL Governance:** Security approval and veto cards rendered only when actions are held, preserving security audit trails.
- **AG-UI Reasoning Streaming:** Progressive token-by-token display of agent thoughts and tool calls.
- **Guided Onboarding Walkthrough:** Five-step interactive onboarding flow for first-time operators with client persistence and instant F1 replay.
- **SemVer v1.5.3 Patch Notes Hub:** Dynamic update notes modal synchronized via `/api/changelog`, categorizing modifications across Four Pillars: Included, Adjusted, Deprecated, and Security & Edge.

#### Cross-Surface Navigation via Global Keyboard Chords
Instant, zero-friction transition between system surfaces without requiring a mouse:

| Sequential Chord | Target Surface | Description |
| :--- | :--- | :--- |
| `g` followed by `h` | `/` | Go Home: Official Landing Page & Onboarding |
| `g` followed by `w` | `/app` | Go Workspace: Operational SPA Console / Workstation |
| `g` followed by `d` | `/docs` | Go Docs: Interactive Operator Guide & Technical Reference |

#### High-Productivity SPA Console Shortcuts
Tactical terminal and artifact operations without interface friction:

| Shortcut | Operational Action | Description |
| :--- | :--- | :--- |
| `Key /` | Autocomplete Popover | Triggers catalog of 34 Slash Commands with fuzzy search in teletype |
| `Button [/]` | Touch Autocomplete | Opens slash command popover directly without triggering virtual keyboard |
| `Alt+1` to `Alt+4` | Activity Rail Sidebar | Instantly switches across the 4 contextual panes (Spaces, Dots Studio, Cron Tasks, 64D Memory) |
| `Bottom-Nav` | Mobile View Switch | Switches between [O] DOTS, [>] CHAT, [*] CANVAS, and [?] GUIDE views |
| `Alt+B` / `Ctrl+B` | Toggle Sidebar | Toggles visibility of coworkers and spaces sidebar |
| `Alt+I` | Inspect Artifact | Focuses and expands active artifact in Live Canvas |
| `Ctrl+S` / `Cmd+S` | Save Revision | Persists atomic document revision in Spaces to SQLite WAL |
| `Alt+H` | HITL Dossier | Focuses and opens Human-in-the-Loop governance approval card |
| `F11` | Toggle Canvas | Toggles between split view and maximized canvas view |
| `Ctrl+L` | Clear Teletype | Clears local screen messages from active teletype spool (/clear) |
| `F1` | Technical Panel / Help | Opens retractable side drawer with telemetry, shortcuts, and manual |

#### Unified Slash Commands (/) Protocol
The Operational SPA Console features a native slash command (`/`) engine designed for rapid execution and direct edge hardware control:
- **Zero Token Cost for Local Commands:** System, UI, and hardware inspection commands execute locally in the browser under 16ms with zero LLM API calls.
- **Floating Autocomplete Popover:** Triggered on typing `/`, with fuzzy memory filtering, keyboard navigation (Arrow keys), and instant selection via `Tab` or `Enter`.
- **Levenshtein Fault Tolerance:** Proactively suggests the closest valid command when minor typing mistakes occur (*"Did you mean: /command?"*).
- **Physical Teletype Receipt Slips:** Structured responses with `[CMD] SISTEMA` stamps, ISO UTC timestamps, sequential audit IDs (`SEQ# 000X`), and perforated tear-off edges under a 150-node DOM ceiling.

| Category | Primary Commands | Usage Examples |
| :--- | :--- | :--- |
| **System & UI** | `/help`, `/clear`, `/theme`, `/lang`, `/info`, `/status`, `/telemetry`, `/pwa`, `/tour`, `/onboarding`, `/changelog`, `/computer` | `/tour`, `/computer ls -la`, `/telemetry`, `/theme blueprint` |
| **Agents & Multi-Bot** | `/dots`, `/handoff`, `/council`, `/delegate`, `/archetype`, `/tools`, `/mcp`, `/coagents` | `/dots`, `/handoff dot-auditor`, `/coagents`, `/mcp` |
| **Memory & Knowledge** | `/memory`, `/archival`, `/shared`, `/spaces`, `/diff`, `/save-space` | `/archival SQLite WAL`, `/save-space notes.md`, `/diff` |
| **Tasks & Heartbeat** | `/tasks`, `/cron`, `/run-task` | `/tasks`, `/cron list`, `/run-task task-001` |
| **Governance & Edge** | `/hitl`, `/triggers`, `/maintenance`, `/backup` | `/hitl status`, `/triggers`, `/maintenance run` |
| **Export & Data** | `/export`, `/pack` | `/export chat`, `/export canvas`, `/pack dot-dev-core` |

---

## Governance and Security

### Human-in-the-Loop (HITL)
Commands with destructive potential (such as recursive file deletion, permission modifications with `chmod/chown`, `sudo` execution, or disk file write redirections `> / >> / tee`) are automatically intercepted by the governance engine. Execution is suspended in a pending state (`awaiting_hitl`) and an explanatory message is directly persisted in the active conversation thread with the approval ID and homologation instructions via the web interface (`/app` or `Alt+H`) or the `/hitl` slash command. Safe inspection commands with harmless stream discards (`2>/dev/null`, `2>&1`) execute autonomously without blocking the operator.

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

# Edge expansion plan test suites (Phases 1-5)
python3 scripts/test_phase9_memory.py               # Hierarchical Memory (Core Memory, Archival FTS5, 64d)
python3 scripts/test_phase10_self_healing_planner.py # Self-Healing Harness and Two-Stage Planning
python3 scripts/test_phase11_council_debate.py       # Advisory Council Tripartite Deliberation
python3 scripts/test_phase12_shared_space_dot_packs.py # Shared Knowledge Space and Dot Packs v1.0
python3 scripts/test_phase13_edge_triggers_maintenance.py # Hardware Triggers and MicroSD Maintenance

# AG-UI protocol, CoAgents Shared State, Generative UI Inline, and OpenDots Layout suites
python3 scripts/test_phase1_opendots_agui.py
python3 scripts/test_phase2_opendots_layout.py
python3 scripts/test_phase3_opendots_dynamic_js.py

# End-to-end resilience suite (Typed exceptions, AG-UI v1.0, 3 consumers, Circuit Breaker)
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
├── data/                            # Static application data, changelog, and localization dictionaries
│   ├── changelog.json               # SemVer v1.5.2 release history and categorized update notes
│   └── locales/                     # Atomic internationalization dictionaries (i18n)
│       ├── en.json                  # English localization terms
│       └── pt.json                  # Brazilian Portuguese localization terms
├── docker-compose.yml               # Official Docker Compose orchestration
├── Dockerfile                       # Lean image based on python:3.13-slim
├── LICENSE                          # MIT License
├── MANUAL_OPERACIONAL.md            # Operational administration guide
├── pidots/                          # Core application package source code
│   ├── config.py                    # Pydantic configuration and environment variables
│   ├── main.py                      # FastAPI server, REST endpoints, and SSE streaming
│   ├── core/                        # ReAct loop, multi-bot, scheduler, and messaging
│   │   ├── agent.py                 # Autonomous agent reasoning with Dynamic Tool Pruning
│   │   ├── council.py               # Advisory Council tripartite dialectic deliberation engine
│   │   ├── dot_pack.py              # Portable Dot Pack v1.0 packaging, export, and import manager
│   │   ├── edge_triggers.py         # Event-driven hardware triggers (SoC, MicroSD, RAM)
│   │   ├── hitl.py                  # High-risk command interception and review
│   │   ├── messaging_gateway.py     # Unified messaging gateway and collaborative channel bus
│   │   ├── notifier.py              # Outbound notifications and webhooks
│   │   ├── orchestrator.py          # Multi-Bot orchestrator and subtask delegation
│   │   ├── planner.py               # Two-Stage Planning engine (Goals and Milestones)
│   │   ├── scheduler.py             # Proactive Dot Heartbeat scheduler via croniter
│   │   ├── self_healing.py          # Self-Healing Harness and traceback diagnostic analyzer
│   │   └── state.py                 # Session state and context manager
│   ├── providers/                   # Language model adapters (LLM/SLM)
│   │   └── openai_client.py         # Universal OpenAI-compatible gateway provider
│   ├── storage/                     # SQLite WAL persistence and vector search
│   │   ├── db.py                    # Connection lifecycle and SQLite WAL schema management
│   │   ├── maintenance.py           # Autonomous edge maintenance, WAL checkpoint, and vacuum
│   │   ├── memory_manager.py        # Hierarchical MemGPT memory (Core, Archival FTS5)
│   │   ├── shared_space.py          # Shared knowledge space for collaborative in-thread notes
│   │   ├── spaces_manager.py        # File versioning and unified diffs
│   │   └── vector_store.py          # CRC32-accelerated KNN vector search engine
│   └── tools/                       # Executable agent tools
│       ├── file_ops.py              # Atomic read and write operations
│       ├── registry.py              # Centralized tool registry
│       ├── terminal.py              # Process execution with Bubblewrap (bwrap) sandbox
│       └── web_reader.py            # Lightweight web extraction via trafilatura
├── pages/                           # Decoupled semantic HTML pages
│   ├── app.html                     # Official SPA/PWA operational console (/app)
│   ├── landing.html                 # Official presentation and hero landing page (/)
│   ├── docs.html                    # Step-by-step interactive operational guide (/docs)
│   └── relatorio.html               # Historical technical feasibility report (/relatorio)
├── pyproject.toml                   # PEP 517/518/621 packaging specification
├── README.md                        # Primary documentation (Brazilian Portuguese)
├── README_EN.md                     # Mirrored documentation (American English)
├── requirements.txt                 # Strict dependency pinning
├── SECURITY.md                      # Security policy and vulnerability reporting
├── scripts/                         # Automated test suites and stress benchmarks
└── static/                          # High-performance frontend static assets
    ├── css/                         # Modular segmented stylesheets
    │   ├── tokens.css, reset.css, layout.css, components.css, mobile.css
    │   └── spa.css, landing.css, docs.css, relatorio.css
    └── js/                          # Modular Vanilla JS runtime engines
        ├── core/                    # i18n, scroll-lock, pixel-system
        ├── spa/                     # pidots-api, slash-commands, tour-engine, pidots-ux, app-init
        ├── landing/                 # landing.js (ReAct simulator, silicon ROI, HITL lock)
        └── docs/                    # docs.js (Ctrl+K Omnisearch, interactive API tester)
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Developed by **lyon christopher** (2026).
