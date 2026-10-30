# Centaur Engineering Manifesto: piDots

**Author & Principal Architect:** Lyon Christopher  
**Date:** October 2026  
**Reference Hardware:** Raspberry Pi 4 Model B (Broadcom BCM2711 ARM64 Cortex-A72, 4 GB LPDDR4, MicroSD / USB SSD)

---

## 1. Why This Document Exists

Serious software requires transparent authorship. piDots did not originate from random prompts thrown at a black box, nor was it engineered under the illusion that large language models replace the critical discernment of a systems engineer. We built this platform under the discipline of **Centaur Engineering**: a sharp, unambiguous line dividing human architectural leadership from machine-assisted tactical synthesis.

In advanced chess popularized by Garry Kasparov after 1997, the world's most formidable competitor was neither the isolated grandmaster nor the standalone supercomputer. It was the centaur. The human operator defined positional strategy, pruned sterile calculation branches, and leveraged raw computational power to explore tactical variations in split seconds. We brought that exact operational rigor to systems engineering on edge hardware.

---

## 2. Division of Responsibilities (Human vs. Machine)

A language model does not smell a voltage regulator heating up to 80 °C on a passively cooled board. It does not pay for a MicroSD card destroyed by synchronous writes every second, nor does it wake up at 3 AM when a runaway Node.js or Chromium container consumes 2 GB of RAM and triggers the Linux `OOM Killer`.

Therefore, the boundary of authority in piDots is non-negotiable:

### Exclusively Human (Lyon Christopher)
1. **Physical Budget and Silicon Limits:** The decision to lock nominal memory between 50 MB and 80 MB RAM, run on a single asynchronous worker (`FastAPI + uvloop`), and purge bloated dependencies (zero PyTorch, zero LangChain, zero external containerized vector databases).
2. **Flash-Safe Data Architecture:** Enforcing SQLite in `WAL` (`Write-Ahead Logging`) mode with `synchronous=NORMAL`, `wal_autocheckpoint=1000`, and `cache_size=-16000` (16 MB page cache in RAM). This setup protects flash memory endurance while keeping transaction latencies under one millisecond.
3. **Local Sovereignty and Security:** The strict rule that no agent executes code outside an isolated Linux Bubblewrap (`bwrap`) sandbox, and that any destructive operation mandates real-time human approval (`Human-in-the-Loop`), cryptographically signed with HMAC-SHA256 and a 30-minute expiry window.
4. **Visual Identity and Ergonomics:** The categorical rejection of generic AI-generated interfaces. The operational console (`/app`), the landing page (`/`), and the technical guide (`/docs`) merge 1-bit mechanical precision with high-density telemetry and thumb-reach navigation on mobile devices.

### Accelerated by AI Agents
1. **Code Modularization and Slicing:** Refactoring bulky controllers into decoupled sub-routers (`pidots/api/routes_*.py`) and standalone Vanilla JS engines (`static/js/spa/*.js`), preserving contracts and active routes without regression.
2. **Protocol Implementations and Parsers:** Developing compact 64-dimensional vector projection algorithms on CPU, JSON-RPC 2.0 parsers over STDIO/SSE for the MCP Lite client, and circuit breaker state machines.
3. **Line-by-Line Auditing and Test Suites:** Authoring and running automated test suites (`scripts/test_*.py`) that validate HTTP routes, database migrations, and the strict absence of emojis before every commit.

---

## 3. Our Four Engineering Commitments

For any developer, security auditor, or homelab operator inspecting or contributing to this project, we establish four permanent commitments:

1. **Zero Phantom Code:** No line of code enters this repository without being read, understood, and validated by automated tests that execute locally in seconds. If a module cannot be explained with clarity or introduces accidental complexity without measurable latency or memory gains, it is discarded.
2. **Kernel-Level Containment over Prompt Guarantees:** We never trust plain-text instructions to prevent an LLM from deleting files or exfiltrating data. Containment occurs in the Linux kernel (`bwrap --unshare-all`), in `@dot-auditor` rule validation, in `SHA-256` signatures on agent packs, and in explicit operator confirmation.
3. **Respect for User Hardware:** Every feature is evaluated by its physical impact on RAM, ARM64 CPU cycles, and disk write amplification. If an enhancement runs fine on a 64 GB cloud server but degrades a 4 GB Raspberry Pi 4B, it is treated as an engineering defect.
4. **Direct Workbench Language:** Our documentation, reports, and code comments are written for real engineers. We avoid corporate buzzwords, hollow adjectives, and gratuitous visual clutter.

---

*Signed in the project architecture by Lyon Christopher, creator and architect of piDots.*
