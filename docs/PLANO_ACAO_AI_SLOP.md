# PLANO DE AÇÃO — Sanar Pontas Soltas de AI Slop (piDots)

**Data:** 2026-11-02
**Base:** Auditoria linha por linha de 2 subagentes (landing.html + app.html + docs.html + pt.json + en.json)
**Total de problemas identificados:** ~350
**Status:** Aguardando aprovação do usuário

---

## RESUMO EXECUTIVO

A auditoria linha por linha identificou **~350 problemas** de copywriting distribuídos em 5 arquivos. Os problemas se dividem em 4 categorias de severidade:

| Severidade | Qtd | Descrição |
|:---|:---|:---|
| **CRÍTICA** | 12 | Erros factuais, inconsistências de nomenclatura, afirmações falsas |
| **ALTA** | 58 | AI slop evidente, jargão sem explicação no corpo visível, metáforas confusas |
| **MÉDIA** | 120 | Frases > 150 chars, adjetivos vagos, PT/EN misturado, tom inconsistente |
| **BAIXA** | 160 | Redundâncias, estilo, formatação, detalhes menores |

### Termos que mais precisam de correção

| Termo | Ocorrências | Explicações Atuais | Status |
|:---|:---|:---|:---|
| WAL / SQLite WAL | 40+ | 18 (docs) | Falta explicar em landing + app |
| HITL / Human-in-the-Loop | 30+ | 18 (docs) | Falta explicar em landing + app |
| Bubblewrap | 20+ | 18 (docs) | Falta explicar em landing + app |
| Self-Healing / auto-cura | 16+ | 18 (docs) | Falta explicar em landing + app |
| AG-UI | 10+ | 18 (docs) | Falta explicar em landing + app |
| Poda Dinâmica de Ferramentas | 12+ | 18 (docs) | Falta explicar em landing + app |
| uvloop | 8+ | 18 (docs) | Falta explicar em landing + app |
| HMAC-SHA256 | 8+ | 18 (docs) | Falta explicar em landing + app |

### Metáforas mais problemáticas

| Metáfora | Ocorrências | Problema |
|:---|:---|:---|
| "silício" | 10+ | Metáfora decorativa sem função |
| "cirúrgico" | 6+ | Metáfora médica inflada |
| "bobina" / "picote" | 2 | Metáfora de terminal sem explicação |
| "caixas-pretas" | 3 | Crítica genérica sem alvo |
| "soberania de dados" | 3 | Metáfora inflada sem definição |
| "alucinação cruzada" | 1 | Conceito inexistente |
| "tokens preciosos" | 1 | Personificação de hype |
| "recibos táteis" | 3 | Metáfora confusa |
| "vitrine institucional" | 1 | Jargão de produto |

---

## FASE A — CRÍTICA (12 itens) — Corrigir Primeiro

### A1. Inconsistência de nomenclatura nos 3 arquétipos (docs.html:2198)
- **Problema:** Passo 9 lista "Propositor, Auditor Crítico e Supervisor"; passo 10 lista "Pragmática, Inovadora e Auditor de Borda" — nomes diferentes para o mesmo conceito.
- **Correção:** Alinhar com o passo 9: "Perspectivas: Propositor (@coder), Auditor Crítico (@auditor) e Supervisor (@supervisor)"

### A2. "Execução Determinística" tecnicamente falsa (docs.html:1695)
- **Problema:** Sistema que chama LLM não é determinístico. A barra do diagrama diz "EXECUCAO DETERMINISTICA" — afirmação falsa.
- **Correção:** Remover "EXECUCAO DETERMINISTICA" da barra do diagrama. Substituir por "CONSENSO ALCANÇADO" ou remover.

### A3. "Imunidade total" — afirmação falsa (docs.html:2523)
- **Problema:** "garantindo imunidade total contra bots maliciosos" — nenhum controle garante imunidade total.
- **Correção:** "bloqueando bots e varreduras de portas que não passam pela autenticação"

### A4. "Governança física" — frase sem sentido (docs.html:288)
- **Problema:** "Governança física Human-in-the-Loop" não faz sentido — governança não é física.
- **Correção:** Reescrever o parágrafo inteiro: "Guia de instalação e operação do piDots no Raspberry Pi 4B: menos de 70 MB de RAM e 6 W, com aprovação humana antes de comandos de risco e dados 100% locais."

### A5. "Monólito enxuto" — oxímoro de hype (docs.html:338)
- **Problema:** "monólito" tem conotação negativa em arquitetura; "enxuto" é vago.
- **Correção:** "O piDots é uma aplicação única em Python assíncrono. Não sobe navegadores Chromium nem bancos vetoriais em contêineres separados: tudo roda num processo só."

### A6. "Alucinação cruzada" — conceito inexistente (docs.html:465)
- **Problema:** "alucinação cruzada" não existe como conceito técnico.
- **Correção:** "Dividir o trabalho entre agentes especializados deixa cada prompt mais curto e focado: o Supervisor não gasta contexto com sintaxe de shell e o Coder não gasta com redações longas."

### A7. "Early Consensus Exit" — nome não explicado (docs.html:1625/1695/1705)
- **Problema:** Aparece 3 vezes sem explicação.
- **Correção:** Explicar uma vez: "saída antecipada por consenso (o debate termina na rodada 2 se o auditor aprovar)"

### A8. "WAL durável" — redundância (docs.html:288)
- **Problema:** WAL existe justamente para durabilidade. "WAL durável" é redundante.
- **Correção:** Remover "durável" — manter apenas "SQLite WAL"

### A9. "Poda dinâmica de contexto" — nome errado (docs.html:684)
- **Problema:** O recurso é poda de *ferramentas*, não de *contexto*.
- **Correção:** "utilize as 15 ferramentas nativas, carregadas sob demanda para economizar tokens"

### A10. "6 Watts" vs "6.2W" vs "6,2 watts" — formatação inconsistente
- **Problema:** Três formas diferentes de escrever o mesmo número.
- **Correção:** Padronizar "6,2 W" em todos os lugares (PT) / "6.2 W" (EN)

### A11. "recibos tatis" — erro de digitação (docs.html:2071)
- **Problema:** "tatis" em vez de "táteis"
- **Correção:** "recibos táteis"

### A12. "Barramento Físico GPIO/MQTT" — MQTT não é físico (pt:101)
- **Problema:** GPIO é barramento físico; MQTT é protocolo de rede. "Físico" não se aplica a MQTT.
- **Correção:** "Módulo MCP Lite, Aprovação Remota com HMAC-SHA256, Dot Packs v1.1 e gatilhos GPIO/MQTT"

---

## FASE B — ALTA (58 itens) — AI Slop Evidente

### B1. Jargão sem explicação no corpo visível (docs.html)
As 18 explicações adicionadas na Fase 3 estão no **drawer** (aba lateral), mas não no **corpo visível** da página. O leitor que está lendo o texto principal não vê as explicações.

**Correção:** Mover as explicações para a primeira ocorrência no corpo visível (fora do drawer).

| Termo | Linha (docs.html) | Explicação a adicionar |
|:---|:---|:---|
| WAL | 338 | "(Write-Ahead Logging: grava em log sequencial, sem perder dados se faltar energia)" |
| HITL | 420 | "(Human-in-the-Loop: você aprova antes de o sistema executar)" |
| Bubblewrap | 510 | "(sandbox Linux: ambiente isolado onde comandos rodam sem afetar o sistema)" |
| Self-Healing | 1497 | "(auto-reparo: o sistema detecta e corrige erros sozinho)" |
| AG-UI | 598 | "(protocolo de streaming entre agentes e interface)" |
| uvloop | 878 | "(biblioteca que deixa o servidor Python mais rápido)" |
| HMAC | 900 | "(assinatura criptográfica que garante que a mensagem não foi alterada)" |
| MemGPT | 1031 | "(sistema de memória em camadas)" |
| FTS5 | 1031 | "(busca textual completa no banco de dados)" |
| BM25 | 1031 | "(algoritmo de ranking para busca)" |
| ReAct | 338 | "(ciclo de raciocínio + ação: o agente pensa antes de agir)" |
| Tool Pruning | 821 | "(poda de ferramentas: carregar só o que é necessário)" |
| EdgeScheduler | 2287 | "(agendador de tarefas em segundo plano)" |
| Levenshtein | 1067 | "(tolerância a erros de digitação)" |
| KNN | 924 | "(busca por proximidade numérica)" |
| zero trust | 640 | "(nenhum acesso é confiável por padrão)" |
| Letta | 1031 | "(framework de memória para agentes)" |
| hop_count | 1631 | "(limite de delegação entre agentes)" |

### B2. Frases genéricas de IA (landing.html)

| Linha | Texto Atual | Correção |
|:---|:---|:---|
| 220 | "Alocando especialistas via Dynamic Tool Pruning (3/23 esquemas JSON ativos no contexto)" | "Selecionando as ferramentas necessárias (3 de 23 disponíveis no contexto)" |
| 234 | "Gerando teste de integração de hardware em sandbox Bubblewrap sub-15ms" | "Gerando teste de hardware em ambiente isolado (início em menos de 15ms)" |
| 429 | "Executa scripts em sandbox Bubblewrap sub-15ms e aciona auto-cura via Self-Healing Harness" | "Executa scripts em ambiente isolado e repara scripts com erro automaticamente" |
| 471 | "Intercepta comandos de alto risco gerando cards de retenção HITL, monitora a temperatura do SoC" | "Intercepta comandos de alto risco e pede sua aprovação antes de executar. Monitora a temperatura do processador" |
| 490 | "o piDots foi calibrado para operar com folga em nós de 4GB" | "o piDots roda com folga num Raspberry Pi de 4 GB" |
| 549 | "Veja como o piDots se diferencia de soluções em nuvem tradicionais" | "Compare o piDots com serviços em nuvem e frameworks de agentes" |
| 598 | "AG-UI SSE padronizado sub-milissegundo" | "Streaming de eventos em tempo real (SSE), latência menor que 1 ms" |
| 616 | "Dot Heartbeat 24/7 com HEARTBEAT_OK" | "Verificações automáticas 24/7: só avisa quando há algo relevante" |
| 622 | "MemGPT 3 Camadas + Archival FTS5" | "Memória em 3 camadas com busca full-text no SQLite" |
| 640 | "Cloudflare Tunnel Zero Trust nativo" | "Túnel Cloudflare: acesso remoto sem abrir portas no roteador" |
| 878 | "O piDots opera sob um monólito modular assíncrono em Python 3.13 com uvloop" | "O piDots roda em Python 3.13 assíncrono (uvloop), usando menos de 70 MB de RAM" |
| 889 | "Configuramos o SQLite com journal_mode=WAL (Write-Ahead Logging) em modo de escrita sequencial append-only" | "O banco usa WAL: grava em sequência, sem reescrever blocos aleatórios no cartão" |
| 900 | "Nossa camada de governança Human-in-the-Loop (HITL) intercepta preventivamente qualquer comando destrutivo" | "Comandos destrutivos são retidos e registrados no banco. Você recebe o cartão de aprovação" |
| 911 | "O piDots é 100% agnóstico (Bring Your Own Model)" | "O piDots aceita qualquer modelo: local ou em nuvem" |

### B3. Metáforas confusas (todos os arquivos)

| Metáfora | Linhas | Correção |
|:---|:---|:---|
| "silício" | 115, 333, 1258 | → "hardware" |
| "cirúrgico" | 373, 1497, 1560 | → "direto", "preciso" |
| "bobina" / "picote" | 225, 209 | → "log" / "agente" |
| "caixas-pretas" | 549 | → "serviços que você não controla" |
| "soberania de dados" | 319 | → "manter tudo local" |
| "alucinação cruzada" | 465 | → "prompt focado" |
| "tokens preciosos" | 628 | → "tokens de saída" |
| "recibos táteis" | 1067, 2071 | → "confirmação de resultado" |
| "vitrine institucional" | 2425 | → "página inicial" |
| "agilidade tática" | 1289 | → "teclado sem mouse" |
| "squad" | 408 | → "equipe" |
| "handoffs" | 408 | → "transfere a condução" |

### B4. Jargão sem explicação (landing.html)

| Linha | Termo | Correção |
|:---|:---|:---|
| 137 | "RAM RSS" | → "RAM em uso" |
| 186 | "SQLite WAL" | → "SQLite (gravar em log sequencial)" |
| 199 | "Terminal AG-UI" | → "Terminal do agente" |
| 240 | "HMAC-SHA256 VALIDO" | → "Assinatura criptográfica válida" |
| 264 | "OSCILLOSCOPIO DE MEMORIA RSS // uvloop" | → "Memória em uso (MB)" |
| 357 | "Monólito Python 3.13 com uvloop e Poda Dinâmica de Ferramentas" | → "Um único processo Python 3.13 assíncrono" |
| 367 | "Namespaces Bubblewrap (bwrap) montados sem sobrecarga gráfica" | → "Ambientes isolados criados com Bubblewrap" |
| 377 | "Escritas sequenciais em append-only com temp_store em RAM volátil" | → "Gravações em sequência; dados temporários ficam em RAM" |
| 450 | "esquemas relacionais SQLite WAL e contratos de API REST" | → "esquemas do banco de dados SQLite" |
| 475 | "Assinaturas HMAC-SHA256" | → "Verificação de integridade por assinatura" |
| 502 | "controle de concorrência otimista (expectedRevision)" | → "se duas pessoas editarem ao mesmo tempo, o sistema avisa" |
| 513 | "append-only sem reescrita de blocos, tmpfs 64MB, WAL TRUNCATE" | → "Grava em sequência; temporários em RAM; compacta o log à noite" |
| 524 | "modified_args", "loop ReAct" | → "editar os parâmetros", "liberar o agente" |
| 535 | "NAT Traversal" | → "acesso remoto pelo túnel Cloudflare" |
| 604 | "Cards HITL inline com modified_args" | → "Cartões de aprovação com opção de editar" |
| 634 | "Self-Healing Harness com parser AST" | → "Auto-reparo: analisa o erro e corrige o código" |
| 749 | "AST", "correção cirúrgica" | → "parser sintático", "reparo automático" |
| 1031 | "MemGPT", "FTS5", "BM25", "projeção vetorial 64D" | → "3 camadas", "busca por texto", "relevância", "vetores de 64 dimensões" |
| 1055 | "SoC", "throttling", "WAL TRUNCATE" | → "processador", "reduz o ritmo se esquentar", "compacta o banco" |
| 1067 | "Levenshtein", "recibos táteis" | → "busca que tolera erros de digitação", "confirmação de resultado" |
| 1073 | "NAT Traversal" | → "acesso remoto pelo túnel Cloudflare" |

---

## FASE C — MÉDIA (120 itens) — Frases Longas, PT/EN, Tom

### C1. Frases > 150 caracteres (quebrar em 2-3 frases)

| Arquivo | Linha | Chars | Correção |
|:---|:---|:---|:---|
| landing | 148 | 200 | Quebrar em 2 frases |
| landing | 471 | 181 | Quebrar em 2 frases |
| landing | 490 | 157 | Quebrar em 2 frases |
| landing | 502 | 172 | Quebrar em 2 frases |
| landing | 513 | 170 | Quebrar em 2 frases |
| landing | 524 | 166 | Quebrar em 2 frases |
| landing | 535 | 163 | Quebrar em 2 frases |
| landing | 878 | 376 | Quebrar em 3 frases |
| landing | 889 | 360 | Quebrar em 3 frases |
| landing | 900 | 416 | Quebrar em 3 frases |
| landing | 911 | 367 | Quebrar em 3 frases |

### C2. PT/EN misturado sem consistência

| Termo EN | Ocorrências | Correção |
|:---|:---|:---|
| "squad" | 3 | → "equipe" |
| "handoffs" | 1 | → "transfere a condução" |
| "bring your own model" | 1 | → "traga seu próprio modelo" |
| "base url" | 1 | → "URL do servidor" |
| "slip receipts" | 1 | → "recibos de comando" |
| "early consensus exit" | 3 | → "saída antecipada por consenso" |
| "dissector ast" | 1 | → "analisador AST" |
| "activity rail" | 1 | → "barra lateral de navegação" |
| "coagents state" | 1 | → "painel de estado dos agentes" |
| "dot's computer" | 1 | → "terminal interativo" |

### C3. Tom inconsistente entre seções

| Seção | Tom Atual | Tom Alvo |
|:---|:---|:---|
| Hero | Humano, acessível | ✓ (manter) |
| FAQ | Técnico denso | Adicionar "Em termos práticos:..." em cada resposta |
| Métricas | Engenharia formal | ✓ (manter) |
| Comparativo | Crítica de mercado | → "menor consumo, menor custo, mais controle" |
| Arena | Governo industrial | → "teste o bloqueio de comandos de risco" |
| Calculadora | Pitch financeiro | → "quanto você economiza" |
| Landing vs App | 4 termos para a mesma coisa | → "especialista" (termo principal), "Dot" (handle) |

### C4. Títulos com > 8 palavras

| Arquivo | Linha | Título Atual | Correção |
|:---|:---|:---|:---|
| landing | 333 | "DADOS DE ENGENHARIA DE SILÍCIO" | "DADOS DE HARDWARE" |
| landing | 115 | "02 // METRICAS DE SILICIO" | "02 // MÉTRICAS DE HARDWARE" |
| landing | 119 | "06 // ARENA INTERATIVA HITL" | "06 // DEMO DE GOVERNANÇA" |
| landing | 120 | "07 // CALCULADORA DE ROI" | "07 // CALCULADORA DE ECONOMIA" |
| docs | 1287 | "ATALHOS DE ALTA PRODUTIVIDADE DO CONSOLE SPA" | "ATALHOS DE TECLADO DO CONSOLE" |

---

## FASE D — BAIXA (160 itens) — Estilo, Redundância, Detalhes

### D1. Adjetivos vagos (remover ou substituir)

| Termo | Ocorrências | Correção |
|:---|:---|:---|
| "robusto" | 2 | Remover |
| "eficiente" | 3 | Remover ou especificar |
| "poderoso" | 1 | Remover |
| "avançado" | 2 | Remover |
| "moderno" | 1 | Remover |
| "inteligente" | 3 | Remover ou especificar |
| "calibrado" | 1 | → "ajustado" |
| "extremamente simples" | 1 | Remover "extremamente" |
| "com precisão" | 1 | Remover |
| "agressivo" | 1 | → "longo" |

### D2. Repetições redundantes

| Termo | Ocorrências | Correção |
|:---|:---|:---|
| "WAL" sem explicação | 40+ | Explicar na 1ª ocorrência, manter abreviação depois |
| "HITL" sem explicação | 30+ | Explicar na 1ª ocorrência |
| "Bubblewrap" sem explicação | 20+ | Explicar na 1ª ocorrência |
| "Self-Healing" sem explicação | 16+ | Explicar na 1ª ocorrência |
| "AG-UI" sem explicação | 10+ | Explicar na 1ª ocorrência |
| "Poda Dinâmica" sem explicação | 12+ | Explicar na 1ª ocorrência |

### D3. Placeholders visíveis (app.html)

| Linha | Texto | Correção |
|:---|:---|:---|
| 9.1-9.72 | 72 placeholders no app.html | Verificar se são intencionais (debug) ou resíduos |

### D4. Erros de digitação

| Linha | Erro | Correção |
|:---|:---|:---|
| docs:2071 | "recibos tatis" | "recibos táteis" |
| docs:288 | "6 Watts" | "6,2 W" |
| docs:281 | "6.2W" | "6,2 W" |

### D5. Detalhes de formatação

| Item | Correção |
|:---|:---|
| "Autonomos" sem acento (title) | "Autônomos" |
| "Proprio" sem acento (title) | "Próprio" |
| "MANUAL OPERACIONAL // GUIA" redundante | "MANUAL OPERACIONAL" |
| "4 // 4 PILARES" duplicado | "04 // PILARES" |
| "OPEN SOURCE MIT" jargão | "Código aberto (licença MIT)" |

---

## EXECUÇÃO RECOMENDADA

### Ordem de execução

1. **Fase A (12 itens)** — 1h de trabalho — Corrigir erros factuais e inconsistências
2. **Fase B (58 itens)** — 3h de trabalho — AI slop evidente, jargão no corpo visível
3. **Fase C (120 itens)** — 4h de trabalho — Frases longas, PT/EN, tom
4. **Fase D (160 itens)** — 2h de trabalho — Estilo, redundância, detalhes

**Total estimado: 10h de trabalho**

### Estratégia de aplicação

- **Fase A:** Patches manuais (12 patches)
- **Fase B:** Script Python para substituições massivas + patches manuais para casos complexos
- **Fase C:** Script Python para quebra de frases + patches manuais para tom
- **Fase D:** Script Python para adjetivos vagos + patches manuais para digitação

### Validação

Após cada fase:
1. Validar JSON (pt.json, en.json)
2. Validar HTML (sem tags quebradas)
3. Commit + push
4. Relatório de mudanças

---

## ARQUIVOS AFETADOS

| Arquivo | Itens A | Itens B | Itens C | Itens D | Total |
|:---|:---|:---|:---|:---|:---|
| pages/landing.html | 2 | 25 | 30 | 20 | 77 |
| pages/app.html | 1 | 10 | 20 | 40 | 71 |
| pages/docs.html | 5 | 15 | 40 | 50 | 110 |
| data/locales/pt.json | 2 | 5 | 15 | 20 | 42 |
| data/locales/en.json | 2 | 5 | 15 | 20 | 42 |
| **Total** | **12** | **60** | **120** | **150** | **342** |

---

## PRÓXIMOS PASSOS

**Aguardando aprovação do usuário para iniciar a execução.**

Opções:
1. **Executar tudo** (Fase A → D) — ~10h
2. **Executar Fases A + B** (crítico + alto) — ~4h
3. **Executar apenas Fase A** (crítico) — ~1h
4. **Executar por arquivo** (landing → app → docs → locales)
5. **Ajustar escopo** (remover itens não prioritários)
