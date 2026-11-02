# pidots // roadmap de redesign visual: opendots spatial + pixel paper ui

> **escopo:** refatoração visual 1:1 no padrão opendots / openbot mantendo a identidade pixel paper ui
> **superfícies alvo:** `/landing` (`pages/landing.html`), `/app` (`pages/app.html`) e `/docs` (`pages/docs.html`)
> **arquivos de estilo e script:** `static/css/*.css` (9 módulos) e `static/js/**/*.js` (11 módulos)
> **regra de segurança:** zero regressão nos ids de dom consumidos por `pidots-api.js`, `slash-commands.js` e `pidots-i18n.js`

---

## fase 1: fundação global e desobstrução do topo (`static/css/`) [concluída]

o objetivo desta fase foi eliminar o empilhamento de barras no topo da tela em dispositivos móveis e estabelecer o grid base compartilhado pelas 3 superfícies.

### 1.1. refinamento de variáveis (`static/css/tokens.css`)
- [x] padronizar alturas fixas de estrutura: `--header-height: 48px`, `--subheader-height: 38px` e `--mobile-nav-height: 54px`.
- [x] calibrar tokens de contraste dos temas `dark noir` e `blueprint` para bordas técnicas (`--border-crisp`, `--border-bright`) e estados de governança (`--cyan`, `--green`, `--amber`, `--red`).
- [x] definir larguras do tríptico opendots no desktop: `--rail-left-width: 270px` e `--rail-right-width: 340px`.

### 1.2. compactação da barra superior (`static/css/layout.css` e `static/css/mobile.css`)
- [x] **problema resolvido:** o cabeçalho empilhava duas linhas de botões (`[painel]`, `01 visao geral`, `02 workspace`, `03 documentação` + `[idioma: pt | en]`, `[tema: dark noir]`, `[manual tecnico]`), consumindo ~25% da altura útil em smartphones.
- [x] **solução aplicada:** unificado em uma única barra `.top-deck` de `48px` contendo:
  * esquerda: botão `[painel]` (`alt+b`) + indicador de pulso da marca `pidots`.
  * centro: comutador compacto das 3 superfícies (`01 visao geral`, `02 workspace`, `03 documentação`).
  * direita (desktop): botões utilitários `[idioma]`, `[tema]` e `[canvas // spaces]`.
  * mobile (`< 1024px`): ocultar os botões utilitários da faixa superior e move-los para o rodape da gaveta retrátil `[painel]`.

### 1.3. componentes pixel paper ui (`static/css/components.css`)
- [x] padronizar a classe `.paper-slip` (cartões de mensagem com sombra dura e borda sólida de 1px/2px).
- [x] padronizar a faixa `.tractor-holes` (fita perfurada de impressora matricial na margem esquerda da bobina).
- [x] padronizar o divisor `.picote-line` (`---- picote // destacar ----`) e o acordeão `.thought-notebook` (`[caderno de raciocinio - stream interno]`).
- [x] padronizar o componente `.hitl-box` (borda dupla ambar, preview de comando em fundo escuro e botões `[vetar]`, `[homologar]` e `[inspecionar ação]`).

---

## fase 2: redesign da superfície 01 — `/landing` (`pages/landing.html`) [concluída]

transformada a página de apresentação em uma vitrine developer-first no estilo opendots, demonstrando o sistema em ação antes mesmo do login.

### 2.1. estrutura html (`pages/landing.html`)
- [x] substituir o cabeçalho antigo pelo `.top-deck` unificado com a aba `01 visao geral` ativa.
- [x] **hero split-screen opendots:**
  * coluna esquerda: título de impacto focado nos 52 mb de ram no raspberry pi 4b, subtítulo tecnico e botões de ação `[abrir workspace /app]` e `[documentação /docs]`.
  * coluna direita: mini-simulador interativo em pixel paper ui exibindo uma fita real (`seq# 0001` e `seq# 0002`) com um card hitl clicável de demonstração.
- [x] **bento grid de telemetria de borda (4 cards):**
  * card 1: `52 mb / 384 mb ram rss` (folga de 86% no rpi 4b).
  * card 2: `4 especialistas nativos` (`[spv]`, `[cdr]`, `[mus]`, `[aud]` com dynamic tool pruning).
  * card 3: `sqlite wal + fts5 64d` (memória memgpt flash-safe para microsd).
  * card 4: `hop_count <= 3 & hitl crypto` (governança deny-by-default com hmac-sha256).

### 2.2. estilos e interatividade (`static/css/landing.css` e `static/js/landing/landing.js`)
- [x] ajustar o grid do hero e do bento grid para empilhamento fluido de 1 coluna em telas menores que `768px`.
- [x] adicionar interação leve em `landing.js` para permitir alternar os 4 arquetipos na vitrine e visualizar o orçamento de tokens de cada um (~420 a ~780 tokens/turno).

---

## fase 3: redesign da superfície 02 — `/app` (`pages/app.html`) [concluída]

aplicado o layout **1:1 opendots spatial triptych** no console operacional 24/7 mantendo todos os gatilhos do motor react e sse.

### 3.1. coluna esquerda — swarm & channels rail (`pages/app.html` + `static/css/spa.css`)
- [x] **bloco 1 (especialistas / swarm):** lista vertical com os 4 agentes (`dot-supervisor`, `dot-coder`, `dot-muse`, `dot-auditor`), exibindo badge de cor, status atual e orçamento de schema. clicar em um agente insere `@dot-id` no input ou filtra o workspace.
- [x] **bloco 2 (canais de missão `#`):** lista de salas tematicas (`#dot-dev`, `#devops`, `#council-room`) com indicador de `seq#` e limite `hop <= 3`.
- [x] **bloco 3 (rodape de telemetria fisica):** leituras compactas em barras ascii alimentadas por `/api/edge/triggers` (temperatura soc bcm2711 em °c, ram usada e status do sqlite wal).

### 3.2. coluna central — bobina de teletipo & command dock (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [x] **subheader de missão (`38px`):** exibir `canal de missão // dot-dev (sessão #001)` a esquerda e status `ag-ui stream pronto` + botão `[limpar fita]` a direita.
- [x] **bobina de teletipo:** manter a faixa `.tractor-holes` fixa a esquerda do stream de mensagens `.paper-slip`.
- [x] **dock de comando inferior:**
  * campo `textarea` auto-expansivel com suporte a `enter` para transmitir e `shift+enter` para quebra de linha.
  * popover flutuante `.slash-popover` ancorado acima do input, acionado instantaneamente (`< 16ms`) pelo `slash-commands.js` ao digitar `/` ou `@`.
  * botão de destaque `[transmitir comando]` a direita do input.

### 3.3. coluna direita — opendots live canvas, planner & memgpt (`pages/app.html` + `static/js/spa/pidots-ux.js`)
- [x] estruturar o painel direito com 3 abas superiores comutaveis sem recarregamento:
  * **aba `[spaces // md]`:** exibe o arquivo ativo do workspace (ex: `architecture_spec.md`) com suporte a visualização de `diff` unificado quando um agente altera um arquivo.
  * **aba `[plan // %]`:** renderiza a arvore de metas e marcos do `planner.py` (`<execution_plan>`) com barra de progresso percentual.
  * **aba `[memgpt]`:** exibe os 3 blocos residentes da `core memory` (`human`, `persona`, `active_context`) e campo de consulta para a `archival memory` (fts5).
- [x] conectar o botão `[inspecionar ação]` dos cards hitl para abrir automaticamente a analise forense do comando retido dentro da coluna direita.

### 3.4. barra de navegação inferior mobile (`static/css/mobile.css` + `static/js/spa/pidots-ux.js`)
- [x] manter a barra inferior de 4 botões exclusiva para telas `< 1024px`:
  * `[0] dots` -> exibe a coluna esquerda em tela cheia.
  * `[>] chat` -> exibe a coluna central (bobina + input dock).
  * `[*] canvas` -> exibe a coluna direita (spaces / planner / memgpt) com badge luminoso quando houver atualização pendente.
  * `[?] guia` -> abre o manual rapido ou redireciona para `/docs`.

---

## fase 4: redesign da superfície 03 — `/docs` e `/relatório` (`pages/docs.html`) [concluída]

padronizada a documentação tecnica e o relatório de engenharia com o mesmo cabeçalho `.top-deck` e layout de leitura orientada a artefatos.

### 4.1. estrutura split-view de documentação (`pages/docs.html` e `static/css/docs.css`)
- [x] **sidebar esquerda de capitulos (`260px`):** indice navegavel com filtro de busca instantanea (`docs.js`) cobrindo arquitetura, slash commands, api rest, governança hitl, mcp lite e manutencao sqlite wal.
- [x] **canvas central de leitura:** cartões `.paper-slip` com tabelas comparativas responsivas (`overflow-x: auto`) e blocos de codigo copiaveis.
- [x] **painel direito / mini api tester:** console interativo integrado em `docs.js` permitindo disparar requisicoes `get` e `post` ao vivo para `/health`, `/api/dots`, `/api/edge/triggers`, `/api/hitl/pending` e `/api/hitl/signed-resolve`, exibindo o json formatado em tempo real.

---

## fase 5: internacionalização, acessibilidade e homologação (`scripts/`) [concluída]

### 5.1. sincronização de dicionários (`data/locales/pt.json` e `data/locales/en.json`)
- [x] revisar todas as chaves `data-i18n` nas 3 páginas (`landing.html`, `app.html`, `docs.html`) para garantir que a troca em `[idioma: pt | en]` traduza 100% dos rotulos do novo layout sem usar `innerhtml`.

### 5.2. execução da bateria de testes de ui (`scripts/`)
- [x] executar `python3 scripts/test_phase1_opendots_agui.py` para validar eventos sse no novo dom.
- [x] executar `python3 scripts/test_phase2_opendots_layout.py` para verificar a presenca das 3 colunas do tríptico e da barra mobile.
- [x] executar `python3 scripts/test_phase3_opendots_dynamic_js.py` para validar os 30 slash commands e atalhos (`alt+b`, `alt+i`, `alt+h`, `ctrl+l`).
- [x] executar `python3 scripts/test_phase4_opendots_homologation.py` para confirmar integridade completa das rotas `/`, `/app`, `/docs` e `/relatório`.

---

## fase 6: redesign e despoluição da documentação tecnica (`/docs`) no padrão pixel paper technical wiki [concluída]

com base nos frameworks diataxis, stripe docs e nos principios de escaneabilidade tecnica do pixel paper ui, a superfície `/docs` foi integralmente despoluida e reformulada no padrão **pixel paper technical wiki**:

### 6.1. calibração tipográfica e despoluição visual (`static/css/docs.css`)
- [x] **tipografia dual:** títulos de secoes e passos (`.step-heading`, `.step-title`) configurados para usar `--font-display-modern` (`ibm plex sans` 700 / `jetbrains mono`), preservando `silkscreen` exclusivamente nos micro-badges ordinais (`.step-index-badge`).
- [x] **alivio de caixas e bordas:** remocao da sindrome "caixa sobre caixa", eliminando fundos pesados e sombras duras de contêineres textuais.
- [x] **divisores de trilha:** transicao de caixas fechadas para marcadores limpos de trilha com linha horizontal sutil.

### 6.2. estrutura dos 14 passos didaticos (`pages/docs.html`)
- [x] **remocao de carimbos decorativos:** expurgados os carimbos repetitivos (`stamp-notice`, `stamp-approved`) dos cabeçalhos dos passos 01 a 12 e 14.
- [x] **cartões tecnicos limpos:** handles de arquetipos no passo 01 (`@dot-supervisor`, `@dot-coder`, etc.) e subdominios dedicados no passo 14 (`pidots.*`, `app.*`, `docs.*`, `api.*`) em fonte mono tabular.
- [x] **hero compacto:** resumo horizontal com as 4 especificacoes essenciais de silicio (ram rss, especialistas, trava hop, sqlite wal).

### 6.3. reorganização do mini api tester (`pages/docs.html`, `static/css/docs.css`, `static/js/docs/docs.js`)
- [x] **categorização em 4 abas técnicas:** endpoints agrupados em 4 abas colapsáveis:
  * 01 // saude & silicio (`/health`, `/api/changelog`, `/api/edge/triggers`, `/data/locales/pt.json`)
  * 02 // agentes & canais (`/api/dots`, `/api/spaces`, `/api/channels`, `/api/tasks`, `/api/threads`)
  * 03 // computador & mcp (`/api/edge/computer/files`, `/api/edge/computer/exec`, `/api/tools`, `/api/mcp/servers`)
  * 04 // governanca & hitl (`/api/hitl/signed-resolve`, `/api/hitl/expire-stale`, `/api/edge/triggers/simulate`, `/api/edge/maintenance`, etc.)
- [x] **chips com badges de verbo http:** distincao visual semantica com badges para `get` (verde fosforo) e `post` (ciano blueprint).
- [x] **controles js e acessibilidade:** implementação de `alternargrupoapi` com sincronização de `aria-selected` e suporte resiliente a `.closest` em `selecionarendpointapi`.

---

## 7. dossiê de homologação final

o redesign visual do ecossistema pidots para a arquitetura **pixel paper ui (dark paper noir) e pixel paper technical wiki** foi integralmente homologado e consólidado com 100% de aprovação técnica nas suítes automatizadas:
* `scripts/test_pixel_paper_phase1_tokens_components.py` (aprovado).
* `scripts/test_pixel_paper_phase2_landing.py` (aprovado).
* `scripts/test_pixel_paper_phase3_docs.py` (aprovado).
* `scripts/test_pixel_paper_phase4_global_homologation.py` (aprovado).
* `scripts/test_phase20_port_decoupling_nginx.py` (aprovado nas 5 portas).
* `node scripts/test_cross_surface_router.js` (aprovado).
* conformidade total de acessibilidade wcag aa, paleta de alto contraste, tipografia fluida monoespaçada e ausência estrita de emojis.
