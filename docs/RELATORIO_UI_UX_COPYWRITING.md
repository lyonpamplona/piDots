# piDots — Auditoria de UI/UX e Copywriting

**Páginas auditadas:** `/landing`, `/app`, `/docs`
**Data:** 02/11/2026
**Método:** Auditoria linha a linha via subagente + análise automatizada de jargão, frases longas e padrões AI-slop
**Skills aplicadas:** hermes-design-principles, ai-humanizer, hermes-ui-audit, design-taste-frontend

---

## 1. VISÃO GERAL — O QUE ESTÁ BOM

Antes dos problemas, o que já funciona:

- **Design system consistente** — Pixel Paper UI (dark, monospace, 1-bit/8-bit, zero emojis) está aplicado em todas as 3 superfícies
- **Hierarquia visual clara** — o usuário sabe onde está (sidebar + header + conteúdo)
- **ARIA labels presentes** — 30+ labels de acessibilidade no app.html
- **i18n PT/EN** — suporte bilingue implementado
- **PWA** — instalável offline, service worker, manifest
- **Zero emojis** — respeita a diretriz do design system
- **Conteúdo técnico real** — os parâmetros, endpoints e exemplos são concretos, não filler

---

## 2. PROBLEMAS CRÍTICOS (P0)

### 2.1 — `docs.html`: Títulos de passos confusos e longos

**Problema:** Os 14 títulos de passos são telegráficos e usam jargão sem explicação. Uma pessoa que nunca usou o piDots não entende o que é "PODA DINÂMICA (TOOL PRUNING)" ou "MICRO-MOTOR DE INTERNACIONALIZAÇÃO".

| Passo | Título Atual | Problema |
|:---|:---|:---|
| 1 | O QUE É O PIDOTS E A ARQUITETURA DE BORDA | OK |
| 2 | CHAT MULTI-BOT COLABORATIVO E CADERNO DE RACIOCÍNIO | "Caderno de Raciocínio" não é explicado |
| 3 | AUTONOMIA PROATIVA, DOT HEARTBEAT E HEARTBEAT_OK | 3 conceitos num título, nenhum explicado |
| 4 | GATEWAY DE MENSAGERIA UNIFICADA E SALAS TEMÁTICAS | "Gateway unificado" é jargão |
| 5 | ARSENAL DE FERRAMENTAS E PODA DINÂMICA (TOOL PRUNING) | "Arsenal" é metáfora confusa; "Tool Pruning" não traduzido |
| 6 | PASSO A PASSO OPERACIONAL, ENDPOINTS REST E PRESERVAÇÃO DO MICROSD | 3 tópicos, título genérico |
| 7 | MEMÓRIA HIERÁRQUICA AUTÔNOMA (PADRÃO MEMGPT / LETTA) | MemGPT/Letta são referências externas sem contexto |
| 8 | SELF-HEALING HARNESS E PLANEJAMENTO EM DOIS ESTÁGIOS | "Harness" é jargão de engenharia |
| 9 | CONSELHO CONSULTIVO E REVISÃO ENTRE AGENTES | OK mas vago |
| 10 | ESPAÇO DE CONHECIMENTO COMPARTILHADO E DOT PACKS | "Dot Packs" não explicado no título |
| 11 | TRIGGERS DE HARDWARE EDGE E MANUTENÇÃO DO MICROSD | "Triggers de hardware edge" é jargão |
| 12 | MICRO-MOTOR DE INTERNACIONALIZAÇÃO (I18N) & DICCIONÁRIOS JSON DE BORDA | "Micro-motor" é metáfora confusa |
| 13 | CATÁLOGO COMPLETO DE SLASH COMMANDS, PARSER LÉXICO E RECIBOS TÁTIS | "Parser léxico" e "recibos táteis" são jargão |
| 14 | DESACOPLAMENTO POR PORTAS & CLOUDFLARE TUNNEL | "Desacoplamento por portas" é jargão técnico |

**Sugestão:** Cada título deve ter no máximo 8 palavras e usar linguagem que o usuário leigo entende. Jargão vai no corpo do texto, não no título.

### 2.2 — `docs.html`: 65 frases com mais de 200 caracteres

**Problema:** 65 frases longas (> 200 chars) fazem o texto parecer uma parede. A maior tem 1.343 caracteres (é basicamente todo o HTML colado em uma linha).

**Distribuição:**
- 64 frases curtas (< 80 chars) — OK
- 144 frases médias (80-200 chars) — OK
- **65 frases longas (> 200 chars) — PROBLEMA**

**Regra:** Nenhuma frase deve ultrapassar 150 caracteres. Se precisa de mais, quebre em 2-3 frases.

### 2.3 — `landing.html`: Densidade de jargão alta demais para uma página de apresentação

**Problema:** 126 ocorrências de jargão técnico em 2.180 palavras (razão 0.06). Para uma landing page que deve convencer o visitante, isso é demais.

| Termo | Ocorrências | Necessário na landing? |
|:---|:---|:---|
| WAL | 18 | Não — explicar como "banco de dados" |
| SQLite | 12 | Parcial — "banco de dados SQLite" |
| sandbox | 11 | Sim, mas explicar "isolado" |
| Bubblewrap | 9 | Não — "sandbox Linux" |
| HITL | 8 | Sim, mas "aprovação humana" |
| ARM64 | 8 | Parcial — "processador de 64 bits" |
| RSS | 6 | Não — "memória" |
| self-healing | 5 | Parcial — "auto-reparo" |
| AG-UI | 4 | Não — "interface" |
| FTS5 | 3 | Não — "busca no banco" |
| Tool Pruning | 3 | Não — "otimização de ferramentas" |
| zero trust | 3 | Parcial — "seguro" |

**Regra:** Na landing page, máximo 3 termos técnicos por seção. O resto vai para a docs.

### 2.4 — `app.html`: Placeholder genérico sem contexto

**Problema:** `console.input_placeholder` está no HTML como texto literal — é uma chave i18n que não foi traduzida.

```html
<!-- Linha atual -->
placeholder="console.input_placeholder"

<!-- Deveria ser -->
placeholder="Digite uma instrução ou mencione @dot (Enter envia)..."
```

### 2.5 — `landing.html`: Subtítulo do hero é vago

**Problema atual:**
```
Agentes de IA autônomos no seu próprio hardware.
Execute uma equipe de AI coworkers persistentes no Raspberry Pi 4B consumindo menos de 70 MB de RAM e 6.2 Watts. Memória durável em SQLite WAL...
```

**Problema:** "AI coworkers persistentes" é jargão. "Memória durável em SQLite WAL" é irrelevante para o visitante. O que a pessoa quer saber: "o que isso faz por mim?"

**Sugestão:**
```
Agentes de IA que rodam no seu Raspberry Pi.
Sem nuvem. Sem fatura. Sem dependência de internet.
4 especialistas de IA que trabalham 24/7 no seu hardware,
consumindo menos que um app de celular.
```

---

## 3. PROBLEMAS ALTOS (P1)

### 3.1 — Tom inconsistente entre páginas

| Página | Tom | Problema |
|:---|:---|:---|
| landing.html | Técnico-marcial ("silício físico", "bancada", "soberania de dados") | Fala como engenheiro para engenheiro, mas é a página de entrada |
| app.html | Técnico-operacional ("nó de borda", "hot-reload", "teto de tokens") | OK para quem já está usando, confuso para quem está chegando |
| docs.html | Técnico-acadêmico ("arquitetura de borda", "soberania de dados", "hops") | Assume conhecimento prévio que o usuário não tem |

**Problema:** O mesmo usuário que lê a landing (iniciante) vai para a docs e encontra um tom completamente diferente. A transição não é suave.

**Regra:** Landing = linguagem simples. App = linguagem operacional. Docs = linguagem técnica com explicações.

### 3.2 — `docs.html`: Metáforas confusas

| Metáfora | Onde | Problema |
|:---|:---|:---|
| "Caderno de Raciocínio" | Passo 2 | Não é explicado o que é |
| "Arsenal de Ferramentas" | Passo 5 | "Arsenal" sugere guerra, não produtividade |
| "Micro-Motor de Internacionalização" | Passo 12 | "Micro-motor" é metáfora que não ajuda |
| "Recibos Táteis" | Passo 13 | O que é um "recibo tátil"? |
| "Trava de Recursão" | Passo 4 | Termo técnico não explicado |
| "Soberania de Dados" | Várias | Termo de política, não de engenharia |

### 3.3 — `landing.html`: Seção "4 Pilares" usa títulos longos

| Pilar Atual | Sugestão |
|:---|:---|
| Árvore Hierárquica de Conhecimento Durável | Memória que não esquece |
| Preservação Contínua da Mídia Flash do MicroSD | MicroSD que dura anos |
| Governança Human-in-the-Loop Sem Bloqueios | Você aprova antes de executar |
| Desacoplamento e Acesso Remoto Zero Trust | Acesse de qualquer lugar, com segurança |

### 3.4 — `app.html`: Descrições de seções técnicas demais

| Seção | Descrição Atual | Problema |
|:---|:---|:---|
| Estúdio de Dots | "Gerencie especialistas autônomos, prompts de sistema e poda dinâmica de ferramentas (Dynamic Tool Pruning)" | 16 palavras, 3 jargões |
| Tasks Proativas | "Tarefas executadas em background pelo EdgeScheduler com diretriz de silêncio HEARTBEAT_OK" | 12 palavras, 3 jargões |
| Gatilhos de Borda | "Monitorando sensores térmicos, disco MicroSD e barramento GPIO/MQTT" | 9 palavras, 2 jargões |
| Provedor de IA | "Atualize o modelo ou chaves de inferência em tempo real sem reiniciar o processo do nó de borda" | 18 palavras, 3 jargões |

### 3.5 — `docs.html`: Exemplos de código sem contexto

Vários blocos `curl` e JSON aparecem sem uma frase de introdução. O usuário vê o código mas não sabe:
- O que esperar ao executar
- Em que contexto usar
- Como interpretar a resposta

---

## 4. PROBLEMAS MÉDIOS (P2)

### 4.1 — `landing.html`: Matriz comparativa confusa

A tabela "O que muda ao migrar para hardware soberano local" compara 4 colunas (Nuvem, Local Pesado, Local Leve, piDots) mas os cabeçalhos não estão claros. Uma pessoa que nunca ouviu falar de "Local Pesado" não sabe o que comparar.

### 4.2 — `app.html`: "Título da Etapa" como placeholder

Há um `TÍTULO DA ETAPA` literal no HTML que parece ser um placeholder não substituído.

### 4.3 — `docs.html`: Navegação entre passos não óbvia

Os botões "PASSO ANTERIOR" e "AVANÇAR: [TÍTULO DO PRÓXIMO]" funcionam, mas o usuário não sabe quantos passos já percorreu. Um indicador de progresso (ex: "Passo 5 de 14") seria útil.

### 4.4 — `landing.html`: Botões CTA sem hierarquia

Os CTAs "Iniciar Console Operacional" e "Ler Documentação" têm o mesmo peso visual. O primeiro deve ser mais forte (é a ação principal).

### 4.5 — `app.html`: Sidebar com 10+ seções

A sidebar do console tem muitas seções visíveis ao mesmo tempo. Em mobile, isso vira uma lista enorme. Considerar agrupar em categorias (Operação, Configuração, Diagnóstico).

---

## 5. PROBLEMAS BAIXOS (P3)

| # | Problema | Onde |
|:---|:---|:---|
| 1 | "AI Coworkers" mistura EN e PT inconsistemente | landing.html |
| 2 | "No: Online" no header da docs — "No" em vez de "Nó" | docs.html |
| 3 | "PICOTE // BOBINA" no simulador — jargão de hardware sem explicação | landing.html |
| 4 | "SEQ# 0001 · PROT: AG-UI" — siglas sem expansão | landing.html |
| 5 | "Osciloscópio de Memória RSS" — metáfora de hardware para um gráfico de RAM | landing.html |
| 6 | BUILD/COMMIT/CANAL no rodapé do app — informação irrelevante para o usuário final | app.html |
| 7 | "Setas navegam · Tab/Enter insere · Esc fecha" — dica útil mas em fonte 10px quase ilegível | app.html |

---

## 6. PLANO DE AÇÃO

### Fase 1 — Urgente (aplicar imediatamente)

| # | Ação | Arquivo | Impacto |
|:---|:---|:---|:---|
| 1.1 | Substituir `console.input_placeholder` por texto real | app.html | P0 — placeholder literal visível |
| 1.2 | Remover/substituir "TÍTULO DA ETAPA" placeholder | app.html | P0 — placeholder literal visível |
| 1.3 | Reescrever o subtítulo do hero (landing) | landing.html | P0 — primeira impressão |
| 1.4 | Adicionar indicador de progresso "Passo X de 14" | docs.html | P1 — usabilidade |
| 1.5 | Quebrar as 20 frases mais longas (> 300 chars) | docs.html | P1 — legibilidade |

### Fase 2 — Alta prioridade (próxima sprint)

| # | Ação | Arquivo | Impacto |
|:---|:---|:---|:---|
| 2.1 | Reescrever os 14 títulos de passos em linguagem simples | docs.html | P0 — clareza |
| 2.2 | Reduzir jargão na landing para máximo 3 termos/seção | landing.html | P0 — conversão |
| 2.3 | Reescrever as 4 descrições de seções da sidebar (app) | app.html | P1 — onboarding |
| 2.4 | Reescrever os 4 títulos dos "Pilares" (landing) | landing.html | P1 — clareza |
| 2.5 | Explicar cada jargão na primeira ocorrência (docs) | docs.html | P1 — compreensão |

### Fase 3 — Melhoria contínua

| # | Ação | Arquivo | Impacto |
|:---|:---|:---|:---|
| 3.1 | Criar glossário lateral no docs (Ctrl+K já existe) | docs.html | P2 — referência |
| 3.2 | Adicionar contexto antes de cada bloco de código | docs.html | P2 — usabilidade |
| 3.3 | Melhorar hierarquia dos CTAs na landing | landing.html | P2 — conversão |
| 3.4 | Agrupar seções da sidebar do app em categorias | app.html | P2 — mobile |
| 3.5 | Padronizar PT/EN (decidir "AI Coworkers" vs "Colegas de IA") | todos | P3 — consistência |
| 3.6 | Expandir siglas na primeira ocorrência (AG-UI, WAL, HITL) | todos | P3 — acessibilidade |

---

## 7. REGRAS DE ESCRITA (para aplicar em todas as páginas)

1. **Frase curta** — máximo 150 caracteres por frase. Se precisar de mais, quebre.
2. **Um conceito por título** — títulos de seção têm no máximo 8 palavras.
3. **Jargão explicado** — todo termo técnico é explicado na primeira ocorrência: "HITL (Human-in-the-Loop: você aprova antes de executar)"
4. **Zero metáforas confusas** — "arsenal", "micro-motor", "recibos táteis" — se não é óbvio, não usar.
5. **Linguagem por camada** — landing = simples, app = operacional, docs = técnico com explicações
6. **PT-BR consistente** — decidir entre "AI Coworkers" (EN) e "Colegas de IA" (PT) e usar um só
7. **Exemplos com contexto** — todo bloco de código tem uma frase antes ("Execute este comando para...") e uma depois ("A resposta mostra...")
8. **Teste do leigo** — se uma pessoa que nunca usou um computador de placa única não entende em 10 segundos, reescrever

---

## 8. SCORE DE SAUDE DE DESIGN

| Dimensão | Score | Notas |
|:---|:---|:---|
| Hierarquia Visual | 8/10 | Clara, mas sidebar do app tem muitas seções |
| Typography | 8/10 | Consistente (IBM Plex + JetBrains Mono + Silkscreen) |
| Cor e Contraste | 8/10 | Dark theme com acentos funcionais |
| Layout e Composição | 8/10 | Tripartite funcional, responsivo |
| Movimento e Interacção | 7/10 | Transições sutis, tour funcional |
| **Conteúdo / Copywriting** | **5/10** | **Jargão excessivo, títulos confusos, frases longas** |
| Acessibilidade | 7/10 | ARIA labels presentes, mas placeholder não traduzido |
| Performance | 9/10 | PWA, cache, service worker |
| Estados e Edge Cases | 7/10 | Loading states presentes, empty states OK |
| Code Quality | 8/10 | CSS variables, semântica razoável |

**Score geral: 7.4/10** — O design visual é forte (8+), mas o copywriting puxa para baixo (5/10).

---

## 9. VEREDITO

O **design visual** do piDots está bem executado — Pixel Paper UI é consistente, profissional e sem AI slop visual. O problema está no **texto**: os 3 HTMLs foram escritos por alguém que pensa em termos de engenharia e não em termos de usuário.

A landing page usa "soberania de dados" onde deveria dizer "seus dados ficam no seu computador". A docs usa "poda dinâmica de ferramentas" onde deveria dizer "o sistema carrega só as ferramentas que precisa". O app usa "nó de borda" onde deveria dizer "seu Raspberry Pi".

O trabalho não é mudar o design. É **traduzir a engenharia para o usuário**.
