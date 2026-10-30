# Contribution Guidelines (CONTRIBUTING)

**piDots** is a persistent autonomous AI coworker workstation engineered to run on resource-constrained edge hardware, with the Raspberry Pi 4B ARM64 serving as its reference testbed.

Please follow these guidelines to preserve system stability, security boundaries, and strict resource discipline.

---

## 1. Project Engineering Principles

When proposing changes to piDots, keep the following hard constraints in mind:

1. **Memory Efficiency:**
   - Idle memory footprint must stay strictly below **60 MB RAM**.
   - Peak memory under concurrent multi-agent load must not exceed **150 MB RAM**.
   - Do not introduce heavy deep-learning runtimes (PyTorch, TensorFlow, local Transformers) or headless browsers (Puppeteer, Playwright, Chromium) into the core daemon.

2. **Hardware & Flash I/O Preservation:**
   - Avoid frequent or synchronous disk writes (`fsync`).
   - All persistence must flow through the managed SQLite WAL layer (`journal_mode=WAL`, `synchronous=NORMAL`, `temp_store=MEMORY`).

3. **Strict Asynchronous Architecture:**
   - All code must run smoothly under AsyncIO and uvloop.
   - Never block the main event loop thread with synchronous I/O or network calls. Offload unavoidable blocking operations with `asyncio.to_thread` or adopt native async libraries (`httpx`, `aiofiles`).

4. **Style Constraint: Zero Emojis:**
   - The use of emojis is strictly prohibited in source code, variable names, log outputs, technical documentation, commit messages, and user interfaces.

5. **Visual Standard: Pixel Paper UI Design System:**
   - Any modifications to web interfaces (HTML/CSS) must strictly adhere to the **Pixel Paper UI** (Dark Paper Noir).
   - Never introduce heavy third-party CSS frameworks (Tailwind, Bootstrap) or bloated component libraries.
   - Enforce strict orthogonal geometry (`border-radius: 0px`).
   - Use cartesian projection shadows with zero Gaussian blur (`box-shadow: 2px 2px 0px #000000;`, etc.).
   - Dual technical typography: `Silkscreen` for display headers, badges, and stamps; `JetBrains Mono` (with `font-variant-numeric: tabular-nums`) for telemetry, teletipo streams, and tabular data.
   - All SVG vector elements must declare `shape-rendering="crispEdges"`.

---

## 2. Conventional Commits Standard

We adopt the [Conventional Commits](https://www.conventionalcommits.org/) convention to keep the repository history readable and auditable. Commit messages follow the structure:

```
<type>(<scope>): <clear, concise description>
```

### Allowed Types:
- `feat`: Addition of a new feature or tool.
- `fix`: Bug fix or error resolution.
- `docs`: Documentation, guides, or diagram updates.
- `perf`: Performance optimizations or memory/CPU reductions.
- `refactor`: Code refactoring without external behavioral changes.
- `test`: Creation or update of automated test suites.
- `chore`: Dependency updates, packaging, or maintenance tasks.
- `ci`: Changes to continuous integration pipelines.

### Examples:
- `feat(tools): add configurable timeout to web content extractor`
- `fix(storage): tune busy_timeout during sqlite wal initialization`
- `perf(memory): optimize crc32 vector representation to reduce byte allocations`
- `docs(readme): update rest api endpoint reference table`

---

## 3. Workflow and Pull Request Submission

1. **Repository Fork:**
   Fork the official repository to your personal GitHub account.

2. **Feature Branch:**
   Create a descriptive branch off `main`:
   ```bash
   git checkout -b feat/new-telemetry-tool
   ```

3. **Local Development Setup:**
   Set up a clean virtual environment and install dependencies in editable mode:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

4. **Validation and Testing:**
   Before submitting your Pull Request, run the full regression test suite, Pixel Paper UI homologation tests, and the concurrency stress test:
   ```bash
   python3 scripts/test_pixel_paper_phase4_global_homologation.py
   python3 scripts/test_phase20_port_decoupling_nginx.py
   python3 scripts/test_phase1.py
   python3 scripts/test_phase2.py
   python3 scripts/test_phase3.py
   python3 scripts/test_phase4.py
   python3 scripts/test_phase5.py
   python3 scripts/stress_test.py
   ```
   All test suites must pass 100% prior to submission.

5. **Submitting the PR:**
   - Complete the standard PR template detailing the engineering rationale behind the change.
   - Provide concrete evidence that memory footprint did not increase and no command injection vulnerabilities were introduced.
   - Verify that the zero-emoji rule is 100% respected.

---

## 4. Governance and Code Review

All Pull Requests undergo technical code review by the project maintainer (**lyon christopher**). Merging requires:
- Green status on the CI/CD pipeline.
- Automated test coverage for new capabilities.
- Strict compliance with async execution patterns and security sandboxing.
