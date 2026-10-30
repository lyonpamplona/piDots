# Security Policy (SECURITY)

Infrastructure security and deterministic tool execution control are foundational requirements in **piDots**. Because the platform coordinates autonomous agents capable of executing commands on persistent edge hardware, we enforce multi-layered defence-in-depth isolation.

---

## 1. Supported Versions

Security patches apply strictly to the following versions:

| Version | Support Status |
| :--- | :--- |
| `1.5.x` | Actively supported with priority edge fixes |
| `< 1.5.0` | End-of-Life / Unsupported |

---

## 2. Threat Model & Security Boundaries

piDots enforces a defence-in-depth architecture across nine containment layers:

### 1. Bubblewrap Sandbox Isolation (`bwrap`)
- Agent-issued shell commands execute inside isolated Linux kernel namespaces (`CLONE_NEWNS`, `CLONE_NEWPID`, `CLONE_NEWIPC`, `CLONE_NEWUTS`).
- Host operating system paths are mounted read-only (`ro-bind`).
- Write access is strictly limited to the agent's dedicated workspace (`workspaces/<dot_id>`).
- The `--die-with-parent` flag ensures any rogue or orphaned background processes terminate immediately if the parent runtime exits.

### 2. Human-in-the-Loop Governance (HITL)
- A heuristic safety interceptor statically inspects all tool invocations prior to execution.
- Operations involving recursive removal (`rm -rf`), privilege escalation (`sudo`, `su`), permission tampering (`chmod`, `chown`), low-level network manipulation, or system reboot enter the safety queue immediately.
- Critical operations are blocked until an authenticated human operator grants explicit approval via web UI, CLI, or signed messaging.

### 3. Strict Anti-SSRF (Server-Side Request Forgery) Protection
- The `read_web_page` tool validates DNS-resolved IPs against private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), and multicast addresses.
- HTTP redirects (301, 302, 303, 307, 308) are checked hop-by-hop, preventing bypass via open third-party redirects.

### 4. Anti-Path and Symlink Traversal Checks
- All file operations in `file_ops.py` and archive builders in `spaces_manager.py` enforce `os.path.realpath` and `os.path.commonpath` verification.
- The system terminates any request attempting to escape the assigned workspace or unpack symlinks targeting sensitive host files.

### 5. Secrets and Environment Variable Containment
- LLM provider API credentials enter the system solely via environment variables or `.env` files.
- `.env` files, SQLite databases containing conversation histories, and active workspaces are excluded via `.gitignore` and `.dockerignore`, preventing leaks to public source control.

### 6. Decoupled Static Asset Integrity & RAM ETag Cache
- All modular web assets (`pages/*.html`, `static/css/*.css`, `static/js/**/*.js`) are served with `X-Content-Type-Options: nosniff` headers and validated via SHA-256 ETags in `EdgeAssetManager` in memory, neutralizing client script tampering and CDN/cache poisoning.

### 7. HMAC-SHA256 Signed Remote HITL Approvals
- Remote authorization requests over Telegram or WhatsApp utilize unique tokens signed with HMAC-SHA256, verified in constant time (`hmac.compare_digest`) at the `/api/hitl/signed-resolve` endpoint.
- Held operations carry a 30-minute time-to-live (`expires_at`). Once expired, the request transitions to `EXPIRED`, discarding the payload and recording the event in the audit trail.

### 8. Dot Pack v1.1 Integrity & Anti-Prompt-Injection Safeguards
- Exported agent manifests include a canonical `sha256_checksum`.
- On import (`POST /api/dots/import-pack`), pack integrity is verified before persistence, and `core_memory` blocks are scanned against system-prompt subversion patterns.

### 9. Strict Sandbox Requirement (STRICT_SANDBOX)
- When `STRICT_SANDBOX=true` is enabled, the terminal tool refuses to execute commands if the `bwrap` binary is absent. The system exits with code 126 and rejects insecure fallbacks.

---

## 3. Responsible Vulnerability Disclosure

If you discover a security vulnerability in piDots, **please do not open a public issue**. Follow this responsible disclosure protocol:

1. **Reporting Channel:**
   Send a detailed, confidential report directly to the maintainer (**lyon christopher**) or submit a private **Security Advisory** via the repository Security tab on GitHub.

2. **Required Report Information:**
   - Clear vulnerability description and potential blast radius.
   - Reproducible proof of concept (PoC).
   - Target piDots version, Python version, and Linux distribution.
   - Specific indicator of whether the flaw allows sandbox escapes, HITL evasion, or credential exposure.

3. **Response Timeline:**
   - Initial acknowledgement: within **48 hours**.
   - Root-cause analysis and mitigation plan: within **5 business days**.
   - Patch release: coordinated with the finder prior to any public disclosure.
