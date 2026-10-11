# piDots

**Edge AI Coworker Persistente para Hardware Restrito (Raspberry Pi 4B 4GB ARM64)**

[Português](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)
![Arch](https://img.shields.io/badge/Architecture-ARM64%20%7C%20x86__64-informational?style=flat&logo=arm&logoColor=white)
![Hardware](https://img.shields.io/badge/Target-Raspberry%20Pi%204B%20(4GB)-C51A4A?style=flat&logo=raspberrypi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=flat&logo=docker&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Visao Geral

O **piDots** e uma plataforma de agentes autonomos persistentes (AI Coworkers) desenvolvida especificamente para operar 24/7 em hardware de borda com recursos estritamente limitados, tendo como alvo primario o **Raspberry Pi 4B com 4GB de RAM (ARM64)**.

Inspirado nos conceitos de agentes autonomos do OpenDots corporativo, o piDots foi reestruturado e otimizado como um monólito modular assincrono de alta performance. Ele elimina dependencias pesadas de navegadores Chromium headless, conteineres pesados de bancos vetoriais e orquestradores em Node.js, alcancando uma pegada de memoria operacional inferior a **50 MB de RAM** em idle e menos de **150 MB** sob execucao simultanea de multiplos agentes.

O sistema disponibiliza agentes persistentes orientados a tarefas tecnicas (DevOps, Pesquisa, Auditoria de Codigo), equipados com memoria de longo prazo, isolamento em sandbox de seguranca no sistema de arquivos, governanca com aprovacao humana (Human-in-the-Loop) para acoes de alto risco, e uma interface web SPA/PWA dark mode ultra-responsiva.

---

## Comparativo Tecnico: piDots vs OpenDots Corporativo

| Parametro | OpenDots (Padrao Corporativo) | piDots (Edge Computing) |
| :--- | :--- | :--- |
| **Hardware Minimo** | Servidor x86_64 com 8GB a 16GB RAM | Raspberry Pi 4B (4GB RAM) / ARM64 / x86_64 |
| **Stack de Execucao** | Node.js, Electron/Next.js, Python, Redis | Python 3.11-3.13 (FastAPI, uvloop, AsyncIO) |
| **Consumo de Memoria (Idle)** | 2.000 MB - 3.500 MB RAM | ~48 MB - 52 MB RAM (Reducao de ~98%) |
| **Consumo sob Carga (Pico)** | 4.000 MB - 6.000 MB RAM | < 150 MB RAM |
| **Banco de Dados & Estado** | PostgreSQL / Neo4j / Redis | SQLite com WAL Mode e PRAGMAs otimizados |
| **Banco Vetorial / Memoria** | ChromaDB / Pinecone / Qdrant (500MB+) | Extrator Vetorial CRC32 KNN em disco (< 5MB) |
| **Navegador e Leitura Web** | Chromium / Playwright headless (~500MB RAM) | Trafilatura / httpx assincrono puro em CPU (~20MB) |
| **Isolamento de Seguranca** | Docker aninhado / VM Cloud | Sandbox Bubblewrap (`bwrap`) nativo Linux |
| **Desgaste de Armazenamento** | Alto overhead de fsync em disco | Otimizado para preservar MicroSD / SSD USB |
| **Integracao e Distribuicao** | Sistema fechado / Microsservicos | Pacote Python modular (`pip install -e .`) e Docker |

---

## Arquitetura e Principais Modulos

O piDots foi projetado como um monolito modular assincrono com baixa sobrecarga computacional:

```
pidots/
├── __init__.py
├── cli.py               # Interface CLI nativa para terminal
├── config.py            # Configuracoes centralizadas e variaveis de ambiente
├── main.py              # Entrypoint FastAPI, rotas REST, SSE streaming e console SPA
├── core/
│   ├── __init__.py
│   ├── agent.py         # Motor ReAct assincrono com Dynamic Tool Pruning e AG-UI
│   ├── hitl.py          # Governanca Human-in-the-Loop com retencao e aprovacao
│   ├── messaging_gateway.py # Gateway unificado de mensageria e barramento de canais
│   ├── notifier.py      # Notificador HTTP e alertas externos
│   ├── orchestrator.py  # Orquestrador Multi-Bot (Supervisor, Handoff, mencoes @dot)
│   ├── scheduler.py     # Motor proativo Dot Heartbeat com calculo via croniter
│   └── state.py         # Modelos de eventos do protocolo AG-UI e estados de sessao
├── providers/
│   ├── __init__.py
│   └── openai_client.py # Cliente universal compativel com protocolo OpenAI API
├── storage/
│   ├── __init__.py
│   ├── db.py            # SQLite WAL calibrado para microSD e migracoes idempotentes
│   ├── spaces_manager.py # Workspaces isolados, versionamento e diffs unificados
│   └── vector_store.py  # Memoria vetorial KNN em disco com hashing CRC32
└── tools/
    ├── __init__.py
    ├── file_ops.py      # Operacoes atomicas de leitura, escrita e listagem em disco
    ├── registry.py      # Registro centralizado com Dynamic Tool Pruning
    ├── terminal.py      # Executor shell isolado via Bubblewrap ou subprocesso seguro
    └── web_reader.py    # Extrator semantico web assincrono com Trafilatura
```

---

## Capacidades Avancadas de Borda

### 1. Orquestracao Multi-Bot e Arquetipos Cognitivos
O piDots transcende o chat isolado permitindo cooperacao multi-agente in-process:
- **Mencoes Dinamicas (@dot):** O `ThreadRouter` extrai mencoes no formato `@nome_do_dot`, resolvendo interlocutores e gravando os participantes na tabela `thread_participants`.
- **Topologia Supervisor-Worker:** O supervisor planeja e delega subtarefas tecnicas atraves da ferramenta `delegate_task`, executando workers em threads isoladas e consolidando os resultados na conversa principal.
- **Transferencia de Lideranca (Handoff):** Ferramenta `handoff_to_dot` para transferir a titularidade operacional de uma thread para outro especialista com registro na tabela `agent_handoffs`.
- **Fitas de Carbono:** Mensagens de comunicacao inter-agente sao gravadas com `visibility: 'internal'` para auditoria sem poluir a interface do usuario.
- **Arquetipos Cognitivos:** Suporte nativo a perfis operacionais:
  - `supervisor`: Coordenador geral e gestao de metas.
  - `grok`: Analitico-convergente, auditoria de codigo, terminal e testes.
  - `muse`: Criativo-divergente, arquitetura, sintese e documentacao.
  - `auditor`: Inspecao de integridade, telemetria e conformidade.
- **Dynamic Tool Pruning:** Cada Dot carrega apenas as ferramentas permitidas em `allowed_tools_json`, reduzindo em ate 75% o consumo de tokens de contexto e eliminando alucinacoes.

### 2. Automacoes Proativas: Padrao Dot Heartbeat
O modulo `pidots/core/scheduler.py` implementa um scheduler in-process perpetuo baseado em `croniter`, sem necessidade de Redis ou Celery:
- **Rotinas Cron:** Agendamentos persistidos na tabela `scheduled_tasks` do SQLite WAL.
- **Diretriz de Silencio Operacional (HEARTBEAT_OK):** Ao executar checagens rotineiras, se o agente constatar integridade do sistema, responde estritamente `HEARTBEAT_OK`. O scheduler registra o estado como `SILENT` e hiberna sem gerar notificacoes inuteis ou poluir o banco de dados.
- **Controle de Exclusao Mutua in-process:** Trava em memoria (`_running_tasks`) que previne reentrancia e disparos em cascata da mesma tarefa quando o ciclo de raciocinio do LLM ultrapassa o intervalo periodico de varredura (15s).

### 3. Gateway de Mensageria Unificada e Canais Tematicos
O modulo `pidots/core/messaging_gateway.py` centraliza comunicacoes externas via webhooks HTTP stateless:
- **Adaptadores Nativos:** Endpoints dedicados para Telegram (`/api/webhooks/telegram/{dot_id}`), WhatsApp via Evolution API com autenticacao por apikey (`/api/webhooks/whatsapp/{dot_id}`) e Webhooks Genericos (`/api/webhooks/incoming/{dot_id}`).
- **Integracao Nativa Evolution API:** Variaveis `EVOLUTION_API_URL` e `EVOLUTION_API_KEY` com atualizacao a quente e suporte a envio assincrono via cliente HTTPx.
- **Salas Tematicas (#canais):** Canais de discussao colaborativa persistidos na tabela `channels`.
- **Trava Anti-Recursao Estrita:** Para evitar loops infinitos entre bots, o barramento de canais aplica:
  1. Contador de saltos estrito (`hop_count <= 3`).
  2. Bots so respondem a outros bots se houver mencao explicita `@dot_id`.
  3. Resposta silenciosa `NO_ACTION` quando o agente nao tem contribuicao relevante a acrescentar.

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

1. Clone o repositorio:
```bash
git clone https://github.com/lyon-christopher/pidots.git
cd pidots
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
| `GET` | `/` | Console operacional oficial SPA/PWA em Pixel Paper UI (Dark Noir e Blueprint) |
| `GET` | `/apresentacao` | Landing page oficial de alta conversao em Pixel Paper UI |
| `GET` | `/guia` | Guia operacional didatico com drawer lateral retratil e busca integrada |
| `GET` | `/relatorio` | Relatorio tecnico de viabilidade de engenharia e benchmarks |
| `GET` | `/health` | Telemetria de hardware (temperatura SoC, RAM, status SQLite WAL) |
| `GET` | `/manifest.json` | Manifesto PWA para instalacao em dispositivos moveis e desktop |
| `GET` | `/icon.svg` | Logotipo vetorial oficial em formato SVG com cache prolongado |
| `GET` | `/api/dots` | Listagem de AI Coworkers com arquetipos e status |
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
O piDots disponibiliza uma interface SPA/PWA nativa dark mode servida diretamente na rota raiz (`http://localhost:8000/`), projetada sob o design system **Pixel Paper UI**:
- **Estetica Pixel Paper UI:** Visual tatico inspirado em teletipos tecnicos, fichas catalograficas e papel milimetrado com alta densidade de informacoes e zero emojis.
- **Logotipo Vetorial Oficial:** Marca de identidade do piDots servida via `/icon.svg` com nos interconectados em verde (#10b981) e ciano (#38bdf8).
- **Sistema de 26 Icones SVGs Tecnicos:** Iconografia uniforme (`stroke-width: 2`, `stroke-linecap: round`) em telemetria, abas do workspace, secoes da sidebar e botoes de acao.
- **Visualizador de Diffs e Versionamento:** Inspecao lado a lado de alteracoes em arquivos persistidos no SQLite WAL com carimbos analogicos de status.
- **Governanca Interativa HITL:** Cartoes de aprovacao e veto forense de comandos com registro de auditoria e carimbos de estado.
- **Streaming de Raciocinio AG-UI:** Exibicao token a token de pensamentos e chamadas de ferramentas.

---

## Governanca e Seguranca

### Human-in-the-Loop (HITL)
Comandos com potencial destrutivo (como exclusoes recursivas, alteracoes de permissoes `chmod/chown`, comandos `sudo`, ou gravacoes em arquivos criticos do sistema) sao interceptados automaticamente pelo motor de governanca. A execucao e retida em estado pendente ate que um operador humano aprove explicitamente a acao via interface web ou CLI (`pidots hitl approve`).

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
├── docker-compose.yml               # Configuracao oficial de orquestracao Docker
├── Dockerfile                       # Imagem otimizada baseada em python:3.13-slim
├── LICENSE                          # Licenca MIT
├── MANUAL_OPERACIONAL.md            # Guia operacional de administracao e comandos
├── pidots/                          # Pacote de codigo-fonte principal
│   ├── config.py                    # Configuracoes Pydantic e variaveis de ambiente
│   ├── main.py                      # Servidor FastAPI, endpoints REST e streaming SSE
│   ├── core/                        # Ciclo ReAct, multi-bot, scheduler e mensageria
│   │   ├── agent.py                 # Ciclo de execucao autonomo do agente com Tool Pruning
│   │   ├── hitl.py                  # Interceptacao e gestao de acoes de alto risco
│   │   ├── messaging_gateway.py     # Gateway unificado de mensageria e barramento de canais
│   │   ├── notifier.py              # Notificacoes e webhooks externos
│   │   ├── orchestrator.py          # Orquestrador Multi-Bot e delegacao de subtarefas
│   │   ├── scheduler.py             # Escalonador proativo Dot Heartbeat via croniter
│   │   └── state.py                 # Gestao de estado e contexto de sessao
│   ├── providers/                   # Adaptadores de modelos de linguagem (LLM/SLM)
│   │   └── openai_client.py         # Provedor universal compativel com protocolo OpenAI
│   ├── storage/                     # Persistencia em SQLite WAL e busca vetorial
│   │   ├── db.py                    # Gerenciamento de conexao e esquemas de dados
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
└── scripts/                         # Scripts de teste automatizado e benchmarks
```

---

## Licenca

Este projeto e distribuido sob os termos da licenca MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informacoes.

Desenvolvido por **lyon christopher** (2026).
