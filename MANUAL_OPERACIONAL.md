# piDots — Manual Operacional e Guia de Produção 24/7

**Projeto:** piDots (Motor Otimizado de AI Coworkers Persistentes para Raspberry Pi 4B)  
**Autor e Criador:** lyon christopher  
**Assistente:** Logger  
**Ambiente Alvo:** Raspberry Pi 4B (4GB RAM, ARM64 Cortex-A72, Linux / Docker Compose)  
**Versão:** 1.0.0 (Produção Estável)  

---

## 1. Visão Geral da Arquitetura

O **piDots** é uma reengenharia radical do ecossistema OpenDots voltada para hardware restrito. Enquanto o OpenDots original demanda de 1,8 GB a 3,2 GB de memória RAM (dependência pesada de Node.js SSR, Chromium headless contínuo e múltiplos contêineres efêmeros), o piDots foi estruturado como um monólito modular assíncrono em Python com `uvloop`, FastAPI e persistência SQLite WAL calibrada.

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
- **LOW:** Comandos de leitura e consultas seguras (`ls`, `cat`, `python3 script.py`). Execução liberada de forma autônoma.
- **MEDIUM:** Operações com redirecionamento de saída (`>`, `>>`, `tee`).
- **HIGH:** Exclusão de arquivos (`file_delete`), criação de skills persistentes.
- **CRITICAL:** Comandos shell perigosos (`rm -rf`, `mkfs`, `dd`, `chmod`, `sudo`, `curl | bash`, `reboot`, `shutdown`). A execução é **imediatamente bloqueada** até a decisão do operador.

### 3.2 Resolução de Solicitações HITL
As solicitações podem ser resolvidas de três formas:
1. **Pelo Console Web SPA:** No cartão interativo exibido na interface raiz (`GET /`).
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
```

---

## 5. Parametrização Dinâmica do Provedor de IA (Hot-Reload)

O piDots é compatível com qualquer provedor que implemente a especificação `/chat/completions` da OpenAI API (OpenAI, Groq, OpenRouter, DeepSeek, llama-server local).

Para alterar os parâmetros sem reiniciar o contêiner:
```bash
curl -X POST http://localhost:8000/api/settings/ai \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openai.com/v1",
    "model": "qwen3.8-27b",
    "max_retries": 3,
    "timeout_seconds": 60.0
  }'
```

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

### 6.3 Monitoramento de Status Operacional e Exclusao Mutua
Os status registrados na tabela `scheduled_tasks` sao:
- `IDLE`: Tarefa registrada aguardando o proximo horario de disparo (`next_run_at`).
- `RUNNING`: Ciclo em execucao ativa pelo `DotAgent` com trava em memoria (`_running_tasks`). Se o ciclo demorar mais de 15 segundos, novas varreduras ignoram o disparo repetido ate a conclusao da execucao.
- `SILENT`: A tarefa foi concluida com sucesso e emitiu `HEARTBEAT_OK`. Nenhuma notificacao externa foi disparada.
- `COMPLETED`: A tarefa detectou uma condicao relevante e gerou um relatorio textual ou alerta.
- `FAILED`: Ocorreu uma excecao durante o ciclo cognitivo. O erro e registrado em `last_result_summary`.

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

Para validar as novas capacidades de colaboracao e mensageria apos atualizacoes de codigo:

```bash
cd /mnt/storage/piDots

# 1. Validar orquestracao multi-bot, delegacao isolada e Dynamic Tool Pruning
python3 scripts/test_phase6_multibot.py

# 2. Validar agendamento proativo Dot Heartbeat e diretriz HEARTBEAT_OK
python3 scripts/test_phase7_scheduler.py

# 3. Validar gateway de mensageria, canais tematicos e trava anti-recursao
python3 scripts/test_phase8_messaging.py
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

### 13.2 Provedor de IA retornando erros 503 ou 429
- O piDots já possui Circuit Breaker automático com até 3 retentativas e jitter exponencial.
- Verifique a saúde da conexão externa via:
  ```bash
  curl -s http://localhost:8000/health
  ```
- Caso necessário, altere o modelo ou provedor a quente através da rota `POST /api/settings/ai`.

### 13.3 O Console PWA não atualiza dados
- No navegador, execute a limpeza do cache de Service Worker (`Application > Service Workers > Unregister`) ou force o recarregamento com `Ctrl + Shift + R`.
- Verifique se o backend está respondendo normalmente em `http://localhost:8000/health`.

### 13.4 Verificação de Cabeçalhos de Segurança HTTP
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

### 13.5 Exportação e Backup de Workspaces em ZIP
Para baixar o workspace completo e artefatos de um Dot via linha de comando (com fallback e agregação da tabela `spaces`):
```bash
curl -s http://localhost:8000/api/workspaces/dot-dev-core/export.zip -o workspace_dot-dev-core.zip
unzip -l workspace_dot-dev-core.zip
```

---

## 14. Console Web SPA Oficial e Componentes de Interface

O console oficial do piDots opera na porta 8000 (`http://localhost:8000/`) e oferece:
- **Design System Pixel Paper UI:** Interface tatica minimalista com contraste marcante (Dark Noir e Blueprint), visual de papel milimetrado e zero emojis.
- **Identidade e Logotipo Oficial:** Logotipo vetorial servido via rota oficial `/icon.svg` com headers de cache HTTP de 24 horas (`Cache-Control: public, max-age=86400`).
- **Telemetria de Hardware em Tempo Real:** Indicadores integrados de CPU Broadcom, RAM, temperatura do silicio e status do SQLite WAL.
- **Visualizador de Diffs Integrado:** Na aba SPACES, o botao `[VER DIFFS]` aciona a comparacao visual das revisoes armazenadas em `space_revisions` com carimbos analogicos de status.
- **Governanca no Feed:** Alertas de solicitacoes pendentes de comandos de risco com botoes táteis de homologacao e veto forense.
- **Landing Page Institucional:** Disponivel na rota `/apresentacao`, projetada para alta conversao sob a estetica Pixel Paper UI com calculadora de ROI e comparativo de custos Edge vs Nuvem.
- **Guia Didatico do Operador:** Disponivel na rota `/guia`, estruturado em estilo passo a passo com drawer lateral retratil, campo de busca dinamica e layout de largura total responsivo.
- **Roteamento Consolidado:** Todas as interfaces compartilham a mesma estetica visual unificada e consistente em producao.
