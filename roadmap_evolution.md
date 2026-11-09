# pidots // roadmap oficial de engenharia e arquitetura (2026-2027)

> **projeto:** pidots — orquestrador local de agentes para hardware de placa única
> **hardware de referencia:** raspberry pi 4b (arm64 / broadcom bcm2711)
> **baseline auditado:** build 4c25b3b30549df294686789e7f1b9695d71a2a2e
> **orcamento operacional:** ~52 mb / 384 mb ram rss | sqlite wal + fts5 64d | hop_count <= 3
> **design system:** pixel paper ui (dark noir & blueprint) + opendots spatial triptych

---

## 1. baseline consolidado (fases 1 a 15 — concluidas e homologadas)

todas as entregas abaixo ja estao implementadas no codigo-fonte e validadas pela suite de 21 scripts automatizados no diretorio `scripts/`:

- [x] **fase 01 — conceito e arquitetura de borda:** monolito enxuto em python assincrono com 4 especialistas nativos (`[spv] dot-supervisor`, `[cdr] dot-coder`, `[mus] dot-muse`, `[aud] dot-auditor`).
- [x] **fase 02 — colaboracao multi-bot e fitas de carbono:** roteamento deterministico via `threadrouter` (`@dot`), `delegate_task` em sub-threads isoladas, `handoff_to_dot` atomico e `[caderno de raciocinio]` com `visibility='internal'`.
- [x] **fase 03 — autonomia proativa e dot heartbeat:** agendador `edgescheduler` via `croniter` com diretriz silenciosa `heartbeat_ok` para economia de tokens e zero spam.
- [x] **fase 04 — gateway de mensageria e salas tematicas:** integração nativa com telegram, whatsapp (evolution api), webhooks http hmac-sha256 e salas `#canaist` com trava `hop_count <= 3`.
- [x] **fase 05 — catálogo de 23 ferramentas com seleção automática:** filtragem por perfil (`allowed_tools_json`, ~420 a ~780 tokens por turno) e leitura web via trafilatura sem chromium.
- [x] **fase 06 — persistência flash-safe sqlite wal:** configuração `synchronous normal`, `temp_store` em ram e escritas atômicas posix nos workspaces.
- [x] **fase 07 — memória em 3 camadas (padrão memgpt):** `core memory` (memória de trabalho), `archival memory` (busca híbrida fts5 + vetorial 64d) e `recall memory` (memória retrospectiva).
- [x] **fase 08 — auto-reparo e planejamento em 2 etapas:** interceptação de relatórios de erro (traceback) e planejamento estruturado em metas e marcos (`<execution_plan>`).
- [x] **fase 09 — revisão em 3 etapas entre coder, auditor e supervisor:** debate interno isolado em até 3 rodadas.
- [x] **fase 10 — espaço de conhecimento compartilhado e dot packs v1.0:** quadro compartilhado `<shared_knowledge_space>` e exportação/importação de agentes em json.
- [x] **fase 11 — monitores de hardware e manutenção noturna:** monitoramento de temperatura do soc (`thermal_limit_celsius`), `wal_checkpoint(truncate)`, arquivamento de mensagens antigas (>7 dias) e backup `vacuum into`.
- [x] **fase 12 — tradução pt/en sem dependências:** internacionalização em javascript puro (`pidots-i18n.js` < 1.5 kb gzip) com proteção contra xss via `textcontent`.
- [x] **fase 13 — catálogo de 30 comandos locais:** execução no navegador em menos de 16ms, com parser que tolera erros de digitação (distância de levenshtein).
- [x] **fase 14 — desacoplamento de rotas api e strict sandbox:** fatiamento do `main.py` em 8 roteadores dentro de `pidots/api/` (`routes_dots.py`, `routes_threads.py`, `routes_tasks.py`, `routes_channels.py`, `routes_hitl.py`, `routes_webhooks.py`, `routes_edge.py`, `routes_pwa.py`) e validacao de sandbox em `terminal.py`.
- [x] **fase 15 — failover de llm, hitl criptografico e cliente mcp:** implementacao de `pidots/core/hitl_crypto.py`, `pidots/tools/mcp_client.py` e suite de homologacao opendots/ag-ui (`scripts/test_phase15_llm_failover.py` e `test_phase1_opendots_agui.py` a `test_phase4_opendots_homologation.py`).

---

## 2. fase 16 — redesign total ui/ux: opendots spatial triptych + pixel paper ui [concluida]

- [x] **2.1. compactação do cabecalho mobile (`static/css/layout.css` e `mobile.css`):**
  * cabecalho unificado em `48px` com controles secundarios (`[idioma]`, `[tema]`, `[manual]`, `[sobre]`) organizados na barra `#mobilequickcontrolsbar` dentro do painel gaveta retratil (`#retractabledrawer`).
- [x] **2.2. layout triptico espacial no workspace (`pages/app.html` e `static/css/spa.css`):**
  * coluna esquerda: rodape fixo de telemetria fisica em barras ascii (`#sidebarhardwarefooter`, `#sidebarasciirambar`, `#sidebarasciitemp`, `#sidebarasciiwal`).
  * coluna central: bobina de teletipo e command dock com popovers de atalhos e acoes interativas.
  * coluna direita: aba coagents com indicador dinamico de progresso `#canvastabcoagentslabel` (`[coagents // x%]`) e bloco 5 de inspecao rapida memgpt (`#coagentmemgptbox`).
- [x] **2.3. barra inferior mobile sincronizada (`static/js/spa/pidots-ux.js` e `app-init.js`):**
  * badge `#mobilecanvasbadge` ativo no botao `#mobilenavcanvas` com transicoes nao-intrusivas via `notifymobilecanvasupdate()` e `silentmobile: true`.

---

## 3. fase 17 — infraestrutura de borda, nginx e remoções de legado [concluida]

- [x] **3.1. desoneracao de arquivos estaticos via nginx (`nginx/nginx.conf` e `docker-compose.yml`):**
  * servico `pidots-nginx` (`nginx:1.27-alpine`, multi-porta `8081/8082/8083/8088`, limite de memória `32m`) com entrega direta em c de `/static/` e `/data/locales/` com `cache-control: immutable` e sse streaming com `proxy_buffering off`.
- [x] **3.2. limpeza de redirecionamentos e fallbacks (`pidots/api/routes_pwa.py`, `pidots/config.py` e `terminal.py`):**
  * flag configuravel `enable_legacy_redirects` (padrao `true` retornando `308 permanent redirect` para preservar retrocompatibilidade, ou `410 gone` quando delegada ao nginx).
  * trava `strict_sandbox`: quando `true` e o `bwrap` nao esta presente, o terminal recusa execução com `exit_code: 126` impedindo subprocessos abertos sem isolamento.

---

## 4. fase 18 — refinamentos cognitivos, hitl remoto e gatilhos fisicos [concluida]

- [x] **4.1. aprovacao hitl remota no telegram e whatsapp (`messaging_gateway.py` + `hitl_crypto.py`):**
  * rotina de expiracao deterministica de acoes pendentes (`ttl = 30 min`) disponivel via `post /api/hitl/expire-stale`.
- [x] **4.2. otimizacoes de tokens e memória (`council.py`, `self_healing.py`, `memory_manager.py`):**
  * consenso antecipado no conselho (`council.py`): encerramento por consenso imediato (`early_consensus`) na rodada 2 quando o parecer do auditor for `risk_low` / `approved`.
  * trava de loop no self-healing: `max_heal_attempts = 2` em `pidots/core/self_healing.py`.
  * deduplicacao arquival: limiar de similaridade semantica `>= 0.92` em `pidots/storage/memory_manager.py`.
- [x] **4.3. gatilhos fisicos gpio e mqtt (`edge_triggers.py` e `pidots/api/routes_edge.py`):**
  * monitoramento de hardware e endpoint `post /api/edge/triggers/simulate` para injecao e despertar automatico do `@dot-supervisor` na thread `edge-supervisor-wakeup` com nota sincronizada em `thread_shared_notes`.

---

## 5. fase 19 — lancamento open source e engenharia centauro [concluida]

- [x] **manifesto de engenharia centauro (`ai_manifesto.md`):** documento formal estabelecendo a coautoria centauro, limites de silicio (rpi 4b 4gb arm64, broadcom bcm2711), politicas flash-safe e zero emojis.
- [x] **imagens multi-arch automatizadas (`.github/workflows/ci.yml`):** pipeline github actions com `setup-qemu-action@v3` e `setup-buildx-action@v3` para publicacao multi-plataforma (`linux/amd64,linux/arm64`).
- [x] **repositorio comunitario de dot packs (`dot_pack.py` e `pidots/api/routes_dots.py`):** catalogo oficial de 3 pacotes v1.1 assinados criptograficamente com sha-256 (`data/packs/dot-secops.json`, `dot-homelab.json`, `dot-finops.json`), endpoints `get /api/dots/packs/catalog` e `post /api/dots/packs/install/{pack_id}` com instalacao em 1 clique integrada no `/app`.

---

## 6. fase 20 — desacoplamento de portas e nginx multi-porta [concluida]

- [x] **topologia multi-porta isolada (`nginx/nginx.conf`):** quatro blocos de servidor independentes rodando sob nginx alpine (consumo total < 6 mb ram):
  * **8081:** landing page (`x-edge-service: pidots-landing`).
  * **8082:** workspace spa / pwa (`x-edge-service: pidots-workspace`).
  * **8083:** documentação técnica diataxis (`x-edge-service: pidots-docs`).
  * **8088:** gateway central de acesso agregado (`x-edge-service: pidots-gateway`).
- [x] **roteador cross-surface (`static/js/core/pidots-router.js`):** navegação transparente entre superfícies com suporte a hotkeys globais (alt+1 landing, alt+2 app, alt+3 docs, alt+4 gateway) e resolução de urls em ambientes desacoplados ou unificados.
- [x] **suíte de testes automatizada (`scripts/test_phase20_port_decoupling_nginx.py`):** cobertura completa de conformidade http, cabeçalhos de serviço e roteamento reverso.

---

## 7. fase 21 — evolucao ai teammate: dinamica openbot, fast-path e live team chain [concluida]

- [x] **fast-path conversacional e poda dinâmica de ferramentas (`pidots/core/agent.py`):**
  * detecção de saudações e dúvidas leves via `is_conversational_fast_path` com limites estritos de fronteira de palavra (`\b`), suprimindo catálogos pesados de ferramentas e economizando até 70% de tokens de esquema.
  * poda dinâmica real (`archetype_domains` e `dot_id_to_archetype`), limitando cada dot ao seu escopo canônico (7 a 9 ferramentas em vez de 23).
  * sanitização rigorosa para compatibilidade com provedores estritos (openai, verboo, ollama, groq, litellm), eliminando o campo proibido `name` e injetando prefixos textuais `[@actor]:`.
- [x] **personas padrão coworker / ai teammate (`pidots/storage/db.py` e `pidots/core/agent.py`):**
  * atualização dos 6 dots do squad central (ada/@dot-supervisor, linus/@dot-coder, grace/@dot-auditor, etc.) com tom horizontal de colega de bancada, desburocratização em cumprimentos e colaboração visível.
  * injeção padronizada do bloco `como interagir com o operador e com a equipe (padrão coworker)` no contexto de execução de todos os dots.
- [x] **card interativo de diagnóstico do provedor (`static/js/spa/pidots-api.js`):**
  * erradicação completa de falsos positivos ("operação concluida com sucesso.") em falhas e timeouts de inferência.
  * renderização de card industrial pixel paper ui com causa raiz detalhada e ações em um clique: `[tentar novamente]`, `[configurar provedor]` e `[testar conexão]`.
  * blindagem total contra xss e quebra de sintaxe através de armazenamento seguro de prompts em memória (`_lastprompttext`).
- [x] **live team chain inter-agentes e default responder (`routes_threads.py` e `messaging_gateway.py`):**
  * eleição automática do `@dot-supervisor` (ou primeiro especialista do canal) como task owner padrão em canais compartilhados quando o operador não menciona nenhum dot diretamente.
  * encadeamento contínuo na mesma conexão sse: quando um dot cita um colega (ex: `@dot-coder`), o segundo especialista ingressa automaticamente na mesma stream teletipo com ficha catalográfica própria (`ticker-slip`), limitado a um teto seguro de 2 saltos (`max_chain_hops = 2`) e com trava anti-loop.

---

## 8. fase 22 — saneamento integral e auditoria egm review (48 pontas soltas) [concluida]

- [x] **eixo 1: saneamento do nucleo, agent engine, conselho, planner e provedor llm (19 itens):**
  * descarte de conexões de provedores temporários (`self._owns_provider`) via `finally` em `pidots/core/agent.py`.
  * regex restrita em cors e sanitização de path traversal em `StaticPageManager._resolve_file` (`pidots/main.py`).
  * isolamento estrito de reflexões (`<thought>`) da resposta pública do operador em `agent.py`.
  * otimização de consultas sqlite de alvos de dots eliminando padrões n+1 em `orchestrator.py`.
  * reabertura segura de metas e escape de atributos xml em `planner.py`.
  * proteção de sondagem concorrente em `half_open` no disjuntor do provedor llm (`openai_client.py`).
- [x] **eixo 2: seguranca hitl, gateway, scheduler, hardware e tools (13 itens):**
  * transição atômica de status para `executed` em `hitl.py` eliminando riscos de replay attack.
  * ampliação do filtro `dangerous_command_patterns` cobrindo chamadas destrutivas a blocos e permissões.
  * substituição de leituras ilimitadas por buffers controlados em streams de subprocessos em `terminal.py`.
  * injeção compulsória e anti-spoofing de identificadores de sessão em ferramentas (`registry.py`).
  * alinhamento de limiares térmicos em 78.0c com histerese e supressão de alarmes duplicados.
  * buffers ampliados e descarte de notificações json-rpc assíncronas no cliente mcp.
- [x] **eixo 3: api rest e storage sqlite (10 itens):**
  * despacho e execução atômica de comandos aprovados em tokens assinados e webhooks (`routes_hitl.py` e `routes_webhooks.py`).
  * exclusão limpa de registros vinculados (aprovações e metas) ao deletar threads em `routes_threads.py`.
  * validação de expressões cron via `croniter.is_valid` e recálculo seguro no endpoint de tarefas (`routes_tasks.py`).
  * validação prévia de existência de dots em rotas de memória retornando http 404 em vez de 500.
  * rebuild sob demanda do índice fts5 apenas quando a tabela virtual estiver vazia com base populada.
- [x] **eixo 4: frontend spa, slash commands, html, i18n e infraestrutura (11 itens):**
  * catálogo consolidado e calibrado em exatamente 35 comandos slash em `slash-commands.js`.
  * normalização robusta de atributos de arquivos em `pidots-api.js` e seletor da barra ascii wal.
  * sincronização exata de 205 chaves bilíngues em `pt.json` e `en.json` com atributos de acessibilidade (aria).
  * inclusão do roteador cross-surface no manifesto e service worker pwa com cache v8.
  * replicação de cabeçalhos de segurança (`nosniff`, `sameorigin`, `strict-origin`) em todas as portas do nginx.
  * inclusão dos pacotes de agentes nativos (`data/packs/`) na imagem docker e liberação no `.dockerignore`.

---

## 9. homologacao e status dos testes

todas as entregas das fases 16 a 22 e o design system pixel paper ui foram verificados e aprovados:
* **fases 16-19:** `scripts/test_phase16_19_roadmap_evolution.py` (4/4 suítes aprovadas, 100% de sucesso).
* **fase 20 (nginx multi-porta):** `scripts/test_phase20_port_decoupling_nginx.py` (100% de êxito).
* **fase 21 (ai teammate openbot):**
  - fase 1 (fast-path e poda de ferramentas): `scripts/test_phase1_fast_path_and_tool_pruning.py` (100% aprovado).
  - fase 2 (prompts coworker e sqlite wal): `scripts/test_phase2_coworker_prompts_and_identity.py` (100% aprovado).
  - fase 3 (card interativo de diagnóstico): `scripts/test_phase3_error_diagnostic_card.js` (100% aprovado).
  - fase 4 (live team chain e default responder): `scripts/test_phase4_live_team_chain.py` (100% aprovado).
* **fase 22 (saneamento egm review 48 pontas soltas):**
  - validação das 5 portas http pós-rebuild: 8000, 8081, 8082, 8083, 8088 com http 200 ok.
  - paridade de 205 chaves de internacionalização pt/en validadas com zero omissões.
  - subagentes especializados de revisão confirmando 100% de conformidade técnica e zero pontas soltas.
* **roteador cross-surface:** `scripts/test_cross_surface_router.js` (100% de êxito via node.js).
* **pixel paper ui (fases 1-4):** `scripts/test_pixel_paper_phase4_global_homologation.py` (100% aprovado).
* **regressão global:** suítes `test_phase15_llm_failover.py` e `test_phase4_opendots_homologation.py` validadas com 100% de êxito.