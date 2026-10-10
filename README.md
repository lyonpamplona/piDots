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

O piDots foi projetado seguindo o padrao de Clean Architecture modular com baixa sobrecarga computacional:

```
pidots/
├── api/            # Rotas REST, endpoints SSE e servico de arquivos estaticos (SPA PWA)
├── cli.py          # Interface de linha de comando nativa para terminal
├── config.py       # Gerenciamento centralizado de configuracoes e variaveis de ambiente
├── core/
│   ├── agent.py    # Motor ReAct assincrono com streaming token-a-token
│   └── hitl.py     # Sistema de governanca Human-in-the-Loop com fila de retencao
├── main.py         # Entrypoint FastAPI com ciclo de vida assincrono (lifespan)
├── memory/
│   └── vector_store.py # Motor vetorial e busca semantica CRC32 KNN ultra-leve
├── models/
│   └── schemas.py  # Modelos Pydantic v2 com tipagem e validacao rigorosa
├── providers/
│   └── openai_client.py # Cliente universal OpenAI-compativel com streaming SSE
├── storage/
│   ├── database.py       # Camada SQLite com WAL mode, busy_timeout e PRAGMAs
│   └── spaces_manager.py # Gerenciador de workspaces isolados por Dot
└── tools/
    ├── base.py       # Registro central de ferramentas assincronas
    ├── bash.py       # Executor de comandos em sandbox Bubblewrap com timeout
    ├── file_ops.py   # Operacoes seguras de leitura, escrita e patch de arquivos
    ├── memory.py     # Ferramentas de memoria de longo prazo do agente
    └── web_reader.py # Extrator semantico de conteudo web baseado em Trafilatura
```

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
Preencha a sua chave de API e selecione o modelo de linguagem desejado:
```dotenv
OPENAI_API_KEY=sua-chave-aqui
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
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
from pidots.config import settings
from pidots.core.agent import DotAgent
from pidots.models.schemas import DotCreate
from pidots.providers.openai_client import OpenAIUniversalProvider
from pidots.storage.database import Database
from pidots.storage.spaces_manager import SpacesManager
from pidots.tools.base import ToolRegistry

async def main():
    # Inicializar banco de dados otimizado SQLite WAL
    db = Database(settings.DATABASE_PATH)
    await db.initialize()

    # Inicializar gerenciador de workspaces e provedor de inferencia
    spaces = SpacesManager(settings.WORKSPACES_ROOT)
    provider = OpenAIUniversalProvider(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.OPENAI_MODEL,
    )
    tools = ToolRegistry()

    # Criar definicao do agente
    dot_spec = DotCreate(
        name="DevOps-Agent",
        description="Agente autonomo de automacao e auditoria",
        system_prompt="Voce e um engenheiro de infraestrutura e seguranca.",
        allowed_tools=["read_file", "write_file", "execute_bash", "fetch_web_page"]
    )
    dot = await db.create_dot(dot_spec)

    # Instanciar e executar ciclo de raciocinio do agente
    agent = DotAgent(
        dot=dot,
        db=db,
        provider=provider,
        tools=tools,
        spaces_manager=spaces
    )

    result = await agent.run_turn("Analise os arquivos do workspace e crie um relatorio.")
    print("Resposta do agente:", result.response)

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## API REST e Streaming em Tempo Real

A aplicacao expoe endpoints para integracao externa com suporte a streaming Server-Sent Events (SSE):

| Metodo | Endpoint | Descricao |
| :--- | :--- | :--- |
| `GET` | `/` | Interface grafica PWA/SPA em tema escuro |
| `GET` | `/health` | Checagem de integridade e telemetria de RAM/CPU |
| `GET` | `/api/system/status` | Metricas completas do sistema, banco e espacos |
| `GET` | `/api/dots` | Listagem de todos os AI Coworkers registrados |
| `POST` | `/api/dots` | Criacao e configuracao de novo AI Coworker |
| `POST` | `/api/dots/{id}/chat` | Envio de mensagem com execucao sincrona |
| `GET` | `/api/dots/{id}/chat/stream` | Canal de streaming SSE em tempo real (token a token) |
| `GET` | `/api/hitl/pending` | Listagem de acoes retidas aguardando aprovacao |
| `POST` | `/api/hitl/{id}/approve` | Aprovacao humana para execucao de comando retido |
| `POST` | `/api/hitl/{id}/reject` | Rejeicao de comando retido na governanca |
| `GET` | `/api/spaces/{id}/files` | Listagem segura de arquivos no workspace do agente |

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
# Executar todos os testes de regressao
python3 scripts/test_phase1.py
python3 scripts/test_phase2.py
python3 scripts/test_phase3.py
python3 scripts/test_phase4.py
python3 scripts/test_phase5.py

# Executar teste de carga e concorrencia (Edge Stress Test)
python3 scripts/stress_test.py
```

---

## Estrutura do Repositorio

```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── ARCHITECTURE.md          # Especificacao detalhada de arquitetura e I/O
├── docker-compose.yml       # Configuracao oficial de orquestracao Docker
├── Dockerfile               # Imagem otimizada baseada em python:3.13-slim
├── LICENSE                  # Licenca MIT
├── MANUAL_OPERACIONAL.md    # Guia operacional de administracao e comandos
├── pidots/                  # Pacote de codigo-fonte principal
├── pidots_spa_prototype.html# Aplicacao Single Page Application PWA
├── pyproject.toml           # Arquivo padrao PEP 517/518/621 de empacotamento
├── README.md                # Documentacao principal (Portugues do Brasil)
├── README_EN.md             # Documentacao espelhada (Ingles Americano)
├── requirements.txt         # Dependencias estritas do projeto
└── scripts/                 # Scripts de teste automatizado e benchmarks
```

---

## Licenca

Este projeto e distribuido sob os termos da licenca MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informacoes.

Desenvolvido por **lyon christopher** (2026).
