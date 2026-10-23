# piDots

**Edge AI Coworker Persistente para Computação de Borda (SBCs, ARM64 / x86_64, Benchmark: Raspberry Pi 4B)**

[Português](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)
![Arch](https://img.shields.io/badge/Architecture-ARM64%20%7C%20x86__64-informational?style=flat&logo=arm&logoColor=white)
![Hardware](https://img.shields.io/badge/Target-Edge%20SBCs%20%7C%20ARM64%20%7C%20x86__64-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=flat&logo=docker&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Visão Geral

O **piDots** é uma plataforma de agentes autônomos persistentes (AI Coworkers) projetada para operar continuamente em computadores de placa única (SBCs), Mini PCs e servidores locais, tendo o **Raspberry Pi 4B com 4GB de RAM (ARM64)** como bancada de referência.

Projetamos o piDots do zero para o silício real. Frameworks corporativos tradicionais assumem servidores com dezenas de gigabytes de memória, navegadores headless pesados e bancos vetoriais em contêineres separados. Na borda física, essa conta não fecha. O hardware aquece, o cartão MicroSD sofre desgaste precoce por fsync e a fatura em nuvem cresce sem controle.

O piDots resolve isso como um monólito modular assíncrono em Python (`FastAPI + uvloop`). Eliminamos runtimes dispensáveis e estruturamos um motor determinístico que consome **menos de 50 MB de RAM em repouso** e **menos de 80 MB durante a execução simultânea de agentes**.

O sistema entrega especialistas orientados a tarefas reais (programação, arquitetura, auditoria e manutenção de sistemas), munidos de memória persistente em SQLite WAL, isolamento em sandbox Bubblewrap, governança Human-in-the-Loop assinada com HMAC-SHA256 e console web tático dark mode.

---

## Comparativo Técnico: piDots vs Frameworks Tradicionais

| Parâmetro | Frameworks Tradicionais (Padrão Nuvem) | piDots (Computação de Borda) |
| :--- | :--- | :--- |
| **Hardware Mínimo** | Servidor x86_64 com 8GB a 16GB RAM | Raspberry Pi 4B (4GB RAM) / ARM64 / x86_64 |
| **Stack de Execução** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Consumo de Memória (Repouso)** | 2.000 MB - 3.500 MB RAM | ~48 MB - 52 MB RAM (Redução de ~98%) |
| **Consumo sob Carga (Pico)** | 4.000 MB - 6.000 MB RAM | < 100 MB RAM |
| **Banco de Dados & Estado** | PostgreSQL / Neo4j / Redis | SQLite com WAL Mode e PRAGMAs otimizados |
| **Banco Vetorial / Memória** | ChromaDB / Pinecone / Qdrant (500MB+) | Extrator Vetorial CRC32 KNN em disco (< 5MB) |
| **Navegador e Leitura Web** | Chromium / Playwright headless (~500MB RAM) | Trafilatura / httpx assíncrono puro em CPU (~20MB) |
| **Isolamento de Segurança** | Docker aninhado / VM Cloud | Sandbox Bubblewrap (`bwrap`) nativo Linux |
| **Desgaste de Armazenamento** | Alto overhead de fsync em disco | Otimizado para preservar MicroSD / SSD USB |
| **Integração e Distribuição** | Sistema fechado / Microsserviços | Pacote Python modular (`pip install -e .`) e Docker |

---

## Arquitetura e Principais Módulos

O piDots foi projetado como um monólito modular assíncrono com baixa sobrecarga computacional:

```
pidots/
├── __init__.py
├── cli.py               # Interface CLI nativa para terminal
├── config.py            # Configuracoes centralizadas e variaveis de ambiente
├── main.py              # Bootstrap FastAPI, Lifespan e configuracao de middlewares
├── api/                 # Sub-roteadores modulares desacoplados (APIRouters)
│   ├── __init__.py      # Agregador central de rotas da aplicacao
│   ├── routes_dots.py   # Gerenciamento de agentes e Dot Packs v1.1
│   ├── routes_threads.py # Sessoes de conversa, canais e streaming SSE
│   ├── routes_tasks.py  # Agendamentos proativos e manutencao
│   ├── routes_webhooks.py # Webhooks Telegram, WhatsApp e incoming
│   ├── routes_edge.py   # Telemetria, hardware triggers e changelog
│   ├── routes_hitl.py   # Governanca e resolucao remota HMAC-SHA256
│   ├── routes_mcp.py    # Descoberta e gestao de servidores MCP Lite
│   └── routes_static.py # Entrega canonica com EdgeAssetManager
├── core/
│   ├── __init__.py
│   ├── agent.py         # Motor ReAct assincrono com Dynamic Tool Pruning e AG-UI
│   ├── council.py       # Conselho Consultivo e debate dialetico tripartite
│   ├── dot_pack.py      # Dot Packs v1.1 assinados com SHA-256 e auditoria anti-injection
│   ├── edge_triggers.py # Triggers de hardware (BCM2711), barramento GPIO e listener MQTT
│   ├── hitl.py          # Governanca Human-in-the-Loop com retencao e expiracao TTL
│   ├── hitl_crypto.py   # Assinatura e verificacao de tokens HMAC-SHA256
│   ├── messaging_gateway.py # Gateway unificado de mensageria e barramento de canais
│   ├── notifier.py      # Notificador HTTP e alertas externos assinados
│   ├── orchestrator.py  # Orquestrador Multi-Bot (Supervisor, Handoff, mencoes @dot)
│   ├── planner.py       # Planejamento em dois estagios (Goals, Milestones e Checkpoints)
│   ├── scheduler.py     # Motor proativo Dot Heartbeat com calculo via croniter e circuit breaker
│   ├── self_healing.py  # Self-Healing Harness e diagnostico cirurgico de tracebacks
│   └── state.py         # Modelos de eventos do protocolo AG-UI e estados de sessao
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Gateway universal de inferencia com Circuit Breaker de 3 estados
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL calibrado para microSD e migracoes idempotentes
│   ├── maintenance.py   # Manutencao noturna autonoma, WAL checkpoint TRUNCATE e VACUUM INTO
│   ├── memory_manager.py # Memoria hierarquica MemGPT (Core Memory, Archival FTS5 + 64d)
│   ├── shared_space.py  # Espaco de conhecimento compartilhado entre bots na thread
│   ├── spaces_manager.py # Workspaces isolados, versionamento e diffs unificados
│   └── vector_store.py  # Memoria vetorial KNN em disco com hashing CRC32
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Operacoes atomicas de leitura, escrita e listagem em disco
    ├── mcp_client.py    # Cliente MCP Lite assincrono sobre STDIO/SSE com Tool Pruning
    ├── registry.py      # Registro centralizado de ferramentas com Dynamic Tool Pruning
    ├── terminal.py      # Executor shell isolado via Bubblewrap com trava STRICT_SANDBOX
    └── web_reader.py    # Extrator semantico web assincrono com Trafilatura
```

---

## Capacidades Avançadas de Borda

### 1. Orquestração Multi-Bot e Especialistas Locais
Em vez de chats isolados, o piDots conecta múltiplos especialistas dentro do mesmo processo:
- **Menções Dinâmicas (@dot):** O `ThreadRouter` extrai menções no formato `@nome_do_dot`, resolvendo interlocutores e gravando os participantes na tabela `thread_participants`.
- **Topologia Supervisor-Worker:** O supervisor planeja e delega subtarefas técnicas através da ferramenta `delegate_task`, executando workers em threads isoladas e consolidando os resultados na conversa principal.
- **Transferência de Liderança (Handoff):** Ferramenta `handoff_to_dot` para transferir a titularidade operacional de uma thread para outro especialista com registro na tabela `agent_handoffs`.
- **Logs Internos de Depuração:** Mensagens de comunicação inter-agente são gravadas com `visibility: 'internal'` para auditoria sem poluir a interface do usuário.
- **Perfis Especializados:** Suporte nativo a papeis operacionais bem definidos:
  - `supervisor`: Coordenador geral e gestao de metas executivas.
  - `coder`: Desenvolvimento de software, depuracao de erros, execucao em terminal isolado e testes automatizados.
  - `arquiteto`: Arquitetura de sistemas, modelagem de dados, sintese conceitual e documentacao tecnica.
  - `auditor`: Inspecao de seguranca, telemetria e conformidade de comandos.
- **Dynamic Tool Pruning:** Cada Dot carrega apenas as ferramentas permitidas em `allowed_tools_json`, reduzindo em até 75% o consumo de tokens de contexto e eliminando alucinações.

### 2. Automações Proativas: Padrão Dot Heartbeat e Circuit Breaker
O módulo `pidots/core/scheduler.py` implementa um agendador contínuo in-process baseado em `croniter`, sem necessidade de Redis ou Celery:
- **Rotinas Cron:** Agendamentos persistidos na tabela `scheduled_tasks` do SQLite WAL.
- **Diretriz de Silêncio Operacional (HEARTBEAT_OK):** Ao executar checagens rotineiras, se o agente constatar integridade do sistema, responde estritamente `HEARTBEAT_OK`. O agendador registra o estado como `SILENT` e hiberna sem gerar notificações inúteis ou poluir o banco de dados.
- **Controle de Exclusão Mútua in-process:** Trava em memória (`_running_tasks`) que previne reentrância e disparos em cascata da mesma tarefa quando o ciclo de raciocínio do LLM ultrapassa o intervalo periódico de varredura (15s).
- **Circuit Breaker com Backoff Exponencial:** Tarefas proativas com falhas recorrentes aplicam retardo progressivo de 30s até 3.600s (`min(3600, 30 * 2^(n-1))`). Na 5ª falha consecutiva, o circuito abre (`CIRCUIT_OPEN`), desativando a tarefa (`is_active = 0`) para preservar ciclos de CPU ARM64 e conectividade.
- **Verificação Preventiva de Inicialização (AUTH_REQUIRED):** Caso a chave de API esteja vazia ou configurada com valores placeholder, tarefas proativas são pausadas em `AUTH_REQUIRED` com backoff protetivo de 10 minutos, poupando requisições externas inúteis.

### 3. Gateway de Mensageria Unificada e Canais Temáticos
O módulo `pidots/core/messaging_gateway.py` centraliza comunicações externas via webhooks HTTP stateless:
- **Adaptadores Nativos:** Endpoints dedicados para Telegram (`/api/webhooks/telegram/{dot_id}`), WhatsApp via Evolution API com autenticação por apikey (`/api/webhooks/whatsapp/{dot_id}`) e Webhooks Genéricos (`/api/webhooks/incoming/{dot_id}`).
- **Integração Nativa Evolution API:** Variáveis `EVOLUTION_API_URL` e `EVOLUTION_API_KEY` com atualização a quente e suporte a envio assíncrono via cliente HTTPx.
- **Salas Temáticas (#canais):** Canais de discussão colaborativa persistidos na tabela `channels`.
- **Trava Anti-Recursão Estrita:** Para evitar loops infinitos entre bots, o barramento de canais aplica:
  1. Contador de saltos estrito (`hop_count <= 3`).
  2. Bots só respondem a outros bots se houver menção explícita `@dot_id`.
  3. Resposta silenciosa `NO_ACTION` quando o agente não tem contribuição relevante a acrescentar.
- **Retorno Operacional Amigável em Falhas:** Em caso de indisponibilidade do provedor, o gateway captura a interrupção e devolve aviso estruturado `[FALHA OPERACIONAL]` ao interlocutor externo sem degradar o canal.

### 4. Arquitetura de Resiliência e Tratamento Tipado de Falhas
O motor central do piDots implementa um protocolo unificado de resiliência de ponta a ponta:
- **Exceções Tipadas de Provedor:** O cliente `OpenAIUniversalProvider` distingue `ProviderAuthError` (HTTP 401/403 com short-circuit imediato sem retentativas inúteis) de `ProviderTransientError` (HTTP 503/429/timeout com políticas de retry e jitter).
- **Contrato AG-UI v1.0 Padronizado:** O ciclo `DotAgent.run_thread` emite o evento terminal `run:finished` com status `'failed'`, populando `error`, `error_type` (`auth_error` ou `transient_error`) e `final_response: ""`.
- **Registro Interno de Diagnóstico:** Erros críticos são gravados na tabela `messages` do SQLite WAL com visibilidade `internal` (`[FALHA DE INFERENCIA]` ou `[FALHA DE AUTENTICACAO]`), garantindo rastreabilidade técnica sem poluir o feed do usuário.
- **Resiliência Integrada dos Três Consumidores:**
  - *EdgeScheduler:* Registra o status `FAILED` com sumário técnico real no SQLite, eliminando falsos positivos de sucesso.
  - *MessagingGateway:* Devolve retorno amigável claro para canais externos (`[FALHA OPERACIONAL]`).
  - *MultiBotOrchestrator:* Marca a subtarefa em `agent_handoffs` como `FAILED`, registra alerta interno na thread pai e retorna feedback estruturado `{'success': False, 'error': ...}` para permitir replanejamento pelo supervisor.

### 5. Memória Hierárquica Autônoma (Padrão MemGPT / Letta)
O módulo `pidots/storage/memory_manager.py` disponibiliza memória em 3 camadas gerida pelo próprio Dot via Function Calling nativo:
- **Core Memory In-Context (`<core_memory>`):** Blocos fixos de memória residente injetados diretamente no system prompt com teto rígido de caracteres contra overflow: `human` (dados do usuário), `persona` (identidade do agente) e `active_context` (foco da missão).
- **Ferramentas de Auto-Edição:** `core_memory_append` e `core_memory_replace` permitem ao Dot aprender e atualizar sua própria identidade sem comandos do operador.
- **Archival Memory Duradoura com Busca Híbrida:** Fatos e documentações gravados em `archival_memories` e indexados sincronicamente na Virtual Table SQLite FTS5 (`archival_memories_fts`). Combina ranking BM25 com projeção vetorial esparsa 64d (baseada em hashing de trigramas e ativação semântica), com as ferramentas `archival_memory_insert` e `archival_memory_search`.
- **Recall Memory:** A ferramenta `recall_memory_search` permite consultar conversas anteriores na mesma thread sem poluir o contexto com turnos brutos.

### 6. Auto-Cura (Self-Healing Harness) e Planejamento em Dois Estágios (Goals & Milestones)
- **Self-Healing Harness (`pidots/core/self_healing.py`):** Inspeciona resultados de shell e scripts Python. Ao detectar falhas de execução, disseca o traceback bruto, identifica o arquivo, a linha e o tipo da exceção, emitindo o evento AG-UI `self_healing:triggered` e fornecendo diagnóstico com recomendação técnica de correção via ferramenta `execute_and_verify`.
- **Two-Stage Planning (`pidots/core/planner.py`):** Modela metas (`goals`) e marcos operacionais (`milestones`) persistidos no SQLite. O agente cria planos (`plan_create`), atualiza o status de cada marco com evidências técnicas (`plan_update_step`) e consulta o progresso percentual (`plan_get_status`), com formatação XML automática `<execution_plan>`.

### 7. Conselho Consultivo e Deliberação Dialética Multi-Bot
O módulo `pidots/core/council.py` implementa deliberação dialética formal entre especialistas cognitivos:
- **Papéis do Conselho:** Propositor (`@coder` formula proposta técnica), Auditor Crítico (`@auditor` faz revisão adversarial de riscos) e Supervisor Geral (`@supervisor` sintetiza o veredito executivo).
- **Isolamento de Deliberação Interna:** As rodadas intermediárias de debate são gravadas com `visibility: 'internal'`. Somente a resolução final é publicada no feed com o cabeçalho `[CONSELHO CONSULTIVO - RESOLUCAO FINAL]`.
- **Trava de Segurança:** Teto máximo rígido de 3 rodadas de debate para conter custos e memória, com consumo medido inferior a 53 MB de RAM.
- **Ferramenta Nativa:** Invocação direta via `run_council_debate`.

### 8. Espaço de Conhecimento Compartilhado e Dot Packs Portáveis (v1.1)
- **Shared Knowledge Space (`pidots/storage/shared_space.py`):** Quadro colaborativo indexado por `(thread_id, topic_key)` na tabela `thread_shared_notes`. Permite gravação (`shared_space_write`), leitura (`shared_space_read`) e sobrescrita colaborativa entre bots na mesma thread, com formatação XML `<shared_knowledge_space>`.
- **Dot Packs v1.1 com Assinatura SHA-256 (`pidots/core/dot_pack.py`):** Manifesto JSON padronizado com hash criptografico de integridade `sha256_checksum`. Na importacao atômica (`POST /api/dots/import-pack`), o sistema valida a correspondencia do hash e aciona auditoria estatica contra tecnicas de Prompt Injection em `core_memory` antes de instanciar o agente.

### 9. Triggers de Hardware e Manutenção Noturna do MicroSD
- **Triggers Orientados a Eventos de Hardware (`pidots/core/edge_triggers.py`):** Monitora temperatura do SoC Broadcom BCM2711 via sysfs Linux (`/sys/class/thermal/thermal_zone0/temp`), espaço livre no MicroSD e memória RAM livre. Emite alertas proativos e ativa throttle automático caso a temperatura ultrapasse 72°C ou o espaço em disco seja inferior a 10%. Endpoint: `GET /api/edge/triggers`.
- **Rotina de Manutenção Noturna Autônoma (`pidots/storage/maintenance.py`):** Executa `PRAGMA wal_checkpoint(TRUNCATE)` para esvaziar o arquivo WAL, consolida e poda mensagens brutas antigas (> 7 dias) na tabela `episodic_memories`, gera backups atômicos seguros via `VACUUM INTO` em conexão isolada (`isolation_level=None`) e atualiza índices com `PRAGMA optimize`. Endpoint: `POST /api/edge/maintenance`.

### 10. Internacionalização Bilíngue Nativa (PT/EN) e Micro-Motor de Borda
- **Micro-Motor Vanilla JS (`static/pidots-i18n.js`):** Alternância instantânea de idioma (< 10ms) sem frameworks pesados ou consumo extra de RAM, com detecção e persistência segura em `localStorage.getItem('pidots_lang')`.
- **Dicionários Atômicos JSON (`data/locales/pt.json` e `data/locales/en.json`):** Dicionários semânticos servidos com cache de borda e fallback defensivo inteligente.
- **Mutação Estrita via textContent:** Mecanismo declarativo baseado em atributos `data-i18n` e `data-i18n-attr`, com imunidade total a injeções de script (XSS).
- **Onboarding e Patch Notes SemVer v1.5.5:** Esteira de ativação guiada de primeiro acesso e modal de patch notes dinâmico com categorização semântica das atualizações (`/api/changelog`).

### 11. Protocolo Unificado de Slash Commands (/), Tríptico Adaptativo e Engenharia Mobile-First
- **Catálogo Completo de 30 Slash Commands:** Comandos categorizados em 6 grupos operacionais (Sistema, Agentes, Memória, Tarefas, Borda, Exportação), invocados com `/` no teletipo ou via botão mecânico touch `[/]`. Comandos locais (`/clear`, `/theme`, `/lang`, `/telemetry`, etc.) executam instantaneamente no cliente (< 16ms) com zero chamadas externas e zero consumo de tokens.
- **Atalho Tático de Barra Touch [/]:** Botão mecânico rápido (`#slashTriggerBtn`) integrado ao console operacional, abrindo diretamente o popover flutuante de comandos em smartphones sem a necessidade de acionar o teclado virtual.
- **Motor de Autocomplete Popover em Vanilla JS:** Componente ultraleve (< 10KB) com busca fuzzy em memória, navegação cíclica por setas (ArrowUp/ArrowDown), autocompletar com Tab/Enter, fechamento por Esc e tolerância a falhas via distância Levenshtein.
- **Recibos Táteis de Teletipo (Slash Receipt Slip):** Emissão de comprovantes com timestamp UTC, identificador sequencial `SEQ#`, picote serrilhado e teto estrito de 150 nós DOM para estabilidade de memória sob operação contínua.
- **Tríptico Adaptativo do Workspace (1024px-1440px):** Layout inteligente que colapsa a barra lateral esquerda sob demanda em uma gaveta de 260px com backdrop, preservando a visibilidade da bobina de teletipo (largura útil elevada de 202px para > 750px) e mantendo o Live Canvas em split 50/50.
- **Telemetria Consolidada Edge Pulse Chip:** Linha única de alta densidade no cabeçalho (`[EDGE // 48.2 °C // 118 MB // WAL ATIVO // HITL 0]`), economizando mais de 360px de espaço horizontal.
- **Barra de Navegação Inferior Mobile (Bottom Navigation Bar):** Barra de alta densidade fixada no rodapé em telas <= 768px (`.mobile-bottom-nav`) com 4 abas táteis (`[O] DOTS`, `[>] CHAT`, `[*] CANVAS`, `[?] GUIA`), isolada com `env(safe-area-inset-bottom)` e hitbox mínima de 44x44pt (Thumb Zone) via pseudo-elementos `::after`.
- **Sincronização Dinâmica com Teclado Virtual (window.visualViewport):** Escuta reativa da API `window.visualViewport` redimensionando a altura física do corpo (`document.body.style.height = ${vv.height}px`), ocultando compulsoriamente a barra inferior através da classe `keyboard-open` e realizando auto-scroll do chat após 60ms, eliminando colisões de layout no iOS Safari e Android Chrome.
- **Proteção Anti-Zoom e Ergonomia no Apple WebKit:** Imposição estrita de `font-size: 16px` em inputs e textareas móveis com `touch-action: manipulation`, neutralizando o auto-zoom compulsório do Safari iOS.

### 12. Tour Spotlight Interativo In-Context e Onboarding FTUE de Alto Desempenho
- **Motor PiDotsTourEngine em Vanilla JS (< 12KB):** Substituição completa de modais estáticos por um sistema de ancoragem espacial in-context no DOM real. Utiliza `box-shadow: 0 0 0 9999px rgba(7, 9, 12, 0.84)` em camada de composição direta da GPU, demandando < 1% de CPU no Raspberry Pi 4B e zero dependências externas.
- **Cinco Etapas Canônicas de Capacitação:** Guia prático cobrindo o Squad Central de Especialistas, o Terminal de Comandos & Teletipo, o Comutador de Modo Foco (Zen vs 50/50), o Live Canvas & Diffs e a Gaveta Técnica (F1).
- **Ancoragem Defensiva e Foco Não-Intrusivo no Mobile:** Posicionamento fixo de `.pixel-tour-popover` acima da barra inferior respeitando as safe areas do iOS e inibição de foco compulsório em inputs durante o tour em smartphones para evitar a subida acidental do teclado virtual.
- **Comando de Barra `/tour`:** Permite rever o tour a qualquer momento ou reiniciá-lo do zero via `/tour reset`.
- **Acionamento Tático na Gaveta Técnica e Context Menu:** Card dedicado `[REVER GUIA OPERACIONAL SPOTLIGHT]` dentro da central F1 / `[SISTEMA]` e atalho rápido com botão direito do mouse.
- **Disparo Automático no Primeiro Acesso:** Detecta novos operadores via `localStorage.getItem('pidots_tour_completed')` e dispara suavemente com 600ms de desacoplamento após o assentamento do cockpit.

### 13. Cliente MCP Lite (Model Context Protocol) com Dynamic Tool Pruning
- **Conectividade Externa Sob Demanda (`pidots/tools/mcp_client.py`):** Conecta servidores MCP externos leves via STDIO ou Server-Sent Events (SSE) assíncrono em Python puro (< 5MB RAM).
- **Conversão Automática de Esquemas:** Converte definições de ferramentas JSON-RPC 2.0 em callables registrados no `ToolRegistry`.
- **Dynamic Tool Pruning Rigoroso:** As ferramentas MCP importadas submetem-se compulsoriamente à lista de permissões `allowed_tools_json`, impedindo a inflação desnecessária do prompt de contexto dos agentes que não as utilizam.

### 14. Governança HITL Remota Assinada com HMAC-SHA256 e TTL
- **Aprovação Segura via Celular (`pidots/core/hitl_crypto.py`):** Geração de links e botões interativos para Telegram e WhatsApp com assinatura HMAC-SHA256 em tempo constante (`hmac.compare_digest`).
- **Endpoint Dedicado (`/api/hitl/signed-resolve`):** Autorização ou veto de comandos críticos com um clique no smartphone sem necessidade de autenticação por senha no navegador.
- **Expiração Temporal Automática (TTL 30m):** Solicitações pendentes retidas recebem `expires_at`. Após 30 minutos sem deliberação, o status migra para `EXPIRED`, cancelando a execução com log de segurança.

### 15. Barramento Físico GPIO e Sensores MQTT de Borda
- **Leitura Direta de Hardware (`pidots/core/edge_triggers.py`):** Suporte nativo à leitura de pinos GPIO físicos no Raspberry Pi 4B (com fallback defensivo caso execute em containers sem privilégios de hardware ou sistemas x86_64).
- **Listener MQTT Assíncrono:** Permite que sensores locais despachem tópicos de telemetria diretamente ao piDots, disparando missões de agentes autônomos ou rotinas do `EdgeScheduler` sem bloquear o loop de eventos.

### 16. Catálogo Comunitário de Dot Packs v1.1 Assinados com SHA-256
- **Distribuição Oficial Padronizada (`data/packs/`):** Três manifestos comunitários assinados prontos para uso:
  - `@dot-secops`: Sentinel especializado em auditoria de portas, análise de logs SSH e conformidade Linux.
  - `@dot-homelab`: Orquestrador de contêineres Docker, sensores físicos e saúde de armazenamento Flash.
  - `@dot-finops`: Analista de telemetria de tokens, consumo de CPU e eficiência energética de inferência.
- **Endpoints de Catálogo e Instalação em 1 Clique:**
  - `GET /api/dots/packs/catalog`: Lista manifestos disponíveis com contagem de ferramentas e fatos arquivais.
  - `POST /api/dots/packs/install/{pack_id}`: Valida a assinatura SHA-256 canônica, aciona inspeção do `@dot-auditor` contra Prompt Injection e restaura atomicamente o Dot no SQLite WAL.

### 17. Desoneração de Assets com Nginx Alpine Multi-Porta e Sandbox Estrito
- **Contêiner Nginx Alpine Multi-Porta (`nginx/nginx.conf`):** Atua como proxy reverso leve (< 6MB RAM) escutando em quatro portas de borda desacopladas (`8081` Landing, `8082` Workspace, `8083` Docs e `8088` Gateway), assumindo a entrega estática em C de `/static/` e `/data/locales/` com cabeçalhos `Cache-Control: immutable` e streaming SSE com `proxy_buffering off`, liberando 100% da CPU do FastAPI para o motor ReAct e SQLite WAL.
- **Trava de Sandbox Estrito (`STRICT_SANDBOX`):** Quando ativado no `.env`, comandos de terminal recusam execução (`exit_code: 126`) caso o isolamento por namespaces Bubblewrap (`bwrap`) não esteja instalado no contêiner, eliminando execuções abertas sem governança.

### 18. Manifesto de Engenharia Centauro e CI Multi-Arquitetura
- **Manifesto de Engenharia Centauro (`AI_MANIFESTO.md`):** Documento público de coautoria humano-IA, estabelecendo regras de honestidade radical sobre hardware real (BCM2711, 4GB RAM, flash wear, teto térmico de 78°C) e erradicação de AI slop e emojis.
- **Pipeline de Integração Contínua Multi-Arch (`.github/workflows/ci.yml`):** Compilação paralela para `linux/amd64` e `linux/arm64` via QEMU e Buildx com 24 baterias de testes automatizados validados a cada commit.

### 19. Desacoplamento por Portas & Integração com Cloudflare Tunnel (v1.5.5)
- **Superfícies de Borda Isoladas:**
  - `http://localhost:8081`: Apresentação / Landing Page oficial com simulador ReAct.
  - `http://localhost:8082`: Console Operacional Workspace SPA / PWA (recomendada proteção Cloudflare Zero Trust Access).
  - `http://localhost:8083`: Guia Didático Oficial e Estudos Técnicos de Engenharia Reversa (`/relatorio`).
  - `http://localhost:8088`: Gateway Unificado com suporte a rotas canônicas e redirects HTTP 308.
  - `http://localhost:8000`: Backend Uvicorn / FastAPI Core interno.
- **Roteamento Cruzado Inteligente (`cross-surface-router.js`):** Detecta dinamicamente se a conexão provém de portas locais, rede LAN ou subdomínios Cloudflare Tunnel (`app.*`, `docs.*`, `pidots.*`), garantindo navegação instantânea e comutação por acordes de teclado (`g h`, `g w`, `g d`).
- **Automação de Túnel de Borda (`cloudflared/`):** Script `setup-tunnel.sh` e modelo `config.yml.example` com protocolo QUIC para NAT Traversal seguro e publicação 24/7 sem abrir portas no roteador.

---

## Requisitos de Sistema

- **Sistema Operacional:** Linux (Debian 12 / Ubuntu 22.04+ / Raspberry Pi OS 64-bit recomendado).
- **Arquitetura:** ARM64 (aarch64) ou x86_64.
- **Python:** Versao 3.11, 3.12 ou 3.13.
- **Docker (Opcional para modo conteiner):** Docker Engine 24+ e Docker Compose v2.
- **Bubblewrap (Opcional para isolamento estrito):** Pacote `bubblewrap` (`apt install bubblewrap`).

---

## Instalacao e Execucao

### Opcao 1: Docker Compose (Recomendado para Producao e Raspberry Pi)

A execucao em conteiner e o metodo padrao para ambientes persistentes:

1. Clone o repositório:
```bash
git clone https://github.com/lyonchristopher/piDots.git
cd piDots
```

2. Configure as variaveis de ambiente:
```bash
cp .env.example .env
nano .env
```
Preencha a sua chave de API e selecione o modelo de linguagem e canais desejados:
```dotenv
AI_API_KEY=sua-chave-aqui
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# Opcional: Alertas HITL e Mensageria
WEBHOOK_NOTIFICATION_URL=https://seu-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=seu-token-bot
TELEGRAM_CHAT_ID=seu-chat-id
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=sua-apikey-evolution
```

3. Inicie o servico com Docker Compose:
```bash
docker compose up -d
```

4. Verifique a telemetria e a saude da aplicacao:
```bash
docker compose ps
docker compose logs -f pidots-core pidots-nginx
```

As superficies de borda estarao imediatamente acessiveis:
- **Landing Page / Visao Geral:** `http://localhost:8081`
- **Console Operacional Workspace SPA:** `http://localhost:8082`
- **Guia Didatico & Estudos Tecnicos:** `http://localhost:8083`
- **Gateway Unificado de Borda:** `http://localhost:8088`
- **FastAPI Core Interno:** `http://localhost:8000` (saude: `curl http://localhost:8000/health`)

---

### Opcao 2: Instalacao Local e Execucao via CLI

Para desenvolvimento local ou execucao direta no sistema operacional hospedeiro:

1. Crie e ative um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale o pacote piDots e suas dependencias em modo editavel:
```bash
pip install -e .
```

3. Inicialize as estruturas de banco de dados e diretorios:
```bash
pidots init
```

4. Inicie o servidor FastAPI:
```bash
pidots serve --host 0.0.0.0 --port 8000
```

---

## Interface de Linha de Comando (CLI)

O piDots fornece o utilitario de linha de comando `pidots` para gestao e operacao:

```bash
# Exibir versao instalada
pidots --version

# Exibir status do sistema, metricas de memoria, banco e workspaces
pidots status

# Listar agentes (Dots) cadastrados
pidots dots list

# Iniciar o servidor HTTP e WebSockets
pidots serve --host 127.0.0.1 --port 8000 --reload

# Gerenciar acoes retidas na fila de governanca HITL
pidots hitl list
pidots hitl approve <ACTION_ID>
pidots hitl reject <ACTION_ID>
```

---

## Utilizacao como Biblioteca Python / SDK para Agentes

O piDots pode ser importado como biblioteca em outros projetos ou CLIs de agentes:

```python
import asyncio
from pathlib import Path
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.spaces_manager import SpacesManager

async def main():
    # 1. Inicializar banco de dados SQLite WAL com schemas de borda
    await init_edge_database()

    dot_id = "dev-assistant"
    workspace_path = str(Path(settings.workspaces_root) / dot_id)

    # 2. Registrar o Dot na base SQLite se ainda nao existir
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dot_id,
                "DevOps Assistant",
                "Operador de Borda",
                "Voce e um assistente operacional em hardware restrito.",
                settings.ai_model,
                workspace_path
            )
        )
        await db.commit()

    # 3. Inicializar provedor de inferencia universal (OpenAI-compativel)
    provider = OpenAIUniversalProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        default_model=settings.ai_model,
    )

    # 4. Instanciar o agente autônomo (Dot)
    agent = DotAgent(
        dot_id=dot_id,
        provider=provider,
    )

    # 5. Salvar documento versionado em Spaces com diffs e busca vetorial KNN
    doc = await SpacesManager.save_document(
        dot_id=agent.dot_id,
        filename="status_relatorio.txt",
        content="Relatorio operacional gerado via SDK oficial do piDots.",
        title="Relatorio de Status"
    )
    print(f"Documento versionado em Spaces: {doc['filename']} (v{doc['version']})")

    # 6. Executar ciclo de raciocinio com streaming de eventos AG-UI
    async for event in agent.run_thread(thread_id="main-thread", user_message="Status dos servicos"):
        if event["event"] == "message:chunk":
            print(event["data"].get("delta", ""), end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## API REST e Streaming em Tempo Real

A aplicacao expoe endpoints para integracao externa com suporte a streaming Server-Sent Events (SSE):

| Metodo | Endpoint | Descricao |
| :--- | :--- | :--- |
| `GET` | `/` | Landing page oficial de apresentacao e onboarding (Hero ReAct e calculadora de silicio) |
| `GET` | `/app` | Console operacional oficial SPA/PWA (Dark Noir e Blueprint monospace) |
| `GET` | `/workspace` | Alias operacional canonico para a estacao de trabalho SPA/PWA (`/app`) |
| `GET` | `/docs` | Guia didatico canonico com busca client-side (Ctrl+K), drawer retratil e API tester |
| `GET` | `/relatorio` | Relatorio tecnico de engenharia, viabilidade e homologacao |
| `GET` | `/api/docs` | Swagger UI interativo OpenAPI desacoplado para desenvolvedores |
| `GET` | `/api/openapi.json` | Esquema OpenAPI 3.0 estruturado em JSON bruto |
| `GET` | `/health` | Telemetria de hardware (temperatura SoC, RAM, status SQLite WAL) |
| `GET` | `/manifest.json` | Manifesto PWA para instalacao em dispositivos moveis e desktop (`start_url: /app`) |
| `GET` | `/sw.js` | Service Worker PWA com cache defensivo v7 para operacao offline |
| `GET` | `/icon.svg` | Logotipo vetorial oficial em formato SVG com cache prolongado |
| `GET` | `/static/pidots-i18n.js` | Micro-motor Vanilla JS de internacionalizacao client-side |
| `GET` | `/data/locales/{lang}.json` | Dicionarios atomicos de localizacao bilingue (PT/EN) com cache de borda |
| `GET` | `/api/changelog` | Historico SemVer e notas de atualizacao categorizadas (Patch Notes v1.5.5) |
| `GET` | `/api/dots` | Listagem de AI Coworkers com arquetipos e status |
| `GET` | `/api/dots/{id}/export-pack` | Exportacao portavel de DotPack v1.1 assinado com SHA-256 |
| `POST` | `/api/dots/import-pack` | Importacao atomica de novos agentes a partir de DotPack v1.1 com auditoria |
| `POST` | `/api/threads` | Criacao de thread de conversacao duravel |
| `GET` | `/api/threads/{id}/messages` | Historico de mensagens com metadados multi-ator e visibilidade |
| `POST` | `/api/threads/{id}/runs` | Ciclo autonomo do Dot com streaming SSE (Protocolo AG-UI v1.0) |
| `GET` | `/api/hitl/pending` | Fila de solicitacoes de aprovacao humana pendentes |
| `POST` | `/api/hitl/{id}/resolve` | Resolucao oficial (aprovacao ou veto) de acao retida |
| `POST` | `/api/hitl/signed-resolve` | Resolucao remota de HITL assinada com HMAC-SHA256 para Telegram/WhatsApp |
| `POST` | `/api/hitl/webhook-callback` | Callback assincrono para resolucao de HITL remota |
| `GET` | `/api/mcp/servers` | Descoberta e status operacional dos servidores MCP Lite conectados |
| `GET` | `/api/spaces` | Listagem de documentos versionados em Spaces |
| `POST` | `/api/spaces` | Gravacao/atualizacao de documento com calculo de diff |
| `GET` | `/api/spaces/{id}` | Conteudo integral de documento em Space |
| `GET` | `/api/spaces/{id}/revisions` | Historico de revisoes e diffs unificados |
| `POST` | `/api/spaces/search` | Busca semantica vetorial KNN em memoria de borda (CRC32) |
| `GET` | `/api/spaces/{id}/download` | Download individual de documento em texto puro |
| `GET` | `/api/workspaces/{dot_id}/export.zip` | Exportacao do workspace completo do Dot em ZIP (com fallback de Spaces) |
| `GET` | `/api/tasks` | Listagem de tarefas proativas agendadas (Dot Heartbeats) |
| `POST` | `/api/tasks` | Criacao de nova tarefa proativa com expressao cron |
| `GET` | `/api/edge/triggers` | Telemetria de triggers de hardware (temperatura SoC, MicroSD livre, RAM livre) |
| `POST` | `/api/edge/maintenance` | Disparo sob demanda da rotina de manutencao noturna (WAL checkpoint e backup) |
| `GET` | `/api/channels` | Listagem de salas tematicas com contagem de mensagens |
| `POST` | `/api/channels` | Criacao de nova sala tematica colaborativa |
| `GET` | `/api/channels/{id}/messages` | Mensagens recentes da sala tematica com limite parametrizavel |
| `POST` | `/api/channels/{id}/messages` | Envio de mensagem para a sala com orquestracao multi-bot |
| `POST` | `/api/channels/{id}/members` | Associacao de membro (Dot ou Usuario) a sala tematica |
| `POST` | `/api/webhooks/incoming/{dot_id}` | Webhook universal para envio de mensagens via API externa |
| `POST` | `/api/webhooks/telegram/{dot_id}` | Receptor de webhooks oficiais da Telegram Bot API |
| `POST` | `/api/webhooks/whatsapp/{dot_id}` | Receptor de webhooks da Evolution API / Baileys (WhatsApp) |
| `GET` | `/api/settings` | Parametros operacionais, canais de notificacao, status da Evolution API e modelo ativo |
| `POST` | `/api/settings/ai` | Atualizacao a quente (hot-reload) de provedor e chaves de IA |
| `POST` | `/api/settings/notifications` | Atualizacao a quente de canais remotos (Webhook, Telegram e Evolution API) |

> [!NOTE]
> **Cabecalhos Defensivos de Seguranca HTTP:** Todas as respostas HTTP do servidor FastAPI incluem automaticamente protecoes de borda (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`), assegurando que consoles embarcados ou acessados via tuneis HTTPS remotos (Cloudflared) estejam imunes a clickjacking e sniffing de tipo MIME.

---

### Console Operacional Web SPA e Interface Tecnica Minimalista (Redesign Visual OpenDots Spatial)
O piDots disponibiliza uma interface SPA/PWA nativa dark mode servida na rota canonica `/app` (ou `/workspace`), projetada como um console escuro tatil no padrao OpenDots Spatial:
- **Top Deck Canonico de 48px:** Barra superior geometricamente calibrada em 48px com alinhamento triplo (.top-deck-left, .top-deck-center, .top-deck-right), eliminando empilhamento de barras e desobstruindo a visualizacao em smartphones.
- **Hero Split-Screen e Bento Grid (Landing Page):** Vitrine Developer-First na rota `/` apresentando badges de silicio (52 MB RAM RSS), fita continua Pixel Paper UI com furos de trator e demonstrador HITL interativo homologado via HMAC-SHA256, complementada por Bento Grid de 4 Cards de Silicio.
- **Activity Rail Modular de 48px e Tríptico OpenDots:** Quatro painéis verticais contextuais (`Spaces & Canais`, `Estúdio de Dots & Tool Pruning`, `Tasks Agendadas & Sensores`, `Memória Híbrida 64D & MCP Lite`) e subheader de missão de 38px.
- **Guias e Relatorios em Largura Total:** `/docs` e `/relatorio` implementados estritamente com menu lateral direito retrátil (drawer abre/fecha), estilo passo a passo com leitura progressiva, busca instantânea Ctrl+K e largura total sem centralização restritiva.
- **Estetica de Alta Densidade:** Visual tatico inspirado em matrizes tecnicas com alta densidade de informacoes, tipografia crisp e estetica retro minimalista de 1-bit.
- **Logotipo Vetorial Oficial:** Marca de identidade do piDots servida via `/icon.svg` com nos interconectados em verde (#10b981) e ciano (#38bdf8).
- **Tres Modos de Operacao Ergonomicos:**
  - *Modo 1: Criacao 50/50:* Chat de teletipo e Live Canvas lado a lado para trabalho ativo de geracao e edicao de codigo e documentos.
  - *Modo 2: Foco Zen (Claude Code / Linear):* Barra lateral e canvas recolhidos, centralizando o chat com largura calibrada (880px) para leitura contínua e raciocínio profundo.
  - *Modo 3: Painel Tecnico & Gestao:* Telemetria de hardware (SoC/RAM/WAL), configuracao de provedores e sandbox acessiveis sob demanda via gaveta tecnica (F1 / `[SISTEMA]` ou `/telemetry`).
- **Squad Central de Especialistas:** Interface despoluida exibindo apenas os 4 coworkers essenciais (Supervisor, Coder, Arquiteto e Auditor), eliminando a sobrecarga de dezenas de agentes residuais.
- **Teletipo e Input Desobstruidos:** Remocao das calhas laterais de 20px (40px totais) do trator de papel e do prefixo rigido no input, concedendo maxima largura util de leitura e digitacao.
- **Visualizador de Diffs e Versionamento:** Inspecao lado a lado de alteracoes em arquivos persistidos no SQLite WAL com carimbos analogicos de status.
- **Governanca Interativa HITL Just-in-Time:** Cartoes de aprovacao e veto de seguranca exibidos apenas quando ha acoes retidas, com persistencia de logs de seguranca.
- **Streaming de Raciocinio AG-UI:** Exibicao token a token de pensamentos e chamadas de ferramentas.
- **Onboarding Walkthrough Guiado:** Esteira interativa de 5 passos para novos operadores com retencao de conclusao no cliente e reabertura via atalho F1.
- **Central de Patch Notes SemVer (v1.5.5):** Modal dinâmico sincronizado com `/api/changelog`, categorizando novidades em Quatro Pilares: Incluido, Ajustado, Removido e Seguranca & Borda.

#### Navegacao Cruzada via Chords Globais de Teclado
Para transicao instantanea entre as superficies do sistema sem necessidade de mouse:

| Chord Sequencial | Superficie de Destino | Descricao |
| :--- | :--- | :--- |
| `g` seguido de `h` | `/` | Go Home: Landing Page Oficial e Onboarding |
| `g` seguido de `w` | `/app` | Go Workspace: Console Operacional SPA / Estacao de Trabalho |
| `g` seguido de `d` | `/docs` | Go Docs: Guia Didatico e Referencia Tecnica |

#### Atalhos de Alta Produtividade do Console SPA
Operacao tática de terminal e gerenciamento sem atrito:

| Atalho | Acao Operacional | Descricao |
| :--- | :--- | :--- |
| `Tecla /` | Autocomplete Popover | Dispara menu de 34 Slash Commands com busca fuzzy no teletipo |
| `Botão [/]` | Autocomplete Touch | Abre diretamente o popover de comandos sem necessidade de abrir o teclado virtual |
| `Alt+1` a `Alt+4` | Activity Rail Sidebar | Comuta instantaneamente entre os 4 paineis contextuais (Spaces, Dots Studio, Tasks Cron, Memoria 64D) |
| `Bottom-Nav` | Comutação Mobile | Alterna entre visualizações [O] DOTS, [>] CHAT, [*] CANVAS e [?] GUIA em telas móveis |
| `Alt+B` / `Ctrl+B` | Alternar Sidebar | Alterna visibilidade da barra lateral de coworkers e spaces |
| `Alt+I` | Inspecionar Artefato | Foca e expande o artefato ativo no Live Canvas |
| `Ctrl+S` / `Cmd+S` | Gravar Revisao | Grava revisao atomica do documento em Spaces no SQLite WAL |
| `Alt+H` | Dossie HITL | Foca e abre o modal de governanca de aprovacao humana |
| `F11` | Alternar Canvas | Alterna entre visualizacao dividida (split) e maximizada do canvas |
| `Ctrl+L` | Limpar Teletipo | Limpa mensagens visuais da bobina do teletipo/chat local |
| `F1` | Painel Tecnico / Ajuda | Abre a gaveta retratil com telemetria, atalhos e manual |

#### Protocolo Unificado de Slash Commands (/)
O Console SPA incorpora um motor de comandos iniciados por barra (`/`) para execucao direta de acoes operacionais e controle de borda:
- **Execucao Local sem Custo de Tokens:** Comandos operacionais e de telemetria rodam diretamente no cliente em menos de 16ms sem chamada a LLM.
- **Menu Popover com Autocompletar:** Invocado ao digitar `/`, com filtragem fuzzy em memoria, navegacao por setas e selecao via `Tab` ou `Enter`.
- **Tolerancia a Falhas via Levenshtein:** Sugere proativamente o comando correto em caso de pequenos erros de digitacao do operador (*"Voce quis dizer: /comando?"*).
- **Recibos Tatis no Teletipo:** Respostas formatadas com cabecalho `[CMD] SISTEMA`, timestamp ISO UTC, numero sequencial de auditoria `SEQ# 000X` e picote serrilhado.

| Categoria | Comandos Principais | Exemplos de Uso |
| :--- | :--- | :--- |
| **Sistema & UI** | `/help`, `/clear`, `/theme`, `/lang`, `/info`, `/status`, `/telemetry`, `/pwa`, `/tour`, `/onboarding`, `/changelog`, `/computer` | `/tour`, `/computer ls -la`, `/telemetry`, `/theme noir` |
| **Agentes & Multi-Bot** | `/dots`, `/handoff`, `/council`, `/delegate`, `/archetype`, `/tools`, `/mcp`, `/coagents` | `/dots`, `/handoff dot-auditor`, `/coagents`, `/mcp` |
| **Memoria & Conhecimento** | `/memory`, `/archival`, `/shared`, `/spaces`, `/diff`, `/save-space` | `/archival SQLite WAL`, `/save-space ata.md`, `/diff` |
| **Tarefas & Heartbeat** | `/tasks`, `/cron`, `/run-task` | `/tasks`, `/cron listar`, `/run-task task-001` |
| **Governanca & Borda** | `/hitl`, `/triggers`, `/maintenance`, `/backup` | `/hitl status`, `/triggers`, `/maintenance run` |
| **Exportacao & Dados** | `/export`, `/pack` | `/export chat`, `/export canvas`, `/pack dot-dev-core` |

---

## Governanca e Seguranca

### Human-in-the-Loop (HITL)
Comandos com potencial destrutivo (como exclusões recursivas, alterações de permissões `chmod/chown`, comandos `sudo`, ou gravações e redirecionamentos para arquivos em disco `> / >> / tee`) são interceptados automaticamente pelo motor de governança. A execução é retida em estado pendente (`awaiting_hitl`) e uma mensagem explicativa de papel `assistant` é gravada diretamente na conversa com o ID da aprovação e instruções de homologação via interface web (`/app` ou `Alt+H`) ou comando `/hitl`. Comandos com descartes inofensivos de erros (`2>/dev/null`, `2>&1`) executam de forma autônoma sem travar o operador.

### Sandbox com Bubblewrap
Para evitar violacoes de integridade no sistema hospedeiro, o executor de comandos utiliza o Bubblewrap (`bwrap`) nativo do Linux. Os processos sao isolados em namespaces de sistema de arquivos e processos restritos, impedindo o acesso nao autorizado a diretorios fora do workspace alocado para o agente.

---

## Testes Automatizados

O repositorio inclui baterias de testes automatizados e testes de estresse para validar a resiliencia sob concorrencia:

```bash
# Testes fundamentais de infraestrutura e isolamento
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Testes de orquestracao multi-bot e Dynamic Tool Pruning
python3 scripts/test_phase6_multibot.py

# Teste do scheduler proativo Dot Heartbeat (croniter e HEARTBEAT_OK)
python3 scripts/test_phase7_scheduler.py

# Teste do gateway de mensageria, webhooks e canais colaborativos
python3 scripts/test_phase8_messaging.py

# Testes do plano de expansao de borda (Fases 1 a 5)
python3 scripts/test_phase9_memory.py               # Memoria Hierarquica (Core Memory, Archival FTS5, 64d)
python3 scripts/test_phase10_self_healing_planner.py # Self-Healing Harness e Two-Stage Planning
python3 scripts/test_phase11_council_debate.py       # Conselho Consultivo e Debate Tripartite
python3 scripts/test_phase12_shared_space_dot_packs.py # Shared Knowledge Space e Dot Packs v1.0
python3 scripts/test_phase13_edge_triggers_maintenance.py # Triggers de Hardware e Manutencao MicroSD

# Testes do protocolo AG-UI, CoAgents Shared State, Generative UI Inline e Layout OpenDots
python3 scripts/test_phase1_opendots_agui.py
python3 scripts/test_phase2_opendots_layout.py
python3 scripts/test_phase3_opendots_dynamic_js.py

# Teste de resiliencia integral (Tipagem de erros, AG-UI v1.0, 3 consumidores, Circuit Breaker)
python3 scripts/test_resilience_phases.py

# Testes de Desacoplamento de Portas e Roteamento Cruzado
python3 scripts/test_phase20_port_decoupling_nginx.py
node scripts/test_cross_surface_router.js

# Teste de carga e concorrencia sob estresse (Edge Stress Test)
python3 scripts/stress_test.py
```


---

## Estrutura do Repositorio

```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── ARCHITECTURE.md                  # Especificacao detalhada de arquitetura e I/O
├── CONTRIBUTING.md                  # Diretrizes para contribuicao tecnica ao projeto
├── cloudflared/                     # Configuracoes e automacoes de tunel seguro Cloudflare
│   ├── config.yml.example           # Modelo de ingress com subdominios desacoplados
│   └── setup-tunnel.sh              # Script interativo de instalacao e configuracao
├── data/                            # Dados estaticos, changelog e dicionarios de localizacao
│   ├── changelog.json               # Historico de versoes e notas de atualizacao SemVer v1.5.5
│   └── locales/                     # Dicionarios de internacionalizacao atomicos (i18n)
│       ├── en.json                  # Dicionario de termos em Ingles Tecnico
│       └── pt.json                  # Dicionario de termos em Portugues do Brasil
├── docker-compose.yml               # Configuracao oficial de orquestracao Docker (multi-porta)
├── Dockerfile                       # Imagem otimizada baseada em python:3.13-slim
├── LICENSE                          # Licenca MIT
├── MANUAL_OPERACIONAL.md            # Guia operacional de administracao e comandos
├── nginx/                           # Configuracao de proxy reverso leve (< 6MB RAM)
│   └── nginx.conf                   # Quatro blocos de escuta (8081, 8082, 8083, 8088)
├── pages/                           # Superficies HTML monoliticas desacopladas
│   ├── docs.html                    # Guia didatico e manual operacional passo a passo
│   ├── landing.html                 # Pagina de apresentacao oficial e onboarding
│   ├── relatorio.html               # Relatorio de engenharia reversa e benchmarks ARM64
│   └── spa.html                     # Console operacional Workspace SPA/PWA
├── pidots/                          # Pacote de codigo-fonte principal
│   ├── config.py                    # Configuracoes Pydantic e variaveis de ambiente
│   ├── main.py                      # Servidor FastAPI, endpoints REST e streaming SSE
│   ├── core/                        # Ciclo ReAct, multi-bot, scheduler e mensageria
│   │   ├── agent.py                 # Ciclo de execucao autonomo do agente com Tool Pruning
│   │   ├── council.py               # Conselho Consultivo e debate dialetico tripartite
│   │   ├── dot_pack.py              # Empacotamento, exportacao e importacao de Dot Packs v1.0
│   │   ├── edge_triggers.py         # Triggers de hardware edge (SoC, MicroSD e RAM)
│   │   ├── hitl.py                  # Interceptacao e gestao de acoes de alto risco
│   │   ├── messaging_gateway.py     # Gateway unificado de mensageria e barramento de canais
│   │   ├── notifier.py              # Notificacoes e webhooks externos
│   │   ├── orchestrator.py          # Orquestrador Multi-Bot e delegacao de subtarefas
│   │   ├── planner.py               # Planejamento em dois estagios (Goals e Milestones)
│   │   ├── scheduler.py             # Escalonador proativo Dot Heartbeat via croniter
│   │   ├── self_healing.py          # Self-Healing Harness e diagnostico de tracebacks
│   │   └── state.py                 # Gestao de estado e contexto de sessao
│   ├── providers/                   # Adaptadores de modelos de linguagem (LLM/SLM)
│   │   └── openai_client.py         # Provedor universal compativel com protocolo OpenAI
│   ├── storage/                     # Persistencia em SQLite WAL e busca vetorial
│   │   ├── db.py                    # Gerenciamento de conexao e esquemas de dados
│   │   ├── maintenance.py           # Manutencao noturna autonoma e compactacao WAL
│   │   ├── memory_manager.py        # Memoria hierarquica MemGPT (Core, Archival FTS5)
│   │   ├── shared_space.py          # Espaco de conhecimento compartilhado entre bots
│   │   ├── spaces_manager.py        # Versionamento de arquivos e diffs
│   │   └── vector_store.py          # Motor vetorial KNN otimizado com CRC32
│   └── tools/                       # Ferramentas executaveis do agente
│       ├── file_ops.py              # Operacoes atomicas de leitura e escrita
│       ├── registry.py              # Registro centralizado de funcoes do agente
│       ├── terminal.py              # Executor com isolamento Bubblewrap (bwrap)
│       └── web_reader.py            # Extracao leve de conteudo web com trafilatura
├── pages/                           # Paginas HTML semanticas desacopladas
│   ├── app.html                     # Console operacional SPA/PWA (/app)
│   ├── landing.html                 # Landing page oficial de apresentacao (/)
│   ├── docs.html                    # Guia didatico operacional passo a passo (/docs)
│   └── relatorio.html               # Relatorio tecnico historico (/relatorio)
├── pyproject.toml                   # Empacotamento padrao PEP 517/518/621
├── README.md                        # Documentacao principal (Portugues do Brasil)
├── README_EN.md                     # Documentacao espelhada (Ingles Americano)
├── requirements.txt                 # Dependencias estritas do projeto
├── SECURITY.md                      # Politica de seguranca e reporte de vulnerabilidades
├── scripts/                         # Scripts de teste automatizado e benchmarks
└── static/                          # Assets estaticos do frontend
    ├── css/                         # Folhas de estilo modulares segmentadas
    │   ├── tokens.css, reset.css, layout.css, components.css, mobile.css
    │   └── spa.css, landing.css, docs.css, relatorio.css
    └── js/                          # Motores JavaScript modulares em Vanilla JS
        ├── core/                    # i18n, scroll-lock, pixel-system
        ├── spa/                     # pidots-api, slash-commands, tour-engine, pidots-ux, app-init
        ├── landing/                 # landing.js (simulador ReAct, ROI silicio, trava HITL)
        └── docs/                    # docs.js (Omnisearch Ctrl+K, mini API tester)
```

---

## Licenca

Este projeto e distribuido sob os termos da licenca MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informacoes.

Desenvolvido por **lyon christopher** (2026).
