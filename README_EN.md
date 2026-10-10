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

piDots follows a clean modular architecture designed for minimal computational overhead:

```
pidots/
├── api/            # REST routes, SSE streaming endpoints, and static file serving (SPA PWA)
├── cli.py          # Native terminal command-line interface
├── config.py       # Centralized configuration and environment variable resolution
├── core/
│   ├── agent.py    # Asynchronous ReAct execution engine with token streaming
│   └── hitl.py     # Human-in-the-Loop governance engine with retention queue
├── main.py         # FastAPI entrypoint with asynchronous lifespan management
├── memory/
│   └── vector_store.py # Ultra-lightweight CRC32 KNN vector store and semantic search
├── models/
│   └── schemas.py  # Pydantic v2 schemas with strict typing and validation
├── providers/
│   └── openai_client.py # Universal OpenAI-compatible client with SSE streaming
├── storage/
│   ├── database.py       # SQLite layer with WAL mode, busy_timeout, and edge PRAGMAs
│   └── spaces_manager.py # Isolated workspace manager for each Dot
└── tools/
    ├── base.py       # Central asynchronous tool registry
    ├── bash.py       # Bubblewrap-sandboxed command executor with timeouts
    ├── file_ops.py   # Secure file reading, writing, and patching operations
    ├── memory.py     # Agent long-term memory retrieval and persistence tools
    └── web_reader.py # Semantic web content extractor powered by Trafilatura
```

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
Fill in your API key and target language model:
```dotenv
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
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
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.models.schemas import DotCreate
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.database import Database
from pidots.storage.spaces_manager import SpacesManager
from pidots.tools.base import ToolRegistry

async def main():
    # Initialize optimized SQLite WAL database
    db = Database(settings.DATABASE_PATH)
    await db.initialize()

    # Initialize workspace manager and inference provider
    spaces = SpacesManager(settings.WORKSPACES_ROOT)
    provider = OpenAIUniversalProvider(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.OPENAI_MODEL,
    )
    tools = ToolRegistry()

    # Define the coworker specification
    dot_spec = DotCreate(
        name="DevOps-Agent",
        description="Autonomous automation and auditing agent",
        system_prompt="You are an expert infrastructure and security engineer.",
        allowed_tools=["read_file", "write_file", "execute_bash", "fetch_web_page"]
    )
    dot = await db.create_dot(dot_spec)

    # Instantiate and execute reasoning turn
    agent = DotAgent(
        dot=dot,
        db=db,
        provider=provider,
        tools=tools,
        spaces_manager=spaces
    )

    result = await agent.run_turn("Inspect workspace files and compile a summary report.")
    print("Agent Response:", result.response)

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## REST API and Real-Time Streaming

The application provides endpoints for external integration with Server-Sent Events (SSE) streaming:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Responsive dark-mode PWA/SPA dashboard |
| `GET` | `/health` | Healthcheck and live RAM/CPU telemetry |
| `GET` | `/api/system/status` | Comprehensive system, database, and workspace metrics |
| `GET` | `/api/dots` | List all registered AI Coworkers |
| `POST` | `/api/dots` | Create and configure a new AI Coworker |
| `POST` | `/api/dots/{id}/chat` | Send message with synchronous execution |
| `GET` | `/api/dots/{id}/chat/stream` | Real-time token-by-token SSE streaming channel |
| `GET` | `/api/hitl/pending` | List actions awaiting human approval |
| `POST` | `/api/hitl/{id}/approve` | Approve a pending command for execution |
| `POST` | `/api/hitl/{id}/reject` | Reject a pending command in governance |
| `GET` | `/api/spaces/{id}/files` | Securely list files inside the agent workspace |

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
# Run all regression test suites
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Run edge concurrency stress test
python3 scripts/stress_test.py
```

---

## Repository Structure

```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── ARCHITECTURE.md          # In-depth architectural and I/O specifications
├── docker-compose.yml       # Official Docker Compose orchestration
├── Dockerfile               # Lean image based on python:3.13-slim
├── LICENSE                  # MIT License
├── MANUAL_OPERACIONAL.md    # Operational administration guide
├── pidots/                  # Core application package source code
├── pidots_spa_prototype.html# Single Page Application PWA frontend
├── pyproject.toml           # PEP 517/518/621 packaging specification
├── README.md                # Primary documentation (Brazilian Portuguese)
├── README_EN.md             # Mirrored documentation (American English)
├── requirements.txt         # Strict dependency pinning
└── scripts/                 # Automated test suites and stress benchmarks
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Developed by **lyon christopher** (2026).
