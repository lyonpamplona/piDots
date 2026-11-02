# piDots // Roadmap Oficial de Engenharia e Arquitetura (2026-2027)

> **Projeto:** piDots — Orquestrador local de agentes para hardware de placa única
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
- [x] **Fase 05 — Catálogo de 23 Ferramentas com Seleção Automática:** Filtragem por perfil (`allowed_tools_json`, ~420 a ~780 tokens por turno) e leitura web via Trafilatura sem Chromium.
- [x] **Fase 06 — Persistência Flash-Safe SQLite WAL:** Configuração `SYNCHRONOUS NORMAL`, `TEMP_STORE` em RAM e escritas atômicas POSIX nos workspaces.
- [x] **Fase 07 — Memória em 3 Camadas (padrão MemGPT):** `Core Memory` (memória de trabalho), `Archival Memory` (busca híbrida FTS5 + vetorial 64D) e `Recall Memory` (memória retrospectiva).
- [x] **Fase 08 — Auto-reparo e Planejamento em 2 Etapas:** Interceptação de relatórios de erro (traceback) e planejamento estruturado em metas e marcos (`<execution_plan>`).
- [x] **Fase 09 — Revisão em 3 Etapas entre Coder, Auditor e Supervisor:** Debate interno isolado em até 3 rodadas.
- [x] **Fase 10 — Espaço de Conhecimento Compartilhado e Dot Packs v1.0:** Quadro compartilhado `<shared_knowledge_space>` e exportação/importação de agentes em JSON.
- [x] **Fase 11 — Monitores de Hardware e Manutenção Noturna:** Monitoramento de temperatura do SoC (`THERMAL_LIMIT_CELSIUS`), `wal_checkpoint(TRUNCATE)`, arquivamento de mensagens antigas (>7 dias) e backup `VACUUM INTO`.
- [x] **Fase 12 — Tradução PT/EN sem Dependências:** Internacionalização em JavaScript puro (`pidots-i18n.js` < 1.5 KB gzip) com proteção contra XSS via `textContent`.
- [x] **Fase 13 — Catálogo de 30 Comandos Locais:** Execução no navegador em menos de 16ms, com parser que tolera erros de digitação (distância de Levenshtein).
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
  * Servico `pidots-nginx` (`nginx:1.27-alpine`, multi-porta `8081/8082/8083/8088`, limite de memoria `32M`) com entrega direta em C de `/static/` e `/data/locales/` com `Cache-Control: immutable` e SSE streaming com `proxy_buffering off`.
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

## 6. Fase 20 — Desacoplamento de Portas e Nginx Multi-Porta [CONCLUIDA]

- [x] **Topologia Multi-Porta Isolada (`nginx/nginx.conf`):** Quatro blocos de servidor independentes rodando sob Nginx Alpine (consumo total < 6 MB RAM):
  * **8081:** Landing Page (`X-Edge-Service: pidots-landing`).
  * **8082:** Workspace SPA / PWA (`X-Edge-Service: pidots-workspace`).
  * **8083:** Documentação Técnica Diataxis (`X-Edge-Service: pidots-docs`).
  * **8088:** Gateway Central de Acesso Agregado (`X-Edge-Service: pidots-gateway`).
- [x] **Roteador Cross-Surface (`static/js/core/pidots-router.js`):** Navegação transparente entre superfícies com suporte a hotkeys globais (Alt+1 Landing, Alt+2 App, Alt+3 Docs, Alt+4 Gateway) e resolução de URLs em ambientes desacoplados ou unificados.
- [x] **Suíte de Testes Automatizada (`scripts/test_phase20_port_decoupling_nginx.py`):** Cobertura completa de conformidade HTTP, cabeçalhos de serviço e roteamento reverso.

---

## 7. Fase 21 — Evolucao AI Teammate: Dinamica OpenBot, Fast-Path e Live Team Chain [CONCLUIDA]

- [x] **Fast-Path Conversacional e Poda Dinâmica de Ferramentas (`pidots/core/agent.py`):**
  * Detecção de saudações e dúvidas leves via `is_conversational_fast_path` com limites estritos de fronteira de palavra (`\b`), suprimindo catálogos pesados de ferramentas e economizando até 70% de tokens de esquema.
  * Poda dinâmica real (`ARCHETYPE_DOMAINS` e `DOT_ID_TO_ARCHETYPE`), limitando cada Dot ao seu escopo canônico (7 a 9 ferramentas em vez de 23).
  * Sanitização rigorosa para compatibilidade com provedores estritos (OpenAI, Verboo, Ollama, Groq, LiteLLM), eliminando o campo proibido `name` e injetando prefixos textuais `[@actor]:`.
- [x] **Personas Padrão Coworker / AI Teammate (`pidots/storage/db.py` e `pidots/core/agent.py`):**
  * Atualização dos 6 Dots do Squad Central (Ada/@dot-supervisor, Linus/@dot-coder, Grace/@dot-auditor, etc.) com tom horizontal de colega de bancada, desburocratização em cumprimentos e colaboração visível.
  * Injeção padronizada do bloco `COMO INTERAGIR COM O OPERADOR E COM A EQUIPE (PADRÃO COWORKER)` no contexto de execução de todos os Dots.
- [x] **Card Interativo de Diagnóstico do Provedor (`static/js/spa/pidots-api.js`):**
  * Erradicação completa de falsos positivos ("Operacao concluida com sucesso.") em falhas e timeouts de inferência.
  * Renderização de card industrial Pixel Paper UI com causa raiz detalhada e ações em um clique: `[Tentar Novamente]`, `[Configurar Provedor]` e `[Testar Conexão]`.
  * Blindagem total contra XSS e quebra de sintaxe através de armazenamento seguro de prompts em memória (`_lastPromptText`).
- [x] **Live Team Chain Inter-Agentes e Default Responder (`routes_threads.py` e `messaging_gateway.py`):**
  * Eleição automática do `@dot-supervisor` (ou primeiro especialista do canal) como Task Owner padrão em canais compartilhados quando o operador não menciona nenhum Dot diretamente.
  * Encadeamento contínuo na mesma conexão SSE: quando um Dot cita um colega (ex: `@dot-coder`), o segundo especialista ingressa automaticamente na mesma stream teletipo com ficha catalográfica própria (`ticker-slip`), limitado a um teto seguro de 2 saltos (`max_chain_hops = 2`) e com trava anti-loop.

---

## 8. Homologacao e Status dos Testes

Todas as entregas das Fases 16 a 21 e o Design System Pixel Paper UI foram verificados e aprovados:
* **Fases 16-19:** `scripts/test_phase16_19_roadmap_evolution.py` (4/4 suítes aprovadas, 100% de sucesso).
* **Fase 20 (Nginx Multi-Porta):** `scripts/test_phase20_port_decoupling_nginx.py` (100% de êxito).
* **Fase 21 (AI Teammate OpenBot):**
  - Fase 1 (Fast-Path e Poda de Ferramentas): `scripts/test_phase1_fast_path_and_tool_pruning.py` (100% aprovado).
  - Fase 2 (Prompts Coworker e SQLite WAL): `scripts/test_phase2_coworker_prompts_and_identity.py` (100% aprovado).
  - Fase 3 (Card Interativo de Diagnóstico): `scripts/test_phase3_error_diagnostic_card.js` (100% aprovado).
  - Fase 4 (Live Team Chain e Default Responder): `scripts/test_phase4_live_team_chain.py` (100% aprovado).
* **Roteador Cross-Surface:** `scripts/test_cross_surface_router.js` (100% de êxito via Node.js).
* **Pixel Paper UI (Fases 1-4):** `scripts/test_pixel_paper_phase4_global_homologation.py` (100% aprovado).
* **Regressão Global:** Suítes `test_phase15_llm_failover.py` e `test_phase4_opendots_homologation.py` validadas com 100% de êxito.