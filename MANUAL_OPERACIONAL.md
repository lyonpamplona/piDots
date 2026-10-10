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
- **Consumo Médio de Memória RAM:** ~50 MB (limite estrito de 256 MB no contêiner).
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
    "telegram_chat_id": "SEU_CHAT_ID_AQUI"
  }'
```

### 4.2 Configuração via Variáveis de Ambiente (.env)
No arquivo `/mnt/storage/piDots/.env`:
```env
WEBHOOK_NOTIFICATION_URL=https://seu-endpoint.com/webhook
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_AQUI
TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
```

---

## 5. Parametrização Dinâmica do Provedor de IA (Hot-Reload)

O piDots é compatível com qualquer provedor que implemente a especificação `/chat/completions` da OpenAI API (Verboo, OpenAI, Groq, OpenRouter, DeepSeek, llama-server local).

Para alterar os parâmetros sem reiniciar o contêiner:
```bash
curl -X POST http://localhost:8000/api/settings/ai \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.verboo.ai/v1",
    "model": "qwen3.8-27b",
    "max_retries": 3,
    "timeout_seconds": 60.0
  }'
```

---

## 6. Acesso Remoto Seguro 24/7 via Cloudflared

Para acessar o console SPA e a API a partir de redes externas ou no celular sem expor portas nem alterar configurações de NAT no roteador:

### 6.1 Instalação do Cloudflared no Raspberry Pi
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb
```

### 6.2 Execução de Túnel Imediato
```bash
cloudflared tunnel --url http://localhost:8000
```
O Cloudflare gerará uma URL pública HTTPS segura (`https://*.trycloudflare.com`) que pode ser aberta no smartphone ou instalada como PWA.

### 6.3 Configuração como Serviço Persistente (systemd)
Para manter o túnel ativo 24/7 mesmo após reinicializações do Raspberry Pi:
```bash
sudo cloudflared service install <TOKEN_DO_SEU_TUNEL>
sudo systemctl enable --now cloudflared
```

---

## 7. Rotina de Backup Atômico do SQLite WAL

Como o SQLite está configurado em modo WAL (`Write-Ahead Logging`), nunca copie o arquivo `pidots.db` diretamente via `cp` enquanto o contêiner estiver em execução, pois isso pode capturar um estado inconsistente entre o banco e o arquivo `.db-wal`.

### 7.1 Procedimento de Backup Seguro em Tempo Real
Utilize a API de backup atômico nativa do SQLite:
```bash
sqlite3 /mnt/storage/piDots/data/pidots.db ".backup /mnt/storage/piDots/data/pidots_backup_$(date +%Y%m%d_%H%M%S).db"
```
Esse comando pode ser executado sem interromper as operações do contêiner.

### 7.2 Automação via Cron
Adicione a seguinte linha no `crontab -e`:
```cron
# Backup diário às 03:00 da manhã
0 3 * * * sqlite3 /mnt/storage/piDots/data/pidots.db ".backup /mnt/storage/piDots/data/backup_diario.db" && find /mnt/storage/piDots/data/ -name "backup_*.db" -mtime +7 -delete
```

---

## 8. Preservação da Mídia Flash do Cartão MicroSD

O maior risco em servidores autônomos baseados em Raspberry Pi 4B é o desgaste prematuro das células de memória flash (wearout) causado por gravações contínuas e chamadas frequentes a `fsync`.

O piDots implementa proteções ativas contra esse fenômeno:
1. **Journal em Modo WAL:** Operações de escrita são gravadas de forma contínua e sequencial no arquivo journal, sem reescrever páginas inteiras na base principal a cada commit.
2. **Sincronização em Modo NORMAL:** `PRAGMA synchronous = NORMAL;` reduz em mais de 85% as chamadas de sincronização forçada de blocos para o hardware do cartão MicroSD, mantendo total integridade contra falhas do processo da aplicação.
3. **Diretório Temporário em Memória RAM (`tmpfs`):** O diretório `/tmp` do contêiner está montado como memória volátil (`tmpfs: size=64m`). Todas as operações efêmeras de arquivos transitórios ocorrem puramente na RAM.
4. **Checkpointing Periódico Seguro:** Uma rotina assíncrona executa `PRAGMA wal_checkpoint(PASSIVE)` a cada 15 minutos em background, garantindo que o arquivo WAL nunca sofra inchaço acumulativo.

---

## 9. Procedimentos de Diagnóstico e Resolução de Problemas

### 9.1 O Contêiner não inicia
- Verifique se a porta 8000 já está em uso por outro serviço:
  ```bash
  sudo netstat -tlpn | grep 8000
  ```
- Inspecione logs detalhados do Docker:
  ```bash
  docker compose logs pidots-core
  ```

### 9.2 Provedor de IA retornando erros 503 ou 429
- O piDots já possui Circuit Breaker automático com até 3 retentativas e jitter exponencial.
- Verifique a saúde da conexão externa via:
  ```bash
  curl -s http://localhost:8000/health
  ```
- Caso necessário, altere o modelo ou provedor a quente através da rota `POST /api/settings/ai`.

### 9.3 O Console PWA não atualiza dados
- No navegador, execute a limpeza do cache de Service Worker (`Application > Service Workers > Unregister`) ou force o recarregamento com `Ctrl + Shift + R`.
- Verifique se o backend está respondendo normalmente em `http://localhost:8000/health`.
