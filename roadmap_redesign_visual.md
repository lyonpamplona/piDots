# piDots // Roadmap de Redesign Visual: OpenDots Spatial + Pixel Paper UI

> **Escopo:** Refatoração visual 1:1 no padrão OpenDots / OpenBot mantendo a identidade Pixel Paper UI
> **Superfícies Alvo:** `/landing` (`pages/landing.html`), `/app` (`pages/app.html`) e `/docs` (`pages/docs.html`)
> **Arquivos de Estilo e Script:** `static/css/*.css` (9 módulos) e `static/js/**/*.js` (11 módulos)
> **Regra de Segurança:** Zero regressão nos IDs de DOM consumidos por `pidots-api.js`, `slash-commands.js` e `pidots-i18n.js`

---

## Fase 1: Fundação Global e Desobstrução do Topo (`static/css/`) [CONCLUÍDA]

O objetivo desta fase foi eliminar o empilhamento de barras no topo da tela em dispositivos móveis e estabelecer o grid base compartilhado pelas 3 superfícies.

### 1.1. Refinamento de Variáveis (`static/css/tokens.css`)
- [x] Padronizar alturas fixas de estrutura: `--header-height: 48px`, `--subheader-height: 38px` e `--mobile-nav-height: 54px`.
- [x] Calibrar tokens de contraste dos temas `Dark Noir` e `Blueprint` para bordas técnicas (`--border-crisp`, `--border-bright`) e estados de governança (`--cyan`, `--green`, `--amber`, `--red`).
- [x] Definir larguras do Tríptico OpenDots no desktop: `--rail-left-width: 270px` e `--rail-right-width: 340px`.

### 1.2. Compactação da Barra Superior (`static/css/layout.css` e `static/css/mobile.css`)
- [x] **Problema Resolvido:** O cabeçalho empilhava duas linhas de botões (`[PAINEL]`, `01 VISAO GERAL`, `02 WORKSPACE`, `03 DOCUMENTAÇÃO` + `[IDIOMA: PT | EN]`, `[TEMA: DARK NOIR]`, `[MANUAL TECNICO]`), consumindo ~25% da altura útil em smartphones.
- [x] **Solução Aplicada:** Unificado em uma única barra `.top-deck` de `48px` contendo:
  * Esquerda: Botão `[PAINEL]` (`Alt+B`) + Indicador de pulso da marca `piDots`.
  * Centro: Comutador compacto das 3 superfícies (`01 VISAO GERAL`, `02 WORKSPACE`, `03 DOCUMENTAÇÃO`).
  * Direita (Desktop): Botões utilitários `[IDIOMA]`, `[TEMA]` e `[CANVAS // SPACES]`.
  * Mobile (`< 1024px`): Ocultar os botões utilitários da faixa superior e move-los para o rodape da gaveta retrátil `[PAINEL]`.

### 1.3. Componentes Pixel Paper UI (`static/css/components.css`)
- [x] Padronizar a classe `.paper-slip` (cartões de mensagem com sombra dura e borda sólida de 1px/2px).
- [x] Padronizar a faixa `.tractor-holes` (fita perfurada de impressora matricial na margem esquerda da bobina).
- [x] Padronizar o divisor `.picote-line` (`---- PICOTE // DESTACAR ----`) e o acordeão `.thought-notebook` (`[CADERNO DE RACIOCINIO - STREAM INTERNO]`).
- [x] Padronizar o componente `.hitl-box` (borda dupla ambar, preview de comando em fundo escuro e botões `[VETAR]`, `[HOMOLOGAR]` e `[INSPECIONAR AÇÃO]`).

---

## Fase 2: Redesign da Superfície 01 — `/landing` (`pages/landing.html`) [CONCLUÍDA]

Transformada a página de apresentação em uma vitrine Developer-First no estilo OpenDots, demonstrando o sistema em ação antes mesmo do login.

### 2.1. Estrutura HTML (`pages/landing.html`)
- [x] Substituir o cabeçalho antigo pelo `.top-deck` unificado com a aba `01 VISAO GERAL` ativa.
- [x] **Hero Split-Screen OpenDots:**
  * Coluna Esquerda: Título de impacto focado nos 52 MB de RAM no Raspberry Pi 4B, subtítulo tecnico e botões de ação `[ABRIR WORKSPACE /APP]` e `[DOCUMENTAÇÃO /DOCS]`.
  * Coluna Direita: Mini-simulador interativo em Pixel Paper UI exibindo uma fita real (`SEQ# 0001` e `SEQ# 0002`) com um card HITL clicável de demonstração.
- [x] **Bento Grid de Telemetria de Borda (4 Cards):**
  * Card 1: `52 MB / 384 MB RAM RSS` (Folga de 86% no RPi 4B).
  * Card 2: `4 Especialistas Nativos` (`[SPV]`, `[CDR]`, `[MUS]`, `[AUD]` com Dynamic Tool Pruning).
  * Card 3: `SQLite WAL + FTS5 64D` (Memoria MemGPT Flash-Safe para MicroSD).
  * Card 4: `HOP_COUNT <= 3 & HITL Crypto` (Governança Deny-by-Default com HMAC-SHA256).

### 2.2. Estilos e Interatividade (`static/css/landing.css` e `static/js/landing/landing.js`)
- [x] Ajustar o grid do Hero e do Bento Grid para empilhamento fluido de 1 coluna em telas menores que `768px`.
- [x] Adicionar interação leve em `landing.js` para permitir alternar os 4 arquetipos na vitrine e visualizar o orçamento de tokens de cada um (~420 a ~780 tokens/turno).

---

## Fase 3: Redesign da Superfície 02 — `/app` (`pages/app.html`) [CONCLUÍDA]

Aplicado o layout **1:1 OpenDots Spatial Triptych** no console operacional 24/7 mantendo todos os gatilhos do motor ReAct e SSE.

### 3.1. Coluna Esquerda — Swarm & Channels Rail (`pages/app.html` + `static/css/spa.css`)
- [x] **Bloco 1 (Especialistas / Swarm):** Lista vertical com os 4 agentes (`dot-supervisor`, `dot-coder`, `dot-muse`, `dot-auditor`), exibindo badge de cor, status atual e orçamento de schema. Clicar em um agente insere `@dot-id` no input ou filtra o workspace.
- [x] **Bloco 2 (Canais de Missão `#`):** Lista de salas tematicas (`#dot-dev`, `#devops`, `#council-room`) com indicador de `SEQ#` e limite `HOP <= 3`.
- [x] **Bloco 3 (Rodape de Telemetria Fisica):** Leituras compactas em barras ASCII alimentadas por `/api/edge/triggers` (Temperatura SoC BCM2711 em °C, RAM usada e status do SQLite WAL).

### 3.2. Coluna Central — Bobina de Teletipo & Command Dock (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [x] **Subheader de Missão (`38px`):** Exibir `CANAL DE MISSÃO // DOT-DEV (SESSÃO #001)` a esquerda e status `AG-UI STREAM PRONTO` + botão `[LIMPAR FITA]` a direita.
- [x] **Bobina de Teletipo:** Manter a faixa `.tractor-holes` fixa a esquerda do stream de mensagens `.paper-slip`.
- [x] **Dock de Comando Inferior:**
  * Campo `textarea` auto-expansivel com suporte a `Enter` para transmitir e `Shift+Enter` para quebra de linha.
  * Popover flutuante `.slash-popover` ancorado acima do input, acionado instantaneamente (`< 16ms`) pelo `slash-commands.js` ao digitar `/` ou `@`.
  * Botão de destaque `[TRANSMITIR COMANDO]` a direita do input.

### 3.3. Coluna Direita — OpenDots Live Canvas, Planner & MemGPT (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [x] Estruturar o painel direito com 3 abas superiores comutaveis sem recarregamento:
  * **Aba `[SPACES // MD]`:** Exibe o arquivo ativo do workspace (ex: `architecture_spec.md`) com suporte a visualização de `diff` unificado quando um agente altera um arquivo.
  * **Aba `[PLAN // %]`:** Renderiza a arvore de metas e marcos do `planner.py` (`<execution_plan>`) com barra de progresso percentual.
  * **Aba `[MEMGPT]`:** Exibe os 3 blocos residentes da `Core Memory` (`human`, `persona`, `active_context`) e campo de consulta para a `Archival Memory` (FTS5).
- [x] Conectar o botão `[INSPECIONAR AÇÃO]` dos cards HITL para abrir automaticamente a analise forense do comando retido dentro da Coluna Direita.

### 3.4. Barra de Navegação Inferior Mobile (`static/css/mobile.css` + `static/js/spa/pidots-ux.js`)
- [x] Manter a barra inferior de 4 botões exclusiva para telas `< 1024px`:
  * `[0] DOTS` -> Exibe a Coluna Esquerda em tela cheia.
  * `[>] CHAT` -> Exibe a Coluna Central (Bobina + Input Dock).
  * `[*] CANVAS` -> Exibe a Coluna Direita (Spaces / Planner / MemGPT) com badge luminoso quando houver atualização pendente.
  * `[?] GUIA` -> Abre o manual rapido ou redireciona para `/docs`.

---

## Fase 4: Redesign da Superfície 03 — `/docs` e `/relatório` (`pages/docs.html`) [CONCLUÍDA]

Padronizada a documentação tecnica e o relatório de engenharia com o mesmo cabeçalho `.top-deck` e layout de leitura orientada a artefatos.

### 4.1. Estrutura Split-View de Documentação (`pages/docs.html` e `static/css/docs.css`)
- [x] **Sidebar Esquerda de Capitulos (`260px`):** Indice navegavel com filtro de busca instantanea (`docs.js`) cobrindo Arquitetura, Slash Commands, API REST, Governança HITL, MCP Lite e Manutencao SQLite WAL.
- [x] **Canvas Central de Leitura:** Cartões `.paper-slip` com tabelas comparativas responsivas (`overflow-x: auto`) e blocos de codigo copiaveis.
- [x] **Painel Direito / Mini API Tester:** Console interativo integrado em `docs.js` permitindo disparar requisicoes `GET` e `POST` ao vivo para `/health`, `/api/dots`, `/api/edge/triggers`, `/api/hitl/pending` e `/api/hitl/signed-resolve`, exibindo o JSON formatado em tempo real.

---

## Fase 5: Internacionalização, Acessibilidade e Homologação (`scripts/`) [CONCLUÍDA]

### 5.1. Sincronização de Dicionários (`data/locales/pt.json` e `data/locales/en.json`)
- [x] Revisar todas as chaves `data-i18n` nas 3 páginas (`landing.html`, `app.html`, `docs.html`) para garantir que a troca em `[IDIOMA: PT | EN]` traduza 100% dos rotulos do novo layout sem usar `innerHTML`.

### 5.2. Execucao da Bateria de Testes de UI (`scripts/`)
- [x] Executar `python3 scripts/test_phase1_opendots_agui.py` para validar eventos SSE no novo DOM.
- [x] Executar `python3 scripts/test_phase2_opendots_layout.py` para verificar a presenca das 3 colunas do tríptico e da barra mobile.
- [x] Executar `python3 scripts/test_phase3_opendots_dynamic_js.py` para validar os 30 Slash Commands e atalhos (`Alt+B`, `Alt+I`, `Alt+H`, `Ctrl+L`).
- [x] Executar `python3 scripts/test_phase4_opendots_homologation.py` para confirmar integridade completa das rotas `/`, `/app`, `/docs` e `/relatório`.

---

## Fase 6: Redesign e Despoluição da Documentação Tecnica (`/docs`) no Padrão Pixel Paper Technical Wiki [CONCLUÍDA]

Com base nos frameworks Diataxis, Stripe Docs e nos principios de escaneabilidade tecnica do Pixel Paper UI, a superfície `/docs` foi integralmente despoluida e reformulada no padrão **Pixel Paper Technical Wiki**:

### 6.1. Calibração Tipográfica e Despoluição Visual (`static/css/docs.css`)
- [x] **Tipografia Dual:** Títulos de secoes e passos (`.step-heading`, `.step-title`) configurados para usar `--font-display-modern` (`IBM Plex Sans` 700 / `JetBrains Mono`), preservando `Silkscreen` exclusivamente nos micro-badges ordinais (`.step-index-badge`).
- [x] **Alivio de Caixas e Bordas:** Remocao da sindrome "caixa sobre caixa", eliminando fundos pesados e sombras duras de contêineres textuais.
- [x] **Divisores de Trilha:** Transicao de caixas fechadas para marcadores limpos de trilha com linha horizontal sutil.

### 6.2. Estrutura dos 14 Passos Didaticos (`pages/docs.html`)
- [x] **Remocao de Carimbos Decorativos:** Expurgados os carimbos repetitivos (`stamp-notice`, `stamp-approved`) dos cabeçalhos dos passos 01 a 12 e 14.
- [x] **Cartões Tecnicos Limpos:** Handles de arquetipos no Passo 01 (`@dot-supervisor`, `@dot-coder`, etc.) e subdominios dedicados no Passo 14 (`pidots.*`, `app.*`, `docs.*`, `api.*`) em fonte mono tabular.
- [x] **Hero Compacto:** Resumo horizontal com as 4 especificacoes essenciais de silicio (RAM RSS, Especialistas, Trava Hop, SQLite WAL).

### 6.3. Reorganização do Mini API Tester (`pages/docs.html`, `static/css/docs.css`, `static/js/docs/docs.js`)
- [x] **Categorização em 4 Abas Técnicas:** Endpoints agrupados em 4 abas colapsáveis:
  * 01 // SAUDE & SILICIO (`/health`, `/api/changelog`, `/api/edge/triggers`, `/data/locales/pt.json`)
  * 02 // AGENTES & CANAIS (`/api/dots`, `/api/spaces`, `/api/channels`, `/api/tasks`, `/api/threads`)
  * 03 // COMPUTADOR & MCP (`/api/edge/computer/files`, `/api/edge/computer/exec`, `/api/tools`, `/api/mcp/servers`)
  * 04 // GOVERNANCA & HITL (`/api/hitl/signed-resolve`, `/api/hitl/expire-stale`, `/api/edge/triggers/simulate`, `/api/edge/maintenance`, etc.)
- [x] **Chips com Badges de Verbo HTTP:** Distincao visual semantica com badges para `GET` (verde fosforo) e `POST` (ciano blueprint).
- [x] **Controles JS e Acessibilidade:** Implementação de `alternarGrupoApi` com sincronização de `aria-selected` e suporte resiliente a `.closest` em `selecionarEndpointApi`.

---

## 7. Dossiê de Homologação Final

O redesign visual do ecossistema piDots para a arquitetura **Pixel Paper UI (Dark Paper Noir) e Pixel Paper Technical Wiki** foi integralmente homologado e consólidado com 100% de aprovação técnica nas suítes automatizadas:
* `scripts/test_pixel_paper_phase1_tokens_components.py` (Aprovado).
* `scripts/test_pixel_paper_phase2_landing.py` (Aprovado).
* `scripts/test_pixel_paper_phase3_docs.py` (Aprovado).
* `scripts/test_pixel_paper_phase4_global_homologation.py` (Aprovado).
* `scripts/test_phase20_port_decoupling_nginx.py` (Aprovado nas 5 portas).
* `node scripts/test_cross_surface_router.js` (Aprovado).
* Conformidade total de acessibilidade WCAG AA, paleta de alto contraste, tipografia fluida monoespaçada e ausência estrita de emojis.
