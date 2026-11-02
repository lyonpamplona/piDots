# arquitetura e engenharia de software do pidots

este documento detalha as decisões de engenharia, os padrões arquiteturais, o modelo de concorrência e as otimizações de baixo nível adotadas no **pidots**. o sistema foi concebido especificamente para operar 24 horas por dia em hardware restrito e computadores de placa única (sbcs arm64 / x86_64), tendo o **raspberry pi 4b de 4 gb ram** como bancada física de referência.

---

## 1. visão geral da arquitetura

o pidots foi construído como um **monólito modular assíncrono** (single-process, event-driven). não usamos microsserviços pesados nem enxames de contêineres que consomem gigabytes de memória antes mesmo de receber a primeira requisição. em vez disso, todo o núcleo roda em um único processo gerenciado por fastapi e uvloop/asyncio.

o resultado é previsível e econômico: o sistema sobe em menos de dois segundos, consome menos de 50 mb de ram em repouso e raramente ultrapassa 80 mb durante execuções concorrentes.

```mermaid
flowchart td
    subgraph clientsurfaces["superfícies web e clientes locais"]
        landingclient["landing page client"]
        workspaceclient["console spa/pwa client"]
        docsclient["guia técnico & relatório client"]
        gatewayclient["acessos canônicos legados / redirecionamentos"]
        cli["cli nativa (pidots)\n(terminal local)"]
        webhooks["mensageria externa\n(telegram, whatsapp, webhooks)"]
    end

    subgraph edgeproxy["proxy reverso nginx alpine (< 6 mb ram)"]
        p8081["porta 8081\n(apresentação & simulador)"]
        p8082["porta 8082\n(console workspace spa)"]
        p8083["porta 8083\n(documentação técnica)"]
        p8088["porta 8088\n(gateway canônico 308)"]
    end

    subgraph coreengine["motor principal pidots (fastapi core:8000 + uvloop)"]
        api["camada api rest & sse stream\n(/api/dots, /api/threads, /api/edge/*)"]
        gateway["gateway de mensagens\n(unifiedincomingmessage, channels)"]
        orchestrator["orquestrador multi-bot\n(threadrouter, council, handoff)"]
        scheduler["agendador proativo edgescheduler\n(croniter, edge triggers, heartbeat)"]
        agentengine["motor react (dotagent)\n(tool pruning, auto-reparo)"]
        planner["planejador em dois estágios\n(goals e milestones)"]
        hitl["governança de segurança hitl\n(human-in-the-loop interceptor)"]
        memorymgr["memória hierárquica\n(core, archival fts5, shared space)"]
        toolreg["registro de ferramentas\n(ferramentas nativas de borda)"]
        maintenance["manutenção noturna do banco\n(wal truncate, vacuum into)"]
    end

    subgraph securitystorage["isolamento e persistência sqlite wal"]
        bwrap["sandbox bubblewrap\n(linux namespaces & ro-bind)"]
        sqlite["motor sqlite wal\n(synchronous=normal, busy_timeout=30s, cache=16mb)"]
        spaces["workspaces isolados\n(/workspaces/dot_id)"]
    end

    subgraph external["provedores e rede externa"]
        llm["provedor openai-compatível\n(openai, vllm, litellm)"]
        webtarget["web alvo http/https\n(extração leve trafilatura)"]
    end

    landingclient --> p8081
    workspaceclient --> p8082
    docsclient --> p8083
    gatewayclient --> p8088
    cli --> api
    webhooks --> p8088

    p8081 -->|proxy /api/ & /health| api
    p8082 -->|proxy sse ag-ui & /api/| api
    p8083 -->|proxy /api/ & /health| api
    p8088 -->|proxy completo & redirects 308| api

    api --> agentengine
    api --> maintenance
    gateway --> orchestrator
    orchestrator --> agentengine
    scheduler -->|heartbeat e triggers| agentengine

    agentengine --> hitl
    agentengine --> toolreg
    agentengine --> planner
    agentengine --> memorymgr
    agentengine --> llm

    hitl -->|aprovação requerida| sqlite
    toolreg -->|comando shell| bwrap
    toolreg -->|leitura e gravação| spaces
    toolreg -->|extração web| webtarget
    toolreg -->|delegação de subtarefa| orchestrator

    agentengine --> sqlite
    scheduler --> sqlite
    gateway --> sqlite
    spaces --> sqlite
    memorymgr --> sqlite
    maintenance --> sqlite
```

---

## 2. ciclo de execução react e intercepção de segurança

o agente opera sob o padrão react (*reasoning and acting*) com streaming contínuo. ele pensa, decide qual ferramenta usar e avalia o risco da operação antes de disparar qualquer comando no sistema operacional.

se o comando for seguro (como ler um arquivo ou buscar uma memória), a execução ocorre de forma autônoma. se o comando apresentar risco de corrupção ou invasão de privilégios (como comandos com `sudo`, `rm -rf`, `chmod` ou redirecionamento de escrita em disco), a execução é retida imediatamente para aprovação do operador humano.

```mermaid
sequencediagram
    autonumber
    actor operador as operador / ui
    participant agent as motor react (dotagent)
    participant llm as provedor de inferência
    participant hitl as interceptor de segurança
    participant tool as ferramenta (bash/file)
    participant db as sqlite wal

    operador->>agent: mensagem / instrução de tarefa
    agent->>db: carregar histórico recente e memórias arquivais
    agent->>llm: disparar requisição de inferência (streaming)
    llm-->>agent: tokens de resposta (raciocínio e intenção de ferramenta)
    agent-->>operador: streaming de eventos sse no teletipo
    
    alt invocação de ferramenta segura (ex: read_file, search_memory)
        agent->>tool: executa a ação diretamente no sandbox
        tool-->>agent: retorno da ferramenta
        agent->>llm: envia resultado para a próxima etapa de raciocínio
    else invocação de ação de alto risco (ex: rm -rf, sudo, chmod)
        agent->>hitl: avalia comando e classifica risco
        hitl->>db: registra ordem pendente em hitl_approvals (ttl: 30 min)
        hitl-->>agent: retém a execução na fila de segurança
        agent-->>operador: alerta de governança pendente (id de aprovação)
        
        note over operador,hitl: aguarda deliberação humana
        operador->>hitl: post /api/hitl/{id}/resolve (aprovar / vetar)
        hitl->>tool: desbloqueia e executa comando no sandbox bubblewrap
        tool-->>agent: retorno da execução
        agent->>llm: continua o raciocínio com o resultado homologado
    end

    agent->>db: grava mensagens e telemetria no banco
    agent-->>operador: ciclo de execução concluído
```

---

## 3. máquina de estados da aprovação humana (hitl)

a governança segue o princípio de recusa padrão (*deny-by-default*). o sistema não confia cegamente no modelo para executar comandos arriscados.

```mermaid
statediagram-v2
    [*] --> avaliaçãorisco: chamada de ferramenta
    
    avaliaçãorisco --> execuçãodireta: comando seguro (leitura / consulta)
    avaliaçãorisco --> retidohitl: comando de risco detectado
    
    retidohitl --> aguardandoaprovação: registrado em hitl_approvals (ttl: 30 min)
    
    aguardandoaprovação --> execuçãoautorizada: operador aprova (/api/hitl/{id}/resolve)
    aguardandoaprovação --> abortadorejeitado: operador veta (/reject)
    aguardandoaprovação --> expiradotimeout: ttl excedido (> 30 min) -> status expired
    
    execuçãodireta --> [*]: devolve resultado ao agente
    execuçãoautorizada --> [*]: executa e devolve resultado
    abortadorejeitado --> [*]: retorna erro de recusa humana
    expiradotimeout --> [*]: libera thread para ocioso e registra auditoria
```

- **prazo de validade de 30 minutos:** cada solicitação recebe a coluna `expires_at`. se você se ausentar da bancada e não homologar o comando em 30 minutos, a ordem expira por segurança. a thread volta ao estado ocioso e o banco registra o cancelamento.
- **abertura automática de painel:** quando uma ação é retida, o servidor emite os eventos sse `hitl:pending_approval` e `hitl:approval_required`. o console web abre a gaveta de aprovações (`alt+h`) automaticamente.

---

## 4. otimizações de i/o e sqlite para cartão microsd e ssd

computadores como o raspberry pi 4b costumam usar cartões microsd como armazenamento principal. a escrita síncrona contínua com chamadas `fsync()` constantes degrada a performance do sistema e esgota rapidamente a vida útil das células de memória flash.

para proteger o hardware, a camada de dados do pidots configura o sqlite em modo **write-ahead logging (wal)** com diretivas específicas:

```sql
-- permite leitura e escrita simultâneas sem bloqueios no loop assíncrono
pragma journal_mode = wal;

-- substitui o fsync completo por sincronização segura nos checkpoints periódicos
-- poupa a vida útil do cartão microsd sem comprometer a integridade dos dados
pragma synchronous = normal;

-- aloca 16 mb de memória ram para cache de páginas (calibrado para o teto de 384 mb de ram)
-- consultas frequentes a mensagens e índices rodam direto na memória
pragma cache_size = -16000;

-- habilita memória mapeada (mmap) de até 64 mb para leituras ultra-rápidas no kernel linux arm64
pragma mmap_size = 67108864;

-- dispara checkpoint automático do wal a cada 1.000 páginas escritas (aprox. 4 mb)
-- evita o crescimento descontrolado do arquivo .db-wal no disco
pragma wal_autocheckpoint = 1000;

-- aguarda até 30.000 ms em transações concorrentes antes de acusar erro de lock
-- absorve picos de latência de escrita no barramento do cartão microsd
pragma busy_timeout = 30000;

-- mantém tabelas temporárias e ordenações transitórias na memória ram (tmpfs)
pragma temp_store = memory;

-- enforça integridade referencial nas tabelas relacionais do sqlite
pragma foreign_keys = on;
```

---

## 5. estrutura modular do sistema

o monólito organiza suas responsabilidades em módulos coesos dentro da pasta `pidots/`:

### 5.1 orquestração multi-bot (`pidots/core/orchestrator.py`)
coordena múltiplos especialistas locais sem sair do mesmo processo assíncrono:
- o `threadrouter` extrai menções `@nome_do_dot` com expressões regulares, valida se os agentes existem no sqlite e define os interlocutores da conversa.
- o `multibotorchestrator.delegate_subtask()` gerencia subtarefas. o supervisor chama o especialista em uma thread secundária isolada (`subtask-{handoff_id}`), mantendo a tela principal limpa. o resultado consolidado retorna para a conversa do operador com visibilidade interna de diagnóstico.
- se a execução do worker falhar, o orquestrador marca a subtarefa como `failed` na tabela `agent_handoffs`, grava o alerta técnico no banco e retorna um dicionário estruturado para que o supervisor tente outra abordagem.
- o método `handoff_lead()` transfere a liderança da conversa para outro especialista quando a tarefa mudar de área técnica.

### 5.2 agendador proativo dot heartbeat (`pidots/core/scheduler.py`)
elimina filas externas como celery ou rabbitmq, rodando tarefas agendadas em segundo plano:
- o `edgescheduler` interpreta expressões cron com a biblioteca `croniter` e calcula a próxima execução (`next_run_at`) no sqlite.
- o loop perpétuo de verificação roda a cada 15 segundos dentro do lifespan do fastapi.
- a diretriz `heartbeat_ok` instrui o modelo a responder apenas essa frase quando tudo estiver normal. o agendador marca o ciclo como silencioso e não gera notificações desnecessárias.
- travas em memória (`_running_tasks`) impedem que tarefas longas disparem em duplicidade se a resposta da ia demorar mais de 15 segundos.
- um circuit breaker com recuo progressivo protege o sistema contra falhas sucessivas. o tempo de espera sobe de 30 segundos até 1 hora. na 5ª falha consecutiva, o circuito abre e suspende a tarefa para não desperdiçar recursos.

### 5.3 gateway de mensagens e salas temáticas (`pidots/core/messaging_gateway.py`)
centraliza as conexões com plataformas de mensagens sem manter estado:
- utiliza o modelo normalizado `unifiedincomingmessage` para mensagens do telegram, whatsapp (evolution api) e webhooks genéricos.
- a integração com a evolution api usa chamadas httpx assíncronas para enviar mensagens de volta, simulando digitação sem travar a thread do servidor.
- as salas temáticas da tabela `channels` permitem discussões entre vários agentes e usuários humanos.
- para evitar loops infinitos entre bots, o gateway impõe um limite máximo de 3 repasses (`hop_count <= 3`), exige menção direta para que um bot responda a outro e instrui respostas vazias (`no_action`) quando não houver acréscimo relevante.

### 5.4 exportação de workspaces (`pidots/storage/spaces_manager.py`)
cuida do histórico de arquivos e exportação em lote:
- ao gerar o arquivo compactado (`export_workspace_zip`), o motor reúne os arquivos físicos da pasta `/workspaces/{dot_id}` e os documentos salvos na tabela `spaces` do sqlite.
- arquivos que ainda estejam apenas na base de dados são gravados diretamente no buffer zip em memória, garantindo que o arquivo baixado nunca venha vazio.

### 5.5 notificador de segurança (`pidots/core/notifier.py`)
despacha alertas de governança para webhooks http e bots do telegram. mantém compatibilidade com versões anteriores através do alias `notifier = hitlnotifier`.

### 5.6 memória hierárquica em três níveis (`pidots/storage/memory_manager.py`)
- **core memory:** blocos de memória viva injetados no system prompt (`human`, `persona`, `active_context`). cada bloco possui um limite rígido de 2.000 caracteres para evitar overflow de tokens.
- **archival memory híbrida:** documentos e regras duradouras salvos na tabela `archival_memories`. triggers sql automáticos alimentam o índice fts5 (busca bm25). a busca híbrida combina pontuação textual com projeção vetorial compacta de 64 dimensões gerada por hash de trigramas em python puro.
- **recall memory:** busca retrospectiva em conversas anteriores da mesma thread através de consultas rápidas na tabela `messages`.

### 5.7 auto-reparo de código (`pidots/core/self_healing.py`)
analisa a saída de comandos de terminal e scripts python. ao detectar uma falha ou traceback, ele isola o arquivo violado, o número da linha e o tipo de erro, sugerindo uma correção direta através da ferramenta `execute_and_verify`. a rotina possui um teto de 2 tentativas para evitar ciclos repetitivos de correção.

### 5.8 planejamento em dois estágios (`pidots/core/planner.py`)
organiza metas amplas na tabela `goals` e passos detalhados na tabela `milestones`. conforme o agente avança e comprova os resultados, ele atualiza o status de cada marco, recalculando a porcentagem de progresso dentro do bloco xml `<execution_plan>`.

### 5.9 conselho de revisão técnica (`pidots/core/council.py`)
reúne três especialistas antes de tarefas críticas: o coder propõe a solução, o auditor analisa riscos de segurança e estabilidade, e o supervisor sintetiza o resultado final. o debate é limitado a no máximo 3 rodadas e opera dentro de 53 mb de ram. se o auditor aprovar a proposta logo na segunda rodada, o orquestrador encerra a deliberação antecipadamente para economizar tempo e tokens.

### 5.10 quadro de anotações compartilhado (`pidots/storage/shared_space.py`)
área de anotações compartilhada entre bots de uma mesma conversa (`thread_shared_notes`). as notas são organizadas por tópicos e repassadas a todos os participantes no bloco xml `<shared_knowledge_space>`.

### 5.11 pacotes portáteis de agentes (`pidots/core/dot_pack.py`)
manifestos json padronizados (dot packs v1.1) contendo a persona, ferramentas, arquivos e memórias do agente, acompanhados de um hash criptográfico `sha-256`. o instalador confere o hash e inspeciona o prompt contra técnicas de injeção antes de cadastrar o agente.

### 5.12 triggers de hardware e sensores físicos (`pidots/core/edge_triggers.py`)
monitora os sensores térmicos do processador broadcom bcm2711 via sysfs (`/sys/class/thermal/thermal_zone0/temp`), além do espaço em disco e da ram livre. lê pinos gpio físicos no raspberry pi e recebe telemetria de sensores locais via mqtt, disparando alertas se a placa aquecer além de 72 °c.

### 5.13 roteamento modular da api (`pidots/api/`)
o arquivo `main.py` gerencia o ciclo de vida e middlewares da aplicação. as rotas ficam organizadas em sub-roteadores especializados:
- `routes_dots.py`: catálogo de agentes e importação/exportação de pacotes dotpack.
- `routes_hitl.py`: fila de aprovação humana e resolução remota com assinatura hmac-sha256.
- `routes_threads.py`: sessões de conversa e streaming sse no protocolo ag-ui.
- `routes_tasks.py`: tarefas agendadas cron, gerenciamento de spaces e exportação zip.
- `routes_channels.py`: salas temáticas de discussão colaborativa.
- `routes_webhooks.py`: recepção de mensagens externas do telegram e whatsapp.
- `routes_edge.py`: telemetria de hardware (`/health`), sensores térmicos e configurações a quente.
- `routes_pwa.py`: entrega de assets estáticos, manifesto pwa, ícones em memória ram e service worker.

### 5.14 isolamento com bubblewrap (`pidots/tools/terminal.py`)
executa comandos em sandbox linux bubblewrap (`bwrap`), montando `/usr`, `/bin` e `/lib` em modo somente leitura e isolando a árvore de processos. se a variável `strict_sandbox=true` estiver definida e o binário `bwrap` não for encontrado, o comando é bloqueado com erro 126. a saída de texto tem um teto de 10 kb para proteger a memória ram.

### 5.15 cliente mcp lite (`pidots/tools/mcp_client.py`)
conecta servidores mcp externos leves via stdio ou sse/http em python puro, consumindo menos de 5 mb de ram. as ferramentas importadas passam compulsoriamente pela lista de permissões de cada agente.

### 5.16 validação criptográfica de aprovações (`pidots/core/hitl_crypto.py`)
gera e valida assinaturas hmac-sha256 em tempo constante para aprovações enviadas a smartphones, impedindo manipulações ou acessos forjados.

---

## 6. modelagem de dados no sqlite wal

o banco de dados sqlite organiza o estado da estação em tabelas relacionais eficientes:

| tabela | finalidade | chaves principais |
| :--- | :--- | :--- |
| `thread_participants` | rastreia os agentes presentes em cada conversa | `thread_id`, `dot_id`, `is_speaker` |
| `agent_handoffs` | registra delegações de tarefas e transferências de comando | `id`, `thread_id`, `source_dot_id`, `target_dot_id`, `status` |
| `goals` | metas gerais de longo prazo | `id`, `dot_id`, `thread_id`, `title`, `status` |
| `milestones` | marcos sequenciais verificáveis de cada meta | `id`, `goal_id`, `order_index`, `title`, `status` |
| `episodic_memories` | resumos estruturados de conversas anteriores | `id`, `dot_id`, `summary`, `key_decisions` |
| `scheduled_tasks` | rotinas periódicas agendadas (dot heartbeat) | `id`, `dot_id`, `cron_expr`, `next_run_at`, `consecutive_failures` |
| `channels` | salas temáticas de discussão em equipe | `id`, `name`, `description`, `created_at` |
| `channel_messages` | mensagens trocadas nas salas temáticas com contador de saltos | `id`, `channel_id`, `author_id`, `content`, `hop_count` |
| `channel_members` | participantes inscritos em cada sala (bots ou humanos) | `channel_id`, `member_id`, `joined_at` |

### índices de consulta rápida para microsd
para garantir respostas em menos de 5 milissegundos mesmo no barramento de cartões de memória:
```sql
create index if not exists idx_participants_thread on thread_participants(thread_id);
create index if not exists idx_handoffs_thread on agent_handoffs(thread_id, status);
create index if not exists idx_milestones_goal on milestones(goal_id, order_index);
create index if not exists idx_tasks_due on scheduled_tasks(is_active, next_run_at, backoff_until);
create index if not exists idx_channel_msgs on channel_messages(channel_id, created_at);
create index if not exists idx_channel_members on channel_members(channel_id);
```

---

## 7. arquétipos de agentes e poda de ferramentas

### perfis de atuação
os coworkers cadastrados seguem especializações bem definidas:
- **`dot-supervisor`:** visão estratégica, organização de etapas de trabalho e síntese executiva. identificador: `[spv]`.
- **`dot-coder`:** engenharia de software, depuração de erros, execução de comandos no sandbox e validação de testes. identificador: `[cdr]`.
- **`dot-muse`:** modelagem de sistemas, documentação técnica estruturada, especificação de apis e síntese criativa. identificador: `[mus]`.
- **`dot-auditor`:** segurança operacional, integridade de comandos shell, controle térmico e conformidade de governança. identificador: `[aud]`.

### poda dinâmica de ferramentas (dynamic tool pruning)
enviar dezenas de definições de ferramentas json a cada chamada desperdiça tokens e causa lentidão na borda. no pidots, cada agente carrega apenas as ferramentas autorizadas na coluna `allowed_tools_json`. o coder recebe ferramentas de terminal e arquivos; o supervisor recebe ferramentas de planejamento e delegação. essa restrição reduz em mais de 75% o volume de tokens e impede que o agente invente comandos inexistentes.

---

## 8. isolamento de processos com bubblewrap (`bwrap`)

para garantir segurança sem o peso de máquinas virtuais ou contêineres aninhados (docker-in-docker), o pidots usa o bubblewrap nativo do linux:
1. **isolamento de namespaces:** o processo roda em namespaces isolados de montagem de arquivos (`clone_newns`), processos (`clone_newpid`), ipc (`clone_newipc`) e hostname (`clone_newuts`).
2. **sistema de arquivos em modo leitura:** pastas críticas do sistema (`/bin`, `/usr`, `/lib`, `/etc`) são montadas como somente leitura (`--ro-bind`).
3. **pasta de trabalho restrita:** o único local com permissão de escrita é o diretório atribuído ao agente (`--bind {workspaces_root}/{dot_id} /workspace`).
4. **encerramento automático:** a flag `--die-with-parent` assegura que processos filhos sejam finalizados imediatamente caso o processo principal seja interrompido.

### 8.1 orçamento de silício e limites de contêineres (docker compose)

além do sandbox de processos isolados bubblewrap, a infraestrutura define tetos rígidos via cgroups para impedir que o processo consuma todo o raspberry pi 4b:

| serviço | contêiner | limite cpu | reserva cpu | limite ram | reserva ram | montagens especiais |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **fastapi core** | `pidots-core` | `1.2 cores` | `0.2 cores` | `384 mb` | `64 mb` | `tmpfs: /tmp (64 mb, nosuid)` |
| **nginx proxy** | `pidots-nginx` | `0.25 cores` | `0.05 cores` | `32 mb` | `8 mb` | `volumes: estáticos ro` |

a montagem do `/tmp` em memória volátil (`tmpfs: size=64m, nosuid`) assegura que arquivos transitórios e escritas temporárias nunca degradem as células flash do cartão microsd.

---

## 9. busca vetorial leve com hash crc32

bancos vetoriais convencionais exigem runtimes volumosos e dependências em c++/rust que consomem centenas de megabytes de memória.

o pidots resolve a busca semântica com uma abordagem compacta:
- o texto é decomposto em n-gramas e projetado em vetores esparsos através de funções de hashing crc32 calculadas na cpu arm64 em microssegundos.
- a similaridade de cosseno é calculada diretamente sobre os vetores gravados no sqlite.
- o consumo total de memória ram é menor que **5 mb**, dispensando bibliotecas pesadas de tensores.

---

## 10. leitura web assíncrona com trafilatura

em vez de subir instâncias completas de navegadores headless (como chromium ou playwright, que consomem mais de 500 mb de ram), o pidots usa o cliente http assíncrono `httpx` combinado com a biblioteca **trafilatura**.

o extrator analisa a estrutura html em python puro na cpu, descarta propagandas, scripts e estilos visuais, e devolve apenas o texto útil. o consumo de memória cai de 500 mb para cerca de 20 mb por página consultada.

---

## 11. concorrência assíncrona e gestão de silício

- o servidor roda em uma única thread com loop de eventos assíncrono (`asyncio + uvloop`).
- leituras demoradas de disco ou execuções de comandos no sandbox são despachadas com `asyncio.to_thread` ou `create_subprocess_exec`, mantendo o loop livre para atender requisições web e transmissões sse.
- o sistema monitora constantemente a memória residente (rss) e a carga de cpu através do `psutil`.

---

## 12. arquitetura de interface e ergonomia mobile

as telas do pidots combinam a alta densidade de consoles técnicos clássicos com suporte ergonômico para dispositivos móveis:

### roteamento entre superfícies

| superfície | porta nginx | rota canônica | finalidade |
| :--- | :--- | :--- | :--- |
| **landing page** | `8081` | `get /` | apresentação da estação, simulador react e calculadora de silício |
| **console operacional** | `8082` | `get /app` | estação de trabalho spa/pwa com teletipo e live canvas |
| **alias de trabalho** | `8082` | `get /workspace` | apelido direto para o console operacional `/app` |
| **manual técnico** | `8083` | `get /docs` | documentação técnica com busca ctrl+k e testador de api |
| **relatório técnico** | `8083` | `get /relatorio` | relatório de testes de carga e validação técnica |
| **gateway unificado** | `8088` | `get /*` | roteador canônico retrocompatível com redirecionamentos http 308 |
| **backend core** | `8000` | `get /api/*` | api rest e sse assíncrono interno fastapi |
| **openapi swagger ui** | `8088` / `8000` | `get /api/docs` | interface swagger nativa para desenvolvedores |
| **esquema openapi json** | `8088` / `8000` | `get /api/openapi.json` | contrato openapi 3.0 estruturado |
| **dicionários i18n** | todas | `get /data/locales/{lang}.json` | termos traduzidos em português e inglês |
| **micro-motor tradução** | todas | `get /static/js/core/pidots-i18n.js` | motor de tradução client-side em javascript puro |
| **changelog** | `8088` / `8000` | `get /api/changelog` | notas de atualização semver da plataforma |
| **service worker** | `8082` | `get /sw.js` | cache defensivo para carregamento imediato |

### navegação por teclado e atalhos rápidos
- pressionar `g` seguido de `h` abre a página inicial (`/`).
- pressionar `g` seguido de `w` abre a estação de trabalho (`/app`).
- pressionar `g` seguido de `d` abre o manual técnico (`/docs`).

se o operador estiver digitando em um campo de texto ou na caixa de busca, esses atalhos são desativados automaticamente para não interromper a escrita.

### adaptação para telas de celular
em telas com largura igual ou inferior a 768px:
- a barra inferior fixa traz 4 botões de toque com tamanho mínimo de 44x44 pontos: `[o] dots`, `[>] chat`, `[*] canvas` e `[?] guia`.
- o botão físico touch `[/]` permite abrir o catálogo de comandos sem precisar subir o teclado virtual.
- o sistema escuta a api `window.visualviewport`. quando o teclado virtual abre, a barra inferior é recolhida e a caixa de digitação se ajusta na tela, impedindo que o campo fique escondido.
- os campos de texto utilizam tamanho fixo de 16px para evitar que o navegador safari execute zoom compulsório na tela.

### 12.4 especificação arquitetural: design system pixel paper ui

o visual do pidots adota o paradigma **pixel paper ui**, unindo a materialidade tátil de relatórios de teletipo e papel milimetrado com a precisão geométrica do retro-computing de 1-bit. a interface foi calibrada para renderização imediata sem repaints dispendiosos no hardware modesto do raspberry pi 4b:

1. **paleta dark paper noir:**
   - superfície base: `--paper-noir-base: #07090c` (preto carvão fosco de teletipo).
   - superfície contínua: `--paper-surface-sheet: #0b0e12` (folha de formulário contínuo).
   - superfície de cartões: `--paper-surface-card: #11161d` (fichas catalográficas).
   - superfície elevada: `--paper-surface-elevated: #182029` (modais e gavetas).
   - superfície rebaixada: `--paper-surface-recessed: #040608` (terminais afundados).
2. **geometria ortogonal estrita (0px border radius):**
   - todos os componentes utilizam raio de curvatura nulo (`--radius-xs: 0px`, `--radius-sm: 0px`, `--radius-md: 0px`, `--radius-lg: 0px`).
   - eliminação total de cantos arredondados para garantir estética de fichas catalográficas e economizar ciclos de rasterização da gpu.
3. **sombras cartesianas sem difusão (blur-free):**
   - proibição de sombras gaussianas difusas (`var(--shadow*)`).
   - sombras puramente projetadas com deslocamento cartesiano rígido: `box-shadow: 2px 2px 0px #000000;`, `3px 3px 0px #000000;` e `4px 4px 0px #000000;`.
4. **dual-typography de baixa latência:**
   - **cabeçalhos e rótulos retro-técnicos:** tipografia pixelada monoespaçada `silkscreen` (`--font-pixel-head`).
   - **dados, código e fluxo de teletipo:** `jetbrains mono` (`--font-mono-data`) com `font-variant-numeric: tabular-nums` para alinhamento perfeito de colunas numéricas e barras ascii de telemetria.
5. **renderização vetorial 1-bit crisp e dither procedural:**
   - todos os elementos svg contêm a diretiva compulsória `shape-rendering="crispedges"`.
   - elementos gráficos de hardware empregam textura pontilhada matricial gerada via svg procedural (`#bayerrampattern`).
6. **microinterações mecânicas em degraus:**
   - animações fluidas `ease-in-out` e transformações de escala `scale()` são banidas.
   - transições de estado operam em degraus rígidos via `steps(1)` ou `steps(2)`, reproduzindo o comportamento mecânico de relés físicos e impressoras de impacto.
7. **artefatos de papel técnico:**
   - `.paper-slip`: ficha catalográfica de mensagem com chanfro técnico (`clip-path: polygon`).
   - `.tractor-holes` / `.tractor-feed`: fita perfurada de margem contínua na bobina de teletipo.
   - `.picote-line`: separador serrilhado para destacar blocos de execução.
   - `.pixel-rubber-stamp`: carimbo analógico com textura radial para status de governança hitl.

---

## 13. resiliência de conexões e circuit breakers

a operação contínua 24/7 em hardware de borda exige que falhas de rede e limites de taxa de provedores de ia sejam tratados sem travar o servidor.

```mermaid
flowchart td
    req["requisição de inferência via httpx"] --> codecheck{"código http retornado"}
    
    codecheck -->|http 200| ok["sucesso (resposta normal)"]
    codecheck -->|http 401 / 403| autherr["providerautherror\n(interrupção imediata sem retentativas)"]
    codecheck -->|http 502 / 503 / 504 / 429| retrycheck{"tentativas restantes?"}
    codecheck -->|timeout / erro de rede| retrycheck
    
    retrycheck -->|sim| backoff["espera com jitter aleatório\n(asyncio.sleep)"] --> req
    retrycheck -->|não| transerr["providertransienterror\n(falha temporária confirmada)"]
```

erros definitivos de autenticação encerram o ciclo na hora, sem gastar energia com retentativas inúteis. erros de rede ou sobrecarga acionam até 3 tentativas com tempos progressivos e variação aleatória.

se a execução falhar, o evento final `run:finished` reporta o erro detalhado. o diagnóstico é registrado no banco com visibilidade interna para auditoria técnica posterior, sem poluir a tela do usuário.

---

## 14. entrega em quatro portas com proxy nginx

para que o servidor fastapi concentre toda a sua capacidade de processamento no raciocínio dos agentes e no banco sqlite, o serviço `pidots-nginx` assume a entrega dos arquivos estáticos consumindo menos de 6 mb de ram:

```mermaid
flowchart lr
    subgraph wan["acesso externo / túneis"]
        cf_landing["pidots.seu-dominio.com"]
        cf_app["app.seu-dominio.com"]
        cf_docs["docs.seu-dominio.com"]
    end

    subgraph tunneldaemon["raspberry pi 4b (cloudflared)"]
        cftunnel["daemon cloudflared\n(conexão quic segura)"]
    end

    subgraph nginxproxy["nginx alpine (< 6 mb ram)"]
        p8081["porta 8081\n(apresentação)"]
        p8082["porta 8082\n(console spa)"]
        p8083["porta 8083\n(manual técnico)"]
        p8088["porta 8088\n(gateway canônico)"]
    end

    subgraph corebackend["fastapi core (porta 8000)"]
        coreapi["fastapi uvloop\n(react + sqlite wal)"]
    end

    cf_landing --> cftunnel
    cf_app --> cftunnel
    cf_docs --> cftunnel

    cftunnel -->|http://localhost:8081| p8081
    cftunnel -->|http://localhost:8082| p8082
    cftunnel -->|http://localhost:8083| p8083

    p8081 -->|/api/| coreapi
    p8082 -->|/api/ (streaming sse)| coreapi
    p8083 -->|/api/| coreapi
    p8088 --> coreapi
```

as portas locais se dividem de forma clara:
- porta `8081`: apresentação e visão geral.
- porta `8082`: console operacional de trabalho (spa/pwa).
- porta `8083`: manual técnico e especificações.
- porta `8088`: gateway de rotas com redirecionamentos automáticos.
- porta `8000`: backend fastapi interno dedicado.

o script `cross-surface-router.js` detecta se o acesso vem de portas locais, da rede lan ou de subdomínios externos, garantindo que os links e atalhos de navegação funcionem de forma transparente em qualquer ambiente.

---

## 22. padrão opendots & copilotkit coagents / ag-ui protocol (v1.5.3)

a arquitetura do pidots integra os paradigmas do ecossistema **copilotkit/opendots** e do protocolo **ag-ui / coagents** diretamente no monolito modular e no visual **pixel paper ui** do console `/app`:

### 22.1 activity rail lateral e 4 painéis contextuais
- **activity rail (48px):** barra vertical esquerda inspirada no padrão opendots, permitindo alternância instantânea entre 4 painéis operacionais sem recarregar a página:
  1. `[spaces]`: canais multi-bot (`#channel`), tópicos em árvore (`threads`) e documentos versionados (`spaces`) com busca em tempo real.
  2. `[dots]`: squad de agentes especialistas com criação e edição ao vivo via modal `#pixeldotcreatormodal` e matriz visual de *dynamic tool pruning* (`allowed_tools_json`).
  3. `[tasks]`: rotinas autonomas agendadas (cron / heartbeat) com disparo imediato (`post /api/tasks/{id}/run`) e toggle ativo/pausado (`patch /api/tasks/{id}/toggle`).
  4. `[mem/mcp]`: busca híbrida rrf (fts5 bm25 + vetor 64d) e gerenciamento de servidores mcp lite (`get/post /api/edge/mcp/servers`).

### 22.2 generative ui inline e hitl com edição de argumentos (`modified_args`)
- **generative ui cards (`.gen-ui-card`):** eventos sse do protocolo ag-ui (`tool_call:start`, `tool_call:result`, `artifact:updated`) sao renderizados como fichas catalográficas colapsáveis diretamente na fita do teletipo, exibindo status `[executando...]`, tempo de execução em milissegundos e payload formatado.
- **interrupt-resume com `modified_args`:** quando o guardião hitl intercepta uma ação crítica, o operador pode editar os argumentos json no cartão inline ou no dossiê hitl e enviar `modified_args` para `post /api/hitl/{id}/resolve`. o motor `dotagent.resume_after_hitl()` injeta os argumentos corrigidos e retoma o loop react sem perder o contexto da conversa.

### 22.3 coagents shared state (`state_snapshot` e `state_delta`) e computador do dot
- **estado compartilhado bidirecional:** o motor emite `state:snapshot` no início de cada turno e `state:delta` a cada transição de nó cognitivo (`router -> thinker -> tool_executor -> verifier -> responder`), sincronizando a aba `[coagents]` em tempo real e aceitando overrides manuais via `patch /api/threads/{id}/state`.
- **computador do dot (`dot's computer`) e modo takeover:** o painel direito unifica terminal sandbox (`post /api/edge/computer/exec`), navegador de arquivos de workspace (`get /api/edge/computer/files`), editor de artefatos, coagents state e telemetria termica, contando com **modo takeover** para execução manual direta pelo operador humano.

