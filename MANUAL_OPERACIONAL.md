# piDots: Manual Operacional e Guia de Produção 24/7

**Projeto:** piDots (Estação de Trabalho Local de Agentes Autônomos de Borda)  
**Autor e Criador:** lyon christopher  
**Assistente:** Logger  
**Hardware de Referência:** Raspberry Pi 4B 4 GB RAM (ARM64 Cortex-A72, Linux / Docker Compose)  
**Versão:** 1.5.5 (Produção Estável: Entrega em Quatro Portas Nginx, Túnel Seguro Cloudflare, Teletipo Pixel Paper UI e Aprovação Remota HMAC-SHA256)  

---

## 1. Visão Geral da Operação

O piDots foi desenvolvido para rodar de forma contínua em hardware modesto sem travar o sistema ou queimar o cartão de memória. Enquanto ferramentas corporativas de IA consomem vários gigabytes de RAM rodando Node.js pesado e navegadores headless, o piDots opera como um monólito modular assíncrono em Python com `uvloop`, FastAPI e SQLite em modo WAL.

### Indicadores Reais de Consumo (Bancada Raspberry Pi 4B):
- **Consumo de Memória RAM:** ~50 MB em repouso (teto máximo de 384 MB configurado no Docker).
- **Carga de CPU em Ociosidade:** Abaixo de 0.3% em um único núcleo ARM Cortex-A72.
- **I/O no Cartão MicroSD:** Gravações sequenciais em WAL, sem chamadas contínuas de `fsync`, com diretório temporário montado em memória volátil (`tmpfs`).
- **Throughput Medido:** Mais de 85 requisições por segundo com latência mediana de 72 milissegundos.

---

## 2. Comandos de Ciclo de Vida do Serviço

O sistema opera dentro do contêiner Docker `pidots-core`, gerenciado pelo Docker Compose.

### 2.1 Iniciar o Serviço em Segundo Plano
```bash
cd /mnt/storage/piDots
docker compose up -d
```

### 2.2 Verificar o Status de Saúde e Consumo
```bash
# Estado dos contêineres
docker compose ps

# Consumo de memória, CPU e I/O em tempo real
docker stats --no-stream pidots-core pidots-nginx
```

### 2.3 Visualização de Logs
Os logs contam com rotação automática para não lotar o cartão MicroSD (máximo de 2 arquivos de 5 MB cada):
```bash
# Acompanhar logs em tempo real
docker compose logs -f --tail=100 pidots-core
```

### 2.4 Reinicialização dos Serviços
```bash
docker compose restart pidots-core pidots-nginx
```

### 2.5 Parada do Serviço
```bash
docker compose down
```

---

## 3. Governança e Aprovações em Tempo Real (HITL)

O piDots aplica a política de recusa por padrão (*deny-by-default*) para qualquer ação potencialmente destrutiva disparada por um agente.

### 3.1 Classificação de Risco de Comandos
- **LOW (Seguro):** Comandos de leitura (`ls`, `cat`, consultas em arquivos) e scripts com descarte rotineiro de mensagens de erro (`2>/dev/null`, `2>&1`). Roda de forma autônoma sem interromper o operador.
- **MEDIUM (Atenção):** Redirecionamentos reais de escrita para arquivos em disco (`> arquivo`, `>> arquivo`, `tee`).
- **HIGH (Alto Risco):** Exclusão deliberada de arquivos (`file_delete`) ou criação de rotinas persistentes.
- **CRITICAL (Crítico):** Comandos com potencial destrutivo (`rm -rf`, `chmod`, `sudo`, `mkfs`, `curl | bash`, reinicialização do nó). A execução é **retida na hora** até homologação do operador.

### 3.2 Notificação Clara no Teletipo
Ao reter um comando na fila de segurança (`awaiting_hitl`), o sistema grava automaticamente uma mensagem no teletipo ativo:
```text
[GOVERNANÇA HITL // AÇÃO RETIDA]
O agente '<dot_id>' solicitou a ação '<tool_name>' (Risco: <risk>), que requer autorização expressa do operador.
ID de Aprovação: <approval_id>
Comando: homologue a execução na aba de governança (Alt+H) ou via comando /hitl.
```

### 3.3 Como Homologar ou Vetar Ações
Você pode decidir sobre comandos retidos por três caminhos:
1. **Pelo Console Web SPA:** Pressione `Alt+H` ou clique no card de aprovação no Live Canvas.
2. **Pela Linha de Comando (CLI Local):**
   ```bash
   pidots hitl approve <APPROVAL_ID>
   # ou para vetar:
   pidots hitl reject <APPROVAL_ID>
   ```
3. **Pela API REST:**
   ```bash
   curl -X POST http://localhost:8000/api/hitl/<APPROVAL_ID>/resolve \
     -H "Content-Type: application/json" \
     -d '{"approved": true, "notes": "Homologado pelo operador"}'
   ```

### 3.4 Expiração Automática por Segurança (TTL de 30 Minutos)
Toda solicitação retida possui validade de 30 minutos a partir do momento em que foi gerada. Se você não aprovar a ordem nesse intervalo, o status transiciona para `EXPIRED`. O agente cancela a execução, volta ao estado ocioso e registra o cancelamento nos logs do SQLite WAL, impedindo que comandos antigos fiquem esperando indefinidamente.

---

## 4. Configuração de Notificações Remotas (Telegram e Webhook)

Para receber solicitações de aprovação no celular quando estiver longe do computador:

### 4.1 Atualização de Notificações via API (Hot-Reload)
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

### 4.2 Configuração via Arquivo .env
No arquivo `/mnt/storage/piDots/.env`:
```env
WEBHOOK_NOTIFICATION_URL=https://seu-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_AQUI
TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
EVOLUTION_API_URL=http://host.docker.internal:8080
EVOLUTION_API_KEY=SUA_APIKEY_AQUI

# Isolamento Estrito com Bubblewrap (true bloqueia shell caso bwrap não esteja instalado)
STRICT_SANDBOX=false
```

Quando `STRICT_SANDBOX=true`, qualquer tentativa de rodar comandos de terminal sem o binário `bwrap` no host é imediatamente abortada com código de saída 126, impedindo execuções sem jaula de isolamento.

---

## 5. Configuração do Provedor de IA e Circuit Breaker

O piDots aceita qualquer provedor compatível com a API `/chat/completions` da OpenAI (OpenAI, Groq, OpenRouter, DeepSeek ou instâncias locais de llama.cpp/vLLM).

### 5.1 Atualizar Modelo e Chaves sem Reiniciar (Hot-Reload)
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
    "fallback_model": "meta-llama/llama-3.1-8b-instruct"
  }'
```

### 5.2 Funcionamento do Circuit Breaker
1. **Operação Normal (`CLOSED`):** Todas as chamadas vão para o endpoint principal (`AI_BASE_URL`). Falhas temporárias de rede (HTTP 502/503 ou 429) disparam até 3 retentativas com recuo exponencial e variação aleatória.
2. **Desvio para Fallback:** Se o provedor principal falhar de vez e você tiver configurado um provedor secundário (`AI_FALLBACK_URL`), a requisição é desviada na hora para o provedor reserva, sem travar a conversa do agente.
3. **Isolamento de Falhas (`OPEN`):** Ao acumular 3 falhas seguidas no provedor principal, o circuito abre por 60 segundos. Durante esse tempo, novas mensagens vão direto para o provedor reserva, poupando a máquina de esperar timeouts repetidos.
4. **Teste de Recuperação (`HALF_OPEN`):** Passados os 60 segundos, a próxima chamada testa o provedor principal. Se responder com HTTP 200, o tráfego volta ao normal. Se falhar, o circuito reabre por mais 60 segundos.
5. **Sem Provedor Secundário:** Caso não tenha definido uma URL secundária, o sistema simplesmente devolve a mensagem de erro da API sem comportamentos ocultos.

---

## 6. Tarefas Agendadas em Segundo Plano (Dot Heartbeat)

O agendador in-process (`pidots/core/scheduler.py`) executa rotinas cron a cada 15 segundos sem exigir daemons pesados:

### 6.1 Listar Tarefas Ativas
```bash
curl -s http://localhost:8000/api/tasks | jq .
```

### 6.2 Criar Nova Tarefa Agendada
Exemplo de checagem térmica a cada 15 minutos:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "dot_id": "dot-auditor",
    "task_name": "Checagem Térmica do Nó",
    "cron_expr": "*/15 * * * *",
    "action_prompt": "Verificar temperatura do processador e uso de RAM. Se normais, responder apenas HEARTBEAT_OK.",
    "target_channel_type": "internal"
  }'
```

### 6.3 Estados Possíveis de uma Tarefa:
- `IDLE`: Aguardando o próximo horário agendado (`next_run_at`).
- `RUNNING`: Em execução. Uma trava de memória impede que ela seja disparada novamente caso o ciclo demore mais de 15 segundos.
- `SILENT`: A tarefa terminou e respondeu `HEARTBEAT_OK`. Nada foi notificado e o contador de erros foi zerado.
- `COMPLETED`: A tarefa detectou algo importante e gerou um relatório técnico. O contador de erros foi zerado.
- `FAILED`: Ocorreu uma falha durante a execução. O erro real fica gravado em `last_result_summary` e o sistema aplica um recuo de espera entre 30s e 1 hora.
- `CIRCUIT_OPEN`: Ao acumular 5 falhas seguidas, o agendador desativa a tarefa (`is_active = 0`) para não consumir recursos do processador.
- `AUTH_REQUIRED`: Pausa preventiva de 10 minutos ativada quando a chave de API estiver vazia ou com valor padrão.

---

## 7. Mensageria Externa e Conexões Webhook

### 7.1 Bot do Telegram
Para conectar um bot do Telegram ao piDots através de webhooks reversos:
```bash
curl -X POST "https://api.telegram.org/bot<SEU_BOT_TOKEN>/setWebhook" \
  -d "url=https://seu-dominio.com/api/webhooks/telegram/dot-supervisor"
```
Cada mensagem enviada ao bot cria ou atualiza uma conversa correspondente no SQLite WAL.

### 7.2 WhatsApp via Evolution API
Configure o webhook da sua instância da Evolution API para apontar para:
- `http://localhost:8000/api/webhooks/whatsapp/dot-coder`
O piDots ignora mensagens enviadas pelo próprio número (`fromMe: true`) e processa as solicitações dos clientes.

### 7.3 Webhook Genérico para Scripts
Para enviar mensagens a partir de scripts bash, cronjobs ou pipelines:
```bash
curl -X POST http://localhost:8000/api/webhooks/incoming/dot-supervisor \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Executar auditoria nos logs do sistema",
    "sender_name": "Pipeline Local",
    "sender_id": "script-01"
  }'
```

---

## 8. Salas de Discussão Colaborativas (#canais)

As salas temáticas reúnem bots e humanos para debater problemas técnicos:

### 8.1 Criar uma Nova Sala
```bash
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "infraestrutura",
    "description": "Discussão sobre manutenção e saúde do nó"
  }'
```

### 8.2 Adicionar Agentes ao Canal
```bash
# Adicionar o coder
curl -X POST http://localhost:8000/api/channels/infraestrutura/members \
  -H "Content-Type: application/json" \
  -d '{"member_type": "dot", "member_id": "dot-coder"}'

# Adicionar o supervisor
curl -X POST http://localhost:8000/api/channels/infraestrutura/members \
  -H "Content-Type: application/json" \
  -d '{"member_type": "dot", "member_id": "dot-supervisor"}'
```

### 8.3 Postar Mensagens com Menções
```bash
curl -X POST http://localhost:8000/api/channels/infraestrutura/messages \
  -H "Content-Type: application/json" \
  -d '{
    "author_type": "user",
    "author_id": "lyon",
    "content": "Atenção @dot-coder favor verificar o consumo de RAM do Raspberry Pi"
  }'
```

O sistema impede conversas infinitas entre bots com regras rígidas: limite de 3 repasses por assunto, exigência de menção direta para um bot responder a outro e silêncio quando não houver o que acrescentar.

---

## 9. Manutenção Noturna e Cuidados com a Mídia Flash

Cartões MicroSD sofrem desgaste quando submetidos a escritas contínuas de disco. O piDots aplica proteções em várias camadas de engenharia:
1. **Modo WAL (`PRAGMA journal_mode = WAL;`):** Escritas sequenciais contínuas que evitam reescrever setores inteiros a cada transação.
2. **`PRAGMA synchronous = NORMAL;`:** Reduz drasticamente as chamadas de bloqueio `fsync` no hardware sem risco de corrupção do banco.
3. **`PRAGMA cache_size = -16000;`:** Aloca 16 MB de cache em memória RAM para aceleração de consultas e redução de leituras no cartão.
4. **`PRAGMA busy_timeout = 30000;`:** Aguarda até 30 segundos em concorrência pesada para eliminar erros de `database is locked`.
5. **`PRAGMA mmap_size = 67108864;`:** Habilita 64 MB de memory-mapped I/O no kernel Linux ARM64 para leitura de alta densidade.
6. **`PRAGMA temp_store = MEMORY;`:** Processa ordenações e tabelas temporárias inteiramente em RAM.
7. **`PRAGMA foreign_keys = ON;`:** Garante integridade referencial rigorosa em todas as relações de dados.
8. **Pasta `/tmp` em Memória (`tmpfs` de 64 MB):** Arquivos temporários residem na RAM, poupando o cartão de memória MicroSD contra degradação precoce de células.
9. **Checkpoint Noturno:** Rotina que consolida o log de transações, arquiva mensagens antigas (> 7 dias) e cria cópias de segurança consistentes.

### 9.1 Disparar Manutenção Manualmente
```bash
curl -s -X POST http://localhost:8000/api/edge/maintenance \
  -H "Content-Type: application/json" \
  -d '{"days_threshold": 7, "create_backup": true}' | jq .
```

### 9.2 Criar Backup Seguro do Banco sem Parar o Serviço
Nunca use `cp` direto no arquivo `pidots.db` enquanto o servidor estiver rodando, pois o arquivo WAL pode conter dados pendentes. Use sempre a rotina nativa do SQLite:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db ".backup /mnt/storage/piDots/data/pidots_backup_$(date +%Y%m%d_%H%M%S).db"
```

---

## 10. Diagnóstico de Falhas Comuns

### 10.1 Portas em Conflito ou Servidor Não Sobe
Verifique se outro processo está escutando nas portas do piDots:
```bash
sudo ss -tulpn | grep -E '8081|8082|8083|8088|8000'
```
Inspecione os logs detalhados:
```bash
docker compose logs pidots-core pidots-nginx
```

### 10.2 Chave de API Inválida (HTTP 401/403)
O agente interrompe a execução na hora, sem gastar chamadas extras:
- O banco registra o log interno com o prefixo `[FALHA DE AUTENTICAÇÃO]`.
- Atualize a credencial no arquivo `.env` ou envie a nova chave via API:
  ```bash
  curl -X POST http://localhost:8000/api/settings/ai \
    -H "Content-Type: application/json" \
    -d '{"api_key": "SUA_NOVA_CHAVE_AQUI"}'
  ```

### 10.3 Temperatura Elevada no Processador (SoC >= 72 °C)
Se o processador Broadcom passar dos 72 °C, o sistema desacelera o polling de segundo plano para resfriar a placa. Caso atinja 78 °C, um alerta crítico é emitido. Verifique se o dissipador térmico do Raspberry Pi está bem assentado ou instale uma ventoinha de refrigeração.

---

## 11. Estrutura de Portas do Proxy Reverso Nginx

O Nginx Alpine (`pidots-nginx`) gerencia a entrega estática e o proxy reverso em quatro portas públicas dedicadas e isoladas, conectando-se internamente ao `pidots-core` na porta 8000, consumindo menos de 6 MB de RAM total:

- **Porta 8081 (Landing Page):** Apresentação, simulador ReAct e benchmarks (`X-Edge-Service: landing-surface`).
- **Porta 8082 (Workspace SPA/PWA):** Console operacional, chat multi-bot e workspaces (`X-Edge-Service: app-console-root`).
- **Porta 8083 (Docs):** Manual técnico, relatórios e Mini API Tester (`X-Edge-Service: docs-guide-root`).
- **Porta 8088 (Gateway Unificado):** Roteamento reverso canônico e acesso agregado multi-superfície.
- **Porta 8000 (FastAPI Core):** Runtime assíncrono interno da API REST e WebSockets.

Para testar a resposta e os cabeçalhos das 5 portas operacionais:
```bash
# 1. Landing Page (Porta 8081)
curl -s -I http://localhost:8081/ | grep -E "HTTP/|X-Edge-Service"

# 2. Workspace SPA (Porta 8082)
curl -s -I http://localhost:8082/ | grep -E "HTTP/|X-Edge-Service"

# 3. Documentação Técnica (Porta 8083)
curl -s -I http://localhost:8083/ | grep -E "HTTP/|X-Edge-Service"

# 4. Gateway Central (Porta 8088)
curl -s -I http://localhost:8088/ | grep -E "HTTP/|X-Edge-Service"

# 5. Core FastAPI Interno (Porta 8000)
curl -s http://localhost:8000/health | jq .
```

---

## 12. Acesso Remoto com Cloudflare Tunnel (cloudflared)

Para acessar seu nó de qualquer lugar pela internet sem abrir portas no roteador de casa:

### 12.1 Instalação Automatizada
```bash
./cloudflared/setup-tunnel.sh
```
O instalador identifica se a máquina é ARM64 ou x86_64, baixa o binário e ajuda na autenticação.

### 12.2 Configuração de Subdomínios (`/etc/cloudflared/config.yml`)
```yaml
tunnel: SEU-TUNNEL-UUID
credentials-file: /etc/cloudflared/SEU-TUNNEL-UUID.json

ingress:
  - hostname: app.seu-dominio.com
    service: http://localhost:8082
  - hostname: docs.seu-dominio.com
    service: http://localhost:8083
  - hostname: pidots.seu-dominio.com
    service: http://localhost:8081
  - service: http_status:404
```

### 12.3 Execução Contínua via systemd
```bash
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared
```

---

## 23. Operação do Console `/app` Padrão OpenDots & CoAgents AG-UI (v1.6.0)

### 23.1 Navegação pela Activity Rail e 4 Painéis Laterais
Na lateral esquerda do Console `/app` (ou na visão `[O] DOTS` em dispositivos móveis), o operador dispõe da **Activity Rail** com 4 botões contextuais:
- **`[S] SPACES`:** Filtra e alterna entre Canais Multi-Bot (`#devops`, `#dot-dev`, `#council-room`), Threads de Conversa e Documentos persistidos em Spaces.
- **`[D] DOTS`:** Lista os coworkers ativos (`@dot-supervisor`, `@dot-coder`, `@dot-muse`, `@dot-auditor`), permite invocar o modal **Dots Studio** (`[+ CRIAR DOT]`) para cadastrar ou editar agentes com matriz visual de *Dynamic Tool Pruning*, e acionar **Handoff** ou **Conselho Tripartite**.
- **`[T] TASKS`:** Gerencia tarefas periódicas em segundo plano, disparos imediatos e monitoramento de logs de execução.
- **`[M] MEM/MCP`:** Inspeciona Core Memory, memórias arquivísticas FTS5 e gerencia ferramentas MCP Lite externas conectadas.

### 23.2 Tríptico Espacial e Modos de Operação
- **Modo 1 (Criação 50/50):** Teletipo à esquerda e Live Canvas à direita para codificação e visualização simultânea de diffs.
- **Modo 2 (Foco Teletipo):** Canvas recolhido via `Ctrl+B` ou `F11` para foco estrito em diálogo e comandos de terminal.
- **Modo 3 (Foco Canvas):** Área de artefato expandida para leitura imersiva de documentos longos e inspeção forense de governança HITL.

