# Manifesto de Engenharia Centauro: piDots

**Autor e Arquiteto Principal:** Lyon Christopher  
**Data:** Outubro de 2026  
**Hardware de Referência:** Raspberry Pi 4 Model B (Broadcom BCM2711 ARM64 Cortex-A72, 4 GB LPDDR4, MicroSD / USB SSD)

---

## 1. Por Que Este Documento Existe

Software sério exige autoria transparente. O piDots não nasceu de prompts aleatórios jogados contra uma caixa-preta, nem foi escrito sob a ilusão de que modelos de linguagem substituem o discernimento de um engenheiro de sistemas. Projetamos e construímos o sistema sob a **Engenharia Centauro**: uma divisão clara entre direção arquitetural humana e síntese tática assistida por inteligência artificial.

No xadrez avançado introduzido por Garry Kasparov após 1997, o jogador mais forte do mundo não é o grande mestre isolado, nem o supercomputador sozinho. É o centauro, o operador humano que define a estratégia posicional, poda ramos de decisão estéreis e utiliza o motor computacional para explorar variações táticas com velocidade. Trouxemos exatamente esse princípio para a engenharia de sistemas em hardware restrito.

---

## 2. A Divisão de Responsabilidades (Humano vs. Máquina)

Um modelo de linguagem não sente o cheiro de um regulador de tensão aquecendo a 80 °C numa placa sem cooler. Ele não paga a fatura de um cartão MicroSD corrompido por chamadas `fsync()` excessivas a cada segundo, nem sofre quando um contêiner Node.js ou Chromium devora 2 GB de RAM e aciona o `OOM Killer` do kernel Linux no meio da madrugada.

Por isso, a fronteira de autoridade no piDots é inegociável:

### O Que É Exclusivamente Humano (Lyon Christopher)
1. **Orçamento Físico e Restrições de Silício:** A decisão de fixar o teto operacional em `< 300 MB RSS` (com operação nominal entre `50 MB` e `80 MB`), rodar sobre um único worker assíncrono `FastAPI + uvloop` e banir dependências pesadas de runtime (zero PyTorch, zero LangChain, zero bancos vetoriais externos em contêiner).
2. **Arquitetura de Persistência Flash-Safe:** A escolha do SQLite 3 em modo `WAL` (`Write-Ahead Logging`) com `synchronous=NORMAL`, `wal_autocheckpoint=1000` e `cache_size=-64000`. Essa configuração protege a vida útil da mídia Flash e mantém a latência abaixo de um milissegundo.
3. **Topologia de Segurança e Soberania:** A regra de que nenhum agente executa código fora de um namespace Linux isolado (`Bubblewrap / bwrap`) com raiz somente-leitura, e que toda operação destrutiva exige homologação humana (`Human-in-the-Loop`) assinada criptograficamente com `HMAC-SHA256` e tempo de vida (`TTL`) de 30 minutos.
4. **Identidade Visual e Ergonomia:** A recusa deliberada de interfaces genéricas geradas por IA. O design tático do console (`/app`), da apresentação (`/`) e do manual (`/docs`) combina a precisão de terminais técnicos de 1-bit com fichas catalográficas de alta densidade e suporte nativo à zona do polegar em smartphones.

### O Que Foi Acelerado por Agentes de IA
1. **Desacoplamento Sistemático e Fatiamento Modular:** A refatoração de controladores monolíticos para roteadores modulares (`pidots/api/routes_*.py`) e motores Vanilla JS independentes (`static/js/spa/*.js`), sem alterar contratos de API.
2. **Implementação de Protocolos Determinísticos:** A codificação de algoritmos de projeção vetorial compacta em 64 dimensões (Feature Hashing + L2 em Python puro), parsers JSON-RPC 2.0 sobre STDIO/SSE para o cliente `MCP Lite` e máquinas de estado do `Circuit Breaker` multi-provedor.
3. **Auditoria Linha a Linha e Suítes de Regressão:** A geração e execução contínua de mais de 20 suítes de testes automatizados (`scripts/test_*.py`) que verificam cada rota HTTP, cada migração SQLite, cada trava de segurança e a ausência absoluta de emojis ou código morto antes de qualquer commit.

---

## 3. Nossos Quatro Compromissos de Engenharia

Para qualquer desenvolvedor, auditor de segurança ou operador de homelab que inspecione ou contribua com este repositório, definimos quatro regras permanentes:

1. **Zero Código Fantasma:** Nenhuma linha gerada por assistentes entra na árvore principal sem ser lida, compreendida e submetida a testes determinísticos que rodam localmente em segundos. Se um módulo não pode ser explicado de ponta a ponta ou se adiciona complexidade acidental sem ganho mensurável de latência ou memória, ele é descartado.
2. **Contenção Determinística Acima de Promessas de Prompt:** Nunca confiamos apenas em instruções textuais (`system_prompt`) para impedir que um modelo apague arquivos ou exfiltre segredos. A contenção ocorre no nível do sistema operacional (`bwrap --unshare-all`), na validação de expressões regulares do `@dot-auditor`, no checksum `SHA-256` dos pacotes `DotPack v1.1` e na confirmação manual da governança humana.
3. **Respeito Radical pelo Hardware do Usuário:** Todo recurso novo é medido pelo impacto em memória residente (`VmRSS`), ciclos de CPU ARM64 e operações de escrita em bloco. Se uma funcionalidade funciona em uma estação de trabalho de 64 GB mas degrada um Raspberry Pi 4B de 4 GB, ela é considerada defeituosa.
4. **Linguagem Técnica Direta:** Nossa documentação, nossos relatórios e nossos comentários de código são escritos para engenheiros humanos. Não usamos jargões corporativos vazios, adjetivos inflados ou ornamentos visuais desnecessários.

---

*Assinado na arquitetura do projeto por Lyon Christopher, criador e arquiteto do piDots.*
