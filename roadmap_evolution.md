# piDots // Roadmap Oficial de Engenharia e Arquitetura (2026-2027)

> **Projeto:** piDots — Sovereign Edge Multi-Agent Orchestrator
> **Hardware de Referencia:** Raspberry Pi 4B (ARM64 / Broadcom BCM2711)
> **Baseline Auditado:** Build 4c25b3b30549df294686789e7f1b9695d71a2a2e
> **Orcamento Operacional:** ~52 MB / 384 MB RAM RSS | SQLite WAL + FTS5 64D | HOP_COUNT <= 3
> **Design System:** Pixel Paper UI (Dark Noir & Blueprint) + OpenDots Spatial Triptych

---

## 1. Baseline Consolidado (Fases 1 a 15 — Concluidas e Homologadas)

Todas as entregas abaixo ja estao implementadas no codigo-fonte e validadas pela suite de 21 scripts automatizados no diretorio `scripts/`:

- [x] **Fase 01 — Conceito e Arquitetura de Borda:** Monolito enxuto em Python assincrono com 4 especialistas nativos (`[SPV] dot-supervisor`, `[CDR] dot-coder`, `[MUS] dot-muse`, `[AUD] dot-auditor`).
- [x] **Fase 02 — Colaboracao Multi-Bot e Fitas de Carbono:** Roteamento deterministico via `ThreadRouter` (`@dot`), `delegate_task` em sub-threads isoladas, `handoff_to_dot` atomico e `[CADERNO DE RACIOCINIO]` com `visibility='internal'`.
- [x] **Fase 03 — Autonomia Proativa e Dot Heartbeat:** Agendador `EdgeScheduler` via `croniter` com diretriz silenciosa `HEARTBEAT_OK` para economia de tokens e zero spam.
- [x] **Fase 04 — Gateway de Mensageria e Salas Tematicas:** Integracao nativa com Telegram, WhatsApp (Evolution API), Webhooks HTTP HMAC-SHA256 e salas `#canaist` com trava `hop_count <= 3`.
- [x] **Fase 05 — Arsenal de 23 Ferramentas e Dynamic Tool Pruning:** Filtragem automatica de `allowed_tools_json` por arquetipo (~420 a ~780 tokens por turno) e leitura web via Trafilatura sem Chromium.
- [x] **Fase 06 — Persistencia Flash-Safe SQLite WAL:** Configuracao `SYNCHRONOUS NORMAL`, `TEMP_STORE` em RAM e escritas atomicas POSIX nos workspaces.
- [x] **Fase 07 — Memoria Hierarquica Padrao MemGPT (3 Camadas):** `Core Memory` in-context, `Archival Memory` hibrida (`SQLite FTS5 BM25` + projecao vetorial esparsa 64D CRC32) e `Recall Memory`.
- [x] **Fase 08 — Self-Healing Harness e Two-Stage Planner:** Interceptor de tracebacks AST (`self_healing:triggered`) e planejamento estruturado em metas e marcos (`<execution_plan>`).
- [x] **Fase 09 — Conselho Consultivo Tripartite:** Debate dialetico isolado em ate 3 rodadas entre Propositor (`@coder`), Critico (`@auditor`) e Mediador (`@supervisor`).
- [x] **Fase 10 — Shared Knowledge Space e Dot Packs v1.0:** Quadro sincrono `<shared_knowledge_space>` e exportacao/importacao portavel de agentes em JSON.
- [x] **Fase 11 — Triggers Fisicos de Hardware e Manutencao Noturna:** Monitoramento termico do SoC Broadcom BCM2711 (`THERMAL_LIMIT_CELSIUS`), `wal_checkpoint(TRUNCATE)`, poda episodica (>7 dias) e backup `VACUUM INTO`.
- [x] **Fase 12 — Micro-Motor i18n Zero-Dependency:** Internacionalizacao PT/EN em Vanilla JS (`pidots-i18n.js` < 1.5 KB gzip) imune a XSS via `textContent`.
- [x] **Fase 13 — Catalogo de 30 Slash Commands Locais:** Execucao client-side em menos de 16ms com parser lexico e tolerancia a falhas via Levenshtein (`slash-commands.js`).
- [x] **Fase 14 — Desacoplamento de Rotas API e Strict Sandbox:** Fatiamento do `main.py` em 8 roteadores dentro de `pidots/api/` (`routes_dots.py`, `routes_threads.py`, `routes_tasks.py`, `routes_channels.py`, `routes_hitl.py`, `routes_webhooks.py`, `routes_edge.py`, `routes_pwa.py`) e validacao de sandbox em `terminal.py`.
- [x] **Fase 15 — Failover de LLM, HITL Criptografico e Cliente MCP:** Implementacao de `pidots/core/hitl_crypto.py`, `pidots/tools/mcp_client.py` e suite de homologacao OpenDots/AG-UI (`scripts/test_phase15_llm_failover.py` e `test_phase1_opendots_agui.py` a `test_phase4_opendots_homologation.py`).

---

## 2. Fase 16 — Redesign Total UI/UX: OpenDots Spatial Triptych + Pixel Paper UI [CONCLUIDA]

- [x] **2.1. Compactacao do Cabecalho Mobile (`static/css/layout.css` e `mobile.css`):**
  * Cabecalho unificado em `48px` com controles secundarios (`[IDIOMA]`, `[TEMA]`, `[MANUAL]`, `[SOBRE]`) organizados na barra `#mobileQuickControlsBar` dentro do painel gaveta retratil (`#retractableDrawer`).
- [x] **2.2. Layout Triptico Espacial no Workspace (`pages/app.html` e `static/css/spa.css`):**
  * Coluna Esquerda: Rodape fixo de telemetria fisica em barras ASCII (`#sidebarHardwareFooter`, `#sidebarAsciiRamBar`, `#sidebarAsciiTemp`, `#sidebarAsciiWal`).
  * Coluna Central: Bobina de teletipo e Command Dock com popovers de atalhos e acoes interativas.
  * Coluna Direita: Aba CoAgents com indicador dinamico de progresso `#canvasTabCoagentsLabel` (`[COAGENTS // X%]`) e Bloco 5 de Inspecao Rapida MemGPT (`#coagentMemgptBox`).
- [x] **2.3. Barra Inferior Mobile Sincronizada (`static/js/spa/pidots-ux.js` e `app-init.js`):**
  * Badge `#mobileCanvasBadge` ativo no botao `#mobileNavCanvas` com transicoes nao-intrusivas via `notifyMobileCanvasUpdate()` e `silentMobile: true`.

---

## 3. Fase 17 — Infraestrutura de Borda, Nginx e Remoções de Legado [CONCLUIDA]

- [x] **3.1. Desoneracao de Arquivos Estaticos via Nginx (`nginx/nginx.conf` e `docker-compose.yml`):**
  * Servico `pidots-nginx` (`nginx:1.27-alpine`, porta `8080:80`, limite de memoria `32M`) com entrega direta em C de `/static/` e `/data/locales/` com `Cache-Control: immutable` e SSE streaming com `proxy_buffering off`.
- [x] **3.2. Limpeza de Redirecionamentos e Fallbacks (`pidots/api/routes_pwa.py`, `pidots/config.py` e `terminal.py`):**
  * Flag configuravel `ENABLE_LEGACY_REDIRECTS` (padrao `True` retornando `308 Permanent Redirect` para preservar retrocompatibilidade, ou `410 Gone` quando delegada ao Nginx).
  * Trava `STRICT_SANDBOX`: Quando `True` e o `bwrap` nao esta presente, o terminal recusa execucao com `exit_code: 126` impedindo subprocessos abertos sem isolamento.

---

## 4. Fase 18 — Refinamentos Cognitivos, HITL Remoto e Gatilhos Fisicos [CONCLUIDA]

- [x] **4.1. Aprovacao HITL Remota no Telegram e WhatsApp (`messaging_gateway.py` + `hitl_crypto.py`):**
  * Rotina de expiracao deterministica de acoes pendentes (`TTL = 30 min`) disponivel via `POST /api/hitl/expire-stale`.
- [x] **4.2. Otimizacoes de Tokens e Memoria (`council.py`, `self_healing.py`, `memory_manager.py`):**
  * Consenso Antecipado no Conselho (`council.py`): Encerramento por consenso imediato (`early_consensus`) na rodada 2 quando o parecer do auditor for `RISK_LOW` / `APPROVED`.
  * Trava de Loop no Self-Healing: `MAX_HEAL_ATTEMPTS = 2` em `pidots/core/self_healing.py`.
  * Deduplicacao Arquival: Limiar de similaridade semantica `>= 0.92` em `pidots/storage/memory_manager.py`.
- [x] **4.3. Gatilhos Fisicos GPIO e MQTT (`edge_triggers.py` e `pidots/api/routes_edge.py`):**
  * Monitoramento de hardware e endpoint `POST /api/edge/triggers/simulate` para injecao e despertar automatico do `@dot-supervisor` na thread `edge-supervisor-wakeup` com nota sincronizada em `thread_shared_notes`.

---

## 5. Fase 19 — Lancamento Open Source e Engenharia Centauro [CONCLUIDA]

- [x] **Manifesto de Engenharia Centauro (`AI_MANIFESTO.md`):** Documento formal estabelecendo a coautoria centauro, limites de silicio (RPi 4B 4GB ARM64, Broadcom BCM2711), politicas flash-safe e zero emojis.
- [x] **Imagens Multi-Arch Automatizadas (`.github/workflows/ci.yml`):** Pipeline GitHub Actions com `setup-qemu-action@v3` e `setup-buildx-action@v3` para publicacao multi-plataforma (`linux/amd64,linux/arm64`).
- [x] **Repositorio Comunitario de Dot Packs (`dot_pack.py` e `pidots/api/routes_dots.py`):** Catalogo oficial de 3 pacotes v1.1 assinados criptograficamente com SHA-256 (`data/packs/dot-secops.json`, `dot-homelab.json`, `dot-finops.json`), endpoints `GET /api/dots/packs/catalog` e `POST /api/dots/packs/install/{pack_id}` com instalacao em 1 clique integrada no `/app`.

---

## 6. Homologacao e Status dos Testes

Todas as entregas das Fases 16 a 19 foram verificadas pela suite integrada de testes:
* **Script:** `scripts/test_phase16_19_roadmap_evolution.py` (4/4 suites aprovadas com 100% de sucesso).
* **Regressao:** Suites `test_phase15_llm_failover.py` e `test_phase4_opendots_homologation.py` validadas com 100% de exito.