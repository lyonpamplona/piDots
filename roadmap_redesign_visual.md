# piDots // Roadmap de Redesign Visual: OpenDots Spatial + Pixel Paper UI

> **Escopo:** Refatoracao visual 1:1 no padrao OpenDots / OpenBot mantendo a identidade Pixel Paper UI
> **Superficies Alvo:** `/landing` (`pages/landing.html`), `/app` (`pages/app.html`) e `/docs` (`pages/docs.html`)
> **Arquivos de Estilo e Script:** `static/css/*.css` (9 modulos) e `static/js/**/*.js` (11 modulos)
> **Regra de Seguranca:** Zero regressao nos IDs de DOM consumidos por `pidots-api.js`, `slash-commands.js` e `pidots-i18n.js`

---

## Fase 1: Fundacao Global e Desobstrucao do Topo (`static/css/`)

O objetivo desta fase e eliminar o empilhamento de barras no topo da tela em dispositivos moveis e estabelecer o grid base compartilhado pelas 3 superficies.

### 1.1. Refinamento de Variaveis (`static/css/tokens.css`)
- [ ] Padronizar alturas fixas de estrutura: `--header-height: 48px`, `--subheader-height: 38px` e `--mobile-nav-height: 54px`.
- [ ] Calibrar tokens de contraste dos temas `Dark Noir` e `Blueprint` para bordas tecnicas (`--border-crisp`, `--border-bright`) e estados de governanca (`--cyan`, `--green`, `--amber`, `--red`).
- [ ] Definir larguras do Triptico OpenDots no desktop: `--rail-left-width: 270px` e `--rail-right-width: 340px`.

### 1.2. Compactacao da Barra Superior (`static/css/layout.css` e `static/css/mobile.css`)
- [ ] **Problema Atual:** O cabecalho empilha duas linhas de botoes (`[PAINEL]`, `01 VISAO GERAL`, `02 WORKSPACE`, `03 DOCUMENTACAO` + `[IDIOMA: PT | EN]`, `[TEMA: DARK NOIR]`, `[MANUAL TECNICO]`), consumindo ~25% da altura util em smartphones.
- [ ] **Solucao:** Unificar em uma unica barra `.top-deck` de `48px` contendo:
  * Esquerda: Botao `[PAINEL]` (`Alt+B`) + Indicador de pulso da marca `piDots`.
  * Centro: Comutador compacto das 3 superficies (`01 VISAO GERAL`, `02 WORKSPACE`, `03 DOCUMENTACAO`).
  * Direita (Desktop): Botoes utilitarios `[IDIOMA]`, `[TEMA]` e `[CANVAS // SPACES]`.
  * Mobile (`< 1024px`): Ocultar os botoes utilitarios da faixa superior e move-los para o rodape da gaveta retratil `[PAINEL]`.

### 1.3. Componentes Pixel Paper UI (`static/css/components.css`)
- [ ] Padronizar a classe `.paper-slip` (cartoes de mensagem com sombra dura e borda solida de 1px/2px).
- [ ] Padronizar a faixa `.tractor-holes` (fita perfurada de impressora matricial na margem esquerda da bobina).
- [ ] Padronizar o divisor `.picote-line` (`---- PICOTE // DESTACAR ----`) e o acordeao `.thought-notebook` (`[CADERNO DE RACIOCINIO - STREAM INTERNO]`).
- [ ] Padronizar o componente `.hitl-box` (borda dupla ambar, preview de comando em fundo escuro e botoes `[VETAR]`, `[HOMOLOGAR]` e `[INSPECIONAR ACAO]`).

---

## Fase 2: Redesign da Superficie 01 — `/landing` (`pages/landing.html`)

Transformar a pagina de apresentacao em uma vitrine Developer-First no estilo OpenDots, demonstrando o sistema em acao antes mesmo do login.

### 2.1. Estrutura HTML (`pages/landing.html`)
- [ ] Substituir o cabecalho antigo pelo `.top-deck` unificado com a aba `01 VISAO GERAL` ativa.
- [ ] **Hero Split-Screen OpenDots:**
  * Coluna Esquerda: Titulo de impacto focado nos 52 MB de RAM no Raspberry Pi 4B, subtitulo tecnico e botoes de acao `[ABRIR WORKSPACE /APP]` e `[DOCUMENTACAO /DOCS]`.
  * Coluna Direita: Mini-simulador interativo em Pixel Paper UI exibindo uma fita real (`SEQ# 0001` e `SEQ# 0002`) com um card HITL clicavel de demonstracao.
- [ ] **Bento Grid de Telemetria de Borda (4 Cards):**
  * Card 1: `52 MB / 384 MB RAM RSS` (Folga de 86% no RPi 4B).
  * Card 2: `4 Especialistas Nativos` (`[SPV]`, `[CDR]`, `[MUS]`, `[AUD]` com Dynamic Tool Pruning).
  * Card 3: `SQLite WAL + FTS5 64D` (Memoria MemGPT Flash-Safe para MicroSD).
  * Card 4: `HOP_COUNT <= 3 & HITL Crypto` (Governanca Deny-by-Default com HMAC-SHA256).

### 2.2. Estilos e Interatividade (`static/css/landing.css` e `static/js/landing/landing.js`)
- [ ] Ajustar o grid do Hero e do Bento Grid para empilhamento fluido de 1 coluna em telas menores que `768px`.
- [ ] Adicionar interacao leve em `landing.js` para permitir alternar os 4 arquetipos na vitrine e visualizar o orcamento de tokens de cada um (~420 a ~780 tokens/turno).

---

## Fase 3: Redesign da Superficie 02 — `/app` (`pages/app.html`)

Aplicar o layout **1:1 OpenDots Spatial Triptych** no console operacional 24/7 mantendo todos os gatilhos do motor ReAct e SSE.

### 3.1. Coluna Esquerda — Swarm & Channels Rail (`pages/app.html` + `static/css/spa.css`)
- [ ] **Bloco 1 (Especialistas / Swarm):** Lista vertical com os 4 agentes (`dot-supervisor`, `dot-coder`, `dot-muse`, `dot-auditor`), exibindo badge de cor, status atual e orcamento de schema. Clicar em um agente insere `@dot-id` no input ou filtra o workspace.
- [ ] **Bloco 2 (Canais de Missao `#`):** Lista de salas tematicas (`#dot-dev`, `#devops`, `#council-room`) com indicador de `SEQ#` e limite `HOP <= 3`.
- [ ] **Bloco 3 (Rodape de Telemetria Fisica):** Leituras compactas em barras ASCII alimentadas por `/api/edge/triggers` (Temperatura SoC BCM2711 em °C, RAM usada e status do SQLite WAL).

### 3.2. Coluna Central — Bobina de Teletipo & Command Dock (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [ ] **Subheader de Missao (`38px`):** Exibir `CANAL DE MISSAO // DOT-DEV (SESSAO #001)` a esquerda e status `AG-UI STREAM PRONTO` + botao `[LIMPAR FITA]` a direita.
- [ ] **Bobina de Teletipo:** Manter a faixa `.tractor-holes` fixa a esquerda do stream de mensagens `.paper-slip`.
- [ ] **Dock de Comando Inferior:**
  * Campo `textarea` auto-expansivel com suporte a `Enter` para transmitir e `Shift+Enter` para quebra de linha.
  * Popover flutuante `.slash-popover` ancorado acima do input, acionado instantaneamente (`< 16ms`) pelo `slash-commands.js` ao digitar `/` ou `@`.
  * Botao de destaque `[TRANSMITIR COMANDO]` a direita do input.

### 3.3. Coluna Direita — OpenDots Live Canvas, Planner & MemGPT (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [ ] Estruturar o painel direito com 3 abas superiores comutaveis sem recarregamento:
  * **Aba `[SPACES // MD]`:** Exibe o arquivo ativo do workspace (ex: `architecture_spec.md`) com suporte a visualizacao de `diff` unificado quando um agente altera um arquivo.
  * **Aba `[PLAN // %]`:** Renderiza a arvore de metas e marcos do `planner.py` (`<execution_plan>`) com barra de progresso percentual.
  * **Aba `[MEMGPT]`:** Exibe os 3 blocos residentes da `Core Memory` (`human`, `persona`, `active_context`) e campo de consulta para a `Archival Memory` (FTS5).
- [ ] Conectar o botao `[INSPECIONAR ACAO]` dos cards HITL para abrir automaticamente a analise forense do comando retido dentro da Coluna Direita.

### 3.4. Barra de Navegacao Inferior Mobile (`static/css/mobile.css` + `static/js/spa/pidots-ux.js`)
- [ ] Manter a barra inferior de 4 botoes exclusiva para telas `< 1024px`:
  * `[0] DOTS` -> Exibe a Coluna Esquerda em tela cheia.
  * `[>] CHAT` -> Exibe a Coluna Central (Bobina + Input Dock).
  * `[*] CANVAS` -> Exibe a Coluna Direita (Spaces / Planner / MemGPT) com badge luminoso quando houver atualizacao pendente.
  * `[?] GUIA` -> Abre o manual rapido ou redireciona para `/docs`.

---

## Fase 4: Redesign da Superficie 03 — `/docs` e `/relatorio` (`pages/docs.html`)

Padronizar a documentacao tecnica e o relatorio de engenharia com o mesmo cabeçalho `.top-deck` e layout de leitura orientada a artefatos.

### 4.1. Estrutura Split-View de Documentacao (`pages/docs.html` e `static/css/docs.css`)
- [ ] **Sidebar Esquerda de Capitulos (`260px`):** Indice navegavel com filtro de busca instantanea (`docs.js`) cobrindo Arquitetura, Slash Commands, API REST, Governanca HITL, MCP Lite e Manutencao SQLite WAL.
- [ ] **Canvas Central de Leitura:** Cartoes `.paper-slip` com tabelas comparativas responsivas (`overflow-x: auto`) e blocos de codigo copiaveis.
- [ ] **Painel Direito / Mini API Tester:** Console interativo integrado em `docs.js` permitindo disparar requisicoes `GET` ao vivo para `/health`, `/api/dots`, `/api/edge/triggers` e `/api/hitl/pending`, exibindo o JSON formatado em tempo real.

---

## Fase 5: Internacionalizacao, Acessibilidade e Homologacao (`scripts/`)

### 5.1. Sincronizacao de Dicionarios (`data/locales/pt.json` e `data/locales/en.json`)
- [ ] Revisar todas as chaves `data-i18n` nas 3 paginas (`landing.html`, `app.html`, `docs.html`) para garantir que a troca em `[IDIOMA: PT | EN]` traduza 100% dos rotulos do novo layout sem usar `innerHTML`.

### 5.2. Execucao da Bateria de Testes de UI (`scripts/`)
- [ ] Executar `python3 scripts/test_phase1_opendots_agui.py` para validar eventos SSE no novo DOM.
- [ ] Executar `python3 scripts/test_phase2_opendots_layout.py` para verificar a presenca das 3 colunas do triptico e da barra mobile.
- [ ] Executar `python3 scripts/test_phase3_opendots_dynamic_js.py` para validar os 30 Slash Commands e atalhos (`Alt+B`, `Alt+I`, `Alt+H`, `Ctrl+L`).
- [ ] Executar `python3 scripts/test_phase4_opendots_homologation.py` para confirmar integridade completa das rotas `/`, `/app`, `/docs` e `/relatorio`.