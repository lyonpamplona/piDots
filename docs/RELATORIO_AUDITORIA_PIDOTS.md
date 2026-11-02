# piDots — Relatório de Estudo Técnico e Auditoria de Código

**Projeto:** piDots — Estação Local de Agentes Autônomos para Hardware de Borda
**Versão Auditada:** 1.5.5
**Hardware de Referência:** Raspberry Pi 4B 4 GB RAM (ARM64 Cortex-A72)
**Data da Auditoria:** 01/11/2026
**Método:** Auditoria linha a linha via agentes delegados (3 rodadas) + verificação direta

---

## 1. RESUMO EXECUTIVO

O **piDots** é um monólito modular assíncrono em Python (FastAPI + uvloop) que transforma um computador de placa única em uma estação de trabalho para agentes de inteligência artificial. O sistema roda localmente, sem depender de nuvens externas, e foi projetado especificamente para operar 24/7 em hardware restrito.

**Principais métricas declaradas:**
- Menos de 50 MB de RAM em repouso
- Menos de 80 MB durante execução simultânea de agentes
- Boot em menos de 2 segundos
- ~18.828 linhas de código Python em produção (39 arquivos)
- 4 superfícies web (landing, console SPA, docs, relatório)
- 9 routers REST + streaming SSE
- 22 tabelas SQLite WAL

**Propósito:** Disponibilizar uma equipe de agentes especializados (programação, arquitetura, auditoria técnica, manutenção) que operam de forma autônoma com governança humana (HITL), persistência local e capacidade de auto-reparo.

---

## 2. ARQUITETURA GERAL

### 2.1 Diagrama de Blocos

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTES EXTERNOS                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │ Landing  │  │ Console  │  │ Docs     │  │ Relatório│  │ CLI  │  │
│  │ (:8081)  │  │ SPA(:8082)│ │ (:8083)  │  │ (SPA)    │  │      │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘  │
│       │             │             │             │           │      │
│  ┌────┴─────────────┴─────────────┴─────────────┴───────────┴───┐  │
│  │           Webhooks (Telegram, WhatsApp, Genérico)            │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
┌──────────────────────────────┼─────────────────────────────────────┐
│              NGINX ALPINE (Proxy Reverso)                          │
│  :8081 → Landing   :8082 → Console   :8083 → Docs   :8088 → GW   │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
┌──────────────────────────────┼─────────────────────────────────────┐
│         FASTAPI CORE (:8000) + uvloop (worker único)               │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CAMADA API (9 routers)                                      │  │
│  │  routes_dots │ routes_threads │ routes_tasks │ routes_edge   │  │
│  │  routes_hitl │ routes_pwa    │ routes_channels │ webhooks    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CAMADA ORQUESTRAÇÃO (core/)                                 │  │
│  │  MultiBotOrchestrator → ThreadRouter → Council → Planner     │  │
│  │  DotAgent (ReAct) → SelfHealing → Scheduler → EdgeTriggers   │  │
│  │  HITLManager → MessagingGateway → Notifier                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CAMADA FERRAMENTAS (tools/)                                 │  │
│  │  ToolRegistry → TerminalSandbox (bwrap) → WebReader          │  │
│  │  FileManager → MCPClient → MCPRegistry                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CAMADA PERSISTÊNCIA (storage/)                              │  │
│  │  SQLite WAL → MemoryManager (3 camadas) → VectorStore        │  │
│  │  SpacesManager → SharedSpace → Maintenance → db.py           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PROVEDOR LLM (providers/)                                   │  │
│  │  OpenAIUniversalProvider (Circuit Breaker 3 estados)         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ SQLite WAL  │  │ Sandbox     │  │ Provedor    │
       │ (MicroSD)   │  │ Bubblewrap  │  │ LLM Externo │
       └─────────────┘  └─────────────┘  └─────────────┘
```

### 2.2 Camadas

| Camada | Pasta | Responsabilidade |
|:---|:---|:---|
| **API** | `pidots/api/` | Routers REST, streaming SSE, injeção de dependências |
| **Orquestração** | `pidots/core/` | Agentes, debate multi-bot, HITL, scheduler, auto-reparo |
| **Ferramentas** | `pidots/tools/` | Terminal sandboxed, web reader, file ops, MCP client |
| **Persistência** | `pidots/storage/` | SQLite WAL, memória hierárquica, vector store, spaces |
| **Provedor LLM** | `pidots/providers/` | Gateway universal com circuit breaker e failover |
| **Bootstrap** | `pidots/main.py` | Lifespan, PageManager, middlewares, background tasks |
| **Config** | `pidots/config.py` | Settings Pydantic, portas, caminhos, variáveis de ambiente |
| **CLI** | `pidots/cli.py` | Interface de linha de comando (init, status, dots, hitl) |

### 2.3 Fluxo de Dados Principal (Conversa)

```
Usuário → Console SPA → POST /api/threads/{id}/runs
  → MultiBotOrchestrator (ruteia @menções)
    → DotAgent.execute() (loop ReAct)
      → OpenAIUniversalProvider (LLM)
        → ToolRegistry (chama ferramentas)
          → TerminalSandbox / WebReader / FileManager
            → HITLManager (intercepta ações de risco)
              → SQLite WAL (persiste tudo)
                → SSE Stream (eventos AG-UI de volta ao frontend)
```

---

## 3. MÓDULOS BACKEND

### 3.1 Raiz (`pidots/`)

| Arquivo | Linhas | Propósito |
|:---|:---|:---|
| `__init__.py` | 5 | Declaração do pacote, `__version__ = "1.5.5"` |
| `main.py` | 308 | Bootstrap FastAPI: `StaticPageManager` (cache RAM/Gzip/ETag), `lifespan` (pool httpx + provider IA + WAL checkpoint + heartbeat), CORS, security headers, funções de telemetria SoC |
| `config.py` | 243 | `Settings` (Pydantic BaseSettings): provedor IA (URL, key, model, retries, timeout), failover secundário, circuit breaker params, portas (8000/8081/8082/8083/8088), caminhos SQLite/workspaces, HITL TTL, sandbox, notificações |
| `cli.py` | 172 | Entrypoints: `run_server`, `_init_cmd`, `_status_cmd`, `_dots_list_cmd`, `_hitl_list_cmd`, `_hitl_resolve_cmd` |

### 3.2 Core (`pidots/core/`) — 16 módulos

| Módulo | Classe Principal | Função |
|:---|:---|:---|
| **agent.py** (703L) | `DotAgent` | Motor ReAct assíncrono: loop de execução (pensar → agir → observar), streaming AG-UI, poda dinâmica de ferramentas, integração HITL, self-healing |
| **council.py** (528L) | `CouncilOrchestrator` | Debate dialético em 3 vias: Propositor → Auditor Crítico → Supervisor, com teto de turnos e persistência |
| **dot_pack.py** (277L) | `DotPackManager` | Empacotamento/export/import de templates de agentes (JSON + SHA-256), detecção de prompt injection (9 regex), validação de checksum |
| **edge_triggers.py** (488L) | `EdgeHardwareTriggers`, `EdgeGPIOMonitor`, `EdgeMQTTListener` | Telemetria térmica SoC BCM2711, GPIO, MQTT, disco, RAM, load; alertas proativos com mitigação |
| **hitl.py** (367L) | `HITLManager` | Governança Deny-by-Default: análise sintática de comandos, fila de aprovações, TTL 30min, expiração automática |
| **hitl_crypto.py** | `generate_hitl_hmac`, `verify_hitl_hmac` | Assinatura HMAC-SHA256 em tempo constante para aprovações remotas (Telegram/WhatsApp) |
| **messaging_gateway.py** (362L) | `MessagingGateway`, `ChannelOrchestrator`, `UnifiedIncomingMessage` | Webhooks Telegram/WhatsApp/Discord/Slack, salas temáticas, prevenção de loops infinitos |
| **notifier.py** (182L) | `HITLNotifier` | Notificações HTTP e Telegram Bot para alertas HITL no celular |
| **orchestrator.py** (411L) | `MultiBotOrchestrator`, `ThreadRouter` | Roteamento de menções @dot, topologias Supervisor-Worker, handoffs dinâmicos, debate com teto de turnos |
| **planner.py** (273L) | `TwoStagePlanner` | Planejamento em 2 etapas: Goals → Milestones, checkpoints persistentes, injeção XML no system prompt |
| **scheduler.py** (386L) | `EdgeScheduler` + `execute_proactive_task` + `heartbeat_worker_loop` | Dot Heartbeat (croniter), tarefas agendadas com backoff, diretriz de silêncio HEARTBEAT_OK |
| **self_healing.py** (174L) | `SelfHealingHarness` | Detecção de tracebacks/testes quebrados, diagnóstico estruturado, correção iterativa (teto 2 tentativas) |
| **state.py** | `DotModel`, `ThreadModel`, `MessageModel`, `HITLApprovalModel`, `AGUIEvent` | Modelos Pydantic do protocolo AG-UI e estados de sessão |

### 3.3 Storage (`pidots/storage/`) — 6 módulos

| Módulo | Classe Principal | Função |
|:---|:---|:---|
| **db.py** (578L) | `init_edge_database`, `get_db`, `_apply_schema_migrations` | SQLite WAL calibrado: `synchronous=NORMAL`, `busy_timeout=30s`, cache 16MB, 22 tabelas, 18 índices, migrações idempotentes |
| **maintenance.py** (329L) | `EdgeMaintenanceManager` | Manutenção noturna: VACUUM INTO, TRUNCATE WAL, ANALYZE, consolidação de mensagens em memórias episódicas |
| **memory_manager.py** (496L) | `MemoryManager`, `compute_compact_embedding` (dim=64) | 3 camadas: Core Memory (in-context), Recall (SQLite), Archival (FTS5 + vetor 64d CRC32) |
| **shared_space.py** (170L) | `SharedSpaceManager` | Notas técnicas compartilhadas entre Dots na mesma thread, serialização XML |
| **spaces_manager.py** (220L) | `SpacesManager` | Biblioteca de artefatos com versionamento incremental, diffs unificados, export ZIP |
| **vector_store.py** | `VectorStore` | KNN em disco com hashing CRC32, similaridade de cosseno, < 4 MB RAM |

### 3.4 Tools (`pidots/tools/`) — 5 módulos

| Módulo | Classe Principal | Função |
|:---|:---|:---|
| **registry.py** (1047L) | `ToolRegistry` | Registro centralizado de ferramentas (formato OpenAI Function Calling), poda dinâmica, compartilhamento de espaço |
| **terminal.py** (278L) | `TerminalSandbox`, `bwrap_is_working` | Executor shell em sandbox Bubblewrap (CLONE_NEWNS/PID/IPC/UTS), fallback para subprocess sanitizado, STRICT_SANDBOX mode |
| **file_ops.py** | `FileManager` | Leitura/escrita/listagem de arquivos com proteção Path Traversal (realpath + commonpath) e escrita atômica (tempfile) |
| **mcp_client.py** (385L) | `LiteMCPClient`, `MCPRegistryManager` | Cliente MCP Lite: JSON-RPC 2.0 sobre STDIO/SSE, < 5 MB RAM, sem SDK de terceiros |
| **web_reader.py** (161L) | `WebReader`, `_is_safe_host` | Extração semântica com HTTPX + Trafilatura (< 20 MB RAM), proteção anti-SSRF (validação de IPs privados/loopback) |

### 3.5 Providers (`pidots/providers/`)

| Módulo | Classe Principal | Função |
|:---|:---|:---|
| **openai_client.py** (352L) | `OpenAIUniversalProvider` + 3 exceptions | Gateway multi-provedor: Circuit Breaker 3 estados (CLOSED→OPEN→HALF_OPEN), backoff exponencial, failover secundário transparente |

### 3.6 API (`pidots/api/`) — 10 módulos

| Módulo | Rotas Principais | Função |
|:---|:---|:---|
| **`__init__.py`** | Agregador | Consolida todos os sub-roteadores |
| **deps.py** | `get_ai_provider`, `get_http_client`, `get_page_manager` | Injeção de dependências compartilhadas |
| **routes_dots.py** (391L) | `/api/dots/*` | CRUD de Dots, memória em 3 camadas, export/import DotPacks |
| **routes_threads.py** (400L) | `/api/threads/*` | CRUD de threads, streaming SSE AG-UI, council, handoff, CoAgent state |
| **routes_edge.py** (598L) | `/api/edge/*` | Telemetria, hardware triggers, MCP servers, config a quente, manutenção, computer exec |
| **routes_hitl.py** | `/api/hitl/*` | Fila HITL, resolução, webhook callback, resolução assinada HMAC |
| **routes_pwa.py** (447L) | `/`, `/app`, `/docs`, `/relatorio`, `/manifest.json`, `/sw.js`, ícones | PWA, Service Worker, ícones rasterizados PIL, redirecionamentos canônicos |
| **routes_tasks.py** (245L) | `/api/spaces/*`, `/api/tasks/*` | Spaces (CRUD, busca vetorial), tarefas agendadas, export workspace ZIP |
| **routes_channels.py** | `/api/channels/*` | Salas temáticas colaborativas (CRUD, mensagens, membros) |
| **routes_webhooks.py** (220L) | `/api/webhooks/*` | Webhooks genérico, Telegram, WhatsApp (Evolution API) |

---

## 4. MÓDULOS FRONTEND

### 4.1 Páginas (4 superfícies)

| Página | Arquivo | Porte | Função |
|:---|:---|:---|:---|
| **Landing** | `pages/landing.html` | ~60 KB | Apresentação: simulador ReAct ao vivo, calculadora de ROI, trava mecânica HITL, sanfona de objeções, PWA |
| **Console SPA** | `pages/app.html` | ~74 KB | Workspace tático: sidebar de Dots, teletipo ReAct, Live Canvas, inspetor de diffs, slash commands, mentions, tour |
| **Docs** | `pages/docs.html` | ~59 KB | Guia operacional didático: 4 trilhas temáticas, 14 passos, code tabs, mini API tester, omnisearch Ctrl+K |
| **Relatório** | `pages/relatorio.html` | ~46 KB | Estudo técnico de viabilidade e engenharia reversa |

### 4.2 Design System — Pixel Paper UI

**Tokens CSS** (`tokens.css`):
- **Tema padrão:** Dark Paper Noir (fundo `#0c1012` ardosia profunda)
- **Tema alternativo:** Blueprint (claro)
- **Tipografia:** IBM Plex Sans (corpo) + JetBrains Mono (código) + Silkscreen (títulos pixel)
- **Diretriz:** Zero emojis, 1-bit/8-bit ortogonal, sombras 0-blur
- **Paleta:** Acentos menta, âmbar, ciano sobre superfícies técnicas

**Arquitetura CSS (9 módulos):**

| Arquivo | Função |
|:---|:---|
| `tokens.css` | CSS Custom Properties (design tokens) |
| `reset.css` | Normalização, tipografia, scrollbars teletipo |
| `layout.css` | Casca tripartite, surface switcher, drawer |
| `components.css` | Botões pixel, carimbos, toasts, badges |
| `spa.css` | Console SPA: sidebar, teletipo, canvas, popover |
| `docs.css` | 4 trilhas, code tabs, omnisearch, drawer retrátil |
| `landing.css` | Simuladores, ROI calculator, sanfona |
| `mobile.css` | Bottom-nav, safe areas, touch acessível |
| `relatorio.css` | Drawer de navegação, pesquisa client-side |

### 4.3 JavaScript (12 arquivos)

| Arquivo | Função |
|:---|:---|
| **`core/pixel-system.js`** | Motor central: substitui alert/confirm/prompt, tooltips, context menu, Web Audio API (feedback haptic) |
| **`core/pidots-i18n.js`** | Micro-i18n (< 1.2 KB): PT/EN, alternância < 5ms, zero XSS |
| **`core/cross-surface-router.js`** | Roteador inteligente entre Landing ↔ Console ↔ Docs ↔ Relatório |
| **`core/scroll-lock.js`** | Trava de rolagem iOS Safari/Android (modais, drawers) |
| **`spa/app-init.js`** | Orquestrador central da SPA: atalhos, responsivo, abas, gavetas |
| **`spa/pidots-api.js`** (~2000L) | Camada de API: SSE AG-UI, Dots, Spaces, Canais, Threads, CoAgents, HITL, Tasks |
| **`spa/pidots-ux.js`** | Onboarding, Patch Notes, PWA (instalação, tela cheia) |
| **`spa/slash-commands.js`** (~1500L) | 30 slash commands, fuzzy search, popover, mentions @dot |
| **`spa/tour-engine.js`** | Spotlight tour interativo (< 12 KB), máscara SVG, popover trigonométrico |
| **`docs/docs.js`** | Barra de leitura, omnisearch Ctrl+K, API tester, simulador HITL, PWA |
| **`docs/relatorio.js`** | Navegação e pesquisa client-side do relatório |
| **`landing/landing.js`** | Simulador ReAct, calculadora ROI, trava HITL, PWA, keyboard chords |

### 4.4 Comunicação Frontend ↔ Backend

- **REST:** `fetch()` assíncrono para CRUD de dots, threads, spaces, tasks, channels
- **SSE (Server-Sent Events):** `/api/threads/{id}/runs` para streaming AG-UI em tempo real
- **PWA:** Service Worker com cache offline, manifest.json, ícones rasterizados

---

## 5. SEGURANÇA

### 5.1 Modelo de Defesa em Profundidade (9 barreiras)

| # | Barreira | Implementação |
|:---|:---|:---|
| 1 | **Sandbox Bubblewrap** | Namespaces Linux (NEWNS/PID/IPC/UTS), ro-bind do host, write-only no workspace do dot, `--die-with-parent` |
| 2 | **HITL Deny-by-Default** | Análise sintática de comandos (rm -rf, sudo, chmod, chown, reboot), fila de aprovações, TTL 30min |
| 3 | **Anti-SSRF** | Validação de IPs privados/loopback/link-local, inspeção hop-by-hop de redirecionamentos |
| 4 | **Anti-Path-Traversal** | `os.path.realpath` + `os.path.commonpath` em todas as operações de arquivo |
| 5 | **Segredos em .env** | API keys via variáveis de ambiente, .gitignore + .dockerignore |
| 6 | **Integridade de Assets** | ETag SHA-256 no EdgeAssetManager, `X-Content-Type-Options: nosniff` |
| 7 | **HMAC-SHA256** | Assinatura de aprovações remotas, validação em tempo constante (`hmac.compare_digest`), TTL |
| 8 | **Dot Pack Integrity** | SHA-256 checksum + 9 regex anti-prompt-injection na importação |
| 9 | **STRICT_SANDBOX** | Recusa de fallback se bwrap indisponível (exit code 126) |

### 5.2 Pontos Notáveis

- **Circuit Breaker** no provedor LLM: 3 falhas consecutivas → OPEN (60s cooldown) → HALF_OPEN (canário)
- **Backoff exponencial** com jitter em 503/429
- **Escrita atômica** de arquivos (tempfile + rename)
- **WAL checkpoint periódico** (900s) para proteger o MicroSD

---

## 6. MODELO DE DADOS (22 Tabelas SQLite WAL)

| Tabela | Propósito |
|:---|:---|
| `dots` | Agentes (id, name, persona, is_core, tools_json, etc.) |
| `threads` | Sessões de conversa (id, dot_id, title, created_at) |
| `messages` | Mensagens (id, thread_id, role, content, dot_id, created_at) |
| `spaces` | Artefatos/versionados (id, dot_id, filename, content, version) |
| `space_revisions` | Histórico de revisões (space_id, content, diff, created_at) |
| `document_embeddings` | Embeddings vetoriais (space_id, vector_json) |
| `hitl_approvals` | Fila de aprovações (id, dot_id, action, status, expires_at) |
| `tool_runs` | Log de execuções de ferramentas (id, dot_id, tool, input, output) |
| `thread_participants` | Membros de threads multi-bot (thread_id, dot_id) |
| `agent_handoffs` | Transfers entre agentes (thread_id, source, target, type, status) |
| `goals` | Metas do planner (id, dot_id, title, status) |
| `milestones` | Marcos do planner (id, goal_id, order_index, status, evidence) |
| `episodic_memories` | Memórias episódicas consolidadas (dot_id, thread_id, content) |
| `scheduled_tasks` | Tarefas agendadas (id, dot_id, cron, next_run_at, backoff_until) |
| `channels` | Salas temáticas (id, name, description) |
| `channel_messages` | Mensagens de canais (channel_id, dot_id, content) |
| `channel_members` | Membros de canais (channel_id, dot_id) |
| `agent_core_memory_blocks` | Memória primária (dot_id, block_name, content, max_chars) |
| `archival_memories` | Memória arquivística (dot_id, content, tags_json, vector_json) |
| `archival_memories_fts` | FTS5 full-text search sobre archival_memories |
| `thread_shared_notes` | Notas compartilhadas (thread_id, dot_id, topic_key, content) |
| `mcp_servers` | Servidores MCP registrados (id, name, transport, command) |

**PRAGMAs otimizados:**
- `journal_mode = WAL`
- `synchronous = NORMAL`
- `busy_timeout = 30000`
- `cache_size = -16000` (16 MB)
- `temp_store = MEMORY`

---

## 7. PROTOCOLOS

### 7.1 AG-UI v1.0 (Agent-UI)
- Protocolo de streaming de eventos para a interface web
- Eventos: `RUN_STARTED`, `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`, `TOOL_CALL_START`, `TOOL_CALL_RESULT`, `RUN_FINISHED`
- Transporte: SSE (Server-Sent Events) via `StreamingResponse`

### 7.2 MCP (Model Context Protocol)
- Implementação Lite em Python puro (sem SDK de terceiros)
- Transportes: STDIO e SSE
- JSON-RPC 2.0
- Conversão para schema OpenAI Function Calling
- Registro de servidores com conexão sob demanda

### 7.3 Webhooks Externos
- **Genérico:** `POST /api/webhooks/incoming/{dot_id}`
- **Telegram:** `POST /api/webhooks/telegram/{dot_id}` (bot API)
- **WhatsApp:** `POST /api/webhooks/whatsapp/{dot_id}` (Evolution API)
- Normalização para `UnifiedIncomingMessage`

### 7.4 Notificações
- HTTP webhook genérico (configurável)
- Telegram Bot API (alertas HITL no celular)
- Assinatura HMAC-SHA256 nos callbacks

---

## 8. DESEMPENHO E OTIMIZAÇÕES

### 8.1 Calibrações para Pi 4B

| Otimização | Detalhe |
|:---|:---|
| **Worker único** | Evita race conditions e overhead de fork |
| **uvloop** | Loop de eventos em C (2x mais rápido que asyncio padrão) |
| **WAL Mode** | Leituras não bloqueiam escritas |
| **synchronous=NORMAL** | Reduz fsync (protege MicroSD) |
| **Cache 16 MB** | Aproveita a RAM disponível |
| **temp_store=MEMORY** | Evita escritas temporárias em disco |
| **Vector store em disco** | < 4 MB RAM, hashing CRC32 + cosseno |
| **Memory embedding dim=64** | Compacto, suficiente para similaridade |
| **Trafilatura** | < 20 MB vs ~500 MB de Chromium |
| **MCP Lite** | < 5 MB vs SDK Node.js completo |
| **PageManager em RAM** | HTML servido de memória com ETag |
| **WAL checkpoint 900s** | Evita crescimento infinito do WAL |
| **VACUUM INTO noturno** | Compactação atômica sem lock |
| **Pool httpx** | Conexões reutilizáveis para LLM |

### 8.2 Consumo Declarado

| Estado | RAM |
|:---|:---|
| Repouso | ~48-52 MB |
| Pico (multi-agente) | < 100 MB |
| Vector store | < 4 MB |
| Web reader | < 20 MB |
| MCP client | < 5 MB |

---

## 9. ROADMAP E VERSÃO ATUAL

### Versão 1.5.5 (Atual)
- Produção estável
- Entrega em 4 portas Nginx (8081/8082/8083/8088)
- Túnel Cloudflare
- Docker Compose
- 20 fases de desenvolvimento documentadas (scripts/test_phase*.py)

### Fases Implementadas (20+):
1. Docs layout sanitization
2. Pixel Paper purification
3. Mobile responsiveness + z-index
4. JS HITL/A11Y/i18n
5. (novas features)
6. Multi-bot
7. Scheduler
8. Messaging
9. Memory
10. Self-healing + Planner
11. Council debate
12. Shared Space + Dot Packs
13. Edge Triggers + Maintenance
14. Strict Sandbox + Routers
15. LLM Failover
16-19. Roadmap evolution
20. Port decoupling + Nginx

---

## 10. PONTOS FRACOS E RECOMENDAÇÕES

### 10.1 Pontos Fracos Identificados

| # | Problema | Severidade | Localização |
|:---|:---|:---|:---|
| 1 | **Nenhum teste de integração automatizado** — os scripts test_phase*.py existem mas não há CI/CD configurado | Média | `scripts/` |
| 2 | **Sem rate limiting na API** — endpoints de webhook podem ser alvos de abuso | Média | `api/routes_webhooks.py` |
| 3 | **Auth ausente** — não há autenticação de usuário no console web (qualquer pessoa com acesso à rede pode operar) | Alta | `api/` global |
| 4 | **CORS amplo demais** — `allow_origin_regex=r"^https?://.*"` + `allow_credentials=True` permite qualquer origem com credenciais | Alta | `main.py` |
| 5 | **HMAC secret hardcoded** — `hitl_hmac_secret` tem valor default no código, deveria ser obrigatório via env | Média | `config.py` |
| 6 | **Consenso Council por string matching** — detecção de `APPROVED`/`RISK_LOW` via regex no texto LLM é frágil e sujeita a false positives/negatives | Média | `core/council.py` |
| 7 | **Código duplicado em agent.py** — tratamento de `ProviderEndpointError` tem blocos quase idênticos repetidos | Baixa | `core/agent.py` |
| 8 | **PIL (Pillow) para ícones** — dependência pesada para uma tarefa simples de rasterização | Baixa | `routes_pwa.py` |
| 9 | **Sem logging estruturado** — usa `logging` padrão sem handler JSON (difícil debug em produção) | Baixa | Global |
| 10 | **Vector store em memória** — KNN em disco funciona para volumes pequenos, mas escala mal (> 10K documentos) | Baixa | `storage/vector_store.py` |
| 11 | **Sem observabilidade** — métricas internas (temperatura, RAM) existem mas não há endpoint /metrics Prometheus | Baixa | `routes_edge.py` |
| 12 | **`evolution_api_url` default usa `host.docker.internal`** — só funciona em Docker, quebra em bare-metal | Baixa | `config.py` |

### 10.2 Recomendações

| # | Recomendação | Impacto |
|:---|:---|:---|
| 1 | **Adicionar autenticação** (token API ou OAuth local) antes de expor via Cloudflare | Crítico |
| 2 | **Restringir CORS** — substituir regex genérico por lista de origens permitidas (domínios Cloudflare) | Crítico |
| 3 | **HMAC secret obrigatório via env** — remover valor default, exigir `HITL_HMAC_SECRET` no `.env` | Importante |
| 4 | **Rate limiting** nos endpoints de webhook (por IP, ex: slowapi) | Importante |
| 5 | **CI/CD** com GitHub Actions rodando os scripts test_phase*.py | Importante |
| 6 | **Refatorar consenso Council** — usar JSON structured output do LLM em vez de string matching | Médio |
| 7 | **Logging JSON** com structured fields (ex: structlog) para debug em produção | Médio |
| 8 | **Endpoint /metrics** (formato Prometheus) para telemetria externa | Médio |
| 9 | **Substituir PIL** por geração de ícones em SVG (elimina dependência) | Baixo |
| 10 | **Fixar `evolution_api_url`** para IP/hostname real em bare-metal, ou documentar o requisito Docker | Baixo |

---

## 11. VEREDITO FINAL

O piDots é um projeto de **engenharia de borda sofisticado** com decisões arquiteturais coerentes e bem documentadas. O monólito modular assíncrono é a escolha correta para o hardware alvo — frameworks corporativos simplesmente não cabem em 4 GB de RAM com a sobrecarga de MicroSD.

**Forças principais:**
- Arquitetura limpa com separação clara de responsabilidades
- Segurança em 9 camadas (HITL, sandbox, HMAC, anti-injection)
- Otimizações calibradas para hardware real (não para servidores)
- Design system próprio consistente (Pixel Paper UI)
- Protocolo AG-UI bem especificado
- 22 tabelas bem normalizadas com índices adequados
- Circuit breaker + failover no provedor LLM
- Auto-reparo com teto de tentativas (evita loops infinitos)

**Fraqueza principal:**
- Ausência de autenticação de usuário no console web (o maior risco se exposto via Cloudflare)
- Sem pipeline de CI/CD

O código está em **estado de produção estável** (v1.5.5) com 20+ fases de desenvolvimento completadas e documentadas.
