# Manifesto de Engenharia Centauro: piDots

**Autor e Arquiteto Principal:** Lyon Christopher  
**Data:** Outubro de 2026  
**Hardware de Referência:** Raspberry Pi 4 Model B (Broadcom BCM2711 ARM64 Cortex-A72, 4 GB LPDDR4, MicroSD / USB SSD)

---

## 1. Por Que Este Documento Existe

Software sério exige autoria transparente. O piDots não nasceu de prompts aleatórios jogados contra uma caixa-preta, nem foi escrito sob a ilusão de que modelos de linguagem substituem o discernimento de um engenheiro de sistemas. Construímos o projeto sob o princípio da **Engenharia Centauro**: uma fronteira nítida entre direção arquitetural humana e síntese tática assistida por máquina.

No xadrez avançado introduzido por Garry Kasparov após 1997, o competidor mais formidável do mundo não era o grande mestre isolado, nem o supercomputador sozinho. Era o centauro. O operador humano definia o plano posicional, podava ramos de cálculo estéreis e usava o motor computacional para explorar variações táticas em segundos. Trouxemos esse mesmo rigor para a engenharia de sistemas em hardware restrito.

---

## 2. A Divisão de Responsabilidades (Humano vs. Máquina)

Um modelo de linguagem não sente o cheiro de um regulador de tensão aquecendo a 80 °C em uma placa sem ventoinha. Ele não paga a fatura de um cartão MicroSD corrompido por escritas síncronas a cada segundo, nem acorda de madrugada quando um contêiner Node.js ou Chromium devora 2 GB de RAM e aciona o `OOM Killer` do Linux.

Por isso, a fronteira de autoridade no piDots é inegociável:

### O Que É Exclusivamente Humano (Lyon Christopher)
1. **Orçamento Físico e Limites de Silício:** A decisão de travar o consumo nominal entre 50 MB e 80 MB de RAM, rodar sobre um único worker assíncrono `FastAPI + uvloop` e banir bibliotecas desnecessárias (zero PyTorch, zero LangChain, zero bancos vetoriais externos em contêineres separados).
2. **Arquitetura de Dados Flash-Safe:** A escolha do SQLite em modo `WAL` (`Write-Ahead Logging`) com `synchronous=NORMAL`, `wal_autocheckpoint=1000` e `cache_size=-64000`. Essa configuração preserva a integridade das células Flash e mantém a latência abaixo de um milissegundo.
3. **Segurança e Soberania Local:** A regra de que nenhum agente executa código fora de uma jaula isolada via Linux Bubblewrap (`bwrap`), e que toda operação com risco destrutivo exige aprovação humana em tempo real (`Human-in-the-Loop`), assinada com HMAC-SHA256 e prazo de expiração de 30 minutos.
4. **Identidade Visual e Ergonomia:** A recusa categórica de interfaces genéricas geradas por IA. O console operacional (`/app`), a apresentação (`/`) e o manual (`/docs`) combinam a precisão de matrizes técnicas de 1-bit com alta densidade de informação e alcance tátil para o polegar em smartphones.

### O Que Foi Acelerado por Agentes de IA
1. **Modularização e Fatiamento de Código:** A refatoração de controladores extensos para sub-roteadores modulares (`pidots/api/routes_*.py`) e motores independentes em Vanilla JS (`static/js/spa/*.js`), preservando contratos e rotas ativas.
2. **Implementação de Protocolos e Parsers:** O desenvolvimento de algoritmos de projeção vetorial compacta em 64 dimensões na CPU, parsers JSON-RPC 2.0 sobre STDIO/SSE para o cliente MCP Lite e máquinas de estado de Circuit Breaker.
3. **Auditoria Linha por Linha e Suítes de Teste:** A criação e execução contínua de baterias de testes automatizados (`scripts/test_*.py`) que validam cada rota HTTP, migrações de banco e a ausência absoluta de emojis antes de cada commit.

---

## 3. Nossos Quatro Compromissos de Engenharia

Para qualquer desenvolvedor, auditor de segurança ou operador de homelab que inspecione ou contribua com este projeto, estabelecemos quatro regras permanentes:

1. **Zero Código Fantasma:** Nenhuma linha de código entra no repositório sem ser lida, compreendida e submetida a testes automatizados que rodam localmente em segundos. Se um módulo não pode ser explicado com clareza ou adiciona complexidade acidental sem ganho mensurável de latência ou memória, ele é descartado.
2. **Contenção no Sistema Operacional Acima de Promessas de Prompt:** Nunca confiamos apenas em instruções de texto para impedir que um modelo apague arquivos ou exfiltre dados. A contenção ocorre no kernel do Linux (`bwrap --unshare-all`), nas validações de segurança do `@dot-auditor`, nas assinaturas `SHA-256` dos pacotes de agentes e na confirmação manual do operador.
3. **Respeito pelo Hardware do Usuário:** Todo recurso novo é medido pelo impacto real em memória RAM, ciclos de CPU ARM64 e ciclos de escrita em disco. Se uma funcionalidade roda bem em um servidor de 64 GB mas degrada um Raspberry Pi 4B de 4 GB, ela é considerada um defeito de engenharia.
4. **Linguagem Direta de Bancada:** Nossa documentação, nossos relatórios e nossos comentários de código são escritos para desenvolvedores reais. Não usamos jargões vazios, adjetivos inflados ou ornamentos visuais desnecessários.

---

*Assinado na arquitetura do projeto por Lyon Christopher, criador e arquiteto do piDots.*
