# piDots

**Estação Local de Agentes Autônomos para Hardware de Borda (SBCs, ARM64 / x86_64, Benchmark: Raspberry Pi 4B)**

[Português](README.md) | [English](README_EN.md)

`PYTHON: 3.11 | 3.12 | 3.13` | `ARCH: ARM64 | x86_64` | `HARDWARE: RASPBERRY PI 4B` | `STORAGE: SQLITE WAL` | `SANDBOX: BWRAP` | `LICENSE: MIT`

---

## Visão Geral

O piDots transforma um computador de placa única em uma estação de trabalho para agentes de inteligência artificial. Ele roda localmente, sem depender de nuvens externas para orquestrar o código. O benchmark físico do projeto é o **Raspberry Pi 4B com 4 GB de memória RAM (ARM64)**.

Projetamos o piDots para o silício real. Frameworks corporativos tradicionais assumem servidores com gigabytes de memória sobrando, navegadores headless pesados e bancos vetoriais em contêineres separados. Na bancada física, essa conta não fecha. A placa aquece, o cartão MicroSD sofre desgaste precoce por escritas síncronas e o consumo de energia dispara.

Resolvemos esse gargalo com um monólito modular assíncrono em Python (`FastAPI + uvloop`). Eliminamos runtimes desnecessários para entregar um sistema enxuto: **menos de 50 MB de RAM em repouso** e **menos de 80 MB durante a execução simultânea de agentes**.

O sistema disponibiliza especialistas para tarefas reais: programação, arquitetura de software, auditoria técnica e manutenção preventiva. Toda a operação conta com persistência em SQLite WAL, isolamento de comandos em sandbox Linux Bubblewrap, aprovações Human-in-the-Loop em tempo real e console web tático em modo escuro.

---

## Comparativo Técnico: piDots vs Frameworks Tradicionais

| Parâmetro | Frameworks Tradicionais (Padrão Nuvem) | piDots (Computação de Borda) |
| :--- | :--- | :--- |
| **Hardware Mínimo** | Servidor x86_64 com 8 GB a 16 GB RAM | Raspberry Pi 4B (4 GB RAM) / ARM64 / x86_64 |
| **Stack de Execução** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Consumo de Memória (Repouso)** | 2.000 MB - 3.500 MB RAM | ~48 MB - 52 MB RAM (Redução de ~98%) |
| **Consumo sob Carga (Pico)** | 4.000 MB - 6.000 MB RAM | < 100 MB RAM |
| **Banco de Dados & Estado** | PostgreSQL / Neo4j / Redis | SQLite com WAL Mode e PRAGMAs otimizados |
| **Banco Vetorial / Memória** | ChromaDB / Pinecone / Qdrant (500 MB+) | Extrator Vetorial CRC32 KNN em disco (< 5 MB) |
| **Navegador e Leitura Web** | Chromium / Playwright headless (~500 MB RAM) | Trafilatura / httpx assíncrono puro em CPU (~20 MB) |
| **Isolamento de Segurança** | Docker aninhado / VM Cloud | Sandbox Bubblewrap (`bwrap`) nativo Linux |
| **Desgaste de Armazenamento** | Alto overhead de fsync em disco | Otimizado para preservar MicroSD / SSD USB |
| **Integração e Distribuição** | Sistema fechado / Microsserviços | Pacote Python modular (`pip install -e .`) e Docker |

---

## Arquitetura e Principais Módulos

O piDots foi estruturado como um monólito modular assíncrono para garantir baixa sobrecarga computacional:

```
pidots/
├── __init__.py
├── cli.py               # Interface nativa de linha de comando para o terminal
├── config.py            # Variáveis de ambiente e configurações centrais
├── main.py              # Bootstrap FastAPI, ciclo de vida Lifespan e middlewares
├── api/                 # Sub-roteadores modulares desacoplados (APIRouters)
│   ├── __init__.py      # Agregador central de rotas da aplicação
│   ├── deps.py          # Injeção de dependências compartilhadas e PageManager
│   ├── routes_channels.py # Salas temáticas de discussão e canais colaborativos
│   ├── routes_dots.py   # Gerenciamento de agentes e Dot Packs v1.1
│   ├── routes_edge.py   # Telemetria térmica do SoC, triggers e servidores MCP
│   ├── routes_hitl.py   # Fila de segurança e resolução remota HMAC-SHA256
│   ├── routes_pwa.py    # Superfícies HTML, manifesto PWA e Service Worker
│   ├── routes_tasks.py  # Agendamentos proativos e rotinas de manutenção
│   ├── routes_threads.py # Sessões de conversa e streaming SSE (AG-UI v1.0)
│   └── routes_webhooks.py # Webhooks Telegram, WhatsApp e endpoints incoming
├── core/
│   ├── __init__.py
│   ├── agent.py         # Motor ReAct assíncrono com poda dinâmica de ferramentas (AG-UI)
│   ├── council.py       # Conselho consultivo e debate em três vias entre agentes
│   ├── dot_pack.py      # Dot Packs v1.1 com assinatura SHA-256 e checagem anti-injection
│   ├── edge_triggers.py # Triggers de hardware (BCM2711), pinos GPIO e cliente MQTT
│   ├── hitl.py          # Governança Human-in-the-Loop com retenção e expiração TTL
│   ├── hitl_crypto.py   # Assinatura e validação de tokens HMAC-SHA256
│   ├── messaging_gateway.py # Gateway de mensageria externa e barramento de canais
│   ├── notifier.py      # Notificador HTTP e alertas externos assinados
│   ├── orchestrator.py  # Orquestrador multi-bot (Supervisor, Handoff e menções @dot)
│   ├── planner.py       # Planejamento em dois estágios (Goals, Milestones e Checkpoints)
│   ├── scheduler.py     # Motor proativo Dot Heartbeat com cálculo via croniter
│   ├── self_healing.py  # Auto-reparo com diagnóstico de tracebacks de erro
│   └── state.py         # Modelos de eventos do protocolo AG-UI e estados de sessão
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Gateway universal de inferência com Circuit Breaker de 3 estados
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL calibrado para microSD e migrações idempotentes
│   ├── maintenance.py   # Manutenção noturna autônoma, checkpoint TRUNCATE e VACUUM INTO
│   ├── memory_manager.py # Memória hierárquica (Core Memory e Archival FTS5 + 64d)
│   ├── shared_space.py  # Espaço de anotações compartilhado entre bots na mesma thread
│   ├── spaces_manager.py # Workspaces isolados, versionamento e diffs unificados
│   └── vector_store.py  # Memória vetorial KNN em disco com hashing CRC32
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Leitura, escrita atômica e listagem de arquivos
    ├── mcp_client.py    # Cliente MCP Lite assíncrono sobre STDIO/SSE
    ├── registry.py      # Registro centralizado de ferramentas com poda dinâmica
    ├── terminal.py      # Executor shell em sandbox Bubblewrap com trava de segurança
    └── web_reader.py    # Extrator semântico web assíncrono com Trafilatura
```

---

## Capacidades de Engenharia de Borda

### 1. Orquestração Multi-Bot e Especialistas Locais

Em vez de manter janelas de chat isoladas, o piDots conecta múltiplos especialistas dentro do mesmo processo. O `ThreadRouter` extrai menções no formato `@nome_do_dot`, identifica os interlocutores e registra os participantes na tabela `thread_participants`.

Quando uma missão envolve etapas distintas, o Supervisor assume o planejamento e delega partes técnicas com a ferramenta `delegate_task`. Cada worker executa em uma thread isolada e devolve o resultado para a conversa principal. Para mudar o foco de uma conversa, a ferramenta `handoff_to_dot` transfere a liderança da thread para outro agente, registrando o histórico na tabela `agent_handoffs`. Toda troca de mensagens interna entre bots é gravada com visibilidade restrita, mantendo a conversa do usuário limpa.

O sistema traz quatro perfis calibrados de fábrica:
- **Supervisor (`@supervisor`):** Coordena missões, organiza etapas de trabalho e sintetiza resultados.
- **Coder (`@coder`):** Escreve código, corrige bugs, roda comandos no sandbox e valida testes.
- **Arquiteto (`@muse`):** Modela dados, estrutura fluxos de software e organiza documentos técnicos.
- **Auditor (`@auditor`):** Inspeciona segurança de comandos, checa consumo térmico e valida integridade.

Cada agente carrega apenas as ferramentas autorizadas em sua configuração (`allowed_tools_json`). Essa poda dinâmica economiza até 75% dos tokens de contexto e impede que os agentes tentem usar ferramentas fora de seu escopo.

### 2. Automações Proativas: Padrão Dot Heartbeat e Circuit Breaker

O agendador in-process (`pidots/core/scheduler.py`) executa rotinas cron diretamente no loop do FastAPI, sem exigir Redis, Celery ou bancos externos:

As tarefas ficam salvas na tabela `scheduled_tasks` do SQLite. Quando uma checagem periódica constata que o sistema está em ordem, o agente responde com a diretiva `HEARTBEAT_OK`. O agendador marca a execução como silenciosa e volta a dormir, sem disparar alertas desnecessários ou inflar o banco de dados.

Para proteger a CPU do Raspberry Pi, o agendador usa travas de memória que impedem execuções sobrepostas. Se uma tarefa falhar consecutivamente, um Circuit Breaker com backoff exponencial entra em ação. O intervalo de espera sobe gradualmente de 30 segundos até 1 hora. Ao atingir 5 falhas seguidas, o circuito abre e a tarefa é suspensa, evitando que loops de erro consumam a cota de inferência ou travem a máquina. Caso a chave de API esteja vazia ou inválida, as tarefas são pausadas preventivamente.

### 3. Gateway de Mensageria e Salas Temáticas

O gateway (`pidots/core/messaging_gateway.py`) centraliza comunicações externas através de webhooks HTTP simples e sem estado:

Ele oferece conectores nativos para Telegram, WhatsApp (via Evolution API com autenticação por chave) e webhooks genéricos para scripts personalizados. As conversas em grupo ocorrem em salas temáticas salvas na tabela `channels`.

Para impedir que dois bots entrem em conversas infinitas entre si, o barramento de mensagens aplica regras estritas:
1. Contador de saltos limitado a no máximo 3 repasses.
2. Bots só respondem a mensagens de outros bots quando citados diretamente com `@nome_do_dot`.
3. Resposta silenciosa `NO_ACTION` quando o agente avalia que não há contribuição relevante a fazer.

Se a API de inteligência artificial estiver fora do ar, o gateway captura a falha e avisa o interlocutor com uma mensagem clara de erro operacional, mantendo o canal íntegro.

### 4. Resiliência e Tratamento Tipado de Falhas

O cliente de inferência distingue falhas definitivas de autenticação (HTTP 401/403) de falhas transitórias de rede ou sobrecarga (HTTP 429/503). Erros de autenticação interrompem o ciclo imediatamente, sem gastar tempo com retentativas inúteis. Erros de rede passam por tentativas com variação aleatória de tempo (jitter).

O ciclo do agente emite eventos padronizados no protocolo AG-UI. Se uma execução falha, o evento terminal `run:finished` reporta o tipo exato do problema. O erro é gravado no banco SQLite com visibilidade interna para depuração posterior.

Essa proteção se estende aos três serviços consumidores:
- O **Scheduler** registra a falha com o diagnóstico técnico real no banco.
- O **Gateway** avisa o canal externo de forma direta e sem jargões confusos.
- O **Orquestrador Multi-Bot** marca a subtarefa como com falha e devolve o erro estruturado para o supervisor reorganizar o plano.

### 5. Memória Hierárquica em Três Camadas

O módulo de memória (`pidots/storage/memory_manager.py`) dá autonomia para o agente gerenciar seu próprio contexto através de ferramentas nativas:

- **Memória de Trabalho (`<core_memory>`):** Blocos fixos injetados diretamente no prompt inicial, divididos em dados do usuário, persona do agente e objetivo ativo da missão. O agente pode editar essas seções com `core_memory_append` e `core_memory_replace` conforme aprende novas preferências.
- **Memória Arquival com Busca Híbrida:** Notas, códigos e referências gravados na tabela `archival_memories`. A busca combina o índice SQLite FTS5 (BM25 em texto puro) com projeção vetorial compacta de 64 dimensões baseada em hashing de n-gramas. A busca roda inteiramente na CPU local via `archival_memory_search`, sem exigir bibliotecas de machine learning pesadas.
- **Memória de Retrospectiva (`recall_memory_search`):** Permite vasculhar conversas anteriores na mesma thread sem precisar carregar centenas de mensagens brutas no contexto ativo.

### 6. Auto-Reparo e Planejamento em Dois Estágios

O módulo `self_healing.py` inspeciona a saída de comandos shell e scripts Python executados no sandbox. Ao detectar um erro, ele disseca o traceback, aponta o arquivo e a linha da falha e sugere a correção técnica através da ferramenta `execute_and_verify`.

Para missões complexas, o planejador (`planner.py`) quebra o objetivo principal em marcos menores salvos no SQLite. O agente cria a estrutura com `plan_create`, atualiza cada marco com evidências reais de execução via `plan_update_step` e acompanha a porcentagem de conclusão com `plan_get_status`.

### 7. Revisão em Três Vias (Conselho Consultivo)

O módulo `council.py` reúne três agentes antes da execução de tarefas arriscadas:
1. O **Coder** propõe a implementação técnica.
2. O **Auditor** faz uma revisão crítica em busca de brechas de segurança, impacto térmico e consumo de memória.
3. O **Supervisor** avalia os dois pontos e emite a decisão final.

O debate intermediário é registrado internamente para auditoria. Apenas o parecer consolidado aparece na conversa do operador. Para evitar gastos excessivos de tempo e tokens, a discussão é travada em no máximo 3 rodadas. O consumo medido dessa rotina fica abaixo de 53 MB de RAM.

### 8. Quadro de Anotações e Dot Packs Assinados (v1.1)

O `shared_space.py` funciona como um quadro compartilhado entre os agentes de uma mesma thread, permitindo escrita, leitura e revisão mútua de notas técnicas sob chaves temáticas.

Para transportar configurações de agentes entre diferentes máquinas, o sistema utiliza o padrão Dot Pack v1.1 (`data/packs/`). Trata-se de um manifesto JSON com assinatura criptográfica `SHA-256`. Ao importar um pacote (`POST /api/dots/import-pack`), o sistema confere a integridade do hash e inspeciona a memória inicial contra tentativas de prompt injection antes de cadastrar o agente no banco.

### 9. Triggers de Hardware e Cuidados com o MicroSD

O módulo `edge_triggers.py` lê os sensores térmicos do processador Broadcom BCM2711 via sysfs Linux (`/sys/class/thermal/thermal_zone0/temp`), além do espaço em disco e da memória RAM livre. Se a placa passar dos 72 °C ou o espaço livre cair abaixo de 10%, o sistema desacelera a frequência de checagens para resfriar o silício.

A manutenção noturna (`maintenance.py`) cuida da integridade da mídia Flash. Ela roda `PRAGMA wal_checkpoint(TRUNCATE)` para consolidar o log de transações, arquiva mensagens com mais de 7 dias e cria cópias de segurança consistentes usando `VACUUM INTO` em conexões isoladas, mantendo o banco ágil e sem fragmentação.

### 10. Suporte Bilíngue Nativo (PT/EN)

O micro-motor de internacionalização (`static/js/core/pidots-i18n.js`) é escrito em JavaScript puro (< 10 KB). Ele alterna entre Português e Inglês em menos de 10 milissegundos sem recarregar a página e sem depender de bibliotecas externas.

As traduções ficam organizadas em arquivos JSON (`data/locales/pt.json` e `data/locales/en.json`). A renderização usa estritamente `textContent` em elementos com atributos `data-i18n`, eliminando qualquer risco de injeção de scripts (XSS).

### 11. Design System: Pixel Paper UI (Dark Paper Noir)

A interface do piDots foi desenhada especificamente para computadores de placa única e telas operacionais de alta densidade. Rejeitamos intencionalmente bibliotecas pesadas de terceiros (Tailwind, React, Electron ou frameworks de componentes inflados) em favor de CSS nativo modular desacoplado em 8 folhas estilísticas (`static/css/*.css`), garantindo carregamento inicial abaixo de 100 milissegundos e consumo nulo de CPU na renderização:

1. **Materialidade de Papel Técnico & Alto Contraste:** Inspirado em teletipos, carimbos de controle de qualidade, fichas catalográficas e grafite técnico sobre papel escuro.
   - Fundo base Dark Paper (`#07090c` e `#0c0d0e`).
   - Tinta fosforosa verde para sucesso e prontidão (`#33ff66`).
   - Tinta azul blueprint para enlaces técnicos (`#38bdf8`).
   - Âmbar de alerta para ordens retidas em segurança (`#f59e0b`).
2. **Geometria Ortogonal Estrita:** Bordas retas com `border-radius: 0px`. Ausência de cantos arredondados genéricos. Cada painel delimita fronteiras cartesianas precisas com bordas de 1 pixel (`1px solid var(--border)`).
3. **Sombras Cartesianas Mecânicas:** Toda elevação utiliza sombras sem desfoque (zero blur radius): `box-shadow: 2px 2px 0px #000000;`, `3px 3px 0px #000000;` ou `4px 4px 0px #000000;`. Isso simula relevo mecânico tátil sem exigir esforço de composição de sombras na GPU integrada da placa.
4. **Dupla Tipografia Técnica:**
   - **Silkscreen:** Tipografia bitmap crisp aplicada estritamente em títulos, identificadores, tags de estado e carimbos de auditoria.
   - **JetBrains Mono:** Tipografia monoespaçada legível aplicada ao corpo de texto, teletipo de execução, tabelas e janelas de código (com `font-variant-numeric: tabular-nums`).
5. **Ergonomia Mobile-First (Thumb Zone):** Em smartphones, o console ativa uma barra inferior ancorada na zona confortável do polegar, botões com alvos de toque mínimos de 44x44 pontos e compensação dinâmica de altura útil via `window.visualViewport` para evitar oclusão pelo teclado virtual.

### 12. Terminal com 35 Slash Commands e Console Mobile

O console SPA traz um catálogo completo de comandos rápidos acionados pela barra (`/`):
- Comandos operacionais locais (`/clear`, `/theme`, `/lang`, `/status`, `/telemetry`) respondem em menos de 16 milissegundos no próprio navegador, sem consumir tokens.
- O popover flutuante conta com busca por proximidade textual, navegação por setas e suporte ao botão físico touch `[/]` para celulares.
- Cada ordem executada emite um comprovante no teletipo com carimbo de data/hora UTC e número sequencial de auditoria.

Em telas menores de smartphones (<= 768px), uma barra inferior dedicada organiza o acesso com botões dimensionados para toque confortável (mínimo de 44x44 pontos). A altura útil se adapta à abertura do teclado virtual via `window.visualViewport`, evitando que o campo de digitação fique escondido atrás do teclado.

### 13. Tour de Onboarding no Console Real

O motor de tour (`tour-engine.js`) guia novos operadores diretamente na interface ativa, sem usar modais estáticos. Ele aplica sombras calculadas na GPU para destacar os elementos reais na tela:
1. Barra lateral e biblioteca de arquivos/spaces.
2. Teletipo e terminal de comandos dos agentes.
3. Sandbox Bubblewrap e isolamento de segurança.
4. Prancheta de trabalho do Live Canvas (código, terminal e aprovações).
5. Painel de telemetria e parâmetros de modelos de IA.

O tour pode ser revisto a qualquer momento digitando `/tour` no teletipo ou pressionando a tecla `F1`.

### 14. Conexão Externa via Protocolo MCP Lite

O piDots integra servidores MCP externos através de conexões assíncronas por STDIO ou Server-Sent Events (SSE) escritas em Python puro (`pidots/tools/mcp_client.py`). O cliente consome menos de 5 MB de RAM.

Ferramentas importadas via protocolo JSON-RPC 2.0 são registradas diretamente no catálogo do piDots. Elas respeitam a lista de ferramentas permitidas de cada agente, impedindo que ferramentas não utilizadas poluam o contexto do modelo.

### 15. Aprovações de Segurança Remotas (HMAC-SHA256)

Comandos arriscados podem ser aprovados diretamente pelo celular via links ou botões seguros enviados para o Telegram ou WhatsApp. Cada ordem recebe uma assinatura HMAC-SHA256 validada em tempo constante.

Toda solicitação retida possui um prazo de validade de 30 minutos. Se o operador não aprovar o comando dentro desse período, a ordem expira por segurança, liberando o agente de volta para o estado ocioso sem executar nada arriscado.

### 16. Pinos GPIO Físicos e Sensores MQTT

O piDots lê diretamente os pinos GPIO do Raspberry Pi 4B para capturar eventos de botões físicos ou sensores locais. Caso o sistema esteja rodando em computadores x86_64 ou contêineres sem acesso direto aos pinos, o driver ativa um modo de contingência seguro.

Um cliente MQTT assíncrono permite que sensores da rede local enviem dados diretamente para a estação, disparando rotinas dos agentes sem travar o processamento principal.

### 17. Catálogo de Pacotes de Agentes

O diretório `data/packs/` reúne três agentes especializados com instalação em um clique:
- **`@dot-secops`:** Auditor de segurança focado em portas abertas, acessos SSH e integridade do Linux.
- **`@dot-homelab`:** Cuida da saúde de contêineres Docker, sensores físicos e armazenamento.
- **`@dot-finops`:** Analisa uso de tokens, ciclos de CPU e eficiência energética das chamadas de IA.

### 18. Proxy Reverso Nginx com Entrega em Quatro Portas

Um contêiner Nginx Alpine leve (< 6 MB de RAM) assume a entrega dos arquivos estáticos (`/static/` e `/data/locales/`) com cache estrito. Ele gerencia as quatro superfícies do sistema em portas separadas:
- Porta `8081`: Apresentação e introdução ao sistema.
- Porta `8082`: Console operacional de trabalho (SPA/PWA).
- Porta `8083`: Manual técnico e documentação da API.
- Porta `8088`: Gateway de rotas com redirecionamentos canônicos.

Essa divisão libera 100% dos recursos do FastAPI para processar a lógica dos agentes e as transações no banco SQLite.

### 19. Sandbox Estrito com Bubblewrap

Quando a variável `STRICT_SANDBOX=true` está ativa no arquivo `.env`, o piDots recusa a execução de qualquer comando shell caso o utilitário Bubblewrap (`bwrap`) não esteja instalado no sistema hospedeiro. O comando retorna erro com código de saída 126, impedindo que scripts executem sem o devido isolamento de namespaces.

### 20. Acesso Remoto Seguro com Cloudflare Tunnel

O diretório `cloudflared/` traz scripts prontos para publicar as portas locais na internet de forma segura, utilizando túneis criptografados via protocolo QUIC. A conexão não exige abertura de portas no roteador doméstico nem liberação de IP público, permitindo proteger o console com políticas de acesso Zero Trust.

---

## Requisitos de Sistema

- **Sistema Operacional:** Linux (Debian 12 / Ubuntu 22.04+ / Raspberry Pi OS 64-bit recomendado).
- **Arquitetura:** ARM64 (aarch64) ou x86_64.
- **Python:** Versão 3.11, 3.12 ou 3.13.
- **Docker (Opcional):** Docker Engine 24+ e Docker Compose v2.
- **Bubblewrap (Recomendado):** Pacote `bubblewrap` para isolamento de comandos (`sudo apt install bubblewrap`).
- **Node.js (Opcional):** Necessário apenas para validar a suíte client-side de testes de roteamento cruzado (`node scripts/test_cross_surface_router.js`).

---

## Instalação e Execução

### Opção 1: Docker Compose (Recomendado para Produção)

1. Clone o repositório:
```bash
git clone https://github.com/lyonchristopher/piDots.git
cd piDots
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
nano .env
```

Defina sua chave de API e o modelo de linguagem desejado:
```dotenv
AI_API_KEY=sua-chave-aqui
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# Canais opcionais de notificação e governança
WEBHOOK_NOTIFICATION_URL=https://seu-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=seu-token-bot
TELEGRAM_CHAT_ID=seu-chat-id
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=sua-apikey-evolution
```

3. Suba os contêineres:
```bash
docker compose up -d
```

4. Verifique a saúde dos serviços:
```bash
docker compose ps
docker compose logs -f pidots-core pidots-nginx
```

As portas locais estarão disponíveis:
- **Apresentação:** `http://localhost:8081`
- **Console Operacional:** `http://localhost:8082`
- **Manual Técnico:** `http://localhost:8083`
- **Gateway Canônico:** `http://localhost:8088`
- **API FastAPI Interna:** `http://localhost:8000` (saúde: `curl http://localhost:8000/health`)

---

### Opção 2: Instalação Nativa em Python

Para rodar diretamente na sua máquina de desenvolvimento:

1. Crie e ative um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale o pacote em modo editável:
```bash
pip install -e .
```

3. Inicialize o banco de dados e os diretórios de trabalho:
```bash
pidots init
```

4. Inicie o servidor:
```bash
pidots serve --host 0.0.0.0 --port 8000
```

Após iniciar o servidor (`pidots serve --host 0.0.0.0 --port 8000`), todas as superfícies estarão centralizadas na porta `8000`:
- **Apresentação:** `http://localhost:8000/`
- **Console Operacional:** `http://localhost:8000/app` (ou `http://localhost:8000/workspace`)
- **Manual Técnico:** `http://localhost:8000/docs`
- **Relatório de Engenharia:** `http://localhost:8000/relatorio`
- **Verificação de Saúde:** `http://localhost:8000/health`

*Nota sobre a Arquitetura Multi-Porta:* O desacoplamento por portas distintas (8081 Landing, 8082 Workspace, 8083 Docs, 8088 Gateway) é ativado automaticamente ao executar o sistema via **Docker Compose**, através do proxy reverso Nginx Alpine integrado. Na execução nativa direta via Python, o servidor FastAPI gerencia todas as rotas canonicamente na porta 8000.

---

## Interface de Linha de Comando (CLI)

O comando `pidots` gerencia o sistema pelo terminal:

```bash
# Exibir versão instalada
pidots --version

# Exibir sensores térmicos, consumo de RAM e saúde do banco
pidots status

# Listar agentes cadastrados na bancada
pidots dots list

# Subir o servidor para desenvolvimento
pidots serve --host 127.0.0.1 --port 8000

# Inspecionar e resolver ações retidas na fila de segurança
pidots hitl list
pidots hitl approve <ACTION_ID>
pidots hitl reject <ACTION_ID>
```

---

## Utilização como Biblioteca Python (SDK)

Você pode importar o piDots como biblioteca em outros projetos ou ferramentas de terminal:

```python
import asyncio
from pathlib import Path
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.db import init_edge_database, get_db
from pidots.storage.spaces_manager import SpacesManager

async def main():
    # 1. Inicializar o banco de dados SQLite WAL
    await init_edge_database()

    dot_id = "dev-assistant"
    workspace_path = str(Path(settings.workspaces_root) / dot_id)

    # 2. Cadastrar o agente se ainda não existir
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO dots (id, name, role, system_prompt, model, workspace_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dot_id,
                "DevOps Assistant",
                "Operador de Borda",
                "Você é um assistente operacional em hardware restrito.",
                settings.ai_model,
                workspace_path
            )
        )
        await db.commit()

    # 3. Configurar o provedor de inferência
    provider = OpenAIUniversalProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        default_model=settings.ai_model,
    )

    # 4. Instanciar o agente
    agent = DotAgent(
        dot_id=dot_id,
        provider=provider,
    )

    # 5. Salvar documento com controle de versão em Spaces
    doc = await SpacesManager.save_document(
        dot_id=agent.dot_id,
        filename="status_relatorio.txt",
        content="Relatório operacional gerado via SDK oficial do piDots.",
        title="Relatório de Status"
    )
    print(f"Documento versionado: {doc['filename']} (v{doc['version']})")

    # 6. Rodar o ciclo de raciocínio com streaming de eventos
    async for event in agent.run_thread(thread_id="main-thread", user_message="Status dos serviços"):
        if event["event"] == "message:chunk":
            print(event["data"].get("delta", ""), end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Catálogo de Endpoints da API REST

| Método | Endpoint | Finalidade |
| :--- | :--- | :--- |
| `GET` | `/` | Página de apresentação com simulador ReAct e calculadora de silício |
| `GET` | `/app` | Console operacional SPA/PWA (estação de trabalho com teletipo) |
| `GET` | `/workspace` | Alias direto para o console operacional `/app` |
| `GET` | `/docs` | Manual técnico com busca rápida (Ctrl+K) e testador de API |
| `GET` | `/relatorio` | Relatório de testes, consumo e viabilidade de engenharia |
| `GET` | `/api/docs` | Interface OpenAPI interativa para desenvolvedores |
| `GET` | `/api/openapi.json` | Esquema OpenAPI 3.0 estruturado em JSON |
| `GET` | `/health` | Telemetria de hardware (temperatura do SoC, RAM física e estado do SQLite) |
| `GET` | `/manifest.json` | Manifesto PWA para instalação no celular e desktop |
| `GET` | `/sw.js` | Service Worker com cache para carregamento instantâneo |
| `GET` | `/icon.svg` | Logotipo vetorial oficial da plataforma |
| `GET` | `/static/js/core/pidots-i18n.js` | Micro-motor JavaScript de tradução no navegador |
| `GET` | `/data/locales/{lang}.json` | Dicionários de termos em Português e Inglês |
| `GET` | `/api/changelog` | Histórico de atualizações e notas de versão |
| `GET` | `/api/dots` | Lista de agentes cadastrados com papéis e status |
| `GET` | `/api/dots/{id}/export-pack` | Exportação de pacote DotPack v1.1 assinado com SHA-256 |
| `POST` | `/api/dots/import-pack` | Importação de agente com checagem de integridade |
| `POST` | `/api/threads` | Criação de nova conversa |
| `GET` | `/api/threads/{id}/messages` | Histórico de mensagens com remetente e visibilidade |
| `POST` | `/api/threads/{id}/runs` | Execução do agente com streaming SSE (Protocolo AG-UI v1.0) |
| `GET` | `/api/hitl/pending` | Fila de ordens de segurança aguardando aprovação |
| `POST` | `/api/hitl/{id}/resolve` | Aprovação ou veto manual de um comando retido |
| `POST` | `/api/hitl/signed-resolve` | Resolução remota com assinatura HMAC-SHA256 (Telegram/WhatsApp) |
| `POST` | `/api/hitl/webhook-callback` | Retorno assíncrono para resolução remota de segurança |
| `GET` | `/api/mcp/servers` | Status dos servidores MCP externos conectados |
| `GET` | `/api/spaces` | Lista de documentos salvos no espaço de trabalho |
| `POST` | `/api/spaces` | Gravação ou edição de documento com cálculo de diff |
| `GET` | `/api/spaces/{id}` | Conteúdo completo de um documento |
| `GET` | `/api/spaces/{id}/revisions` | Histórico de revisões e diffs de um documento |
| `POST` | `/api/spaces/search` | Busca semântica vetorial em memória (CRC32) |
| `GET` | `/api/spaces/{id}/download` | Download de documento em formato texto |
| `GET` | `/api/workspaces/{dot_id}/export.zip` | Exportação completa dos arquivos do agente em arquivo ZIP |
| `GET` | `/api/tasks` | Lista de tarefas agendadas |
| `POST` | `/api/tasks` | Cadastro de nova tarefa periódica com expressão cron |
| `GET` | `/api/edge/triggers` | Sensores de hardware (temperatura, memória e disco) |
| `POST` | `/api/edge/maintenance` | Disparo manual da manutenção do SQLite (checkpoint WAL e backup) |
| `GET` | `/api/channels` | Lista de canais de discussão em grupo |
| `POST` | `/api/channels` | Criação de novo canal colaborativo |
| `GET` | `/api/channels/{id}/messages` | Mensagens recentes de um canal |
| `POST` | `/api/channels/{id}/messages` | Envio de mensagem com orquestração entre bots |
| `POST` | `/api/channels/{id}/members` | Adição de participante a um canal |
| `POST` | `/api/webhooks/incoming/{dot_id}` | Entrada para mensagens enviadas por APIs externas |
| `POST` | `/api/webhooks/telegram/{dot_id}` | Receptor de webhooks do Telegram Bot |
| `POST` | `/api/webhooks/whatsapp/{dot_id}` | Receptor de webhooks do WhatsApp via Evolution API |
| `GET` | `/api/settings` | Configurações atuais, canais de alerta e modelo ativo |
| `POST` | `/api/settings/ai` | Atualização a quente de chave de API e modelo de IA |
| `POST` | `/api/settings/notifications` | Atualização a quente de canais de notificação |

---

## Atalhos e Navegação por Teclado

### Navegação Direta entre Superfícies
Pressione a tecla `g` seguida da letra de destino:

| Sequência | Destino | Função |
| :--- | :--- | :--- |
| `g` e depois `h` | `/` | Início: Página de apresentação |
| `g` e depois `w` | `/app` | Estação de Trabalho: Console operacional |
| `g` e depois `d` | `/docs` | Manual: Documentação técnica |

### Atalhos no Console Operacional

| Atalho | Ação | Descrição |
| :--- | :--- | :--- |
| `Barra /` | Comandos Rápidos | Abre o menu flutuante com 35 comandos rápidos |
| `Botão [/]` | Menu Touch | Abre o menu de comandos em telas de toque sem abrir o teclado |
| `Alt+1` a `Alt+4` | Activity Rail | Alterna entre painéis contextuais do Activity Rail (Spaces, Agentes, Tarefas, Memória) |
| `Alt+B` / `Ctrl+B` | Ocultar Barra | Oculta ou exibe a barra lateral para ganhar espaço |
| `Alt+I` | Focar Artefato | Foca no documento ativo no Live Canvas |
| `Ctrl+S` | Salvar Versão | Salva uma nova revisão do documento ativo no SQLite |
| `Alt+H` | Fila de Segurança | Abre a lista de comandos retidos para homologação |
| `F11` | Maximizar Canvas | Alterna entre visualização dividida e canvas em tela cheia |
| `Ctrl+L` | Limpar Tela | Limpa o teletipo visual mantendo o histórico salvo no banco |
| `F1` | Ajuda / Sistema | Abre a gaveta lateral com telemetria e manual rápido |

---

## Catálogo de Slash Commands (/)

Comandos iniciados por barra (`/`) rodam direto no console para controle da estação:

| Categoria | Comandos Principais | Exemplos de Uso |
| :--- | :--- | :--- |
| **Sistema & Interface** | `/help`, `/clear`, `/theme`, `/lang`, `/info`, `/status`, `/telemetry`, `/pwa`, `/tour`, `/onboarding`, `/changelog`, `/computer` | `/tour`, `/computer ls -la`, `/telemetry`, `/theme noir` |
| **Agentes & Multi-Bot** | `/dots`, `/handoff`, `/council`, `/delegate`, `/archetype`, `/tools`, `/mcp`, `/coagents` | `/dots`, `/handoff dot-auditor`, `/coagents`, `/mcp` |
| **Memória & Documentos** | `/memory`, `/archival`, `/shared`, `/spaces`, `/diff`, `/save-space` | `/archival SQLite WAL`, `/save-space nota.md`, `/diff` |
| **Tarefas Agendadas** | `/tasks`, `/cron`, `/run-task` | `/tasks`, `/cron listar`, `/run-task task-001` |
| **Segurança & Hardware** | `/hitl`, `/triggers`, `/maintenance`, `/backup` | `/hitl status`, `/triggers`, `/maintenance run` |
| **Exportação de Dados** | `/export`, `/pack` | `/export chat`, `/export canvas`, `/pack dot-dev-core` |

---

## Governança e Segurança

### Aprovação Humana em Tempo Real (HITL)
Comandos com potencial destrutivo (como exclusões recursivas `rm -rf`, alterações de permissões `chmod/chown`, comandos com privilégios `sudo` ou redirecionamento de escrita para arquivos `> / >> / tee`) são interceptados na hora pelo motor de segurança.

A execução é retida no estado pendente. O teletipo exibe o identificador da ordem e você decide se aprova ou veta o comando no console web (`/app` ou `Alt+H`) ou digitando `/hitl`. Comandos seguros de leitura (`ls`, `cat`) ou scripts com descarte rotineiro de mensagens (`2>/dev/null`) rodam de forma autônoma sem interromper seu fluxo de trabalho.

### Isolamento em Jaula Bubblewrap
Para impedir que um script afete arquivos fora do escopo de trabalho, todos os comandos shell rodam dentro de um sandbox Linux Bubblewrap (`bwrap`). O processo roda com namespaces restritos e permissões mínimas, sem acesso a pastas críticas do sistema hospedeiro.

---

## Suíte de Testes Automatizados

O projeto conta com baterias completas de testes para validar integridade, concorrência e ausência de regressões:

```bash
# Infraestrutura e isolamento de processos
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Orquestração multi-bot e poda de ferramentas
python3 scripts/test_phase6_multibot.py

# Agendador proativo e rotinas de silêncio (HEARTBEAT_OK)
python3 scripts/test_phase7_scheduler.py

# Gateway de mensagens e salas temáticas
python3 scripts/test_phase8_messaging.py

# Memória hierárquica e busca vetorial compacta
python3 scripts/test_phase9_memory.py

# Auto-reparo e planejador em dois estágios
python3 scripts/test_phase10_self_healing_planner.py

# Conselho consultivo e revisão em três vias
python3 scripts/test_phase11_council_debate.py

# Quadro compartilhado e pacotes de agentes
python3 scripts/test_phase12_shared_space_dot_packs.py

# Sensores térmicos e manutenção noturna do banco
python3 scripts/test_phase13_edge_triggers_maintenance.py

# Protocolo AG-UI, CoAgents Shared State, Generative UI Inline e eventos de interface
python3 scripts/test_phase1_opendots_agui.py
python3 scripts/test_phase2_opendots_layout.py
python3 scripts/test_phase3_opendots_dynamic_js.py

# Resiliência de conexões e Circuit Breaker
python3 scripts/test_resilience_phases.py

# Roteamento entre portas do proxy Nginx
python3 scripts/test_phase20_port_decoupling_nginx.py
node scripts/test_cross_surface_router.js

# Teste de carga sob alta concorrência
python3 scripts/stress_test.py
```

---

## Licença

Distribuído sob os termos da licença MIT. Consulte o arquivo [LICENSE](LICENSE) para detalhes.

Criado por **lyon christopher** (2026).
