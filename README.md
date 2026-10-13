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

O **piDots** é uma plataforma de agentes autônomos persistentes (AI Coworkers) projetada para funcionar 24 horas por dia em computadores de placa única (SBCs), Mini PCs e servidores locais, tendo o **Raspberry Pi 4B com 4GB de RAM (ARM64)** como referência de hardware.

Desenvolvido a partir dos conceitos de agentes persistentes do OpenDots, o piDots foi totalmente reconstruído como um monólito modular assíncrono em Python (FastAPI + uvloop). Eliminamos navegadores Chromium headless em segundo plano, bancos vetoriais pesados em contêineres separados e dependências de Node.js. O resultado prático é uma aplicação estável que consome menos de **50 MB de RAM** em repouso e menos de **100 MB** durante a execução ativa de múltiplos agentes.

O sistema disponibiliza especialistas orientados a tarefas técnicas (DevOps, Pesquisa, Auditoria de Código), equipados com memória de longo prazo, isolamento em sandbox de segurança no sistema de arquivos, governança com aprovação humana (Human-in-the-Loop) para ações de alto risco, e uma interface web SPA/PWA dark mode ultra-responsiva.

---

## Comparativo Técnico: piDots vs OpenDots Corporativo

| Parâmetro | OpenDots (Padrão Corporativo) | piDots (Computação de Borda) |
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
├── main.py              # Entrypoint FastAPI, rotas REST, SSE streaming e console SPA
├── core/
│   ├── __init__.py
│   ├── agent.py         # Motor ReAct assincrono com Dynamic Tool Pruning e AG-UI
│   ├── council.py       # Conselho Consultivo e debate dialetico tripartite
│   ├── dot_pack.py      # Empacotamento, exportacao e importacao portavel de Dot Packs v1.0
│   ├── edge_triggers.py # Triggers de hardware edge (SoC Broadcom BCM2711, MicroSD e RAM)
│   ├── hitl.py          # Governanca Human-in-the-Loop com retencao e aprovacao
│   ├── messaging_gateway.py # Gateway unificado de mensageria e barramento de canais
│   ├── notifier.py      # Notificador HTTP e alertas externos
│   ├── orchestrator.py  # Orquestrador Multi-Bot (Supervisor, Handoff, mencoes @dot)
│   ├── planner.py       # Planejamento em dois estagios (Goals, Milestones e Checkpoints)
│   ├── scheduler.py     # Motor proativo Dot Heartbeat com calculo via croniter e circuit breaker
│   ├── self_healing.py  # Self-Healing Harness e diagnostico cirurgico de tracebacks
│   └── state.py         # Modelos de eventos do protocolo AG-UI e estados de sessao
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Cliente universal compativel com protocolo OpenAI API
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
    ├── registry.py      # Registro centralizado de 23 ferramentas com Dynamic Tool Pruning
    ├── terminal.py      # Executor shell isolado via Bubblewrap ou subprocesso seguro
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
- **Perfis Especializados:** Suporte nativo a papéis operacionais bem definidos:
  - `supervisor`: Coordenador geral e gestão de metas.
  - `grok` ou `coder`: Analítico, terminal, automação e testes de código.
  - `muse`: Arquitetura de sistemas, síntese e redação técnica.
  - `auditor`: Inspeção de segurança, telemetria e conformidade de comandos.
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

### 8. Espaço de Conhecimento Compartilhado e Dot Packs Portáveis
- **Shared Knowledge Space (`pidots/storage/shared_space.py`):** Quadro colaborativo indexado por `(thread_id, topic_key)` na tabela `thread_shared_notes`. Permite gravação (`shared_space_write`), leitura (`shared_space_read`) e sobrescrita colaborativa entre bots na mesma thread, com formatação XML `<shared_knowledge_space>`.
- **Dot Packs v1.0 (`pidots/core/dot_pack.py`):** Formato portável de manifesto JSON que empacota definições do Dot, perfil, ferramentas, blocos de Core Memory, memórias duradouras e arquivos de workspace. Exportação via `GET /api/dots/{dot_id}/export-pack` e importação atômica via `POST /api/dots/import-pack`.

### 9. Triggers de Hardware e Manutenção Noturna do MicroSD
- **Triggers Orientados a Eventos de Hardware (`pidots/core/edge_triggers.py`):** Monitora temperatura do SoC Broadcom BCM2711 via sysfs Linux (`/sys/class/thermal/thermal_zone0/temp`), espaço livre no MicroSD e memória RAM livre. Emite alertas proativos e ativa throttle automático caso a temperatura ultrapasse 72°C ou o espaço em disco seja inferior a 10%. Endpoint: `GET /api/edge/triggers`.
- **Rotina de Manutenção Noturna Autônoma (`pidots/storage/maintenance.py`):** Executa `PRAGMA wal_checkpoint(TRUNCATE)` para esvaziar o arquivo WAL, consolida e poda mensagens brutas antigas (> 7 dias) na tabela `episodic_memories`, gera backups atômicos seguros via `VACUUM INTO` em conexão isolada (`isolation_level=None`) e atualiza índices com `PRAGMA optimize`. Endpoint: `POST /api/edge/maintenance`.

### 10. Internacionalização Bilíngue Nativa (PT/EN) e Micro-Motor de Borda
- **Micro-Motor Vanilla JS (`static/pidots-i18n.js`):** Alternância instantânea de idioma (< 10ms) sem frameworks pesados ou consumo extra de RAM, com detecção e persistência segura em `localStorage.getItem('pidots_lang')`.
- **Dicionários Atômicos JSON (`data/locales/pt.json` e `data/locales/en.json`):** Dicionários semânticos servidos com cache de borda e fallback defensivo inteligente.
- **Mutação Estrita via textContent:** Mecanismo declarativo baseado em atributos `data-i18n` e `data-i18n-attr`, com imunidade total a injeções de script (XSS).
- **Onboarding e Patch Notes SemVer v1.3.0:** Esteira de ativação guiada de primeiro acesso e modal de patch notes dinâmico com categorização semântica das atualizações (`/api/changelog`).

### 11. Protocolo Unificado de Slash Commands (/), Triptico Adaptativo e Resiliencia Mobile (v1.3.0)
- **Catalogo Completo de 30 Slash Commands:** Comandos categorizados em 6 grupos operacionais (Sistema, Agentes, Memoria, Tarefas, Borda, Exportacao), invocados com `/` no teletipo. Comandos locais (`/clear`, `/theme`, `/lang`, `/telemetry`, etc.) executam instantaneamente no cliente (< 16ms) com zero chamadas externas e zero consumo de tokens.
- **Motor de Autocomplete Popover em Vanilla JS:** Componente ultraleve (< 10KB) com busca fuzzy em memoria, navegacao ciclica por setas (ArrowUp/ArrowDown), autocompletar com Tab/Enter, fechamento por Esc e tolerancia a falhas via distancia Levenshtein.
- **Recibos Tatis de Teletipo (Slash Receipt Slip):** Emissao de comprovantes com timestamp UTC, identificador sequencial `SEQ#`, picote serrilhado e teto estrito de 150 nos DOM para estabilidade de memoria sob operacao continua.
- **Triptico Adaptativo do Workspace (1024px-1440px):** Layout inteligente que colapsa a barra lateral esquerda sob demanda em uma gaveta de 260px com backdrop, preservando a visibilidade da bobina de teletipo (largura util elevada de 202px para > 750px) e mantendo o Live Canvas em split 50/50.
- **Telemetria Consolidada Edge Pulse Chip:** Linha unica de alta densidade no cabecalho (`[EDGE // 48.2 °C // 118 MB // WAL ATIVO // HITL 0]`), economizando mais de 360px de espaco horizontal.
- **Engine Mobile window.visualViewport & Touch WCAG 2.2:** Deteccao automatica de abertura de teclado virtual que oculta barras inferiores, mantem a rolagem suave do input no iOS Safari e Android Chrome, e garante tap targets minimos de 44px (WCAG 2.2 AA).

### 12. Novo Tour Spotlight Interativo In-Context e Onboarding FTUE de Alto Desempenho (v1.5.0)
- **Motor PiDotsTourEngine em Vanilla JS (< 12KB):** Substituicao completa de modais estaticos por um sistema de ancoragem espacial in-context no DOM real. Utiliza `box-shadow: 0 0 0 9999px rgba(7, 9, 12, 0.84)` em camada de composicao direta da GPU, demandando < 1% de CPU no Raspberry Pi 4B e zero dependencias externas.
- **Cinco Etapas Canonicas de Capacitacao:** Guia pratico cobrindo o Squad Central de Especialistas, o Terminal de Comandos & Teletipo, o Comutador de Modo Foco (Zen vs 50/50), o Live Canvas & Diffs e a Gaveta Tecnica (F1).
- **Comando de Barra `/tour`:** Permite rever o tour a qualquer momento ou reinicia-lo do zero via `/tour reset`.
- **Acionamento Tatico na Gaveta Tecnica e Context Menu:** Card dedicado `[REVER GUIA OPERACIONAL SPOTLIGHT]` dentro da central F1 / `[SISTEMA]` e atalho rapido com botao direito do mouse.
- **Disparo Automatico no Primeiro Acesso:** Detecta novos operadores via `localStorage.getItem('pidots_tour_completed')` e dispara suavemente com 600ms de desacoplamento apos o assentamento do cockpit.

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
AI_MODEL=qwen3.8-27b

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
docker compose logs -f pidots-core
```
O servidor estara acessivel na porta `8000` (`http://localhost:8000`).

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
| `GET` | `/` | Landing page oficial de apresentacao e onboarding em Pixel Paper UI |
| `GET` | `/app` | Console operacional oficial SPA/PWA em Pixel Paper UI (Dark Noir e Blueprint) |
| `GET` | `/workspace` | Alias operacional canonico para a estacao de trabalho SPA/PWA (`/app`) |
| `GET` | `/docs` | Guia didatico canonico com busca client-side (Ctrl+K), drawer retratil e API tester |
| `GET` | `/api/docs` | Swagger UI interativo OpenAPI desacoplado para desenvolvedores |
| `GET` | `/api/openapi.json` | Esquema OpenAPI 3.0 estruturado em JSON bruto |
| `GET` | `/apresentacao` | Redirecionamento permanente HTTP 308 (RFC 7538) para a raiz `/` |
| `GET` | `/guia` | Redirecionamento permanente HTTP 308 (RFC 7538) para `/docs` |
| `GET` | `/console` | Redirecionamento permanente HTTP 308 (RFC 7538) para `/app` |
| `GET` | `/relatorio` | Relatorio tecnico de viabilidade de engenharia e benchmarks |
| `GET` | `/health` | Telemetria de hardware (temperatura SoC, RAM, status SQLite WAL) |
| `GET` | `/manifest.json` | Manifesto PWA para instalacao em dispositivos moveis e desktop (`start_url: /app`) |
| `GET` | `/sw.js` | Service Worker PWA com cache defensivo v5 para operacao offline |
| `GET` | `/icon.svg` | Logotipo vetorial oficial em formato SVG com cache prolongado |
| `GET` | `/static/pidots-i18n.js` | Micro-motor Vanilla JS de internacionalizacao client-side |
| `GET` | `/data/locales/{lang}.json` | Dicionarios atomicos de localizacao bilingue (PT/EN) com cache de borda |
| `GET` | `/api/changelog` | Historico SemVer e notas de atualizacao categorizadas (Patch Notes v1.3.0) |
| `GET` | `/api/dots` | Listagem de AI Coworkers com arquetipos e status |
| `GET` | `/api/dots/{id}/export-pack` | Exportacao portavel do manifesto DotPack v1.0 (persona, memorias, workspace) |
| `POST` | `/api/dots/import-pack` | Importacao atomica de novos agentes a partir de arquivo de DotPack |
| `POST` | `/api/threads` | Criacao de thread de conversacao duravel |
| `GET` | `/api/threads/{id}/messages` | Historico de mensagens com metadados multi-ator e visibilidade |
| `POST` | `/api/threads/{id}/runs` | Ciclo autonomo do Dot com streaming SSE (Protocolo AG-UI v1.0) |
| `GET` | `/api/hitl/pending` | Fila de solicitacoes de aprovacao humana pendentes |
| `POST` | `/api/hitl/{id}/resolve` | Resolucao oficial (aprovacao ou veto) de acao retida |
| `POST` | `/api/hitl/webhook-callback` | Callback assincrono para resolucao de HITL remota |
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

### Console Operacional Web SPA e Design System Pixel Paper UI
O piDots disponibiliza uma interface SPA/PWA nativa dark mode servida na rota canonica `/app` (ou `/workspace`), projetada sob o design system **Pixel Paper UI**:
- **Estetica Pixel Paper UI:** Visual tatico inspirado em teletipos tecnicos, fichas catalograficas e papel milimetrado com alta densidade de informacoes, tipografia tecnica crisp e estetica retro minimalista de 1-bit.
- **Logotipo Vetorial Oficial:** Marca de identidade do piDots servida via `/icon.svg` com nos interconectados em verde (#10b981) e ciano (#38bdf8).
- **Tres Modos de Operacao Ergonomicos:**
  - *Modo 1: Criacao 50/50:* Chat de teletipo e Live Canvas lado a lado para trabalho ativo de geracao e edicao de codigo e documentos.
  - *Modo 2: Foco Zen (Claude Code / Linear):* Barra lateral e canvas recolhidos, centralizando o chat com largura calibrada (880px) para leitura contínua e raciocínio profundo.
  - *Modo 3: Painel Tecnico & Gestao:* Telemetria de hardware (SoC/RAM/WAL), configuracao de provedores e sandbox acessiveis sob demanda via gaveta tecnica (F1 / `[SISTEMA]` ou `/telemetry`).
- **Squad Central de Especialistas:** Interface despoluida exibindo apenas os 4 coworkers essenciais (Supervisor, Dev Assistant, Muse e Auditor), eliminando a sobrecarga de dezenas de agentes residuais.
- **Teletipo e Input Desobstruidos:** Remocao das calhas laterais de 20px (40px totais) do trator de papel e do prefixo rigido no input, concedendo maxima largura util de leitura e digitacao.
- **Visualizador de Diffs e Versionamento:** Inspecao lado a lado de alteracoes em arquivos persistidos no SQLite WAL com carimbos analogicos de status.
- **Governanca Interativa HITL Just-in-Time:** Cartoes de aprovacao e veto forense exibidos apenas quando ha acoes retidas, com persistencia de logs de seguranca.
- **Streaming de Raciocinio AG-UI:** Exibicao token a token de pensamentos e chamadas de ferramentas.
- **Onboarding Walkthrough Guiado:** Esteira interativa de 5 passos para novos operadores com retencao de conclusao no cliente e reabertura via atalho F1.
- **Central de Patch Notes SemVer (v1.4.0):** Modal dinâmico sincronizado com `/api/changelog`, categorizando novidades em Quatro Pilares: Incluido, Ajustado, Removido e Seguranca & Borda.

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
| `Tecla /` | Autocomplete Popover | Dispara menu de 30 Slash Commands com busca fuzzy no teletipo |
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
| **Sistema & UI** | `/help`, `/clear`, `/theme`, `/lang`, `/info`, `/status`, `/telemetry`, `/pwa`, `/tour`, `/onboarding`, `/changelog` | `/tour`, `/tour reset`, `/telemetry`, `/theme noir` |
| **Agentes & Multi-Bot** | `/dots`, `/handoff`, `/council`, `/delegate`, `/archetype`, `/tools` | `/dots`, `/handoff dot-researcher`, `/council analise termica` |
| **Memoria & Conhecimento** | `/memory`, `/archival`, `/shared`, `/spaces`, `/diff` | `/archival SQLite WAL`, `/spaces analise.md`, `/diff` |
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

# Teste de resiliencia integral (Tipagem de erros, AG-UI v1.0, 3 consumidores, Circuit Breaker)
python3 scripts/test_resilience_phases.py

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
├── data/                            # Dados estaticos, changelog e dicionarios de localizacao
│   ├── changelog.json               # Historico de versoes e notas de atualizacao SemVer v1.3.0
│   └── locales/                     # Dicionarios de internacionalizacao atomicos (i18n)
│       ├── en.json                  # Dicionario de termos em Ingles Tecnico
│       └── pt.json                  # Dicionario de termos em Portugues do Brasil
├── docker-compose.yml               # Configuracao oficial de orquestracao Docker
├── Dockerfile                       # Imagem otimizada baseada em python:3.13-slim
├── LICENSE                          # Licenca MIT
├── MANUAL_OPERACIONAL.md            # Guia operacional de administracao e comandos
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
├── pidots_apresentacao_pixel_paper.html # Landing page oficial de apresentacao
├── pidots_guia.html                 # Guia operacional didatico passo a passo
├── pidots_spa_prototype.html        # Console operacional SPA/PWA oficial
├── pyproject.toml                   # Empacotamento padrao PEP 517/518/621
├── README.md                        # Documentacao principal (Portugues do Brasil)
├── README_EN.md                     # Documentacao espelhada (Ingles Americano)
├── relatorio_estudo_pidots.html     # Relatorio tecnico de viabilidade e engenharia
├── requirements.txt                 # Dependencias estritas do projeto
├── SECURITY.md                      # Politica de seguranca e reporte de vulnerabilidades
├── scripts/                         # Scripts de teste automatizado e benchmarks
└── static/                          # Assets estaticos do frontend
    └── pidots-i18n.js               # Micro-motor Vanilla JS de internacionalizacao client-side
```

---

## Licenca

Este projeto e distribuido sob os termos da licenca MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informacoes.

Desenvolvido por **lyon christopher** (2026).
