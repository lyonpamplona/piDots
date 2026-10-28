# piDots

**Local Autonomous Agent Workstation for Edge Hardware (SBCs, ARM64 / x86_64, Benchmark: Raspberry Pi 4B)**

[Português](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)
![Arch](https://img.shields.io/badge/Architecture-ARM64%20%7C%20x86__64-informational?style=flat&logo=arm&logoColor=white)
![Hardware](https://img.shields.io/badge/Target-Edge%20SBCs%20%7C%20ARM64%20%7C%20x86__64-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=flat&logo=docker&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Overview

piDots turns a single-board computer into an autonomous AI agent workstation. It runs locally on your desk without relying on external cloud orchestration. The hardware benchmark for the project is a **Raspberry Pi 4B with 4 GB RAM (ARM64)**.

We built piDots for real silicon. Enterprise agent frameworks assume cloud servers packed with gigabytes of spare RAM, hidden headless browsers, and containerized vector databases. On edge hardware, that approach falls apart. The SoC overheats, synchronous disk writes destroy MicroSD cards, and energy consumption climbs.

piDots solves this with an asynchronous modular monolith in Python (`FastAPI + uvloop`). We stripped away bloated runtimes to deliver a lean, fast system: **under 50 MB RAM at idle** and **less than 80 MB during concurrent multi-agent runs**.

The platform gives you persistent specialists for practical work: coding, software architecture, technical auditing, and preventive maintenance. The entire stack features SQLite WAL persistence, process containment via Linux Bubblewrap sandboxes, real-time Human-in-the-Loop approvals, and a dark-mode tactical web console.

---

## Technical Comparison: piDots vs Cloud Frameworks

| Parameter | Cloud Frameworks (Industry Standard) | piDots (Edge Computing) |
| :--- | :--- | :--- |
| **Minimum Hardware** | x86_64 Server with 8 GB to 16 GB RAM | Raspberry Pi 4B (4 GB RAM) / ARM64 / x86_64 |
| **Execution Stack** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Memory Footprint (Idle)** | 2,000 MB - 3,500 MB RAM | ~48 MB - 52 MB RAM (~98% reduction) |
| **Memory under Peak Load** | 4,000 MB - 6,000 MB RAM | < 100 MB RAM |
| **Database & State** | PostgreSQL / Neo4j / Redis | SQLite with WAL Mode and tuned PRAGMAs |
| **Vector Search / Memory** | ChromaDB / Pinecone / Qdrant (500 MB+) | On-disk CRC32 KNN vector extractor (< 5 MB) |
| **Web Scraping** | Headless Chromium / Playwright (~500 MB RAM) | Pure CPU async Trafilatura / httpx (~20 MB) |
| **Process Isolation** | Nested Docker / Cloud VM | Native Linux Bubblewrap (`bwrap`) sandbox |
| **Storage Wear** | Heavy fsync write amplification | Flash-friendly append-only WAL writes |
| **Distribution** | Closed SaaS / Heavy Microservices | Python package (`pip install -e .`) & Docker |

---

## Architecture and Core Modules

piDots is organized as an asynchronous modular monolith to keep runtime overhead minimal:

```
pidots/
├── __init__.py
├── cli.py               # Native command-line interface for the terminal
├── config.py            # Environment variables and central settings
├── main.py              # FastAPI bootstrap, Lifespan manager, and middlewares
├── api/                 # Decoupled modular sub-routers (APIRouters)
│   ├── __init__.py      # Central route aggregator
│   ├── routes_dots.py   # Agent management and Dot Packs v1.1
│   ├── routes_threads.py # Conversation sessions, channels, and SSE streaming
│   ├── routes_tasks.py  # Proactive schedules and maintenance routines
│   ├── routes_webhooks.py # Telegram, WhatsApp, and incoming webhooks
│   ├── routes_edge.py   # SoC thermal telemetry, triggers, and changelog
│   ├── routes_hitl.py   # Safety queue and HMAC-SHA256 remote resolution
│   ├── routes_mcp.py    # MCP Lite server discovery and management
│   └── routes_static.py # Static asset delivery via EdgeAssetManager
├── core/
│   ├── __init__.py
│   ├── agent.py         # Async ReAct loop with dynamic tool pruning (AG-UI)
│   ├── council.py       # Advisory Council tripartite peer debate engine
│   ├── dot_pack.py      # Portable Dot Packs v1.1 with SHA-256 signatures
│   ├── edge_triggers.py # Hardware triggers (BCM2711), GPIO pins, and MQTT client
│   ├── hitl.py          # Human-in-the-Loop governance with TTL expiration
│   ├── hitl_crypto.py   # HMAC-SHA256 token signing and verification
│   ├── messaging_gateway.py # External messaging gateway and channel bus
│   ├── notifier.py      # HTTP notifier and signed remote alerts
│   ├── orchestrator.py  # Multi-bot orchestrator (Supervisor, Handoff, @dot mentions)
│   ├── planner.py       # Two-stage planning (Goals, Milestones, and Checkpoints)
│   ├── scheduler.py     # Proactive Dot Heartbeat engine powered by croniter
│   ├── self_healing.py  # Self-healing harness with traceback diagnostic parsing
│   └── state.py         # AG-UI protocol event definitions and session state
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Universal inference gateway with 3-state Circuit Breaker
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL layer tuned for MicroSD and idempotent schemas
│   ├── maintenance.py   # Autonomous maintenance, WAL checkpoint TRUNCATE, and VACUUM INTO
│   ├── memory_manager.py # Hierarchical memory (Core Memory and Archival FTS5 + 64d)
│   ├── shared_space.py  # Collaborative note board for agents in the same thread
│   ├── spaces_manager.py # Isolated workspaces, file versioning, and unified diffs
│   └── vector_store.py  # On-disk KNN vector store with CRC32 n-gram hashing
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Atomic file reading, writing, and directory listing
    ├── mcp_client.py    # Async MCP Lite client over STDIO/SSE
    ├── registry.py      # Central tool registry with dynamic tool pruning
    ├── terminal.py      # Shell executor inside Bubblewrap sandbox
    └── web_reader.py    # Pure-Python async web content extractor via Trafilatura
```

---

## Edge Engineering Capabilities

### 1. Multi-Bot Orchestration and Local Specialists

Instead of running disconnected chat windows, piDots connects multiple specialists inside a single Python process. The `ThreadRouter` scans for `@dot_name` mentions, resolves interlocutors, and tracks participants in the `thread_participants` table.

When a task requires different skills, the Supervisor breaks down the problem and delegates subtasks using `delegate_task`. Workers run in isolated threads and feed their results back to the main conversation. To transfer conversational focus, `handoff_to_dot` reassigns thread ownership while logging the transition in `agent_handoffs`. All background bot-to-bot exchanges use internal visibility to keep your workspace uncluttered.

Four pre-tuned archetypes ship out of the box:
- **Supervisor (`@supervisor`):** Coordinates missions, outlines execution steps, and consolidates final outputs.
- **Coder (`@coder`):** Writes code, debugs errors, runs sandbox commands, and runs automated tests.
- **Architect (`@muse`):** Models data structures, maps software flows, and writes technical specifications.
- **Auditor (`@auditor`):** Audits shell security, monitors thermals, and enforces hardware boundaries.

Each agent loads only the tools allowed in its configuration (`allowed_tools_json`). This dynamic pruning reduces context tokens by up to 75% and prevents agents from hallucinating unavailable tools.

### 2. Proactive Automations: Dot Heartbeat and Circuit Breakers

The built-in scheduler (`pidots/core/scheduler.py`) runs cron routines directly inside the FastAPI loop, eliminating the need for Redis, Celery, or external daemons:

Task definitions live in the SQLite `scheduled_tasks` table. When a recurring check confirms that system parameters are healthy, the agent responds with `HEARTBEAT_OK`. The scheduler logs a silent cycle and returns to sleep without sending noisy notifications or filling the database with empty records.

To protect the ARM CPU from runaways, memory locks prevent overlapping task executions. When an automation experiences repeated failures, an exponential backoff Circuit Breaker engages. Backoff delays scale from 30 seconds up to 1 hour. After 5 consecutive failures, the circuit trips open and the task is suspended. If your API key is missing or invalid, automated tasks pause safely before wasting bandwidth.

### 3. Messaging Gateway and Collaborative Channels

The gateway (`pidots/core/messaging_gateway.py`) manages inbound external webhooks without keeping state:

It includes native connectors for Telegram, WhatsApp (via Evolution API with API key authentication), and generic webhooks for custom shell scripts. Team conversations take place inside group rooms stored in the `channels` table.

To prevent two agents from talking in an endless loop, the messaging bus enforces strict rules:
1. Hard hop limit capped at 3 message forwards.
2. Bots only respond to other bots when explicitly mentioned via `@dot_name`.
3. Silent `NO_ACTION` responses whenever an agent has nothing valuable to contribute.

If your LLM provider suffers an outage, the gateway catches the exception and returns a clean operational alert to the external chat room without breaking the webhook.

### 4. Typed Error Handling and System Resilience

The inference client separates terminal authentication errors (HTTP 401/403) from transient network drops or rate limits (HTTP 429/503). Authentication errors abort execution immediately without wasting time on retries. Network errors use exponential backoff with randomized jitter.

Every run emits standard AG-UI protocol events. When an execution fails, the final `run:finished` event reports the exact failure type. Diagnostic details are saved to SQLite with internal visibility for offline debugging.

All three consuming layers remain resilient:
- The **Scheduler** logs the failure with the real traceback in the database.
- The **Messaging Gateway** delivers a concise failure notice to external chats.
- The **Multi-Bot Orchestrator** flags the subtask as failed and hands a structured error dictionary back to the supervisor to adjust the plan.

### 5. Three-Tier Memory Architecture

The memory manager (`pidots/storage/memory_manager.py`) allows agents to maintain their own state through native tool calls:

- **Working Core Memory (`<core_memory>`):** Fixed sections injected straight into the initial system prompt: user facts, agent persona, and current goal. Agents update these sections autonomously using `core_memory_append` and `core_memory_replace` as they learn new requirements.
- **Archival Memory with Hybrid Search:** Technical notes, code snippets, and references stored in `archival_memories`. Search merges full-text BM25 rankings from SQLite FTS5 with compact 64-dimensional vector projections built from n-gram hashing. Everything runs locally on the CPU via `archival_memory_search` without demanding heavy machine-learning packages.
- **Thread Recall Memory (`recall_memory_search`):** Searches earlier messages within the active thread so agents can retrieve past decisions without bloating context with hundreds of raw messages.

### 6. Self-Healing Harness and Two-Stage Planning

The self-healing engine (`self_healing.py`) inspects output from shell commands and Python scripts run in the sandbox. When a command fails, it parses the traceback, flags the file and line number, and proposes a fix through the `execute_and_verify` tool.

For larger projects, the planner (`planner.py`) breaks goals into smaller milestones stored in SQLite. The agent creates the roadmap with `plan_create`, attaches code artifacts and verification evidence using `plan_update_step`, and checks overall progress with `plan_get_status`.

### 7. Three-Way Peer Review (Advisory Council)

The `council.py` module convenes three specialists before high-risk tasks execute:
1. The **Coder** drafts the technical implementation.
2. The **Auditor** reviews the code for security bugs, thermal spikes, and excessive memory use.
3. The **Supervisor** evaluates both positions and renders the final operational decision.

The intermediate debate is logged internally for security auditing. Only the synthesized consensus appears in the operator feed. To prevent runaway token consumption, discussions are capped at 3 rounds. The entire debate loop runs within 53 MB RAM.

### 8. Shared Note Boards and Signed Dot Packs (v1.1)

The `shared_space.py` module acts as a collaborative blackboard for agents working within the same thread, allowing them to read, write, and review structured notes under shared topic keys.

To migrate agent configurations between physical machines, piDots uses the Dot Pack v1.1 standard (`data/packs/`). Each pack is a JSON manifest backed by a cryptographic `SHA-256` checksum. When importing a pack (`POST /api/dots/import-pack`), the system verifies hash integrity and inspects initial memories for prompt-injection payloads before saving the agent to SQLite.

### 9. Hardware Triggers and Flash Protection

The `edge_triggers.py` module tracks Broadcom BCM2711 CPU thermals via Linux sysfs (`/sys/class/thermal/thermal_zone0/temp`), alongside free RAM and storage capacity. If the SoC exceeds 72 °C or storage drops below 10%, the system throttles background polling to cool the hardware down.

Nightly maintenance (`maintenance.py`) protects the MicroSD card. It runs `PRAGMA wal_checkpoint(TRUNCATE)` to flush the WAL journal, archives raw messages older than 7 days, and takes crash-consistent snapshots using `VACUUM INTO` on isolated database connections to prevent storage fragmentation.

### 10. Native Bilingual Support (PT/EN)

The client-side internationalization engine (`static/pidots-i18n.js`) is written in vanilla JavaScript (< 10 KB). It swaps between Portuguese and English in under 10 milliseconds without reloading the page or requiring large frontend frameworks.

Translations are stored in clean JSON files (`data/locales/pt.json` and `data/locales/en.json`). UI updates strictly use `textContent` on elements carrying `data-i18n` attributes, eliminating cross-site scripting (XSS) risks.

### 11. Command Palette with 34 Slash Commands and Mobile Console

The SPA console provides a complete catalog of slash commands triggered by typing `/`:
- Local utility commands (`/clear`, `/theme`, `/lang`, `/status`, `/telemetry`) execute in under 16 milliseconds in the browser without consuming LLM tokens.
- The command popover features fuzzy text matching, keyboard arrow navigation, and a physical touch trigger `[/]` for smartphones.
- Every run command prints a receipt to the teletipo with UTC timestamps and audit sequence numbers.

On screens 768px wide or smaller, a dedicated bottom navigation bar organizes controls with comfortable touch targets (at least 44x44 points). Layout heights adjust smoothly to the virtual keyboard using `window.visualViewport`, preventing text boxes from being hidden while typing.

### 12. In-Context Guided Tour

The onboarding engine (`tour-engine.js`) walks new operators through the live interface without modal popups. It uses GPU-accelerated shadows to highlight active controls directly on screen:
1. Sidebar and spaces library.
2. Teletipo feed and agent command terminal.
3. Bubblewrap sandbox and process isolation.
4. Live Canvas workspace (code artifacts, terminal, and security approvals).
5. Hardware telemetry and AI model controls.

The walkthrough can be relaunched at any time with the `/tour` slash command or by pressing `F1`.

### 13. External Tools via MCP Lite Protocol

piDots connects external Model Context Protocol servers over async STDIO or Server-Sent Events (SSE) using pure Python (`pidots/tools/mcp_client.py`). The MCP client consumes less than 5 MB RAM.

Imported JSON-RPC 2.0 tools register directly in the piDots tool catalog. They adhere to each agent's allowed-tools whitelist, keeping prompts free of unneeded schemas.

### 14. Remote Security Approvals (HMAC-SHA256)

Risky commands can be authorized directly from a phone using signed links or buttons sent to Telegram or WhatsApp. Every request carries a constant-time HMAC-SHA256 signature.

All pending approvals include a 30-minute time-to-live. If an operator does not authorize a pending command before it expires, the request is canceled automatically and the agent returns to idle without executing anything dangerous.

### 15. Physical GPIO Pins and MQTT Sensors

piDots interacts directly with physical GPIO pins on the Raspberry Pi 4B to capture hardware button presses and sensor signals. When running on standard x86_64 machines or containers without hardware access, the driver falls back safely without throwing errors.

An asynchronous MQTT client enables local IoT sensors to stream readings straight to the station, triggering agent workflows without blocking the primary event loop.

### 16. Official Agent Pack Catalog

The `data/packs/` directory provides pre-configured specialist agents ready to install with a single click:
- **`@dot-secops`:** Security auditor focused on open network ports, SSH logs, and Linux system hardening.
- **`@dot-homelab`:** Monitors Docker container health, physical sensors, and flash drive wear.
- **`@dot-finops`:** Tracks token consumption, CPU cycles, and energy efficiency across inference calls.

### 17. Nginx Alpine Reverse Proxy on Four Ports

A lightweight Nginx Alpine container (< 6 MB RAM) delivers static files (`/static/` and `/data/locales/`) with strict caching headers. It routes four distinct surfaces across separate local ports:
- Port `8081`: Overview and landing page.
- Port `8082`: Operational workspace console (SPA/PWA).
- Port `8083`: Technical manual and API documentation.
- Port `8088`: Unified gateway with canonical redirects.

This offloads static file delivery from the Python process, leaving 100% of FastAPI CPU cycles available for agent execution and SQLite transactions.

### 18. Strict Bubblewrap Sandboxing

When `STRICT_SANDBOX=true` is set in your `.env` file, piDots refuses to execute any shell command if the Linux Bubblewrap (`bwrap`) utility is missing on the host. Blocked commands exit with code 126, ensuring that scripts never run without namespace containment.

### 19. Remote Access with Cloudflare Tunnels

The `cloudflared/` directory provides scripts to publish local ports securely across the web using encrypted QUIC tunnels. Setup requires no open router ports and no public IP addresses, allowing you to protect the console with Cloudflare Zero Trust policies.

---

## System Requirements

- **Operating System:** Linux (Debian 12 / Ubuntu 22.04+ / Raspberry Pi OS 64-bit recommended).
- **Architecture:** ARM64 (aarch64) or x86_64.
- **Python:** Version 3.11, 3.12, or 3.13.
- **Docker (Optional):** Docker Engine 24+ and Docker Compose v2.
- **Bubblewrap (Recommended):** Linux `bubblewrap` package for command sandboxing (`sudo apt install bubblewrap`).

---

## Installation and Setup

### Option 1: Docker Compose (Recommended for Production)

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

Set your API key and preferred language model:
```dotenv
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# Optional alerts and messaging
WEBHOOK_NOTIFICATION_URL=https://your-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=your-evolution-apikey
```

3. Start services:
```bash
docker compose up -d
```

4. Check system health:
```bash
docker compose ps
docker compose logs -f pidots-core pidots-nginx
```

Local web surfaces will be accessible immediately:
- **Landing Page:** `http://localhost:8081`
- **Operational Console:** `http://localhost:8082`
- **Technical Manual:** `http://localhost:8083`
- **Canonical Gateway:** `http://localhost:8088`
- **Internal FastAPI Core:** `http://localhost:8000` (health: `curl http://localhost:8000/health`)

---

### Option 2: Native Python Installation

For local development directly on your host machine:

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the package in editable mode:
```bash
pip install -e .
```

3. Initialize the database and workspace directories:
```bash
pidots init
```

4. Start the server:
```bash
pidots serve --host 0.0.0.0 --port 8000
```

---

## Command-Line Interface (CLI)

The `pidots` command lets you manage the station from your terminal:

```bash
# Print installed version
pidots --version

# Display thermals, memory usage, and database metrics
pidots status

# List active agents on the bench
pidots dots list

# Start the development server with auto-reload
pidots serve --host 127.0.0.1 --port 8000 --reload

# Inspect and resolve pending security actions
pidots hitl list
pidots hitl approve <ACTION_ID>
pidots hitl reject <ACTION_ID>
```

---

## Python SDK Usage

You can import piDots directly into other Python applications or agent scripts:

```python
import asyncio
from pathlib import Path
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.spaces_manager import SpacesManager

async def main():
    # 1. Initialize the SQLite WAL database
    await init_edge_database()

    dot_id = "dev-assistant"
    workspace_path = str(Path(settings.workspaces_root) / dot_id)

    # 2. Register the agent if not present
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dot_id,
                "DevOps Assistant",
                "Edge Operator",
                "You are an edge-native operations assistant.",
                settings.ai_model,
                workspace_path
            )
        )
        await db.commit()

    # 3. Configure the inference provider
    provider = OpenAIUniversalProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        default_model=settings.ai_model,
    )

    # 4. Instantiate the agent
    agent = DotAgent(
        dot_id=dot_id,
        provider=provider,
    )

    # 5. Save a versioned document inside Spaces
    doc = await SpacesManager.save_document(
        dot_id=agent.dot_id,
        filename="status_report.txt",
        content="Operational status report generated via the piDots SDK.",
        title="Status Report"
    )
    print(f"Versioned document saved: {doc['filename']} (v{doc['version']})")

    # 6. Stream reasoning events from the agent loop
    async for event in agent.run_thread(thread_id="main-thread", user_message="Check service health"):
        if event["event"] == "message:chunk":
            print(event["data"].get("delta", ""), end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## REST API Endpoint Catalog

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/` | Landing page with live ReAct simulator and silicon calculator |
| `GET` | `/app` | Operational SPA/PWA console with teletipo feed |
| `GET` | `/workspace` | Canonical alias pointing to `/app` |
| `GET` | `/docs` | Technical manual with search (Ctrl+K) and API tester |
| `GET` | `/relatorio` | Engineering verification and load test report |
| `GET` | `/api/docs` | Interactive OpenAPI documentation for developers |
| `GET` | `/api/openapi.json` | Raw OpenAPI 3.0 schema |
| `GET` | `/health` | Hardware telemetry (SoC temperature, RAM, SQLite status) |
| `GET` | `/manifest.json` | PWA manifest for desktop and mobile installation |
| `GET` | `/sw.js` | Service Worker with offline caching logic |
| `GET` | `/icon.svg` | Official vector brand mark |
| `GET` | `/static/pidots-i18n.js` | Client-side vanilla JavaScript translation engine |
| `GET` | `/data/locales/{lang}.json` | Localization dictionaries in Portuguese and English |
| `GET` | `/api/changelog` | Release history and SemVer patch notes |
| `GET` | `/api/dots` | List registered agents and operational roles |
| `GET` | `/api/dots/{id}/export-pack` | Export portable DotPack v1.1 signed with SHA-256 |
| `POST` | `/api/dots/import-pack` | Import an agent with integrity and prompt-injection checks |
| `POST` | `/api/threads` | Create a new conversation thread |
| `GET` | `/api/threads/{id}/messages` | Retrieve thread messages with actor and visibility metadata |
| `POST` | `/api/threads/{id}/runs` | Start an agent cycle with SSE streaming (AG-UI v1.0) |
| `GET` | `/api/hitl/pending` | View pending actions awaiting operator approval |
| `POST` | `/api/hitl/{id}/resolve` | Approve or reject a held command |
| `POST` | `/api/hitl/signed-resolve` | Remote approval endpoint signed with HMAC-SHA256 |
| `POST` | `/api/hitl/webhook-callback` | Async callback for remote governance decisions |
| `GET` | `/api/mcp/servers` | Status of connected external MCP servers |
| `GET` | `/api/spaces` | List documents saved in the active workspace |
| `POST` | `/api/spaces` | Create or update a document with unified diff tracking |
| `GET` | `/api/spaces/{id}` | Read full content of a workspace document |
| `GET` | `/api/spaces/{id}/revisions` | View unified revision diffs for a document |
| `POST` | `/api/spaces/search` | Fast in-memory KNN vector search (CRC32 hashing) |
| `GET` | `/api/spaces/{id}/download` | Download raw document text file |
| `GET` | `/api/workspaces/{dot_id}/export.zip` | Export entire agent workspace as a ZIP archive |
| `GET` | `/api/tasks` | List scheduled background tasks |
| `POST` | `/api/tasks` | Create a new proactive task with a cron expression |
| `GET` | `/api/edge/triggers` | Read hardware sensors (CPU temperature, RAM, disk) |
| `POST` | `/api/edge/maintenance` | Trigger manual SQLite maintenance (WAL checkpoint and backup) |
| `GET` | `/api/channels` | List collaborative team channels |
| `POST` | `/api/channels` | Create a new discussion channel |
| `GET` | `/api/channels/{id}/messages` | Read recent messages from a channel |
| `POST` | `/api/channels/{id}/messages` | Post a message with multi-bot dispatch |
| `POST` | `/api/channels/{id}/members` | Add an agent or user to a channel |
| `POST` | `/api/webhooks/incoming/{dot_id}` | Inbound webhook for external API notifications |
| `POST` | `/api/webhooks/telegram/{dot_id}` | Webhook endpoint for Telegram bot integrations |
| `POST` | `/api/webhooks/whatsapp/{dot_id}` | Webhook endpoint for WhatsApp via Evolution API |
| `GET` | `/api/settings` | Current configuration, notification channels, and active model |
| `POST` | `/api/settings/ai` | Hot-reload API keys and AI model parameters |
| `POST` | `/api/settings/notifications` | Hot-reload remote notification channels |

---

## Keyboard Shortcuts and Navigation

### Quick Navigation Between Surfaces
Press `g` followed by the destination letter:

| Sequence | Destination | Action |
| :--- | :--- | :--- |
| `g` then `h` | `/` | Home: Landing overview and onboarding |
| `g` then `w` | `/app` | Workspace: Operational console |
| `g` then `d` | `/docs` | Docs: Technical manual and API reference |

### Console Operational Shortcuts

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Slash /` | Slash Palette | Opens floating command menu with 34 quick actions |
| `Button [/]` | Touch Menu | Opens command palette on mobile devices without opening keyboard |
| `Alt+1` to `Alt+4` | Activity Rail | Cycles panels (Spaces, Agents, Tasks, Memory) |
| `Alt+B` / `Ctrl+B` | Toggle Sidebar | Shows or hides the left activity sidebar |
| `Alt+I` | Inspect Artifact | Focuses active document inside Live Canvas |
| `Ctrl+S` | Save Revision | Commits a new version of current document to SQLite |
| `Alt+H` | Security Queue | Opens pending Human-in-the-Loop review queue |
| `F11` | Maximize Canvas | Toggles split view and maximized canvas view |
| `Ctrl+L` | Clear Feed | Clears the visible teletipo log while preserving database history |
| `F1` | Help / System | Opens sliding drawer with telemetry and reference |

---

## Slash Command Catalog (/)

Slash commands run directly in the console for instant station control:

| Category | Primary Commands | Example Usage |
| :--- | :--- | :--- |
| **System & UI** | `/help`, `/clear`, `/theme`, `/lang`, `/info`, `/status`, `/telemetry`, `/pwa`, `/tour`, `/onboarding`, `/changelog`, `/computer` | `/tour`, `/computer ls -la`, `/telemetry`, `/theme noir` |
| **Agents & Multi-Bot** | `/dots`, `/handoff`, `/council`, `/delegate`, `/archetype`, `/tools`, `/mcp`, `/coagents` | `/dots`, `/handoff dot-auditor`, `/coagents`, `/mcp` |
| **Memory & Documents** | `/memory`, `/archival`, `/shared`, `/spaces`, `/diff`, `/save-space` | `/archival SQLite WAL`, `/save-space notes.md`, `/diff` |
| **Scheduled Tasks** | `/tasks`, `/cron`, `/run-task` | `/tasks`, `/cron list`, `/run-task task-001` |
| **Security & Edge** | `/hitl`, `/triggers`, `/maintenance`, `/backup` | `/hitl status`, `/triggers`, `/maintenance run` |
| **Data Export** | `/export`, `/pack` | `/export chat`, `/export canvas`, `/pack dot-dev-core` |

---

## Governance and Security

### Real-Time Human-in-the-Loop (HITL)
Commands with destructive potential (such as recursive deletes `rm -rf`, permission changes `chmod/chown`, elevated privileges `sudo`, or file write redirections `> / >> / tee`) are intercepted immediately by the governance engine.

Execution pauses in a pending state. The teletipo displays the approval ID, allowing you to inspect the command and authorize or reject it from the console (`/app` or `Alt+H`) or by typing `/hitl`. Safe inspection commands (`ls`, `cat`) and commands with standard error redirects (`2>/dev/null`) run autonomously without disrupting your work.

### Bubblewrap Sandbox Isolation
To prevent scripts from modifying files outside of designated workspaces, all shell commands execute inside a native Linux Bubblewrap (`bwrap`) container. The process runs under isolated namespaces with restricted file access, preventing modifications to critical system paths on the host.

---

## Automated Test Suite

The repository includes comprehensive automated tests to verify stability, concurrency, and regression resistance:

```bash
# Core infrastructure and process isolation
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Multi-bot orchestration and dynamic tool pruning
python3 scripts/test_phase6_multibot.py

# Proactive scheduler and silent heartbeats (HEARTBEAT_OK)
python3 scripts/test_phase7_scheduler.py

# Messaging gateway and channel discussions
python3 scripts/test_phase8_messaging.py

# Hierarchical memory and compact vector search
python3 scripts/test_phase9_memory.py

# Self-healing harness and two-stage planner
python3 scripts/test_phase10_self_healing_planner.py

# Advisory council and three-way peer review
python3 scripts/test_phase11_council_debate.py

# Shared note space and portable agent packs
python3 scripts/test_phase12_shared_space_dot_packs.py

# Thermal triggers and flash storage maintenance
python3 scripts/test_phase13_edge_triggers_maintenance.py

# AG-UI protocol and UI state events
python3 scripts/test_phase1_opendots_agui.py
python3 scripts/test_phase2_opendots_layout.py
python3 scripts/test_phase3_opendots_dynamic_js.py

# Connection resilience and Circuit Breaker
python3 scripts/test_resilience_phases.py

# Multi-port Nginx routing
python3 scripts/test_phase20_port_decoupling_nginx.py
node scripts/test_cross_surface_router.js

# Stress and concurrency testing
python3 scripts/stress_test.py
```

---

## License

Distributed under the terms of the MIT License. See [LICENSE](LICENSE) for details.

Created by **lyon christopher** (2026).
