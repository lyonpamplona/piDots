# Politica de Seguranca (SECURITY)

A seguranca da infraestrutura e o controle deterministico sobre a execucao de ferramentas sao prioridades absolutas no **piDots**. Como a plataforma opera agentes autonomos com capacidade de execucao de comandos em sistemas de borda persistentes, adotamos medidas rigorosas de isolamento em camadas.

---

## 1. Versoes com Suporte Ativo

Correcoes de seguranca sao aplicadas exclusivamente nas seguintes versoes:

| Versao | Status de Suporte |
| :--- | :--- |
| `1.5.x` | Suportada ativamente com correcoes prioritarias de borda |
| `< 1.5.0` | Descontinuada / Nao suportada |

---

## 2. Modelo de Ameacas e Fronteiras de Seguranca

O piDots implementa o principio de defesa em profundidade estruturado em nove barreiras independentes:

### 1. Isolamento via Sandbox Bubblewrap (`bwrap`)
- Comandos de terminal despachados pelos agentes sao executados dentro de namespaces isolados do kernel Linux (`CLONE_NEWNS`, `CLONE_NEWPID`, `CLONE_NEWIPC`, `CLONE_NEWUTS`).
- O sistema operacional hospedeiro e montado com permissao estrita de somente leitura (`ro-bind`).
- Apenas o subdiretorio atribuido ao workspace especifico do agente (`workspaces/<dot_id>`) possui permissao de escrita.
- O parametro `--die-with-parent` impede a persistencia de processos orfaos ou daemons nao autorizados em segundo plano.

### 2. Governanca Human-in-the-Loop (HITL)
- O motor de avaliacao de risco analisa sintaticamente todas as chamadas de ferramentas.
- Comandos que envolvam remocao recursiva (`rm -rf`), elevacao de privilegios (`sudo`, `su`), alteracao de permissoes (`chmod`, `chown`), operacoes de rede de baixo nivel ou reinicializacao do sistema sao retidos imediatamente em fila de governanca.
- Nenhuma acao de risco critico e executada sem a confirmacao explicita do operador humano autenticado via interface web, CLI ou canal assinado.

### 3. Protecao Rigorosa Anti-SSRF (Server-Side Request Forgery)
- A ferramenta `read_web_page` valida os enderecos IP resolvidos por DNS contra faixas de rede privada (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`) e multicast.
- Redirecionamentos HTTP (301, 302, 303, 307, 308) sao inspecionados salto a salto (hop-by-hop), impedindo evasao por open-redirects externos.

### 4. Protecao Anti-Path-Traversal e Symlink Traversal
- Todas as operacoes de arquivo em `file_ops.py` e empacotamento em `spaces_manager.py` aplicam verificacao estrita com `os.path.realpath` e `os.path.commonpath`.
- O acesso fora da arvore autorizada do workspace ou a inclusao de symlinks apontando para arquivos sensiveis do hospedeiro e sumariamente bloqueado.

### 5. Protecao de Segredos e Variaveis de Ambiente
- Chaves de API de provedores de inferencia sao injetadas exclusivamente via variaveis de ambiente ou arquivo `.env`.
- Arquivos `.env`, bancos de dados SQLite com dados transacionais e workspaces de usuarios sao rigorosamente bloqueados no `.gitignore` e no `.dockerignore`, impedindo commit acidental em repositorios publicos.

### 6. Integridade de Assets Estáticos Desacoplados e Cache ETag
- Todos os arquivos estáticos desacoplados (`pages/*.html`, `static/css/*.css`, `static/js/**/*.js`) são servidos com cabeçalhos de defesa `X-Content-Type-Options: nosniff` e validados via ETag SHA-256 no `EdgeAssetManager` em memória RAM, neutralizando adulterações de scripts client-side e contaminação de cache por intermediários.

### 7. Governanca HITL Remota Assinada com HMAC-SHA256
- Autorizacoes remotas via Telegram ou WhatsApp utilizam tokens unívocos assinados com HMAC-SHA256, validados em tempo constante (`hmac.compare_digest`) no endpoint `/api/hitl/signed-resolve`.
- As requisicoes retidas possuem janela de validade temporal (TTL de 30 minutos em `expires_at`). Transcorrido o prazo, o status muda automaticamente para `EXPIRED`, descartando a acao e registrando log de auditoria forense.

### 8. Integridade de Dot Packs v1.1 e Defesa contra Prompt Injection
- Manifestos exportados recebem hash criptografico `sha256_checksum` gerado a partir do conteudo canonico normalizado.
- Na importacao (`POST /api/dots/import-pack`), a integridade do pacote e verificada antes da persistencia e os blocos de `core_memory` sao auditados contra padroes de subversao de instrucao de sistema (Prompt Injection).

### 9. Isolamento Estrito de Terminal (STRICT_SANDBOX)
- Sob a diretiva `STRICT_SANDBOX=true`, a ferramenta de execucao de terminal recusa terminantemente a execucao caso o binario `bwrap` nao esteja disponivel no ambiente, retornando codigo de saida 126 com erro de governanca, impedindo qualquer fallback permissivo em processos desprotegidos.

---

## 3. Reporte Responsavel de Vulnerabilidades

Caso voce identifique uma vulnerabilidade de seguranca no piDots, solicitamos que **nao abra uma issue publica**. Siga o protocolo de divulgacao responsavel:

1. **Canal de Comunicacao:**
   Envie um relatorio confidencial detalhado para o mantenedor do projeto (**lyon christopher**) ou abra um **Security Advisory** privado diretamente na aba de seguranca do repositorio no GitHub.

2. **Informacoes Necessarias no Relatorio:**
   - Descricao clara da vulnerabilidade e seu potencial de impacto.
   - Prova de conceito (PoC) com passos reproduziveis.
   - Versao do piDots, versao do Python e distribuicao Linux utilizada.
   - Indicacao se a vulnerabilidade permite escape de sandbox, evasao da governanca HITL ou exposicao de credenciais.

3. **Prazo de Resposta:**
   - Confirmacao inicial de recebimento: ate **48 horas**.
   - Analise de causa raiz e plano de mitigacao: ate **5 dias uteis**.
   - Publicacao de patch de correcao: coordenado em conjunto com o pesquisador antes de qualquer divulgacao publica.
