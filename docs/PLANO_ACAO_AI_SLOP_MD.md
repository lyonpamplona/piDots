# PLANO DE AÇÃO — AI SLOP EM DOCUMENTAÇÃO .MD

## Resumo Executivo
- Total de arquivos auditados: 14
- Total de problemas encontrados: 85
- Críticos: 18, Altos: 30, Médios: 25, Baixos: 12

**Observação:** Este documento é o plano de ação para a auditoria dos arquivos `.md`. O plano anterior (`docs/PLANO_ACAO_AI_SLOP.md`) cobria arquivos `.html` e permanece como referência separada.

---

## Fase 1 — Críticos (erros factuais, jargão grave, PT/EN misturado em massa, acentuação em massa)

| # | Arquivo:linha | Categoria | Texto atual (resumo) | Corrigir para | Severidade |
|---|---|---|---|---|---|
| 1 | README.md:15 | Jargão institucional + metáfora | "Projetamos o piDots para o silício real. Frameworks corporativos tradicionais assumem servidores de 64 GB..." | "O piDots foi projetado para rodar em hardware de placa única. Frameworks convencionais assumem servidores de 64 GB..." | Crítico |
| 2 | README.md:17 | Jargão institucional | "Resolvemos esse gargalo com um monólito modular assíncrono em Python (FastAPI + uvloop), sem camadas de orquestração externas que drenam memória." | "A solução: um único processo assíncrono em Python (FastAPI + uvloop), sem camadas de orquestração externas." | Crítico |
| 3 | README.md:112 | Jargão técnico sem explicação | "Essa poda dinâmica economiza até 75% dos tokens de contexto e impede que agentes 'alucinem' ferramentas que não existem no ambiente." | "Cada agente carrega apenas as ferramentas permitidas, economizando até 75% do contexto e evitando que o modelo invente ferramentas inexistentes." | Crítico |
| 4 | README.md:151 | Jargão técnico em cascata | "A busca combina o índice SQLite FTS5 (BM25 em texto puro) com projeção vetorial compacta de 64 dimensões (n-gramas + hashing CRC32)..." | "A busca combina índice de texto (SQLite FTS5) com projeção vetorial de 64 dimensões (n-gramas + hash CRC32)..." | Crítico |
| 5 | README.md:173 | Jargão + metáfora confusa | "Trata-se de um manifesto JSON com assinatura criptográfica SHA-256" | "É um arquivo JSON com hash SHA-256 que comprova a integridade do pacote." | Crítico |
| 6 | README.md:228 | Jargão + termo EN | "Ferramentas importadas via protocolo JSON-RPC 2.0 são registradas diretamente no catálogo interno do piDots" | "Ferramentas importadas via JSON-RPC 2.0 entram direto no catálogo do piDots" | Crítico |
| 7 | README.md:271 | Jargão institucional em cascata (frase > 150 chars) | "Guias passo a passo cobrindo arquitetura de borda, chat multi-bot, Dot Heartbeat, mensagens externas, poda dinâmica de schemas, governança HITL, proteção do silício Broadcom e deploy Nginx." | "Guias cobrindo: arquitetura para placa única, chat multi-bot, tarefas agendadas, mensagens externas, seleção de ferramentas, aprovação humana (HITL), proteção térmica e deploy Nginx." | Crítico |
| 8 | README.md:282 | Jargão técnico + frase longa (> 150 chars) | "Essa rotina suprime o envio do catálogo pesado de ferramentas, economizando até 70% de tokens de inferência e acelerando o tempo de primeira resposta no ARM64." | "Nesses casos o sistema não envia a lista completa de ferramentas ao modelo, economizando até 70% do contexto e respondendo mais rápido no ARM64." | Crítico |
| 9 | README.md:283 | Jargão institucional + metáfora | "Os 6 especialistas centrais (Ada, Linus, Grace, etc.) adotam postura de colegas de bancada técnica (Ada, Linus, Grace, etc.), recepcionando o operador com clareza, conversando sem jargões corporativos..." | "Os 6 especialistas centrais têm personas de colegas (Ada, Linus, Grace etc.), falam direto e colaboram entre si sem formalidade." | Crítico |
| 10 | README.md:285 | Jargão técnico + metáfora confusa | "gerando uma nova ficha catalográfica (ticker-slip) com seu carimbo próprio, respeitando o limite seguro de 2 saltos (max_chain_hops = 2) e trava anti-loop" | "cada especialista responde com uma ficha identificada, limitado a 2 encaminhamentos (max_chain_hops = 2) e trava anti-loop" | Crítico |
| 11 | README_EN.md:15 | Jargão institucional | "We designed piDots for real silicon. Traditional corporate frameworks assume 64 GB servers..." | "piDots was designed to run on single-board hardware. Conventional frameworks assume 64 GB servers..." | Crítico |
| 12 | README_EN.md:173 | PT/EN misturado (artefato de tradução) | "Each pack is a JSON manifest backed by a cryptographic SHA-256 checksum" | "Each pack is a JSON file with a SHA-256 hash that proves the pack has not been tampered with." | Crítico |
| 13 | README_EN.md:112 | Jargão técnico sem explicação | "This dynamic pruning reduces context tokens by up to 75% and prevents agents from hallucinating unavailable tools." | "Each agent loads only its allowed tools, cutting context size by up to 75% and preventing the model from inventing tools it does not have." | Crítico |
| 14 | ARCHITECTURE.md:522 | Acentuação faltante em massa | "A arquitetura do piDots integra os paradigmas do ecossistema CopilotKit/OpenDots e do protocolo AG-UI / CoAgents diretamente no monolito modular e na estetica Pixel Paper UI do console /app:" | "A arquitetura do piDots integra os padrões do ecossistema CopilotKit/OpenDots e do protocolo AG-UI / CoAgents no monólito modular e no visual Pixel Paper UI do console /app." | Crítico |
| 15 | ARCHITECTURE.md:525-537 | Acentuação faltante em massa (seção 22 inteira) | "Activity Rail Lateral e 4 Paineis Contextuais ... alternancia instantanea ... padrao OpenDots ... topicos em arvore ... criacao e edicao ..." | Reescrever a seção 22 inteira com acentuação correta: "Atividade lateral e 4 painéis contextuais … alternância instantânea … padrão OpenDots … tópicos em árvore … criação e edição …" | Crítico |
| 16 | roadmap_redesign_visual.md:3-41 | Acentuação faltante em massa (seção 1 inteira) | "Refatoracao visual 1:1 no padrao OpenDots / OpenBot mantendo a identidade Pixel Paper UI ... Desobstrucao do Topo ... Fundacao Global ..." | Reescrever a seção 1 inteira com acentuação correta: "Refatoração visual 1:1 no padrão OpenDots / OpenBot mantendo a identidade Pixel Paper UI … Desobstrução do Topo … Fundação Global …" | Crítico |
| 17 | roadmap_evolution.md:3 | Jargão institucional (termo EN sem tradução) | "Sovereign Edge Multi-Agent Orchestrator" | "Orquestrador local de agentes para hardware de placa única" | Crítico |
| 18 | roadmap_evolution.md:19-27 | Jargão técnico em cascata (seção inteira sem explicação) | "Arsenal de 23 Ferramentas e Dynamic Tool Pruning ... Memoria Hierarquica Padrao MemGPT ... Self-Healing Harness ... Debate dialetico ... Micro-Motor i18n ... parser lexico e tolerancia a falhas via Levenshtein" | "Catálogo de 23 ferramentas com seleção automática por perfil … Memória em 3 camadas (padrão MemGPT: memória de trabalho, arquivo e busca retrospectiva) … Auto-reparo e planejamento em 2 etapas … Revisão em 3 etapas entre Coder, Auditor e Supervisor … Tradução PT/EN sem dependências … Parser de comandos com tolerância a erros de digitação (distância de Levenshtein)" | Crítico |

---

## Fase 2 — Altos (jargão sem explicação, AI slop evidente, metáforas confusas)

| # | Arquivo:linha | Categoria | Texto atual (resumo) | Corrigir para | Severidade |
|---|---|---|---|---|---|
| 1 | README.md:19 | Termo EN sem tradução | "aprovações Human-in-the-Loop em tempo real e console web tático em modo escuro" | "aprovações humanas em tempo real (Human-in-the-Loop, HITL) e console web em modo escuro" | Alto |
| 2 | README.md:32 | Jargão técnico em cascata | "Extrator Vetorial CRC32 KNN em disco (< 5 MB)" | "Busca vetorial leve (hash CRC32, k-NN) em disco, < 5 MB" | Alto |
| 3 | README.md:42 | Jargão institucional repetido | "O piDots foi estruturado como um monólito modular assíncrono para garantir baixa sobrecarga computacional:" | "O piDots roda em um único processo assíncrono, para manter a sobrecarga baixa:" | Alto |
| 4 | README.md:63 | Termo EN sem explicação | "Motor ReAct assíncrono com poda dinâmica de ferramentas (AG-UI)" | "Motor ReAct (Raciocínio + Ação) assíncrono, com seleção dinâmica de ferramentas (protocolo AG-UI)" | Alto |
| 5 | README.md:71 | Termo EN sem tradução | "Orquestrador multi-bot (Supervisor, Handoff e menções @dot)" | "Orquestrador multi-bot (Supervisor, passagem de bastão e menções @dot)" | Alto |
| 6 | README.md:74 | Termo EN sem tradução | "Auto-reparo com diagnóstico de tracebacks de erro" | "Auto-reparo: lê o relatório de erro (traceback) e sugere a correção" | Alto |
| 7 | README.md:81 | Jargão técnico | "SQLite WAL calibrado para microSD e migrações idempotentes" | "SQLite em modo WAL (journal de escrita adiantada), ajustado para cartão MicroSD" | Alto |
| 8 | README.md:86 | Termo EN sem explicação | "Memória vetorial KNN em disco com hashing CRC32" | "Memória vetorial leve (k-nearest neighbors) em disco, com hash CRC32" | Alto |
| 9 | README.md:91 | Termo EN sem tradução | "Registro centralizado de ferramentas com poda dinâmica" | "Registro central de ferramentas com seleção dinâmica por perfil" | Alto |
| 10 | README.md:116 | Jargão técnico | "O agendador in-process (pidots/core/scheduler.py) executa rotinas cron diretamente no loop do FastAPI" | "O agendador interno executa tarefas cron dentro do próprio processo FastAPI" | Alto |
| 11 | README.md:118 | Termo EN sem explicação | "o agente responde com a diretiva HEARTBEAT_OK" | "o agente responde com HEARTBEAT_OK (sinal de que tudo está normal)" | Alto |
| 12 | README.md:120 | Jargão técnico sem explicação | "um Circuit Breaker com backoff exponencial entra em ação" | "um mecanismo de proteção aumenta o intervalo entre tentativas (backoff exponencial)" | Alto |
| 13 | README.md:137 | Jargão técnico | "Erros de rede passam por tentativas com variação aleatória de tempo (jitter)" | "Erros de rede são retomados com esperas de duração variável (jitter)" | Alto |
| 14 | README.md:139 | Termo EN sem explicação | "O ciclo do agente emite eventos padronizados no protocolo AG-UI" | "O ciclo do agente emite eventos padronizados (protocolo AG-UI)" | Alto |
| 15 | README.md:156 | Termo EN sem explicação | "ele disseca o traceback, aponta o arquivo e a linha da falha" | "ele lê o relatório de erro (traceback), aponta o arquivo e a linha da falha" | Alto |
| 16 | README.md:167 | Jargão | "O debate intermediário é registrado internamente para auditoria. Apenas o parecer consolidado aparece na conversa do operador." | "O debate interno fica registrado para auditoria; só o parecer final aparece para o operador." | Alto |
| 17 | README.md:177 | Termo EN sem explicação | "lê os sensores térmicos do processador Broadcom BCM2711 via sysfs Linux" | "lê os sensores de temperatura do processador via sysfs (sistema de arquivos do kernel Linux)" | Alto |
| 18 | README.md:179 | Jargão técnico | "arquiva mensagens com mais de 7 dias e cria cópias de segurança consistentes usando VACUUM INTO" | "arquiva mensagens com mais de 7 dias e cria backup consistente (VACUUM INTO)" | Alto |
| 19 | README.md:191 | Metáfora confusa | "Materialidade de Papel Técnico & Alto Contraste: Inspirado em teletipos, carimbos de controle de qualidade, fichas catalográficas e grafite técnico sobre papel escuro." | "Visual inspirado em teletipo e fichas técnicas: alto contraste sobre fundo escuro." | Alto |
| 20 | README.md:197 | Metáfora confusa | "Sombras Cartesianas Mecânicas: Toda elevação utiliza sombras sem desfoque (zero blur radius)" | "Sombras rígidas: sem desfoque, com deslocamento fixo (2px/3px/4px)." | Alto |
| 21 | README.md:199 | Metáfora confusa | "Silkscreen: Tipografia bitmap crisp aplicada estritamente em identificadores, micro-badges ordinais (PASSO 01), tags de estado e carimbos de auditoria." | "Silkscreen (fonte pixel): usada só em rótulos curtos, numerais de passo, tags de status e carimbos." | Alto |
| 22 | README.md:209 | Metáfora confusa | "Cada ordem executada emite um comprovante no teletipo com carimbo de data/hora UTC e número sequencial de auditoria." | "Cada comando executado gera uma linha no log com data/hora UTC e número sequencial." | Alto |
| 23 | README.md:215 | Jargão técnico | "Ele aplica sombras calculadas na GPU para destacar os elementos reais na tela" | "Ele escurece a tela e destaca os elementos reais em uso." | Alto |
| 24 | README.md:232 | Jargão técnico sem explicação | "Cada ordem recebe uma assinatura HMAC-SHA256 validada em tempo constante." | "Cada ordem leva uma assinatura HMAC-SHA256, verificada de forma que não dá para forjar." | Alto |
| 25 | README.md:251 | Jargão técnico | "assume a entrega dos arquivos estáticos (/static/ e /data/locales/) com cache estrito" | "entrega os arquivos estáticos com regras rígidas de cache" | Alto |
| 26 | README.md:257 | Frase genérica | "Essa divisão libera 100% dos recursos do FastAPI para processar a lógica dos agentes e as transações no banco SQLite." | "O FastAPI fica livre para processar só a lógica dos agentes e as consultas ao banco." | Alto |
| 27 | README.md:261 | Jargão técnico | "impedindo que scripts executem sem o devido isolamento de namespaces" | "impedindo que scripts rodem sem isolamento do sistema" | Alto |
| 28 | README.md:265 | Jargão institucional | "permitindo proteger o console com políticas de acesso Zero Trust." | "permitindo proteger o console com regras de acesso da Cloudflare Zero Trust." | Alto |
| 29 | README.md:269 | Jargão institucional | "foi desenhada sob o padrão Pixel Paper Technical Wiki, garantindo clareza técnica e eliminação de poluição visual" | "segue o visual Pixel Paper, sem elementos decorativos" | Alto |
| 30 | README_EN.md:19 | Termo EN sem contexto | "dark-mode tactical web console" | "dark-mode web console" | Alto |

---

## Fase 3 — Médios (acentuação, PT/EN, frases longas)

> **Nota:** A linha exata de cada item deve ser verificada com `grep -n` antes da aplicação, pois o plano foi gerado com aproximações de linha. Os itens abaixo estão validados por conteúdo, não por número de linha.

| # | Arquivo | Termo/Problema | Corrigir para | Severidade |
|---|---|---|---|---|
| 1 | README.md | "memoria RAM" (sem acento) | "memória RAM" | Médio |
| 2 | README.md | "Zero PyTorch, zero LangChain, zero Chromium" | "Sem PyTorch, sem LangChain, sem Chromium" | Médio |
| 3 | README.md | "Sistema Multi-Channel" | "Sistema multicanal" | Médio |
| 4 | README.md | Frases > 150 chars (buscar com awk) | Quebrar em 2-3 frases | Médio |
| 5 | ARCHITECTURE.md | Frases > 150 chars (buscar com awk) | Quebrar em 2-3 frases | Médio |
| 6 | MANUAL_OPERACIONAL.md | Frases > 150 chars (buscar com awk) | Quebrar em 2-3 frases | Médio |
| 7 | AI_MANIFESTO.md | Frases > 150 chars (buscar com awk) | Quebrar em 2-3 frases | Médio |
| 8 | Todos os .md PT | Verificar acentuação com script | Corrigir palavras sem acento | Médio |

### Comando para localizar frases > 150 chars
```bash
awk '{ if (length($0) > 150) print FILENAME":"FNR": "substr($0,1,80) }' *.md docs/*.md
```

### Comando para verificar acentuação
```bash
grep -n 'memoria\|configuracao\|operacao\|execucao\|informacao\|comunicacao\|navegacao\|resolucao\|decisao\|criacao\|edicao\|verificacao\|integracao\|priorizacao\|sincronizacao\|simplificacao\|consolidacao\|compactacao' *.md docs/*.md
```

---

## Fase 4 — Baixos (estilo, redundância, micro-ajustes)

| # | Arquivo:linha | Categoria | Texto atual (resumo) | Corrigir para | Severidade |
|---|---|---|---|---|---|
| 1 | README.md:15 | Redundância | "Projetamos o piDots para o silício real" (repete a ideia da linha 17) | Manter apenas uma das duas menções ao "silício/hardware real" | Baixo |
| 2 | README.md:17 | Redundância | "sem camadas de orquestração externas que drenam memória" (jargão "drenam") | "sem camadas de orquestração externas" | Baixo |
| 3 | README.md:42 | Repetição | "monólito modular assíncrono" aparece 3 vezes no README | Padronizar para "processo único assíncrono" ou "arquitetura monolítica assíncrona" | Baixo |
| 4 | README.md:112 | Repetição | "poda dinâmica" aparece 4 vezes no README | Padronizar para "seleção dinâmica de ferramentas" | Baixo |
| 5 | README.md:191-209 | Repetição | "teletipo" aparece 5 vezes na seção de design | Reduzir para 2 menções, explicar o termo na primeira | Baixo |
| 6 | README.md:283 | Repetição | "Ada, Linus, Grace, etc." aparece 2 vezes na mesma frase | Manter apenas uma menção | Baixo |
| 7 | ARCHITECTURE.md:9 | Repetição | "monólito modular" aparece 3 vezes | Padronizar para "processo único" ou "arquitetura monolítica" | Baixo |
| 8 | ARCHITECTURE.md:522-537 | Repetição | "padrão OpenDots" aparece 4 vezes na seção 22 | Reduzir para 2 menções | Baixo |
| 9 | roadmap_evolution.md:3-27 | Repetição | "Sovereign" aparece 2 vezes no título e na descrição | Manter apenas no título | Baixo |
| 10 | roadmap_redesign_visual.md:3-41 | Repetição | "Pixel Paper UI" aparece 5 vezes na seção 1 | Reduzir para 2 menções | Baixo |
| 11 | CONTRIBUTING.md:30 | Estilo | "Dark Paper Noir" (nome próprio do tema) | Manter, mas adicionar "(tema escuro)" na primeira ocorrência | Baixo |
| 12 | SECURITY.md:3 | Estilo | "determinístico" (jargão leve) | "exato" ou "controlado" | Baixo |

---

## Instruções de Execução

### Como aplicar as correções de forma cirúrgica

1. **Fase 1 (Críticos) — prioridade máxima**
   - Começar por `ARCHITECTURE.md:522-537` e `roadmap_redesign_visual.md:3-41` (acentuação em massa — correção rápida, alto impacto).
   - Depois `README.md` (jargão institucional e metáforas confusas).
   - Depois `README_EN.md` (PT/EN misturado).
   - Por fim `roadmap_evolution.md` (jargão técnico em cascata).
   - Usar `sed` ou `patch` para correções pontuais; reescrever seções inteiras quando a acentuação está ausente em massa.

2. **Fase 2 (Altos) — jargão e AI slop**
   - Substituir termos EN por PT com explicação na primeira ocorrência (ex.: "Human-in-the-Loop (HITL)", "traceback (relatório de erro)").
   - Quebrar frases > 150 chars em 2-3 frases mais curtas.
   - Substituir metáforas confusas por descrições diretas.
   - Validar que cada termo técnico tem explicação na primeira ocorrência do arquivo.

3. **Fase 3 (Médios) — acentuação e PT/EN**
   - Passar `accent` ou revisor ortográfico nos arquivos PT.
   - Traduzir termos EN que não são nomes próprios (ex.: "tactical" → "tático" ou remover).
   - Quebrar frases > 150 chars.

4. **Fase 4 (Baixos) — estilo e redundância**
   - Padronizar termos recorrentes (escolher uma expressão e usar consistentemente).
   - Reduzir repetições de 3+ ocorrências para no máximo 2.
   - Adicionar "(tema escuro)" ou similar para nomes próprios de temas.

### Como validar após cada fase

1. **Após Fase 1:**
   - `grep -n "silício\|monólito\|arsenal\|soberania\|Sovereign" *.md docs/*.md` → deve retornar 0 resultados (ou apenas onde intencional).
   - `grep -n "[a-z]a[a-z]\|[a-z]e[a-z]\|[a-z]i[a-z]\|[a-z]o[a-z]\|[a-z]u[a-z]" *.md` → verificar acentuação (usar script de verificação de acentos PT).
   - Ler `ARCHITECTURE.md:522-537` e `roadmap_redesign_visual.md:3-41` → acentuação correta.

2. **Após Fase 2:**
   - `grep -n "Human-in-the-Loop\|HITL\|ReAct\|AG-UI\|traceback\|KNN\|BM25\|FTS5\|WAL\|HMAC\|MemGPT\|Levenshtein\|Bubblewrap\|uvloop\|hop_count" *.md` → cada termo deve ter explicação na primeira ocorrência.
   - Verificar que nenhuma frase excede 150 chars: `awk '{ if (length($0) > 150) print FILENAME":FNR" }' *.md`
   - Ler seções de design (`README.md:191-209`) → metáforas substituídas por descrições diretas.

3. **Após Fase 3:**
   - Verificar que não há termos EN soltos em arquivos PT (exceto nomes próprios e siglas já explicadas).
   - `grep -n "tactical\|zero\|handoff\|squad" *.md` → devem estar traduzidos ou explicados.
   - Frases > 150 chars devem estar quebradas.

4. **Após Fase 4:**
   - Contar ocorrências de termos recorrentes: `grep -o "monólito" *.md | wc -l` → no máximo 2 por arquivo.
   - Contar "poda dinâmica": `grep -o "poda dinâmica" *.md | wc -l` → no máximo 2 por arquivo.
   - Ler o README inteiro → tom consistente, sem repetições.

### Resumo de Correções por Arquivo

| Arquivo | Críticos | Altos | Médios | Baixos | Total |
|---|---|---|---|---|---|
| README.md | 10 | 29 | 15 | 6 | 60 |
| README_EN.md | 3 | 1 | 0 | 0 | 4 |
| ARCHITECTURE.md | 2 | 0 | 0 | 2 | 4 |
| roadmap_redesign_visual.md | 1 | 0 | 0 | 1 | 2 |
| roadmap_evolution.md | 2 | 0 | 0 | 1 | 3 |
| CONTRIBUTING.md | 0 | 0 | 0 | 1 | 1 |
| SECURITY.md | 0 | 0 | 0 | 1 | 1 |
| **Total** | **18** | **30** | **15** | **12** | **75** |

*(Nota: alguns itens foram agrupados por seção quando a acentuação/jargão afeta um bloco inteiro. O total de 85 inclui itens agrupados.)*
