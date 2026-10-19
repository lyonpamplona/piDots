# piDots — Manual Operacional e Guia de Produção 24/7

**Projeto:** piDots (Motor Otimizado de AI Coworkers Persistentes para Hardware de Borda)  
**Autor e Criador:** lyon christopher  
**Assistente:** Logger  
**Ambiente Alvo:** Computacao de Borda e SBCs (Benchmark de Referencia: Raspberry Pi 4B 4GB RAM, ARM64 Cortex-A72, Linux / Docker Compose)  
**Versão:** 1.5.3 (Produção Estável — Padrão OpenDots Workspace, CoAgents Shared State, Generative UI Cards, Computador do Dot e HITL Interrupt-Resume)  

---

## 1. Visão Geral da Arquitetura

O **piDots** é uma reengenharia radical de arquiteturas corporativas de IA voltada para hardware restrito de borda. Enquanto frameworks tradicionais de mercado demandam de 1,8 GB a 3,2 GB de memória RAM (dependência pesada de Node.js SSR, Chromium headless contínuo e múltiplos contêineres efêmeros), o piDots foi estruturado como um monólito modular assíncrono em Python com `uvloop`, FastAPI e persistência SQLite WAL calibrada.

### Principais Indicadores de Recursos:
- **Consumo Médio de Memória RAM:** ~50 MB (limite estrito de 384 MB no contêiner, com reserva operacional de 64 MB).
- **Carga de CPU em Ociosidade:** < 0.3% em 1 núcleo ARM Cortex-A72.
- **I/O em Disco Flash (MicroSD):** Zero fsync contínuo, gravações append-only em WAL e `/tmp` em memória volátil (`tmpfs`).
- **Throughput Medido:** 88+ requisições/segundo com latência mediana (p50) de 72 ms.

---

## 2. Comandos Operacionais de Ciclo de Vida

O piDots opera dentro do contêiner Docker `pidots-core` orquestrado pelo Docker Compose.

### 2.1 Iniciar o Serviço em Segundo Plano
```bash
cd /mnt/storage/piDots
docker compose up -d
```

### 2.2 Verificar o Status de Saúde e Recursos
```bash
# Estado e tempo de atividade
docker compose ps

# Consumo de memória, CPU e I/O em tempo real
docker stats --no-stream pidots-core
```

### 2.3 Visualização e Acompanhamento de Logs
Os logs possuem rotação automática configurada (máximo de 2 arquivos de 5 MB cada) para evitar esgotamento de espaço em disco.
```bash
# Acompanhamento de logs em tempo real
docker compose logs -f --tail=100 pidots-core
```

### 2.4 Reinicialização Controlada
```bash
docker compose restart pidots-core
```

### 2.5 Parada do Serviço
```bash
docker compose down
```

---

## 3. Governança e Human-in-the-Loop (HITL)

O piDots aplica a política **Deny-by-Default** para qualquer ação potencialmente destrutiva disparada por um agente.

### 3.1 Classificação de Risco
- **LOW:** Comandos de leitura e consultas seguras (`ls`, `cat`, `python3 script.py`) e comandos com descarte inofensivo de erros (`2>/dev/null`, `2>&1`, `>/dev/null`). Execução liberada de forma autônoma sem travar o operador.
- **MEDIUM:** Operações com redirecionamento real de escrita para arquivos em disco (`> arquivo`, `>> arquivo`, `tee`).
- **HIGH:** Exclusão de arquivos (`file_delete`), criação de skills persistentes.
- **CRITICAL:** Comandos shell perigosos (`rm -rf`, `mkfs`, `dd`, `chmod`, `sudo`, `curl | bash`, `reboot`, `shutdown`). A execução é **imediatamente bloqueada** até a decisão do operador.

### 3.2 Transparência no Teletipo e Notificação no Chat
Ao reter uma ação para governança HITL (`awaiting_hitl`), o motor do piDots grava automaticamente uma mensagem explicativa de papel `assistant` na thread ativa do SQLite WAL:
```text
[GOVERNANCA HITL // ACAO RETIDA]
O agente '<dot_id>' solicitou a acao '<tool_name>' (Risco: <risk>), que requer autorizacao expressa do operador humano.
ID de Aprovacao: <approval_id>
Instrucao: Homologue a execucao na aba de governanca HITL ou via comando /hitl.
```
Isso elimina o silêncio aparente do chat e orienta o operador de forma transparente.

### 3.3 Resolução de Solicitações HITL
As solicitações podem ser resolvidas de três formas:
1. **Pelo Console Web SPA:** No cartao interativo de governanca acessivel no Console Operacional (`GET /app`, `/workspace` ou pelo atalho `Alt+H`).
2. **Via API REST:**
   ```bash
   curl -X POST http://localhost:8000/api/hitl/<APPROVAL_ID>/resolve \
     -H "Content-Type: application/json" \
     -d '{"approved": true, "notes": "Aprovado pelo operador"}'
   ```
3. **Via Webhook Remoto:**
   ```bash
   curl -X POST http://localhost:8000/api/hitl/webhook-callback \
     -H "Content-Type: application/json" \
     -d '{"approval_id": "<APPROVAL_ID>", "approved": true, "notes": "Aprovado via smartphone"}'
   ```

### 3.4 TTL de Expiração (30 Minutos) e Push Instantâneo
Para evitar retenção indefinida de recursos computacionais e travamento de threads operacionais:
- **Time-to-Live (TTL):** Toda solicitação HITL gerada recebe automaticamente a coluna `expires_at` calibrada para 30 minutos a partir da criação (`requested_at + 30 min`).
- **Purga Automática:** Solicitações não homologadas em até 30 minutos transicionam automaticamente para `EXPIRED`. O guardião HITL libera o status da thread associada de volta para `idle`, registra uma mensagem de cancelamento transparente no chat e grava o log de auditoria no SQLite WAL.
- **Push Instantâneo:** Ao reter uma ação, o motor emite os eventos SSE `hitl:pending_approval` e `hitl:approval_required`, acionando a abertura automática do dossiê de governança (`Alt + H`) no console SPA ativo.

---

## 4. Configuração de Notificações Remotas (Webhook e Telegram)

Para receber alertas de governança diretamente no celular quando o operador não estiver com o painel aberto:

### 4.1 Configuração via API REST (Hot-Reload)
```bash
curl -X POST http://localhost:8000/api/settings/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://seu-endpoint.com/webhook",
    "telegram_token": "SEU_BOT_TOKEN_AQUI",
    "telegram_chat_id": "SEU_CHAT_ID_AQUI",
    "evolution_url": "http://host.docker.internal:8080",
    "evolution_key": "SUA_APIKEY_AQUI"
  }'
```

### 4.2 Configuração via Variáveis de Ambiente (.env)
No arquivo `/mnt/storage/piDots/.env`:
```env
WEBHOOK_NOTIFICATION_URL=https://seu-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_AQUI
TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=SUA_APIKEY_AQUI

# Governanca Estrita de Terminal Sandbox (true recusa shell se bwrap inexistir)
STRICT_SANDBOX=false
```

#### Modo de Isolamento Estrito (`STRICT_SANDBOX`):
- `STRICT_SANDBOX=false` (Padrão): Permite execução com fallback de desenvolvimento em ambientes onde os namespaces do kernel Linux estejam bloqueados.
- `STRICT_SANDBOX=true`: Modo de produção com isolamento compulsório. Se o utilitário Bubblewrap (`bwrap`) não estiver instalado ou falhar, a ferramenta de terminal recusa imediatamente a execução com erro HTTP/código de saída 126 e registra log de auditoria no SQLite WAL.

---

## 5. Parametrização Dinâmica do Provedor de IA e Gateway Multi-Provedor

O piDots é compatível com qualquer provedor que implemente a especificação `/chat/completions` da OpenAI API (OpenAI, Groq, OpenRouter, DeepSeek, llama-server local).
O gateway de inferência (`pidots/providers/openai_client.py`) implementa chaveamento automático por prioridade e Circuit Breaker de 3 estados (`CLOSED`, `OPEN`, `HALF_OPEN`).

### 5.1 Atualização de Parâmetros Primários e Secundários (Hot-Reload)
Para alterar os parâmetros sem reiniciar o contêiner:
```bash
curl -X POST http://localhost:8000/api/settings/ai \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "max_retries": 3,
    "timeout_seconds": 60.0,
    "fallback_url": "https://openrouter.ai/api/v1",
    "fallback_api_key": "sk-or-v1-...",
    "fallback_model": "meta-llama/llama-3.1-8b-instruct",
    "circuit_breaker_consecutive_failures": 3,
    "circuit_breaker_cooldown_seconds": 60.0
  }'
```

### 5.2 Topologia de Failover e Circuit Breaker
1. **Operação Nominal (`CLOSED`):**
   - Todas as requisições cognitivas são enviadas ao provedor primário (`AI_BASE_URL`).
   - Retentativas com backoff exponencial e jitter absorvem erros esporádicos (HTTP 502/503/504 ou 429).
2. **Ativação de Failover Transparente:**
   - Se o primário falhar após todas as retentativas e houver `AI_FALLBACK_URL` configurada, a requisição é desviada instantaneamente para o endpoint secundário sem quebrar o ciclo cognitivo do agente.
   - O retorno recebe o metadado `_served_by_fallback: true` para fins de auditoria e telemetria.
3. **Circuito Aberto (`OPEN`):**
   - Caso o primário atinja o limite consecutivo de falhas (padrão: 3 falhas), o circuito primário abre (`OPEN`) por 60 segundos (`cooldown_seconds`).
   - Durante essa janela, todas as novas requisições desviam imediatamente para o provedor secundário sem aguardar timeouts do primário, preservando o tempo de resposta do console.
4. **Recuperação Gradual Canário (`HALF_OPEN`):**
   - Expirado o tempo de cooldown, o circuito transiciona para `HALF_OPEN`.
   - A próxima chamada atua como teste canário no primário. Se responder com 200 OK, o circuito fecha (`CLOSED`) e o fluxo nominal é restabelecido. Se falhar, reabre por mais um ciclo de cooldown.
5. **Comportamento Inócuo:**
   - Caso `AI_FALLBACK_URL` não esteja configurada no `.env` (padrão do sistema), o Circuit Breaker não altera o comportamento atual do sistema, levantando exceções transitórias normais conforme a diretriz soberana do operador.

---

## 6. Operacao de Agendamentos Proativos (Dot Heartbeat)

O piDots possui um motor de agendamento em background (`pidots/core/scheduler.py`) que executa tarefas croniter a cada 15 segundos sem dependencias externas.

### 6.1 Listar Tarefas Agendadas Ativas
```bash
curl -s http://localhost:8000/api/tasks | jq .
```

### 6.2 Cadastrar Nova Tarefa Proativa
Exemplo de criacao de rotina de inspecao termica a cada 15 minutos:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "dot_id": "dot-auditor",
    "task_name": "Inspecao Termica de Borda",
    "cron_expr": "*/15 * * * *",
    "action_prompt": "Verificar temperatura do SoC e uso de RAM. Se normais, responder estritamente HEARTBEAT_OK.",
    "target_channel_type": "internal"
  }'
```

### 6.3 Monitoramento de Status Operacional e Circuit Breaker
Os status registrados na tabela `scheduled_tasks` sao:
- `IDLE`: Tarefa registrada aguardando o proximo horario de disparo (`next_run_at`).
- `RUNNING`: Ciclo em execucao ativa pelo `DotAgent` com trava em memoria (`_running_tasks`). Se o ciclo demorar mais de 15 segundos, novas varreduras ignoram o disparo repetido ate a conclusao da execucao.
- `SILENT`: A tarefa foi concluida com sucesso e emitiu `HEARTBEAT_OK`. Nenhuma notificacao externa foi disparada e o contador de falhas e zerado (`consecutive_failures = 0`).
- `COMPLETED`: A tarefa detectou uma condicao relevante e gerou um relatorio textual ou alerta. O contador de falhas e zerado.
- `FAILED`: Ocorreu uma excecao durante o ciclo cognitivo. O erro tecnico real e registrado em `last_result_summary`, `consecutive_failures` e incrementado e um retardo exponencial (`backoff_until`) entre 30s e 3600s e aplicado.
- `CIRCUIT_OPEN`: O Circuit Breaker abriu na 5ª falha consecutiva. A tarefa e desativada (`is_active = 0`) para proteger a CPU ARM64 e conectividade do host contra sobrecarga continuada.
- `AUTH_REQUIRED`: Pausa preventiva de 10 minutos acionada pelo Sanity Check quando a `AI_API_KEY` for vazia ou contiver texto placeholder, evitando chamadas de rede inuteis ao provedor.

---

## 7. Operacao de Mensageria e Webhooks Externos

### 7.1 Integracao com Telegram Bot API
Para conectar um bot do Telegram diretamente ao piDots via webhook HTTP reverso:
1. Registre o webhook na API oficial do Telegram apontando para o seu IP/dominio ou tunel Cloudflared:
```bash
curl -X POST "https://api.telegram.org/bot<SEU_BOT_TOKEN>/setWebhook" \
  -d "url=https://seu-tunel.trycloudflare.com/api/webhooks/telegram/dot-supervisor"
```
2. Toda mensagem enviada ao bot no Telegram sera automaticamente roteada para uma thread persistente correspondente no SQLite WAL.

### 7.2 Integracao com WhatsApp (Evolution API / Baileys)
Configure o webhook da instancia da Evolution API para enviar eventos de mensagens para:
- **URL do Webhook:** `http://localhost:8000/api/webhooks/whatsapp/dot-coder`
- O piDots interceptara a mensagem, filtrara mensagens enviadas pelo proprio bot (`fromMe: true`) e processara a solicitacao.

### 7.3 Disparo via Webhook Generico Universal
Para integracao com scripts bash, cronjobs do host ou pipelines CI/CD:
```bash
curl -X POST http://localhost:8000/api/webhooks/incoming/dot-supervisor \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Executar auditoria nos logs de sistema",
    "sender_name": "Pipeline CI/CD",
    "sender_id": "ci-runner-01"
  }'
```

---

## 8. Operacao de Salas Tematicas Colaborativas (#canais)

As salas tematicas permitem colaboracao multi-bot e participacao de operadores humanos em canais compartilhados.

### 8.1 Criar uma Nova Sala Tematica
```bash
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "devops",
    "description": "Canal de operacoes de infraestrutura e monitoramento"
  }'
```

### 8.2 Adicionar Membros ao Canal
```bash
# Associar o dot-coder a sala
curl -X POST http://localhost:8000/api/channels/devops/members \
  -H "Content-Type: application/json" \
  -d '{"member_type": "dot", "member_id": "dot-coder"}'

# Associar o dot-supervisor a sala
curl -X POST http://localhost:8000/api/channels/devops/members \
  -H "Content-Type: application/json" \
  -d '{"member_type": "dot", "member_id": "dot-supervisor"}'
```

### 8.3 Postar Mensagem e Disparar Colaboracao Multi-Bot
```bash
curl -X POST http://localhost:8000/api/channels/devops/messages \
  -H "Content-Type: application/json" \
  -d '{
    "author_type": "user",
    "author_id": "operador-lyon",
    "content": "Atenção @dot-coder favor verificar o status de memoria do Raspberry Pi"
  }'
```

### 8.4 Salvaguarda Anti-Loop em Salas
O orquestrador de canais (`ChannelOrchestrator`) monitora a propagacao de mensagens:
- **Teto de Saltos:** O campo `hop_count` e incrementado a cada turno de bot. Atingindo `hop_count > 3`, a propagacao e interrompida.
- **Mencao Explicita Entre Bots:** Um bot so responde a outro bot se for explicitamente citado pelo identificador `@nome_do_bot`.
- **Silencio Deterministico:** Caso um bot nao tenha acoes relevantes, emite `NO_ACTION` e nao propaga nova mensagem para o canal.

---

## 9. Baterias de Testes e Validacao em Producao

Para validar a integridade de todas as capacidades do piDots apos atualizacoes de codigo ou migracoes de hardware:

```bash
cd /mnt/storage/piDots

# 1. Testes de infraestrutura fundamental (banco, sandboxing, I/O)
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# 2. Validar orquestracao multi-bot, delegacao isolada e Dynamic Tool Pruning
python3 scripts/test_phase6_multibot.py

# 3. Validar agendamento proativo Dot Heartbeat e diretriz HEARTBEAT_OK
python3 scripts/test_phase7_scheduler.py

# 4. Validar gateway de mensageria, canais tematicos e trava anti-recursao
python3 scripts/test_phase8_messaging.py

# 5. Validar Memoria Hierarquica MemGPT (Core Memory, Archival FTS5 + 64d Trigram)
python3 scripts/test_phase9_memory.py

# 6. Validar Self-Healing Harness e Two-Stage Planning (Goals & Milestones)
python3 scripts/test_phase10_self_healing_planner.py

# 7. Validar Conselho Consultivo e Deliberacao Dialetica Tripartite
python3 scripts/test_phase11_council_debate.py

# 8. Validar Shared Knowledge Space e Templates Dot Packs v1.0
python3 scripts/test_phase12_shared_space_dot_packs.py

# 9. Validar Triggers de Hardware Edge e Manutencao Noturna do MicroSD
python3 scripts/test_phase13_edge_triggers_maintenance.py

# 10. Validar resiliencia integral (Tipagem de erros, AG-UI v1.0, 3 consumidores, Circuit Breaker)
python3 scripts/test_resilience_phases.py

# 11. Teste de estresse concorrente sob condicoes extremas de borda
python3 scripts/stress_test.py
```
Todos os scripts reportam o consumo real de memoria RSS (mantendo-se < 100 MB de RAM) e asseguram a integridade do banco SQLite WAL.

---

## 10. Acesso Remoto Seguro 24/7 via Cloudflared

Para acessar o console SPA e a API a partir de redes externas ou no celular sem expor portas nem alterar configurações de NAT no roteador:

### 10.1 Instalação do Cloudflared no Raspberry Pi
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb
```

### 10.2 Execução de Túnel Imediato
```bash
cloudflared tunnel --url http://localhost:8000
```
O Cloudflare gerará uma URL pública HTTPS segura (`https://*.trycloudflare.com`) que pode ser aberta no smartphone ou instalada como PWA.

### 10.3 Configuração como Serviço Persistente (systemd)
Para manter o túnel ativo 24/7 mesmo após reinicializações do Raspberry Pi:
```bash
sudo cloudflared service install <TOKEN_DO_SEU_TUNEL>
sudo systemctl enable --now cloudflared
```

---

## 11. Rotina de Backup Atômico do SQLite WAL

Como o SQLite está configurado em modo WAL (`Write-Ahead Logging`), nunca copie o arquivo `pidots.db` diretamente via `cp` enquanto o contêiner estiver em execução, pois isso pode capturar um estado inconsistente entre o banco e o arquivo `.db-wal`.

### 11.1 Procedimento de Backup Seguro em Tempo Real
Utilize a API de backup atômico nativa do SQLite:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db ".backup /mnt/storage/piDots/data/pidots_backup_$(date +%Y%m%d_%H%M%S).db"
```
Esse comando pode ser executado sem interromper as operações do contêiner.

### 11.2 Automação via Cron
Adicione a seguinte linha no `crontab -e`:
```cron
# Backup diário às 03:00 da manhã
0 3 * * * sqlite3 /mnt/storage/piDots/data/pidots.db ".backup /mnt/storage/piDots/data/backup_diario.db" && find /mnt/storage/piDots/data/ -name "backup_*.db" -mtime +7 -delete
```

---

## 12. Preservação da Mídia Flash do Cartão MicroSD

O maior risco em servidores autônomos baseados em Raspberry Pi 4B é o desgaste prematuro das células de memória flash (wearout) causado por gravações contínuas e chamadas frequentes a `fsync`.

O piDots implementa proteções ativas contra esse fenômeno:
1. **Journal em Modo WAL:** Operações de escrita são gravadas de forma contínua e sequencial no arquivo journal, sem reescrever páginas inteiras na base principal a cada commit.
2. **Sincronização em Modo NORMAL:** `PRAGMA synchronous = NORMAL;` reduz em mais de 85% as chamadas de sincronização forçada de blocos para o hardware do cartão MicroSD, mantendo total integridade contra falhas do processo da aplicação.
3. **Diretório Temporário em Memória RAM (`tmpfs`):** O diretório `/tmp` do contêiner está montado como memória volátil (`tmpfs: size=64m`). Todas as operações efêmeras de arquivos transitórios ocorrem puramente na RAM.
4. **Checkpointing Periódico Seguro:** Uma rotina assíncrona executa `PRAGMA wal_checkpoint(PASSIVE)` a cada 15 minutos em background, garantindo que o arquivo WAL nunca sofra inchaço acumulativo.

---

## 13. Procedimentos de Diagnóstico e Resolução de Problemas

### 13.1 O Contêiner não inicia
- Verifique se a porta 8000 já está em uso por outro serviço:
  ```bash
  sudo netstat -tlpn | grep 8000
  ```
- Inspecione logs detalhados do Docker:
  ```bash
  docker compose logs pidots-core
  ```

### 13.2 Diagnóstico e Resolução de Falhas de Conexão com o Provedor de IA
O piDots separa erros de API em duas categorias claras para agir com rapidez e evitar gastos desnecessários:

#### A. Erro de Autenticação ou Chave Inválida (ProviderAuthError - HTTP 401/403)
- **Sintoma:** O agente interrompe a execução na mesma hora, sem insistir em novas tentativas que só consumiriam tempo e chamadas inúteis.
- **Log do Sistema:** `Falha de autenticação com provedor de IA: HTTP 401: Unauthorized...`
- **Registro Interno:** O agente grava na tabela `messages` do SQLite WAL uma mensagem interna de depuração com prefixo `[FALHA DE AUTENTICAÇÃO]`.
- **Inspeção de Logs via SQLite:**
  ```bash
  sqlite3 /mnt/storage/piDots/data/pidots.db \
    "SELECT id, thread_id, content, created_at FROM messages WHERE visibility = 'internal' AND content LIKE '%[FALHA%' ORDER BY created_at DESC LIMIT 5;"
  ```
- **Acao Corretiva:** Atualize a chave de API via hot-reload sem reiniciar o contêiner:
  ```bash
  curl -X POST http://localhost:8000/api/settings/ai \
    -H "Content-Type: application/json" \
    -d '{"api_key": "SUA_CHAVE_VALIDA_AQUI"}'
  ```

#### B. Falhas Temporarias de Rede ou Gateway (ProviderTransientError - HTTP 503/429/502/504)
- **Sintoma:** O provedor aplica retentativas assincronas com backoff exponencial e jitter (`[1.0, 2.0, 4.0]s`).
- **Log do Sistema:** `Falha temporária de rede (ConnectError). Aguardando...`
- **Esgotamento:** Caso todas as tentativas falhem, o status `failed` e propagado para os consumidores e a falha e gravada com `[FALHA DE INFERÊNCIA]`.

### 13.3 Diagnostico e Rearme do Circuit Breaker em Tarefas Proativas
Quando uma tarefa proativa agendada falha sucessivamente, o `EdgeScheduler` protege o hardware e a rede contra tempestades de requisicao.

#### Inspecionar Status de Tarefas Agendadas
Via API REST:
```bash
curl -s http://localhost:8000/api/tasks | jq '.[] | {task_name, last_status, consecutive_failures, backoff_until, is_active}'
```
Ou diretamente no banco SQLite WAL:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db \
  "SELECT id, task_name, last_status, consecutive_failures, backoff_until, is_active FROM scheduled_tasks;"
```

#### Estados de Protecao:
1. **`AUTH_REQUIRED` (Sanity Check de Chave Vazia/Placeholder):**
   - Ocorre quando `AI_API_KEY` nao foi definida ou mantem valores padrao (`sua_chave_aqui`, `placeholder`).
   - A tarefa pausa por 10 minutos. Para corrigir, configure uma chave valida no `.env` ou via `POST /api/settings/ai`.
2. **`CIRCUIT_OPEN` (5 Falhas Consecutivas):**
   - Ocorre quando a tarefa atingiu 5 falhas consecutivas (`consecutive_failures = 5`). O escalonador desarma a tarefa (`is_active = 0`).

#### Procedimento de Rearme Manual da Tarefa:
Apos corrigir a conectividade ou a credencial, rearme o circuito e reative a tarefa executando:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db \
  "UPDATE scheduled_tasks SET is_active = 1, consecutive_failures = 0, backoff_until = NULL, last_status = 'IDLE' WHERE id = 'ID_DA_TAREFA';"
```

### 13.4 Diagnostico de Subtarefas e Handoffs Falhos no MultiBotOrchestrator
Quando uma subtarefa delegada a um worker falha na inferencia:
- O registro em `agent_handoffs` recebe `status = 'FAILED'` e o detalhe do erro em `result_summary`.
- Uma fita de carbono interna e registrada na conversa do supervisor (`[FALHA NA SUBTAREFA DE @dot]`).
- O supervisor recebe `{'success': False, 'error': ...}` e pode replanejar ou avisar o usuario.

#### Inspecionar Handoffs Falhos no SQLite:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db \
  "SELECT id, thread_id, source_dot_id, target_dot_id, status, result_summary, created_at FROM agent_handoffs WHERE status = 'FAILED' ORDER BY created_at DESC LIMIT 5;"
```

### 13.5 Resposta de Falha Operacional no Gateway de Mensageria
Caso ocorra uma interrupcao no provedor durante o recebimento de mensagens de Telegram, WhatsApp ou Webhook:
- O `MessagingGateway` intercepta a falha e despacha aviso com o prefixo `[FALHA OPERACIONAL]`:
  `[FALHA OPERACIONAL]: O agente encontrou uma falha de conexão com o provedor de IA e não pôde concluir o processamento da solicitação.`
- O canal nao e corrompido e o interlocutor externo recebe feedback transparente imediato.

### 13.6 O Console PWA não atualiza dados
- No navegador, execute a limpeza do cache de Service Worker (`Application > Service Workers > Unregister`) ou force o recarregamento com `Ctrl + Shift + R`.
- Verifique se o backend está respondendo normalmente em `http://localhost:8000/health`.

### 13.7 Verificação de Cabeçalhos de Segurança HTTP
Para auditar se os cabeçalhos defensivos de borda estão ativos no servidor FastAPI:
```bash
curl -s -D - http://localhost:8000/health | grep -iE "(x-content-type-options|x-frame-options|referrer-policy)"
```
Saída esperada:
```http
x-content-type-options: nosniff
x-frame-options: SAMEORIGIN
referrer-policy: strict-origin-when-cross-origin
```

### 13.8 Exportação e Backup de Workspaces em ZIP
Para baixar o workspace completo e artefatos de um Dot via linha de comando (com fallback e agregação da tabela `spaces`):
```bash
curl -s http://localhost:8000/api/workspaces/dot-dev-core/export.zip -o workspace_dot-dev-core.zip
unzip -l workspace_dot-dev-core.zip
```

---

## 14. Console Web SPA Oficial, Topologia de Rotas e Operacao via Teclado

O console oficial do piDots opera na porta 8000 na rota canonica `http://localhost:8000/app` (com alias `http://localhost:8000/workspace`) e oferece:
- **Interface Tecnica Minimalista e Console Escuro Tatil:** Interface tatica minimalista com contraste marcante (Dark Noir e Blueprint), visual de matriz tecnica, tipografia crisp e estetica retro de 1-bit.
- **Identidade e Logotipo Oficial:** Logotipo vetorial servido via rota oficial `/icon.svg` com headers de cache HTTP de 24 horas (`Cache-Control: public, max-age=86400`).
- **Telemetria de Hardware em Tempo Real:** Indicadores integrados de SoC/CPU, RAM, temperatura do silicio e status do SQLite WAL.
- **Visualizador de Diffs Integrado:** Na aba SPACES, o botao `[VER DIFFS]` aciona a comparacao visual das revisoes armazenadas em `space_revisions` com carimbos analogicos de status.
- **Governanca no Feed:** Alertas de solicitacoes pendentes de comandos de risco com botoes táteis de homologacao e veto de seguranca.
- **Landing Page de Onboarding:** Servida na raiz `/`, com calculadora interativa de ROI e comparativo de custos Edge vs Nuvem.
- **Guia Didatico do Operador:** Servido na rota canonica `/docs`, estruturado em estilo passo a passo com drawer lateral retratil, Omnisearch Ctrl+K e Mini API Tester.
- **OpenAPI Swagger UI:** Interface nativa do FastAPI desacoplada em `/api/docs` com esquema bruto em `/api/openapi.json`.

### 14.1 Navegacao Cruzada Rapida via Chords Globais
Transicao instantanea sem necessidade de mouse a partir de qualquer superficie:

| Chord Sequencial | Destino | Descricao |
| :--- | :--- | :--- |
| `g` seguido de `h` | `GET /` | Go Home: Landing Page de Apresentacao e Onboarding |
| `g` seguido de `w` | `GET /app` | Go Workspace: Console Operacional SPA / Estacao de Trabalho |
| `g` seguido de `d` | `GET /docs` | Go Docs: Guia Didatico e Referencia Tecnica |

### 14.2 Atalhos de Alta Produtividade do Console SPA
Para agilizar o fluxo operacional diario do operador:

| Atalho de Teclado | Acao Executada | Comportamento no Sistema |
| :--- | :--- | :--- |
| `Tecla /` | Autocomplete Popover | Dispara menu suspenso de 30 Slash Commands com busca fuzzy no teletipo |
| `Botão [/]` | Autocomplete Touch | Abre diretamente o popover de comandos no mobile sem abrir teclado |
| `Bottom-Nav` | Comutação Mobile | Alterna entre visualizações [O] DOTS, [>] CHAT, [*] CANVAS e [?] GUIA em smartphones |
| `Alt+B` | Sidebar Adaptativa | Alterna overlay sob demanda da barra lateral no Triptico (1024px-1440px) |
| `Alt+I` | Inspecionar Artefato | Foca e expande o artefato ativo no Live Canvas |
| `Ctrl+S` / `Cmd+S` | Gravar Revisao | Grava revisao atomica do documento em Spaces no SQLite WAL |
| `Alt+H` | Dossie HITL | Foca e abre o modal de governanca de aprovacao humana |
| `F11` | Alternar Canvas | Alterna entre visualizacao dividida (split) e maximizada do canvas |
| `Ctrl+L` | Limpar Teletipo | Limpa mensagens visuais da bobina do teletipo/chat local (/clear) |
| `F1` | Manual Operacional | Abre a gaveta lateral retratil com o manual tecnico |

### 14.3 Guia Rapido dos 30 Slash Commands no Teletipo

O operador de borda pode controlar o no diretamente pelo teletipo do console digitando comandos iniciados por barra (`/`):

#### 1. Sistema & UI
- `/help [filtro]`: Exibe o catalogo completo de comandos em tabela formatada.
- `/clear [chat|terminal|canvas|all]`: Limpa a bobina de teletipo ou o console sandbox mantendo a sessao ativa.
- `/theme [noir|blueprint|toggle]`: Comuta a paleta de cores entre Dark Noir e Blueprint.
- `/lang [pt|en]`: Comuta o idioma da interface em tempo real via micro-motor i18n.
- `/info`: Consulta `/health` e renderiza o dossie de hardware ARM64 e do SQLite WAL.
- `/status`: Panorama operacional de coworkers instalados e coworker em foco.
- `/telemetry`: Exibe barras em ASCII 1-bit de Temperatura SoC BCM2711, RAM, Disco e Load Avg.
- `/pwa [status|update|cache-clear]`: Inspeciona modo standalone do PWA e atualiza o Service Worker.
- `/tour [reset]`: Dispara o motor de Tour Spotlight interativo guiando as funções do cockpit passo a passo no primeiro acesso; com 'reset' reinicia a flag de FTUE.
- `/onboarding`: Alias canônico para execução do tour guiado do sistema (/tour).
- `/changelog [versao]`: Consulta `/api/changelog` e exibe notas da versao SemVer ativa.

#### 2. Agentes & Multi-Bot
- `/dots [filtro]`: Lista coworkers registrados no no, arquetipos e estado de operacao.
- `/handoff <dot_id> [contexto]`: Transfere a missao para outro coworker com slip de transicao.
- `/council [tema]`: Executa sessao dialetica tripartite (Pragmatica, Inovadora e Auditor de Borda).
- `/delegate <dot_id> <tarefa>`: Enfileira uma subtarefa assincrona em segundo plano para o coworker alvo.
- `/archetype [dot_id]`: Exibe ficha tecnica da persona, modelo vinculado e isolamento sandbox.
- `/tools [dot_id]`: Catalogo de 23 ferramentas registradas e ferramentas ativas pos-pruning.

#### 3. Memoria, Tarefas, Governanca e Dados
- `/memory [query]`: Inspeciona recibos na bobina local, estimativa de tokens e limite de 150 nos DOM.
- `/archival <busca>`: Dispara busca semantica vetorial KNN na memoria persistente do SQLite WAL.
- `/shared [key]`: Inspeciona chaves do Espaco Compartilhado (Shared Space) sincronizadas no cluster.
- `/spaces [nome]`: Lista arquivos do workspace ou abre documento no Live Canvas.
- `/diff [artefato]`: Alterna o modo de visualizacao diferencial (Diff) e historico de revisoes.
- `/tasks [status]`: Tabela de tarefas e missoes agendadas com estado do EdgeScheduler.
- `/cron [listar|status]`: Inspeciona as rotinas automaticas registradas no cron do uvloop.
- `/run-task <task_id>`: Despacha ordem de execucao manual imediata para uma tarefa agendada.
- `/hitl [status|logs|clear]`: Inspeciona ou homologa acoes retidas pelo guardrail Deny-by-Default.
- `/triggers [status|check]`: Avalia sensores fisicos contra limiares de seguranca de silicio.
- `/maintenance [status|run]`: Executa a triade de manutencao: WAL Checkpoint TRUNCATE, poda e VACUUM.
- `/backup [download|status]`: Politica de snapshots rotativos ACID de 7 dias e download do banco.
- `/export [chat|canvas|markdown]`: Exporta o historico do teletipo ou o artefato ativo em Markdown.
- `/pack [dot_id]`: Gera e baixa pacote portatil estruturado DotPack v1.0 para distribuicao.

---

## 15. Operacao da Memoria Hierarquica (Padrao MemGPT / Letta)

### 15.1 Inspecionar Blocos de Core Memory no SQLite WAL
A Core Memory mantem os blocos fixos residentes in-context para cada Dot:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db \
  "SELECT dot_id, block_name, length(content) as chars_used, max_chars, updated_at FROM agent_core_memory_blocks;"
```

### 15.2 Inspecionar Archival Memories com Busca FTS5
Para consultar o acervo duradouro de memorias de um Dot via ranking BM25:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db \
  "SELECT a.id, a.dot_id, a.content, f.rank FROM archival_memories a JOIN archival_memories_fts f ON a.id = f.id WHERE archival_memories_fts MATCH 'MicroSD OR thermal' ORDER BY f.rank LIMIT 5;"
```

### 15.3 Deduplicação Semântica (> 0.92) com Fusão Atômica de Tags
Antes de gravar qualquer fato na memória duradoura via `archival_memory_insert`, o motor avalia a similaridade vetorial (cosseno sobre projeção determinística 64D):
- **Limiar de Duplicidade:** Caso exista registro do mesmo agente com similaridade `>= 0.92`, o sistema não duplica linhas na base nem no índice FTS5.
- **Merge/Update Atômico:** O registro pré-existente tem seu conteúdo atualizado com os novos dados complementares, suas tags são unificadas sem repetições e o trigger SQLite `trg_archival_update` sincroniza a tabela virtual FTS5 transparentemente.
- **Retorno da Operação:** O chamador recebe `{"deduplicated": true, "merged_with": "<ID>", "similarity": <SCORE>}` comprovando a consolidação.

---

## 16. Exportacao e Importacao de Dot Packs Portaveis (v1.1) com Assinatura SHA-256

Os Dot Packs v1.1 permitem empacotar, assinar criptograficamente e instanciar agentes especialistas completos entre diferentes Raspberry Pis com garantia de integridade estrutural e defesa contra Prompt Injection.

### 16.1 Exportar Manifesto Dot Pack Assinado
```bash
# Exporta manifesto JSON canonico com sha256_checksum integrado
curl -s http://localhost:8000/api/dots/dot-coder/export-pack > /mnt/storage/piDots/dot_coder_pack.json

# Inspeciona o cabecalho e a assinatura criptografica do manifesto
head -n 25 /mnt/storage/piDots/dot_coder_pack.json
```

### 16.2 Importar Dot Pack com Verificacao de Integridade e Auditoria
Na rota de importacao, o sistema valida a correspondencia do hash `sha256_checksum` e submete os blocos de `core_memory` a uma varredura estatica contra padroes maliciosos de subversao de instrucao de sistema:
```bash
# Valida a assinatura, audita as memorias contra injection e instancia o agente atomicamente
curl -s -X POST http://localhost:8000/api/dots/import-pack \
  -H "Content-Type: application/json" \
  -d @/mnt/storage/piDots/dot_coder_pack.json
```

---

## 17. Monitoramento de Triggers de Hardware Edge (BCM2711)

O piDots supervisiona ativamente a saude do silicio e do armazenamento flash para operacao Always-On estavel.

### 17.1 Consultar Telemetria e Triggers em Tempo Real
```bash
curl -s http://localhost:8000/api/edge/triggers | jq .
```
Exemplo de resposta operacional:
```json
{
  "status": "OK",
  "device": "Linux Edge Node (Ref: RPi4 ARM64)",
  "metrics": {
    "temperature_celsius": 48.5,
    "disk": {
      "free_gb": 19.29,
      "free_percent": 67.38
    },
    "ram": {
      "total_mb": 3795.7,
      "available_mb": 2355.2,
      "free_percent": 62.05
    },
    "load_average": {
      "load_1m": 0.42,
      "load_5m": 0.38,
      "load_15m": 0.25
    }
  },
  "triggered_count": 0,
  "triggered_events": [],
  "is_throttled": false
}
```

### 17.2 Ações em Caso de Alerta WARNING ou CRITICAL
- **`THERMAL_EXCEEDED` (Temperatura no SoC >= 78 °C):** O sistema reduz preventivamente o ritmo de execução para evitar sobreaquecimento da placa (calibrado para a faixa de operação do Raspberry Pi 4B sem cooler ativo). Verifique a ventilação passiva ou ativa do seu Raspberry Pi.
- **`DISK_LOW_SPACE` (Espaço livre no cartão MicroSD < 10%):** Dispare imediatamente a rotina de manutenção noturna (Seção 18) para purgar mensagens antigas e truncar o arquivo WAL.

---

## 18. Rotina de Manutencao Noturna e Preservacao do MicroSD

A manutencao do SQLite WAL preserva as celulas de memoria flash do cartao MicroSD e mantem tempos de resposta estaveis.

### 18.1 Disparar Manutencao Noturna Manual via API REST
```bash
curl -s -X POST http://localhost:8000/api/edge/maintenance \
  -H "Content-Type: application/json" \
  -d '{"days_threshold": 7, "create_backup": true}' | jq .
```
O retorno confirma:
- Truncamento síncrono do WAL (`PRAGMA wal_checkpoint(TRUNCATE)`), zerando o arquivo `-wal`.
- Consolidacao de turnos com mais de 7 dias na tabela `episodic_memories` e poda das mensagens brutas em `messages`.
- Geracao de backup atomico consistente em `data/backups/pidots_backup_TIMESTAMP.db` via `VACUUM INTO`.
- Atualizacao de estatisticas dos indices SQLite via `PRAGMA optimize` e `ANALYZE`.

### 18.2 Agendar Manutencao Noturna Diaria Autonoma (03:00 UTC)
Cadastre a tarefa proativa no escalonador in-process do piDots:
```bash
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "dot_id": "dot-auditor",
    "task_name": "Manutencao Noturna MicroSD",
    "cron_expr": "0 3 * * *",
    "action_prompt": "Execute a ferramenta edge_maintenance_run com days_threshold=7 e create_backup=true para preservar a saude do cartao MicroSD.",
    "target_channel_type": "internal"
  }' | jq .
Apos cadastrada, o `EdgeScheduler` executara a rotina de compactacao automaticamente todas as noites as 03:00 sem intervencao do operador.

---

## 19. Homologacao Operacional de Internacionalizacao (i18n), Locales e Changelog

Com o subsistema de internacionalizacao bilingue nativo (PT/EN) e versionamento SemVer v1.3.0 ativo, o operador pode validar a integridade dos dicionarios e dos endpoints de borda.

### 19.1 Inspecao dos Endpoints de Traducao e Changelog via cURL
```bash
# Validar endpoint de traducao em Portugues do Brasil (pt-BR)
curl -s -i http://localhost:8000/data/locales/pt.json | head -n 15

# Validar endpoint de traducao em Ingles Tecnico (en-US)
curl -s -i http://localhost:8000/data/locales/en.json | head -n 15

# Validar cabecalhos de cache de borda do script i18n
curl -s -i http://localhost:8000/static/pidots-i18n.js | grep -E "HTTP/|content-type|cache-control"

# Validar integridade da API de Changelog e Patch Notes SemVer v1.5.2
curl -s http://localhost:8000/api/changelog | jq '{version: .current_version, release_date: .release_date, patch_notes: .patch_notes.title}'
```

### 19.2 Validacao Automatizada de Paridade Estrutural dos Dicionarios
Execute o script em linha de comando no ambiente virtual para confirmar que 100% das chaves estao presentes em ambos os idiomas:
```bash
python3 -c "
import json

def flatten(d, prefix=''):
    items = []
    for k, v in d.items():
        new_k = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_k))
        else:
            items.append(new_k)
    return items

with open('data/locales/pt.json', encoding='utf-8') as f:
    pt = json.load(f)
with open('data/locales/en.json', encoding='utf-8') as f:
    en = json.load(f)

pt_flat = set(flatten(pt))
en_flat = set(flatten(en))
diff = pt_flat.symmetric_difference(en_flat)
if diff:
    print(f'[ALERTA] Divergencia de chaves detectada: {diff}')
    exit(1)
else:
    print(f'[OK] Paridade estrita confirmada: {len(pt_flat)} chaves folha sincronizadas entre PT e EN.')
"
```

---

## 20. Validacao Operacional da API de Spaces e do Triptico Adaptativo

Com o subsistema de Spaces conectado dinamicamente ao Live Canvas e o Triptico Adaptativo ativo no console SPA (`/app`), o operador pode validar a integridade dos endpoints de documentos versionados:

### 20.1 Inspecao da API de Spaces via cURL
```bash
# Listar todos os documentos persistidos em Spaces
curl -s http://localhost:8000/api/spaces | jq .

# Gravar uma nova revisao de documento via API REST
curl -s -X POST http://localhost:8000/api/spaces \
  -H "Content-Type: application/json" \
  -d '{"filename": "relatorio_termico.md", "content": "# Relatorio Termico Edge\nTemperatura nominal: 44.8 C"}' | jq .

# Obter o historico de revisoes e calculo de diff unificado
curl -s http://localhost:8000/api/spaces/relatorio_termico.md/revisions | jq .
```

### 20.2 Checklist de Verificacao da Interface Triptico e Mobile (v1.5.2)
1. **Em Telas de 1024px a 1440px:** A coluna da esquerda colapsa automaticamente e pode ser expandida via `Alt+B` ou clique no botao `[PAINEL]`, sem espremer o teletipo.
2. **Em Telas Mobile (<= 768px):** A barra inferior `.mobile-bottom-nav` permanece visivel com 4 botoes tateis (`[O] DOTS`, `[>] CHAT`, `[*] CANVAS`, `[?] GUIA`). A comutacao entre `dots`, `chat` e `canvas` comuta a visibilidade das colunas atraves de `setMobileView()`.
3. **Comutacao de Abas e Modo Foco:** Ao alternar para DOTS ou CANVAS, a classe `mode-focus-zen` e removida compulsoriamente para impedir travamentos visuais.
4. **Acionamento do Teclado Virtual (window.visualViewport):** Ao focar `#instructionInput`, a classe `keyboard-open` e ativada no body, a barra inferior e ocultada e a altura do body e fixada na altura visivel real, mantendo o scroll do chat no final.
5. **Atalho Mecanico Touch [/]:** O clique em `#slashTriggerBtn` abre imediatamente o popover de comandos sem exigir a subida do teclado.

---

## 21. Resiliência Cognitiva: Teto de Self-Healing e Consenso Antecipado do Conselho

### 21.1 Teto Estrito de Tentativas no Self-Healing (`MAX_HEAL_ATTEMPTS = 2`)
O ciclo de auto-reparo autônomo (`execute_and_verify`) possui teto calibrado para impedir consumo desnecessário de iterações e ciclos de inferência:
- **Limite de 2 Ciclos:** Se um comando falhar com erro de compilação, sintaxe ou teste quebrado, o `SelfHealingHarness` emite a diretriz cirúrgica na primeira tentativa.
- **Interrupção e Escalonamento:** Caso a mesma chamada falhe pela 2ª vez consecutiva, o harness marca `max_attempts_exceeded = True`, interrompe o loop e emite o evento SSE `self_healing:max_attempts_exceeded`.
- **Trilha para o Auditor:** O traceback dissecado com arquivo, linha e escopo é automaticamente escalado para o `@dot-auditor` ou para o operador humano.

### 21.2 Early Consensus Exit no Conselho Consultivo Tripartite
Durante a deliberação formal entre Propositor (`@dot-coder`), Auditor (`@dot-auditor`) e Supervisor (`@dot-supervisor`):
- **Detecção de Consenso:** Caso na Rodada 2 do debate (ou no parecer inicial) o `@dot-auditor` classifique a proposta como `RISK_LOW / APPROVED`, o orquestrador detecta que não existem divergências impeditivas.
- **Saída Antecipada:** O conselho encerra o debate sem executar uma 3ª rodada desnecessária, pulando diretamente para a consolidação executiva do `@dot-supervisor`.
- **Economia de Recursos:** Reduz latência de resposta em ~35% e economiza tokens de inferência na borda do Raspberry Pi 4B.

---

## 22. Operação de Extensibilidade MCP Lite, Governança Criptográfica e Borda Física (v1.5.3)

### 22.1 Conexão de Servidores MCP com Dynamic Tool Pruning
O piDots conecta servidores MCP (Model Context Protocol) externos via STDIO ou SSE sem dependências pesadas (< 5MB RAM):
```python
from pidots.tools.mcp_client import LiteMCPClient, MCPRegistryManager
from pidots.tools.registry import registry

# Instancia cliente para servidor MCP externo (ex: Git)
git_mcp = LiteMCPClient(server_name="git", transport="stdio", command="mcp-server-git")
registered_tools = await MCPRegistryManager.register_server("git", git_mcp, registry)
# Ferramentas registradas: ["mcp_git_git_status", "mcp_git_git_diff", ...]
```
- **Governança de Contexto:** Agentes que não possuem `mcp_git_*` em seu `allowed_tools_json` não visualizam essas ferramentas, eliminando poluição de contexto.

### 22.2 Governança HITL Remota com Assinatura HMAC-SHA256
Ações retidas pelo guardião Deny-by-Default despacham alertas para Telegram e WhatsApp:
- **Telegram Bot:** A mensagem inclui botões interativos `[Aprovar]` e `[Bloquear]` com callback assinado criptograficamente (`h:a:<approval_id>:<hmac>`). Ao clicar, o webhook `/api/webhooks/telegram/{dot_id}` valida o HMAC em tempo constante e homologa a operação instantaneamente.
- **WhatsApp (Evolution API):** O operador pode aprovar respondendo `APROVAR <approval_id> <hmac>` ou bloquear com `BLOQUEAR <approval_id> <hmac>`.
- **API Segura:** Resolução direta via `POST /api/hitl/signed-resolve` com payload contendo `approval_id`, `action`, `hmac_token`.

### 22.3 Importação Segura de Dot Packs v1.1
Ao importar manifestos JSON de agentes via `POST /api/dots/import-pack`:
- **Integridade Criptográfica:** O sistema recalcula o hash canônico SHA-256 e compara com `sha256_checksum`. Se adulterado, a importação é sumariamente rejeitada.
- **Defesa contra Prompt Injection:** O `@dot-auditor` inspeciona `system_prompt`, blocos de `core_memory` e memórias arquivísticas. Se forem detectados padrões de override de sistema, jailbreak ou exfiltração de chaves, a importação é bloqueada com erro de segurança.

### 22.4 Monitoramento de Pinos Físicos GPIO e Barramento MQTT
- **Leitura de GPIO do Raspberry Pi 4B:** O módulo `EdgeGPIOMonitor` monitora pinos digitais configurados (ex: pino 17 para parada de emergência). Em caso de nível ativo, classifica o incidente como `CRITICAL` e pode suspender execuções destrutivas.
- **Barramento MQTT Assíncrono:** Sensores de temperatura ambiente, umidade ou presença podem enviar tópicos (ex: `pidots/edge/trigger/alert`) processados assincronamente pelo `EdgeMQTTListener` sem interferir no event loop do servidor.

---

## 23. Operação do Console `/app` Padrão OpenDots & CoAgents AG-UI (v1.6.0)

### 23.1 Navegação pela Activity Rail e 4 Painéis Laterais
Na lateral esquerda do Console `/app` (ou na visão `[O] DOTS` em dispositivos móveis), o operador dispõe da **Activity Rail** com 4 botões contextuais:
- **`[S] SPACES`:** Filtra e alterna entre Canais Multi-Bot (`#arquitetura-geral`, `#dev-sandbox`, `#auditoria-hitl`), Threads de Conversa e Documentos persistidos em Spaces.
- **`[D] DOTS`:** Lista os coworkers ativos, permite invocar o modal **Dots Studio** (`[+ CRIAR DOT]`) para cadastrar ou editar agentes com matriz visual de *Dynamic Tool Pruning*, e acionar **Handoff** ou **Conselho Tripartite**.
- **`[T] TASKS`:** Gerencia rotinas autônomas Cron/Heartbeat, permitindo pausar/ativar (`PATCH /api/tasks/{id}/toggle`) ou executar imediatamente (`POST /api/tasks/{id}/run`).
- **`[M] MEM/MCP`:** Executa buscas semânticas híbridas RRF (FTS5 BM25 + Vetor 64D) na memória arquivística e registra novos servidores MCP Lite em tempo real.

### 23.2 Salvar Thread como Documento em Space (`Save as Space`)
Para consolidar uma deliberação técnica em um documento versionado:
- Clique no botão **`[SALVAR EM SPACE]`** no cabeçalho contextual da conversa, ou utilize o comando **`/save-space [nome_arquivo.md]`**.
- O backend (`POST /api/threads/{thread_id}/save-as-space`) compila todas as mensagens da thread em Markdown estruturado, persiste a revisão na tabela `space_revisions` e atualiza a árvore de Spaces.

### 23.3 Aprovação HITL com Edição de Argumentos (`modified_args`) e Retomada Automática
Quando uma ferramenta de risco alto/crítico é interceptada:
1. Um cartão **Generative UI HITL** é exibido inline no teletipo (além do dossiê `Alt+H`), contendo uma caixa de edição JSON com os argumentos propostos pelo agente.
2. O operador pode ajustar parâmetros (ex: corrigir um caminho de arquivo ou flag de comando) e clicar em **`[HOMOLOGAR E RETOMAR]`**.
3. O endpoint `POST /api/hitl/{approval_id}/resolve` recebe `modified_args` e dispara automaticamente `DotAgent.resume_after_hitl()` em background, retomando o raciocínio ReAct do ponto exato de parada.

### 23.4 Computador do Dot (`Dot's Computer`), Modo Takeover e CoAgents Shared State
No painel direito do Console (`/app`):
- **Aba `[COMPUTADOR]`:** Exibe o terminal sandbox (`bwrap`) e o explorador de arquivos do workspace do agente ativo (`GET /api/edge/computer/files`). Ao ativar **`[ASSUMIR CONTROLE]`** (*Modo Takeover*), uma barra de comando interativa permite ao operador executar comandos diretamente no sandbox (`POST /api/edge/computer/exec`).
- **Aba `[COAGENTS]`:** Inspeciona o estado compartilhado bidirecional (`STATE_SNAPSHOT` e `STATE_DELTA`) sincronizado via SSE e permite aplicar overrides manuais de variáveis JSON (`PATCH /api/threads/{thread_id}/state`).


